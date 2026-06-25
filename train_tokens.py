import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import torch

from model import MiniTransformerLanguageModel
from tokenizer import MiniDoorTokenizer


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train token-level MiniDoorLM."
    )

    parser.add_argument(
        "--data",
        type=str,
        default="data/training/opendoor_teaching_examples_v2.txt",
        help="Path to training dataset.",
    )

    parser.add_argument(
        "--out",
        type=str,
        default="minidoorlm_token_transformer.pt",
        help="Path for final token model checkpoint.",
    )

    parser.add_argument(
        "--best-out",
        type=str,
        default="best_minidoorlm_token_transformer.pt",
        help="Path for best validation token model checkpoint.",
    )

    parser.add_argument(
        "--tokenizer-out",
        type=str,
        default="data/tokenizers/minidoor_tokenizer.json",
        help="Path to save tokenizer vocabulary.",
    )

    parser.add_argument(
        "--log",
        type=str,
        default="training_tokens_log.csv",
        help="Path to token training loss log.",
    )

    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--block-size", type=int, default=48)
    parser.add_argument("--max-iters", type=int, default=800)
    parser.add_argument("--eval-interval", type=int, default=100)
    parser.add_argument("--eval-batches", type=int, default=30)
    parser.add_argument("--learning-rate", type=float, default=1e-3)

    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-layer", type=int, default=3)
    parser.add_argument("--dropout", type=float, default=0.2)

    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--min-delta", type=float, default=0.001)
    parser.add_argument("--seed", type=int, default=1337)

    args = parser.parse_args()

    if args.n_embd % args.n_head != 0:
        raise ValueError(
            f"n_embd must be divisible by n_head. Got {args.n_embd} and {args.n_head}."
        )

    if args.batch_size <= 0:
        raise ValueError("batch-size must be greater than 0.")

    if args.block_size <= 0:
        raise ValueError("block-size must be greater than 0.")

    if args.max_iters <= 0:
        raise ValueError("max-iters must be greater than 0.")

    if args.eval_interval <= 0:
        raise ValueError("eval-interval must be greater than 0.")

    if args.eval_batches <= 0:
        raise ValueError("eval-batches must be greater than 0.")

    return args


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Training file not found: {path}")

    text = path.read_text(encoding="utf-8")

    if not text.strip():
        raise ValueError(f"Training file is empty: {path}")

    return text


def split_data(data: torch.Tensor, requested_block_size: int):
    split_index = int(0.9 * len(data))

    train_data = data[:split_index]
    val_data = data[split_index:]

    max_safe_block = min(len(train_data) - 2, len(val_data) - 2)

    if max_safe_block < 8:
        raise ValueError(
            "Token dataset is too small to train safely.\n"
            f"Train tokens: {len(train_data)}\n"
            f"Validation tokens: {len(val_data)}"
        )

    actual_block_size = min(requested_block_size, max_safe_block)

    if actual_block_size != requested_block_size:
        print(
            f"Requested block_size={requested_block_size}, "
            f"but token dataset only supports block_size={actual_block_size}."
        )

    return train_data, val_data, actual_block_size


def save_checkpoint(
    output_file: Path,
    model: MiniTransformerLanguageModel,
    args,
    vocab_size: int,
    block_size: int,
    tokenizer_path: str,
    training_file: Path,
    dataset_stats: Dict[str, int],
    best_val_loss: float,
    step: int,
    checkpoint_type: str,
):
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "vocab_size": vocab_size,
        "block_size": block_size,
        "n_embd": args.n_embd,
        "n_head": args.n_head,
        "n_layer": args.n_layer,
        "dropout": args.dropout,
        "tokenizer_path": tokenizer_path,
        "metadata": {
            "checkpoint_type": checkpoint_type,
            "training_file": str(training_file),
            "tokenizer_path": tokenizer_path,
            "dataset_character_count": dataset_stats["characters"],
            "dataset_token_count": dataset_stats["tokens"],
            "user_examples": dataset_stats["user_examples"],
            "opendoor_examples": dataset_stats["opendoor_examples"],
            "end_tokens": dataset_stats["end_tokens"],
            "vocab_size": vocab_size,
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
            "best_val_loss": best_val_loss,
            "saved_at_step": step,
            "trained_at": datetime.now(timezone.utc).isoformat(),
        },
    }

    torch.save(checkpoint, output_file)


