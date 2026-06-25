import torch
import torch.nn as nn
from torch.nn import functional as F


class Head(nn.Module):
    """One head of self-attention."""

    def __init__(self, head_size, n_embd, block_size, dropout):
        super().__init__()

        self.key = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)

        self.register_buffer(
            "tril",
            torch.tril(torch.ones(block_size, block_size))
        )

        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        batch, time, channels = x.shape

        k = self.key(x)
        q = self.query(x)

        weights = q @ k.transpose(-2, -1) * channels ** -0.5

        mask = torch.tril(torch.ones(time, time, device=x.device)) == 0
        weights = weights.masked_fill(mask, float("-inf"))

        weights = F.softmax(weights, dim=-1)
        weights = self.dropout(weights)

        v = self.value(x)
        out = weights @ v

        return out


class MultiHeadAttention(nn.Module):
    """Multiple attention heads running in parallel."""

    def __init__(self, num_heads, head_size, n_embd, block_size, dropout):
        super().__init__()

        self.heads = nn.ModuleList([
            Head(head_size, n_embd, block_size, dropout)
            for _ in range(num_heads)
        ])

        self.proj = nn.Linear(head_size * num_heads, n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out = torch.cat([head(x) for head in self.heads], dim=-1)
        out = self.dropout(self.proj(out))
        return out


class FeedForward(nn.Module):
    """Small neural network after attention."""

    def __init__(self, n_embd, dropout):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),
            nn.ReLU(),
            nn.Linear(4 * n_embd, n_embd),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)


class Block(nn.Module):
    """Transformer block: attention + feed forward."""

    def __init__(self, n_embd, n_head, block_size, dropout):
        super().__init__()

        head_size = n_embd // n_head

        self.sa = MultiHeadAttention(
            n_head,
            head_size,
            n_embd,
            block_size,
            dropout
        )

        self.ffwd = FeedForward(n_embd, dropout)
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x):
        x = x + self.sa(self.ln1(x))
        x = x + self.ffwd(self.ln2(x))
        return x


class MiniTransformerLanguageModel(nn.Module):
    def __init__(
        self,
        vocab_size,
        block_size=32,
        n_embd=64,
        n_head=4,
        n_layer=2,
        dropout=0.2,
    ):
        super().__init__()

        self.block_size = block_size

        self.token_embedding_table = nn.Embedding(vocab_size, n_embd)
        self.position_embedding_table = nn.Embedding(block_size, n_embd)

        self.blocks = nn.Sequential(*[
            Block(n_embd, n_head, block_size, dropout)
            for _ in range(n_layer)
        ])

        self.ln_f = nn.LayerNorm(n_embd)
        self.lm_head = nn.Linear(n_embd, vocab_size)

    def forward(self, idx, targets=None):
        batch, time = idx.shape

        token_embeddings = self.token_embedding_table(idx)

        position_embeddings = self.position_embedding_table(
            torch.arange(time, device=idx.device)
        )

        x = token_embeddings + position_embeddings
        x = self.blocks(x)
        x = self.ln_f(x)

        logits = self.lm_head(x)

        loss = None

        if targets is not None:
            batch, time, channels = logits.shape
            logits = logits.view(batch * time, channels)
            targets = targets.view(batch * time)
            loss = F.cross_entropy(logits, targets)

        return logits, loss

    def generate(self, idx, max_new_tokens):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]

            logits, loss = self(idx_cond)
            logits = logits[:, -1, :]

            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)

            idx = torch.cat((idx, idx_next), dim=1)

        return idx