import json
import re
from pathlib import Path
from typing import Dict, List


class MiniDoorTokenizer:
    """
    Tiny regex tokenizer for MiniDoorLM.

    This tokenizer keeps special OpenDoor markers intact, then splits normal text
    into words, numbers, punctuation, and whitespace tokens.

    It is intentionally simple so we can understand and debug it.
    """

    SPECIAL_TOKENS = [
        "<PAD>",
        "<UNK>",
        "<END>",
        "### EXAMPLE START",
        "### EXAMPLE END",
        "User:",
        "OpenDoor:",
        "Door opened:",
        "Level:",
        "Learning Mode:",
        "First Lesson:",
        "Analogy:",
        "Safety Note:",
        "Safety Boundary:",
        "Active Recall:",
        "Example Safety Mode:",
    ]

    TOKEN_PATTERN = re.compile(
        r"### EXAMPLE START|### EXAMPLE END|"
        r"Door opened:|Learning Mode:|First Lesson:|"
        r"Safety Boundary:|Safety Note:|Active Recall:|"
        r"Example Safety Mode:|OpenDoor:|User:|Level:|Analogy:|"
        r"<END>|"
        r"[A-Za-z]+(?:'[A-Za-z]+)?|"
        r"\d+(?:\.\d+)?|"
        r"\s+|"
        r"[^\w\s]",
        re.MULTILINE,
    )

    def __init__(self):
        self.token_to_id: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}

        for token in self.SPECIAL_TOKENS:
            self.add_token(token)

    def add_token(self, token: str) -> int:
        if token not in self.token_to_id:
            token_id = len(self.token_to_id)
            self.token_to_id[token] = token_id
            self.id_to_token[token_id] = token

        return self.token_to_id[token]

    def train_from_text(self, text: str) -> None:
        tokens = self.tokenize(text)

        for token in tokens:
            self.add_token(token)

    def tokenize(self, text: str) -> List[str]:
        return self.TOKEN_PATTERN.findall(text)

    def encode(self, text: str) -> List[int]:
        tokens = self.tokenize(text)
        unk_id = self.token_to_id["<UNK>"]

        return [self.token_to_id.get(token, unk_id) for token in tokens]

    def decode(self, token_ids: List[int]) -> str:
        tokens = []

        for token_id in token_ids:
            token = self.id_to_token.get(int(token_id), "<UNK>")
            tokens.append(token)

        return "".join(tokens)

    def vocab_size(self) -> int:
        return len(self.token_to_id)

    def save(self, path: str) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "token_to_id": self.token_to_id,
            "id_to_token": {str(k): v for k, v in self.id_to_token.items()},
            "special_tokens": self.SPECIAL_TOKENS,
        }

        output_path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str):
        input_path = Path(path)

        if not input_path.exists():
            raise FileNotFoundError(f"Tokenizer file not found: {input_path}")

        payload = json.loads(input_path.read_text(encoding="utf-8"))

        tokenizer = cls()
        tokenizer.token_to_id = {
            str(token): int(token_id)
            for token, token_id in payload["token_to_id"].items()
        }
        tokenizer.id_to_token = {
            int(token_id): str(token)
            for token_id, token in payload["id_to_token"].items()
        }

        return tokenizer


def run_demo():
    text = (
        "### EXAMPLE START\n"
        "User: Teach me Python as a beginner.\n"
        "OpenDoor:\n"
        "Door opened: Python Programming.\n"
        "Level: Beginner.\n"
        "Learning Mode: procedural_learning.\n"
        "First Lesson: Python gives instructions to a computer.\n"
        "Active Recall: Explain what a variable is.\n"
        "<END>\n"
    )

    tokenizer = MiniDoorTokenizer()
    tokenizer.train_from_text(text)

    encoded = tokenizer.encode(text)
    decoded = tokenizer.decode(encoded)

    print(f"Vocab size: {tokenizer.vocab_size()}")
    print(f"Encoded tokens: {encoded[:30]}")
    print("")
    print(decoded)


if __name__ == "__main__":
    run_demo()