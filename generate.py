import torch
from model import MiniTransformerLanguageModel


device = "cuda" if torch.cuda.is_available() else "cpu"

checkpoint = torch.load("minidoorlm_transformer.pt", map_location=device)

chars = checkpoint["chars"]
vocab_size = checkpoint["vocab_size"]
block_size = checkpoint["block_size"]
n_embd = checkpoint["n_embd"]
n_head = checkpoint["n_head"]
n_layer = checkpoint["n_layer"]
dropout = checkpoint["dropout"]

stoi = {ch: i for i, ch in enumerate(chars)}
itos = {i: ch for i, ch in enumerate(chars)}

encode = lambda s: [stoi[c] for c in s]
decode = lambda nums: "".join([itos[i] for i in nums])

model = MiniTransformerLanguageModel(
    vocab_size=vocab_size,
    block_size=block_size,
    n_embd=n_embd,
    n_head=n_head,
    n_layer=n_layer,
    dropout=dropout,
)

model.load_state_dict(checkpoint["model_state_dict"])
model = model.to(device)
model.eval()

prompt = "The door"

idx = torch.tensor([encode(prompt)], dtype=torch.long, device=device)

generated = model.generate(idx, max_new_tokens=300)

print(decode(generated[0].tolist()))