import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Tuple

import torch

from model import MiniTransformerLanguageModel


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train MiniDoorLM on an OpenDoor-style text dataset."
    )

    parser.add_argument(
        "--data",
        type=str,
        default="data/training/opendoor_teaching_examples.txt",
        help="Path to the training text file.",
    )

    parser.add_argument(
        "--out",
        type=str,
        default="minidoorlm_transformer.pt",
        help="Path where the trained model checkpoint will be saved.",
    )

    parser.add_argument(
        "--log",
        type=str,
        default="training_log.csv",
        help="Path where the training loss log will be saved.",
    )

    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--block-size", type=int, default=64)
    parser.add_argument("--max-iters", type=int, default=3000)
    parser.add_argument("--eval-interval", type=int, default=200)
    parser.add_argument("--eval-batches", type=int, default=40)
    parser.add_argument("--learning-rate", type=float, default=1e-3)

    parser.add_argument("--n-embd", type=int, default=96)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-layer", type=int, default=3)
    parser.add_argument("--dropout", type=float, default=0.2)

    parser.add_argument("--seed", type=int, default=1337)

    return parser.parse_args()


def load_training_text(training_file: Path) -> str:
    if not training_file.exists():
        raise FileNotFoundError(
            f"Training file not found: {training_file}\n"
            "Create the file or pass a valid path with --data."
        )

    text = training_file.read_text(encoding="utf-8")

    if not text.strip():
        raise ValueError(
            f"Training file is empty: {training_file}\n"
            "Add OpenDoor training examples before training."
        )

    return text


def build_vocab(
    text: str,
) -> Tuple[List[str], int, Callable[[str], List[int]], Callable[[List[int]], str]]:
    chars = sorted(list(set(text)))
    vocab_size = len(chars)

    stoi = {ch: i for i, ch in enumerate(chars)}
    itos = {i: ch for i, ch in enumerate(chars)}

    def encode(s: str) -> List[int]:
        return [stoi[c] for c in s]

    def decode(nums: List[int]) -> str:
        return "".join([itos[i] for i in nums])

    return chars, vocab_size, encode, decode


def print_dataset_report(text: str, training_file: Path, vocab_size: int):
    line_count = len(text.splitlines())
    user_examples = text.count("User:")
    opendoor_examples = text.count("OpenDoor:")
    active_recall_examples = text.count("Active Recall:")

    print("")
    print("Dataset Health Report")
    print("---------------------")
    print(f"Training file: {training_file}")
    print(f"Characters: {len(text)}")
    print(f"Lines: {line_count}")
    print(f"Vocabulary size: {vocab_size}")
    print(f"User examples: {user_examples}")
    print(f"OpenDoor examples: {opendoor_examples}")
    print(f"Active Recall examples: {active_recall_examples}")

    if user_examples == 0:
        print("Warning: no 'User:' examples found.")

    if opendoor_examples == 0:
        print("Warning: no 'OpenDoor:' examples found.")

    if active_recall_examples == 0:
        print("Warning: no 'Active Recall:' prompts found.")

    print("")


def split_data(data: torch.Tensor, requested_block_size: int):
    n = int(0.9 * len(data))

    train_data = data[:n]
    val_data = data[n:]

    max_safe_block = min(len(train_data) - 2, len(val_data) - 2)

    if max_safe_block < 8:
        raise ValueError(
            "Dataset is too small to train safely.\n"
            f"Train tokens: {len(train_data)}\n"
            f"Validation tokens: {len(val_data)}\n"
            "Add more examples to the dataset."
        )

    actual_block_size = min(requested_block_size, max_safe_block)

    if actual_block_size != requested_block_size:
        print(
            f"Requested block_size={requested_block_size}, "
            f"but dataset only supports block_size={actual_block_size}."
        )

    return train_data, val_data, actual_block_size


def validate_model_settings(n_embd: int, n_head: int):
    if n_embd % n_head != 0:
        raise ValueError(
            "n_embd must be divisible by n_head.\n"
            f"Got n_embd={n_embd}, n_head={n_head}."
        )


