import json
import re
from pathlib import Path
from typing import Dict, List


class MiniDoorTokenizer:
    """
    Hybrid tokenizer for MiniDoorLM.

    Why this exists:
    - The first token tokenizer turned unknown words into <UNK>.
    - That caused prompts like "robot" and "soldering" to become invisible.
    - This version keeps known words as tokens, but breaks unknown words into
      character fallback tokens.

    Example:
        known word:
            Python -> Python

        unknown word:
            soldering -> <CH:s> <CH:o> <CH:l> <CH:d> <CH:e> <CH:r> <CH:i> <CH:n> <CH:g>

    This is still simple enough for us to understand and debug.
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

    CHARACTER_FALLBACKS = (
        list("abcdefghijklmnopqrstuvwxyz")
        + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        + list("0123456789")
        + ["-", "_", "/", "\\", ".", ",", ":", ";", "?", "!", "'", '"', "(", ")", "[", "]"]
    )

    def __init__(self):
        self.token_to_id: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}

        for token in self.SPECIAL_TOKENS:
            self.add_token(token)

        for char in self.CHARACTER_FALLBACKS:
            self.add_token(self.to_char_token(char))

    @staticmethod
    def to_char_token(char: str) -> str:
        return f"<CH:{char}>"

    @staticmethod
    def is_char_token(token: str) -> bool:
        return token.startswith("<CH:") and token.endswith(">")

    @staticmethod
    def from_char_token(token: str) -> str:
        return token[4:-1]

    def add_token(self, token: str) -> int:
        if token not in self.token_to_id:
            token_id = len(self.token_to_id)
            self.token_to_id[token] = token_id
            self.id_to_token[token_id] = token

        return self.token_to_id[token]

    def train_from_text(self, text: str) -> None:
        """
        Build vocabulary from training text.

        We still include full known words as tokens because that produces cleaner
        generation when the word exists in the training set.
        """

        tokens = self.tokenize(text)

        for token in tokens:
            self.add_token(token)

    def tokenize(self, text: str) -> List[str]:
        return self.TOKEN_PATTERN.findall(text)

    def encode(self, text: str) -> List[int]:
        """
        Convert text into token IDs.

        If a token is unknown:
        - If it is a word/number/piece we can split, use character fallback tokens.
        - If a character is somehow unsupported, use <UNK>.
        """

        raw_tokens = self.tokenize(text)
        unk_id = self.token_to_id["<UNK>"]
        encoded: List[int] = []

        for token in raw_tokens:
            if token in self.token_to_id:
                encoded.append(self.token_to_id[token])
                continue

            if token.strip() == "":
                encoded.append(unk_id)
                continue

            for char in token:
                char_token = self.to_char_token(char)

                if char_token in self.token_to_id:
                    encoded.append(self.token_to_id[char_token])
                else:
                    encoded.append(unk_id)

        return encoded

    def decode(self, token_ids: List[int]) -> str:
        output_parts: List[str] = []

        for token_id in token_ids:
            token = self.id_to_token.get(int(token_id), "<UNK>")

            if self.is_char_token(token):
                output_parts.append(self.from_char_token(token))
            else:
                output_parts.append(token)

        return "".join(output_parts)

    def vocab_size(self) -> int:
        return len(self.token_to_id)

    def save(self, path: str) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "version": "hybrid_word_char_v2",
            "token_to_id": self.token_to_id,
            "id_to_token": {str(k): v for k, v in self.id_to_token.items()},
            "special_tokens": self.SPECIAL_TOKENS,
            "character_fallbacks": self.CHARACTER_FALLBACKS,
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

    known_prompt = "User: Teach me Python as a beginner.\nOpenDoor:"
    unknown_prompt = "User: Teach me soldering and robotics basics.\nOpenDoor:"

    known_encoded = tokenizer.encode(known_prompt)
    unknown_encoded = tokenizer.encode(unknown_prompt)

    print(f"Vocab size: {tokenizer.vocab_size()}")
    print("")
    print("Known prompt decoded:")
    print(tokenizer.decode(known_encoded))
    print("")
    print("Unknown prompt decoded with character fallback:")
    print(tokenizer.decode(unknown_encoded))


if __name__ == "__main__":
    run_demo()