import csv
import torch
from model import MiniTransformerLanguageModel


# Training settings
batch_size = 4
block_size = 8
max_iters = 1500
eval_interval = 100
learning_rate = 1e-3
device = "cuda" if torch.cuda.is_available() else "cpu"

# Model settings
n_embd = 64
n_head = 4
n_layer = 2
dropout = 0.2


# Load training text
with open("data/input.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Create vocabulary from unique characters
chars = sorted(list(set(text)))
vocab_size = len(chars)

# Character mappings
stoi = {ch: i for i, ch in enumerate(chars)}
itos = {i: ch for i, ch in enumerate(chars)}

encode = lambda s: [stoi[c] for c in s]
decode = lambda nums: "".join([itos[i] for i in nums])

# Convert text into tensor data
data = torch.tensor(encode(text), dtype=torch.long)

# Split into train and validation data
n = int(0.9 * len(data))
train_data = data[:n]
val_data = data[n:]


def get_batch(split):
    source = train_data if split == "train" else val_data

    # Make sure the source is large enough for block_size.
    if len(source) <= block_size:
        raise ValueError(
            f"{split} data is too small for block_size={block_size}. "
            f"Add more text to data/input.txt or lower block_size."
        )

    ix = torch.randint(len(source) - block_size, (batch_size,))

    x = torch.stack([source[i:i + block_size] for i in ix])
    y = torch.stack([source[i + 1:i + block_size + 1] for i in ix])

    x = x.to(device)
    y = y.to(device)

    return x, y


@torch.no_grad()
def estimate_loss():
    out = {}
    model.eval()

    for split in ["train", "val"]:
        losses = torch.zeros(eval_interval)

        for k in range(eval_interval):
            x, y = get_batch(split)
            logits, loss = model(x, y)
            losses[k] = loss.item()

        out[split] = losses.mean()

    model.train()
    return out


model = MiniTransformerLanguageModel(
    vocab_size=vocab_size,
    block_size=block_size,
    n_embd=n_embd,
    n_head=n_head,
    n_layer=n_layer,
    dropout=dropout,
)

model = model.to(device)

optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

print(f"Training on: {device}")
print(f"Vocabulary size: {vocab_size}")
print("Starting transformer training...")

training_log = []

for step in range(max_iters):
    if step % eval_interval == 0:
        losses = estimate_loss()

        train_loss = losses["train"].item()
        val_loss = losses["val"].item()

        print(
            f"step {step}: train loss {train_loss:.4f}, "
            f"val loss {val_loss:.4f}"
        )

        training_log.append({
            "step": step,
            "train_loss": train_loss,
            "val_loss": val_loss,
        })

    xb, yb = get_batch("train")

    logits, loss = model(xb, yb)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()

# Save model checkpoint
torch.save(
    {
        "model_state_dict": model.state_dict(),
        "chars": chars,
        "vocab_size": vocab_size,
        "block_size": block_size,
        "n_embd": n_embd,
        "n_head": n_head,
        "n_layer": n_layer,
        "dropout": dropout,
    },
    "minidoorlm_transformer.pt"
)

# Save training log for visualization
with open("training_log.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["step", "train_loss", "val_loss"])
    writer.writeheader()
    writer.writerows(training_log)

print("Saved training log to training_log.csv")
print("Transformer training complete.")
print("Saved model to minidoorlm_transformer.pt")