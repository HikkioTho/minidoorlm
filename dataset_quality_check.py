import argparse
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple


REQUIRED_MARKERS = [
    "### EXAMPLE START",
    "User:",
    "OpenDoor:",
    "Door opened:",
    "Level:",
    "Learning Mode:",
    "First Lesson:",
    "Active Recall:",
    "<END>",
]

TOPIC_COVERAGE_TERMS = [
    "robot",
    "robotics",
    "soldering",
    "breadboard",
    "resistor",
    "capacitor",
    "servo",
    "python",
    "linux",
    "networking",
    "dns",
    "cybersecurity",
    "project",
    "debugging",
    "git",
    "github",
    "algebra",
    "fractions",
    "physics",
    "chemistry",
    "biology",
    "history",
    "essay",
    "drawing",
    "photography",
    "baking",
    "spanish",
    "study",
    "active recall",
    "spaced repetition",
]

MODE_COVERAGE_TERMS = [
    "conceptual_learning",
    "procedural_learning",
    "hands_on_learning",
    "project_based_learning",
    "systems_learning",
    "controlled_learning",
    "language_learning",
    "retention_learning",
    "visual_learning",
    "creative_learning",
    "adaptive_learning",
    "safety_first_learning",
]

RISK_TERMS = [
    "malware",
    "ethical hacking",
    "cybersecurity",
    "controlled",
    "safety boundary",
    "authorized",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check OpenDoor training dataset quality before model training."
    )

    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/training/opendoor_teaching_examples_v3.txt"),
        help="Path to OpenDoor training dataset.",
    )

    parser.add_argument(
        "--min-examples",
        type=int,
        default=50,
        help="Minimum recommended number of examples.",
    )

    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    text = path.read_text(encoding="utf-8")

    if not text.strip():
        raise ValueError(f"Dataset is empty: {path}")

    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_examples(text: str) -> List[str]:
    chunks = text.split("### EXAMPLE START")
    examples = []

    for chunk in chunks:
        cleaned = chunk.strip()

        if not cleaned:
            continue

        examples.append("### EXAMPLE START\n" + cleaned)

    return examples


def extract_user_prompt(example: str) -> str:
    match = re.search(r"User:\s*(.+)", example)

    if not match:
        return ""

    return match.group(1).strip().lower()


def marker_report(text: str) -> Dict[str, int]:
    return {marker: text.count(marker) for marker in REQUIRED_MARKERS}


def find_broken_examples(examples: List[str]) -> List[Tuple[int, List[str]]]:
    broken = []

    for index, example in enumerate(examples, start=1):
        missing = [marker for marker in REQUIRED_MARKERS if marker not in example]

        if missing:
            broken.append((index, missing))

    return broken


def find_duplicate_prompts(examples: List[str]) -> List[str]:
    prompts = [extract_user_prompt(example) for example in examples]
    counts = Counter(prompt for prompt in prompts if prompt)
    duplicates = sorted([prompt for prompt, count in counts.items() if count > 1])
    return duplicates


def coverage_report(text: str, terms: List[str]) -> Dict[str, bool]:
    lower_text = text.lower()
    return {term: term in lower_text for term in terms}


def average_example_length(examples: List[str]) -> float:
    if not examples:
        return 0.0

    return sum(len(example) for example in examples) / len(examples)


def repeated_line_report(text: str) -> List[Tuple[str, int]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    counts = Counter(lines)

    repeated = [
        (line, count)
        for line, count in counts.items()
        if count > 3 and not line.startswith(("User:", "OpenDoor:", "Level:", "Learning Mode:"))
    ]

    return sorted(repeated, key=lambda item: item[1], reverse=True)


def print_bool_coverage(title: str, coverage: Dict[str, bool]) -> None:
    present = [term for term, found in coverage.items() if found]
    missing = [term for term, found in coverage.items() if not found]

    print(title)
    print("-" * len(title))
    print(f"Present: {len(present)} / {len(coverage)}")

    if missing:
        print("Missing:")
        for term in missing:
            print(f"  - {term}")
    else:
        print("Missing: none")

    print("")


def main() -> int:
    args = parse_args()

    text = read_text(args.data)
    examples = split_examples(text)

    markers = marker_report(text)
    broken = find_broken_examples(examples)
    duplicates = find_duplicate_prompts(examples)
    topic_coverage = coverage_report(text, TOPIC_COVERAGE_TERMS)
    mode_coverage = coverage_report(text, MODE_COVERAGE_TERMS)
    repeated_lines = repeated_line_report(text)

    warning_count = 0

    print("")
    print("OpenDoor Dataset Quality Check")
    print("------------------------------")
    print(f"Dataset: {args.data}")
    print(f"Characters: {len(text)}")
    print(f"Examples: {len(examples)}")
    print(f"Average example length: {average_example_length(examples):.1f} characters")
    print("")

    print("Marker Counts")
    print("-------------")
    for marker, count in markers.items():
        print(f"{marker}: {count}")
    print("")

    if len(examples) < args.min_examples:
        warning_count += 1
        print(f"WARNING: Dataset has fewer than {args.min_examples} examples.")
        print("")

    if markers["User:"] != markers["OpenDoor:"] or markers["User:"] != markers["<END>"]:
        warning_count += 1
        print("WARNING: User/OpenDoor/<END> counts do not match.")
        print("")

    if broken:
        warning_count += 1
        print("Broken Examples")
        print("---------------")
        for index, missing in broken:
            print(f"Example {index} missing: {', '.join(missing)}")
        print("")
    else:
        print("Broken Examples: none")
        print("")

    if duplicates:
        warning_count += 1
        print("Duplicate Prompts")
        print("-----------------")
        for prompt in duplicates:
            print(f"- {prompt}")
        print("")
    else:
        print("Duplicate Prompts: none")
        print("")

    print_bool_coverage("Topic Coverage", topic_coverage)
    print_bool_coverage("Learning Mode Coverage", mode_coverage)

    if repeated_lines:
        warning_count += 1
        print("Repeated Lines")
        print("--------------")
        for line, count in repeated_lines[:15]:
            print(f"{count}x: {line}")
        print("")
    else:
        print("Repeated Lines: none")
        print("")

    risk_coverage = coverage_report(text, RISK_TERMS)
    print_bool_coverage("Safety / Controlled Topic Coverage", risk_coverage)

    if warning_count == 0:
        print("Dataset status: PASS")
    else:
        print(f"Dataset status: REVIEW NEEDED ({warning_count} warning groups)")

    return 0 if warning_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())