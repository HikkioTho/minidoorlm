import argparse
from pathlib import Path
from typing import Dict, List

import torch

from model import MiniTransformerLanguageModel


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate text from a trained MiniDoorLM checkpoint."
    )

    parser.add_argument(
        "--checkpoint",
        type=str,
        default="minidoorlm_transformer.pt",
        help="Path to the model checkpoint.",
    )

    parser.add_argument(
        "--prompt",
        type=str,
        default="User: Teach me quantum physics from beginner level.\nOpenDoor:",
        help="Prompt to start generation.",
    )

    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=300,
        help="Number of new characters to generate.",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature. Lower is safer, higher is wilder.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="Only sample from the top K most likely characters.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=1337,
        help="Random seed for repeatable generation.",
    )

    return parser.parse_args()


def load_checkpoint(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {path}\n"
            "Train the model first with python train.py."
        )

    checkpoint = torch.load(path, map_location="cpu")

    required_keys = [
        "model_state_dict",
        "chars",
        "vocab_size",
        "block_size",
        "n_embd",
        "n_head",
        "n_layer",
        "dropout",
    ]

    for key in required_keys:
        if key not in checkpoint:
            raise KeyError(f"Checkpoint is missing required key: {key}")

    return checkpoint


def build_token_maps(chars: List[str]):
    stoi = {ch: i for i, ch in enumerate(chars)}
    itos = {i: ch for i, ch in enumerate(chars)}

    return stoi, itos


def encode_prompt(prompt: str, stoi: Dict[str, int]) -> List[int]:
    encoded = []

    for char in prompt:
        if char in stoi:
            encoded.append(stoi[char])
        else:
            # Skip unknown characters instead of crashing.
            # This matters because the tiny model only knows characters from training.
            continue

    if not encoded:
        raise ValueError(
            "Prompt could not be encoded because none of its characters exist in the model vocabulary."
        )

    return encoded


def decode_tokens(tokens: List[int], itos: Dict[int, str]) -> str:
    return "".join(itos[token] for token in tokens)


@torch.no_grad()
def generate_text(
    model,
    start_tokens: List[int],
    itos: Dict[int, str],
    block_size: int,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    device: str,
) -> str:
    model.eval()

    idx = torch.tensor([start_tokens], dtype=torch.long, device=device)

    for _ in range(max_new_tokens):
        idx_cond = idx[:, -block_size:]

        logits, loss = model(idx_cond)

        logits = logits[:, -1, :]

        if temperature <= 0:
            next_token = torch.argmax(logits, dim=-1, keepdim=True)
        else:
            logits = logits / temperature

            if top_k > 0:
                values, indices = torch.topk(logits, top_k)
                filtered_logits = torch.full_like(logits, float("-inf"))
                filtered_logits.scatter_(1, indices, values)
                logits = filtered_logits

            probs = torch.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)

        idx = torch.cat((idx, next_token), dim=1)

    output_tokens = idx[0].tolist()
    return decode_tokens(output_tokens, itos)


def print_checkpoint_report(checkpoint_path: Path, checkpoint):
    metadata = checkpoint.get("metadata", {})

    print("")
    print("Checkpoint Report")
    print("-----------------")
    print(f"Checkpoint: {checkpoint_path}")
    print(f"Vocab size: {checkpoint['vocab_size']}")
    print(f"Block size: {checkpoint['block_size']}")
    print(f"Embedding size: {checkpoint['n_embd']}")
    print(f"Heads: {checkpoint['n_head']}")
    print(f"Layers: {checkpoint['n_layer']}")

    if metadata:
        print(f"Training file: {metadata.get('training_file', 'unknown')}")
        print(f"Dataset chars: {metadata.get('dataset_character_count', 'unknown')}")
        print(f"User examples: {metadata.get('user_examples', 'unknown')}")
        print(f"OpenDoor examples: {metadata.get('opendoor_examples', 'unknown')}")
        print(f"Trained at: {metadata.get('trained_at', 'unknown')}")

    print("")


def main():
    args = parse_args()

    torch.manual_seed(args.seed)

    checkpoint_path = Path(args.checkpoint)
    checkpoint = load_checkpoint(checkpoint_path)

    print_checkpoint_report(checkpoint_path, checkpoint)

    chars = checkpoint["chars"]
    stoi, itos = build_token_maps(chars)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = MiniTransformerLanguageModel(
        vocab_size=checkpoint["vocab_size"],
        block_size=checkpoint["block_size"],
        n_embd=checkpoint["n_embd"],
        n_head=checkpoint["n_head"],
        n_layer=checkpoint["n_layer"],
        dropout=checkpoint["dropout"],
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)

    start_tokens = encode_prompt(args.prompt, stoi)

    output = generate_text(
        model=model,
        start_tokens=start_tokens,
        itos=itos,
        block_size=checkpoint["block_size"],
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        device=device,
    )

    print("Generated Text")
    print("--------------")
    print(output)


if __name__ == "__main__":
    main()