import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import torch

from model import MiniTransformerLanguageModel
from tokenizer import MiniDoorTokenizer


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run an overnight token-level MiniDoorLM training session."
    )

    parser.add_argument(
        "--data",
        type=str,
        default="data/training/opendoor_teaching_examples_v2.txt",
        help="Training dataset path.",
    )

    parser.add_argument(
        "--hours",
        type=float,
        default=8.0,
        help="How many hours to train.",
    )

    parser.add_argument(
        "--out",
        type=str,
        default="overnight_minidoorlm_token_transformer.pt",
        help="Final checkpoint path.",
    )

    parser.add_argument(
        "--best-out",
        type=str,
        default="best_overnight_minidoorlm_token_transformer.pt",
        help="Best validation checkpoint path.",
    )

    parser.add_argument(
        "--tokenizer-out",
        type=str,
        default="data/tokenizers/minidoor_tokenizer.json",
        help="Tokenizer output path.",
    )

    parser.add_argument(
        "--log",
        type=str,
        default="overnight_training_log.csv",
        help="Training log path.",
    )

    parser.add_argument(
        "--samples-dir",
        type=str,
        default="training_samples",
        help="Folder for generated sample outputs.",
    )

    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--block-size", type=int, default=48)
    parser.add_argument("--eval-interval", type=int, default=250)
    parser.add_argument("--eval-batches", type=int, default=30)
    parser.add_argument("--sample-interval", type=int, default=500)
    parser.add_argument("--learning-rate", type=float, default=8e-4)
    parser.add_argument("--weight-decay", type=float, default=0.01)

    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-layer", type=int, default=3)
    parser.add_argument("--dropout", type=float, default=0.25)

    parser.add_argument(
        "--patience",
        type=int,
        default=10,
        help="Stop if validation loss fails to improve this many evals in a row.",
    )

    parser.add_argument(
        "--min-delta",
        type=float,
        default=0.001,
        help="Minimum validation improvement needed.",
    )

    parser.add_argument(
        "--keep-running-after-overfit",
        action="store_true",
        help="Keep training even after patience is reached. Best checkpoint is still protected.",
    )

    parser.add_argument("--seed", type=int, default=1337)

    args = parser.parse_args()

    if args.hours <= 0:
        raise ValueError("hours must be greater than 0.")

    if args.batch_size <= 0:
        raise ValueError("batch-size must be greater than 0.")

    if args.block_size <= 0:
        raise ValueError("block-size must be greater than 0.")

    if args.eval_interval <= 0:
        raise ValueError("eval-interval must be greater than 0.")

    if args.eval_batches <= 0:
        raise ValueError("eval-batches must be greater than 0.")

    if args.sample_interval <= 0:
        raise ValueError("sample-interval must be greater than 0.")

    if args.learning_rate <= 0:
        raise ValueError("learning-rate must be greater than 0.")

    if args.n_embd % args.n_head != 0:
        raise ValueError(
            f"n_embd must be divisible by n_head. Got {args.n_embd} and {args.n_head}."
        )

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
            "Dataset is too small for token training.\n"
            f"Train tokens: {len(train_data)}\n"
            f"Validation tokens: {len(val_data)}"
        )

    block_size = min(requested_block_size, max_safe_block)

    if block_size != requested_block_size:
        print(
            f"Requested block_size={requested_block_size}, "
            f"using safer block_size={block_size}."
        )

    return train_data, val_data, block_size


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
            "hours_requested": args.hours,
            "learning_rate": args.learning_rate,
            "weight_decay": args.weight_decay,
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


@torch.no_grad()
def generate_sample(
    model: MiniTransformerLanguageModel,
    tokenizer: MiniDoorTokenizer,
    prompt: str,
    block_size: int,
    device: str,
    max_new_tokens: int = 120,
    temperature: float = 0.7,
    top_k: int = 20,
) -> str:
    model.eval()

    start_tokens = tokenizer.encode(prompt)

    if not start_tokens:
        return "Prompt produced no tokens."

    idx = torch.tensor([start_tokens], dtype=torch.long, device=device)

    for _ in range(max_new_tokens):
        idx_cond = idx[:, -block_size:]

        logits, loss = model(idx_cond)
        logits = logits[:, -1, :]

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

        current_text = tokenizer.decode(idx[0].tolist())

        if "<END>" in current_text:
            break

    output = tokenizer.decode(idx[0].tolist())

    if "<END>" in output:
        output = output.split("<END>")[0].rstrip()

    model.train()
    return output


