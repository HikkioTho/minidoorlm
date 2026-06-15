import torch
from model import BigramLanguageModel


device = "cuda" if torch.cuda.is_available() else "cpu"


# Load the model data
checkpoint = torch.load("minidoorlm.pt", map_location=device)


chars = checkpoint["chars"]
vocab_size = checkpoint["vocab_size"]

stoi = { ch: i for i, ch in enumerate(chars)}
itos = { i: ch for i, ch in enumerate(chars)}

encode = lambda s: [stoi[c] for c in s]
decode = lambda nums: "".join([itos[i] for i in nums])

# Recreate model and load trained weights
model = BigramLanguageModel(vocab_size)
model.load_state_dict(checkpoint["model_state_dict"])
model = model.to(device)
model.eval()

prompt = "The door"

idx = torch.tensor([encode(prompt)], dtype=torch.long, device=device)

generated = model.generate(idx, max_new_tokens=1000)

print(decode(generated[0].tolist()))