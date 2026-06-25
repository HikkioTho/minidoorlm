import argparse
from pathlib import Path
from typing import List

import torch

from model import MiniTransformerLanguageModel
from tokenizer import MiniDoorTokenizer


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate text from a token-level MiniDoorLM checkpoint."
    )

    parser.add_argument(
        "--checkpoint",
        type=str,
        default="best_minidoorlm_token_transformer.pt",
        help="Path to token model checkpoint.",
    )

    parser.add_argument(
        "--tokenizer",
        type=str,
        default="data/tokenizers/minidoor_tokenizer.json",
        help="Path to tokenizer JSON file.",
    )

    parser.add_argument(
        "--prompt",
        type=str,
        default="User: Teach me Python as a beginner.\nOpenDoor:",
        help="Prompt to start generation.",
    )

    parser.add_argument("--max-new-tokens", type=int, default=120)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--stop-token", type=str, default="<END>")
    parser.add_argument("--seed", type=int, default=1337)

    args = parser.parse_args()

    if args.max_new_tokens <= 0:
        raise ValueError("max-new-tokens must be greater than 0.")

    if args.temperature < 0:
        raise ValueError("temperature must be 0 or greater.")

    if args.top_k < 0:
        raise ValueError("top-k must be 0 or greater.")

    return args


def normalize_prompt(prompt: str) -> str:
    return prompt.replace("\\n", "\n")


def load_checkpoint(path: Path):
    if not path.exists():
        fallback = Path("minidoorlm_token_transformer.pt")

        if path.name == "best_minidoorlm_token_transformer.pt" and fallback.exists():
            print(
                "Warning: best token checkpoint not found. "
                "Falling back to minidoorlm_token_transformer.pt."
            )
            path = fallback
        else:
            raise FileNotFoundError(
                f"Token checkpoint not found: {path}\n"
                "Train with python train_tokens.py first."
            )

    checkpoint = torch.load(path, map_location="cpu")

    required_keys = [
        "model_state_dict",
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

    return path, checkpoint


@torch.no_grad()
def generate_token_text(
    model: MiniTransformerLanguageModel,
    start_tokens: List[int],
    tokenizer: MiniDoorTokenizer,
    block_size: int,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    stop_token: str,
    device: str,
) -> str:
    model.eval()

    idx = torch.tensor([start_tokens], dtype=torch.long, device=device)

    for _ in range(max_new_tokens):
        idx_cond = idx[:, -block_size:]

        logits, loss = model(idx_cond)
        logits = logits[:, -1, :]

        if temperature == 0:
            next_token = torch.argmax(logits, dim=-1, keepdim=True)
        else:
            logits = logits / temperature

            if top_k > 0:
                safe_top_k = min(top_k, logits.size(-1))
                values, indices = torch.topk(logits, safe_top_k)

                filtered_logits = torch.full_like(logits, float("-inf"))
                filtered_logits.scatter_(1, indices, values)
                logits = filtered_logits

            probabilities = torch.softmax(logits, dim=-1)
            next_token = torch.multinomial(probabilities, num_samples=1)

        idx = torch.cat((idx, next_token), dim=1)

        current_output = tokenizer.decode(idx[0].tolist())

        if stop_token and stop_token in current_output:
            break

    text = tokenizer.decode(idx[0].tolist())

    if stop_token and stop_token in text:
        text = text.split(stop_token)[0].rstrip()

    return text


def print_checkpoint_report(path: Path, checkpoint):
    metadata = checkpoint.get("metadata", {})

    print("")
    print("Token Checkpoint Report")
    print("-----------------------")
    print(f"Checkpoint: {path}")
    print(f"Checkpoint type: {metadata.get('checkpoint_type', 'unknown')}")
    print(f"Vocab size: {checkpoint['vocab_size']}")
    print(f"Block size: {checkpoint['block_size']}")
    print(f"Embedding size: {checkpoint['n_embd']}")
    print(f"Heads: {checkpoint['n_head']}")
    print(f"Layers: {checkpoint['n_layer']}")
    print(f"Training file: {metadata.get('training_file', 'unknown')}")
    print(f"Dataset tokens: {metadata.get('dataset_token_count', 'unknown')}")
    print(f"Best val loss: {metadata.get('best_val_loss', 'unknown')}")
    print(f"Saved at step: {metadata.get('saved_at_step', 'unknown')}")
    print("")


def main():
    args = parse_args()
    torch.manual_seed(args.seed)

    checkpoint_path, checkpoint = load_checkpoint(Path(args.checkpoint))
    tokenizer = MiniDoorTokenizer.load(args.tokenizer)

    print_checkpoint_report(checkpoint_path, checkpoint)

    prompt = normalize_prompt(args.prompt)
    start_tokens = tokenizer.encode(prompt)

    if not start_tokens:
        raise ValueError("Prompt produced no tokens.")

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

    output = generate_token_text(
        model=model,
        start_tokens=start_tokens,
        tokenizer=tokenizer,
        block_size=checkpoint["block_size"],
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        stop_token=args.stop_token,
        device=device,
    )

    print("Generated Token Text")
    print("--------------------")
    print(output)


if __name__ == "__main__":
    main()