def main():
    args = parse_args()

    validate_model_settings(args.n_embd, args.n_head)

    torch.manual_seed(args.seed)

    training_file = Path(args.data)
    output_file = Path(args.out)
    log_file = Path(args.log)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    text = load_training_text(training_file)
    chars, vocab_size, encode, decode = build_vocab(text)

    print_dataset_report(text, training_file, vocab_size)

    data = torch.tensor(encode(text), dtype=torch.long)
    train_data, val_data, block_size = split_data(data, args.block_size)

    def get_batch(split: str):
        source = train_data if split == "train" else val_data

        ix = torch.randint(len(source) - block_size, (args.batch_size,))

        x = torch.stack([source[i:i + block_size] for i in ix])
        y = torch.stack([source[i + 1:i + block_size + 1] for i in ix])

        x = x.to(device)
        y = y.to(device)

        return x, y

    model = MiniTransformerLanguageModel(
        vocab_size=vocab_size,
        block_size=block_size,
        n_embd=args.n_embd,
        n_head=args.n_head,
        n_layer=args.n_layer,
        dropout=args.dropout,
    )

    model = model.to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
    )

    @torch.no_grad()
    def estimate_loss():
        out = {}
        model.eval()

        for split in ["train", "val"]:
            losses = torch.zeros(args.eval_batches)

            for k in range(args.eval_batches):
                x, y = get_batch(split)
                logits, loss = model(x, y)
                losses[k] = loss.item()

            out[split] = losses.mean()

        model.train()
        return out

    print("Training Setup")
    print("--------------")
    print(f"Device: {device}")
    print(f"Train tokens: {len(train_data)}")
    print(f"Validation tokens: {len(val_data)}")
    print(f"Block size: {block_size}")
    print(f"Batch size: {args.batch_size}")
    print(f"Max iterations: {args.max_iters}")
    print(f"Learning rate: {args.learning_rate}")
    print(f"Embedding size: {args.n_embd}")
    print(f"Heads: {args.n_head}")
    print(f"Layers: {args.n_layer}")
    print(f"Dropout: {args.dropout}")
    print("")
    print("Starting OpenDoor-style transformer training...")

    training_log = []

    for step in range(args.max_iters):
        if step % args.eval_interval == 0:
            losses = estimate_loss()

            train_loss = losses["train"].item()
            val_loss = losses["val"].item()

            print(
                f"step {step}: train loss {train_loss:.4f}, "
                f"val loss {val_loss:.4f}"
            )

            training_log.append(
                {
                    "step": step,
                    "train_loss": train_loss,
                    "val_loss": val_loss,
                }
            )

        xb, yb = get_batch("train")

        logits, loss = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "chars": chars,
        "vocab_size": vocab_size,
        "block_size": block_size,
        "n_embd": args.n_embd,
        "n_head": args.n_head,
        "n_layer": args.n_layer,
        "dropout": args.dropout,
        "metadata": {
            "training_file": str(training_file),
            "output_file": str(output_file),
            "dataset_character_count": len(text),
            "dataset_line_count": len(text.splitlines()),
            "user_examples": text.count("User:"),
            "opendoor_examples": text.count("OpenDoor:"),
            "active_recall_examples": text.count("Active Recall:"),
            "max_iters": args.max_iters,
            "eval_interval": args.eval_interval,
            "eval_batches": args.eval_batches,
            "learning_rate": args.learning_rate,
            "batch_size": args.batch_size,
            "block_size": block_size,
            "requested_block_size": args.block_size,
            "n_embd": args.n_embd,
            "n_head": args.n_head,
            "n_layer": args.n_layer,
            "dropout": args.dropout,
            "seed": args.seed,
            "trained_at": datetime.now(timezone.utc).isoformat(),
        },
    }

    torch.save(checkpoint, output_file)

    with log_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["step", "train_loss", "val_loss"],
        )
        writer.writeheader()
        writer.writerows(training_log)

    print("")
    print("Training complete.")
    print(f"Saved model to {output_file}")
    print(f"Saved training log to {log_file}")
    print(f"Checkpoint metadata saved inside {output_file}")


if __name__ == "__main__":
    main()