import torch
from model import BigramLanguageModel


# Training Settings

batch_size = 4
block_size = 8
max_iters = 1000
eval_interval = 100
learning_rate = 1e-2
device  = 'cuda' if torch.cuda.is_available() else 'cpu'


with open("data/input.txt", "r", encoding="utf- 8") as f:
    text = f.read()

chars = sorted(list(set(text)))
vocab_size = len(chars)

# Character to number and number to character mappings
stoi = { ch: i for i,  ch in enumerate(chars)}
itos = { i: ch for i, ch in enumerate(chars)}

encode = lambda s: [stoi[c] for c in s]
decode = lambda nums: "".join([itos[i] for i in nums])

data = torch.tensor(encode(text), dtype=torch.long)

# Split into train and validation sets
n = int (0.9 *  len(data))
train_data = data[:n]
val_data = data[n:]

def get_batch(split):
    source = train_data if split == "train" else val_data

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

        for k in range (eval_interval):
            x, y = get_batch(split)
            logits, loss = model (x, y)
            losses[k] = loss.item()
        
        out[split] = losses.mean()

    model.train()
    return out

# Create the model
model = BigramLanguageModel(vocab_size)
model = model.to(device)

# Create the optimizer
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

print(f"training on: {device}")
print(f"Vocabulary size: {vocab_size}")
print(f"Starting training...")

for step in range(max_iters):

    if step % eval_interval == 0:
        losses = estimate_loss()
        print(f"step {step}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}")

        xb, yb = get_batch("train")

        logits, loss = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

torch.save(
    {
        "model_state_dict": model.state_dict(),
        "chars": chars ,
        "vocab_size": vocab_size,
        
    },
    "minidoorlm.pt"

)

print("Model saved to minidoorlm.pt")
print("Training complete.")