def main():
    args = parse_args()
    torch.manual_seed(args.seed)

    training_file = Path(args.data)
    final_output_file = Path(args.out)
    best_output_file = Path(args.best_out)
    tokenizer_output_file = Path(args.tokenizer_out)
    log_file = Path(args.log)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    text = load_text(training_file)

    tokenizer = MiniDoorTokenizer()
    tokenizer.train_from_text(text)
    tokenizer.save(str(tokenizer_output_file))

    encoded = tokenizer.encode(text)
    data = torch.tensor(encoded, dtype=torch.long)

    dataset_stats = {
        "characters": len(text),
        "tokens": len(encoded),
        "user_examples": text.count("User:"),
        "opendoor_examples": text.count("OpenDoor:"),
        "end_tokens": text.count("<END>"),
    }

    train_data, val_data, block_size = split_data(data, args.block_size)

    def get_batch(split: str):
        source = train_data if split == "train" else val_data

        if len(source) <= block_size:
            raise ValueError(
                f"{split} data is too small for block_size={block_size}."
            )

        starts = torch.randint(
            len(source) - block_size,
            (args.batch_size,),
        )

        x = torch.stack(
            [source[start:start + block_size] for start in starts]
        )
        y = torch.stack(
            [source[start + 1:start + block_size + 1] for start in starts]
        )

        return x.to(device), y.to(device)

    model = MiniTransformerLanguageModel(
        vocab_size=tokenizer.vocab_size(),
        block_size=block_size,
        n_embd=args.n_embd,
        n_head=args.n_head,
        n_layer=args.n_layer,
        dropout=args.dropout,
    )

    model = model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    @torch.no_grad()
    def estimate_loss():
        results = {}
        model.eval()

        for split in ["train", "val"]:
            losses = torch.zeros(args.eval_batches)

            for batch_index in range(args.eval_batches):
                x, y = get_batch(split)
                logits, loss = model(x, y)
                losses[batch_index] = loss.item()

            results[split] = losses.mean()

        model.train()
        return results

    print("")
    print("Token Dataset Health Report")
    print("---------------------------")
    print(f"Training file: {training_file}")
    print(f"Characters: {dataset_stats['characters']}")
    print(f"Tokens: {dataset_stats['tokens']}")
    print(f"Vocabulary size: {tokenizer.vocab_size()}")
    print(f"User examples: {dataset_stats['user_examples']}")
    print(f"OpenDoor examples: {dataset_stats['opendoor_examples']}")
    print(f"<END> tokens: {dataset_stats['end_tokens']}")
    print(f"Tokenizer saved to: {tokenizer_output_file}")
    print("")

    print("Token Training Setup")
    print("--------------------")
    print(f"Device: {device}")
    print(f"Train tokens: {len(train_data)}")
    print(f"Validation tokens: {len(val_data)}")
    print(f"Block size: {block_size}")
    print(f"Batch size: {args.batch_size}")
    print(f"Max iterations: {args.max_iters}")
    print(f"Eval interval: {args.eval_interval}")
    print(f"Learning rate: {args.learning_rate}")
    print(f"Embedding size: {args.n_embd}")
    print(f"Heads: {args.n_head}")
    print(f"Layers: {args.n_layer}")
    print(f"Dropout: {args.dropout}")
    print("")

    training_log = []
    best_val_loss = float("inf")
    bad_eval_count = 0
    best_step = 0
    stopped_early = False
    step = 0

    print("Starting token-level MiniDoorLM training...")

    for step in range(args.max_iters + 1):
        if step % args.eval_interval == 0:
            losses = estimate_loss()

            train_loss = losses["train"].item()
            val_loss = losses["val"].item()

            improved = val_loss < best_val_loss - args.min_delta

            if improved:
                best_val_loss = val_loss
                bad_eval_count = 0
                best_step = step

                save_checkpoint(
                    output_file=best_output_file,
                    model=model,
                    args=args,
                    vocab_size=tokenizer.vocab_size(),
                    block_size=block_size,
                    tokenizer_path=str(tokenizer_output_file),
                    training_file=training_file,
                    dataset_stats=dataset_stats,
                    best_val_loss=best_val_loss,
                    step=step,
                    checkpoint_type="best_validation",
                )

                best_marker = "yes"
            else:
                bad_eval_count += 1
                best_marker = "no"

            print(
                f"step {step}: train loss {train_loss:.4f}, "
                f"val loss {val_loss:.4f}, best={best_marker}"
            )

            training_log.append(
                {
                    "step": step,
                    "train_loss": train_loss,
                    "val_loss": val_loss,
                    "is_best": best_marker,
                    "best_val_loss": best_val_loss,
                    "bad_eval_count": bad_eval_count,
                }
            )

            if bad_eval_count >= args.patience:
                print(
                    "Early stopping triggered: "
                    f"validation did not improve for {args.patience} eval rounds."
                )
                stopped_early = True
                break

        if step == args.max_iters:
            break

        xb, yb = get_batch("train")

        logits, loss = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    save_checkpoint(
        output_file=final_output_file,
        model=model,
        args=args,
        vocab_size=tokenizer.vocab_size(),
        block_size=block_size,
        tokenizer_path=str(tokenizer_output_file),
        training_file=training_file,
        dataset_stats=dataset_stats,
        best_val_loss=best_val_loss,
        step=step,
        checkpoint_type="final",
    )

    with log_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "step",
                "train_loss",
                "val_loss",
                "is_best",
                "best_val_loss",
                "bad_eval_count",
            ],
        )
        writer.writeheader()
        writer.writerows(training_log)

    print("")
    print("Token training complete.")
    print(f"Stopped early: {stopped_early}")
    print(f"Best validation loss: {best_val_loss:.4f}")
    print(f"Best step: {best_step}")
    print(f"Saved best model to {best_output_file}")
    print(f"Saved final model to {final_output_file}")
    print(f"Saved token training log to {log_file}")
    print(f"Saved tokenizer to {tokenizer_output_file}")


if __name__ == "__main__":
    main()