def write_sample_file(
    samples_dir: Path,
    step: int,
    train_loss: float,
    val_loss: float,
    samples: Dict[str, str],
):
    samples_dir.mkdir(parents=True, exist_ok=True)

    sample_file = samples_dir / f"sample_step_{step}.md"

    lines = [
        f"# MiniDoorLM Overnight Sample",
        "",
        f"Step: {step}",
        f"Train loss: {train_loss:.4f}",
        f"Validation loss: {val_loss:.4f}",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    for prompt, output in samples.items():
        lines.append("## Prompt")
        lines.append("")
        lines.append("```text")
        lines.append(prompt)
        lines.append("```")
        lines.append("")
        lines.append("## Output")
        lines.append("")
        lines.append("```text")
        lines.append(output)
        lines.append("```")
        lines.append("")

    sample_file.write_text("\n".join(lines), encoding="utf-8")


def main():
    args = parse_args()
    torch.manual_seed(args.seed)

    training_file = Path(args.data)
    final_output_file = Path(args.out)
    best_output_file = Path(args.best_out)
    tokenizer_output_file = Path(args.tokenizer_out)
    log_file = Path(args.log)
    samples_dir = Path(args.samples_dir)

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

    if dataset_stats["user_examples"] < 50:
        print("")
        print("WARNING")
        print("-------")
        print(
            "Dataset has fewer than 50 examples. Overnight training may overfit. "
            "Best checkpoint saving is enabled to protect the best model."
        )
        print("")

    def get_batch(split: str):
        source = train_data if split == "train" else val_data

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

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )

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
    print("Overnight Token Training")
    print("------------------------")
    print(f"Device: {device}")
    print(f"Training file: {training_file}")
    print(f"Hours: {args.hours}")
    print(f"Characters: {dataset_stats['characters']}")
    print(f"Tokens: {dataset_stats['tokens']}")
    print(f"Vocabulary size: {tokenizer.vocab_size()}")
    print(f"User examples: {dataset_stats['user_examples']}")
    print(f"OpenDoor examples: {dataset_stats['opendoor_examples']}")
    print(f"<END> tokens: {dataset_stats['end_tokens']}")
    print(f"Train tokens: {len(train_data)}")
    print(f"Validation tokens: {len(val_data)}")
    print(f"Block size: {block_size}")
    print(f"Batch size: {args.batch_size}")
    print(f"Learning rate: {args.learning_rate}")
    print(f"Weight decay: {args.weight_decay}")
    print(f"Dropout: {args.dropout}")
    print(f"Best checkpoint: {best_output_file}")
    print(f"Final checkpoint: {final_output_file}")
    print("")

    start_time = time.time()
    max_seconds = args.hours * 60 * 60

    training_log = []
    best_val_loss = float("inf")
    best_step = 0
    bad_eval_count = 0

    step = 0
    last_train_loss = float("nan")
    last_val_loss = float("nan")

    prompts = [
        "User: Teach me Python as a beginner.\nOpenDoor:",
        "User: Teach me how to build a telescope.\nOpenDoor:",
        "User: Teach me cybersecurity basics.\nOpenDoor:",
    ]

    while True:
        elapsed = time.time() - start_time

        if elapsed >= max_seconds:
            print("Time limit reached.")
            break

        if step % args.eval_interval == 0:
            losses = estimate_loss()
            train_loss = losses["train"].item()
            val_loss = losses["val"].item()

            last_train_loss = train_loss
            last_val_loss = val_loss

            improved = val_loss < best_val_loss - args.min_delta

            if improved:
                best_val_loss = val_loss
                best_step = step
                bad_eval_count = 0

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
                f"val loss {val_loss:.4f}, best={best_marker}, "
                f"bad_evals={bad_eval_count}, elapsed={elapsed / 3600:.2f}h"
            )

            training_log.append(
                {
                    "step": step,
                    "train_loss": train_loss,
                    "val_loss": val_loss,
                    "is_best": best_marker,
                    "best_val_loss": best_val_loss,
                    "bad_eval_count": bad_eval_count,
                    "elapsed_hours": round(elapsed / 3600, 4),
                }
            )

            if bad_eval_count >= args.patience and not args.keep_running_after_overfit:
                print(
                    "Early stopping triggered. "
                    "Use --keep-running-after-overfit if you still want the run to continue."
                )
                break

        if step % args.sample_interval == 0:
            sample_outputs = {}

            for prompt in prompts:
                sample_outputs[prompt] = generate_sample(
                    model=model,
                    tokenizer=tokenizer,
                    prompt=prompt,
                    block_size=block_size,
                    device=device,
                )

            write_sample_file(
                samples_dir=samples_dir,
                step=step,
                train_loss=last_train_loss,
                val_loss=last_val_loss,
                samples=sample_outputs,
            )

        xb, yb = get_batch("train")

        logits, loss = model(xb, yb)

        optimizer.zero_grad(set_to_none=True)
        loss.backward()

        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()

        step += 1

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
                "elapsed_hours",
            ],
        )
        writer.writeheader()
        writer.writerows(training_log)

    print("")
    print("Overnight training complete.")
    print(f"Total steps: {step}")
    print(f"Best validation loss: {best_val_loss:.4f}")
    print(f"Best step: {best_step}")
    print(f"Saved best model to {best_output_file}")
    print(f"Saved final model to {final_output_file}")
    print(f"Saved tokenizer to {tokenizer_output_file}")
    print(f"Saved log to {log_file}")
    print(f"Saved samples to {samples_dir}")


if __name__ == "__main__":
    main()