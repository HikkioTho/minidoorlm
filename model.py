import torch
import torch.nn as nn
from torch.nn import functional as F


class BigramLanguageModel(nn.Module):
    def __init__(self,vocab_size: int):
        super().__init__()

        self.token_embedding_table = nn.Embedding(vocab_size, vocab_size)

    def forward(self, idx,  targets=None):

        logits = self.token_embedding_table(idx)


        loss = None

        if targets is not None:
            batch_size, time_steps, vocab_size = logits.shape

            logits = logits.view(batch_size * time_steps, vocab_size)
            targets = targets.view(batch_size * time_steps)

            loss = F.cross_entropy(logits, targets)

        return logits, loss
    
    def generate(self, idx, max_new_tokens):
        for _ in range(max_new_tokens):
            logits, loss = self(idx)

            logits = logits[:, -1, :]

            probs = F.softmax(logits, dim=-1)

            idx_next = torch.multinomial(probs, num_samples=1)

            idx =  torch.cat((idx, idx_next), dim=1)

            return idx