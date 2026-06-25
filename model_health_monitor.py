from dataclasses import dataclass, asdict
from pathlib import Path
import json
import re
from typing import Dict, List


@dataclass
class DatasetHealthReport:
    file_path: str
    character_count: int
    line_count: int
    user_examples: int
    opendoor_examples: int
    active_recall_examples: int
    end_tokens: int
    example_boundaries: int
    unique_words: int
    repeated_line_count: int
    average_example_length: float
    warnings: List[str]
    recommendations: List[str]


@dataclass
class GenerationHealthReport:
    prompt: str
    output_length: int
    has_door_opened: bool
    has_level: bool
    has_learning_mode: bool
    has_first_lesson: bool
    has_active_recall: bool
    has_end_token: bool
    repeated_phrase_warnings: List[str]
    warnings: List[str]
    recommendations: List[str]


class ModelHealthMonitor:
    """
    ModelHealthMonitor checks MiniDoorLM training data and generated output.

    Core goal:
    prevent silent quality failures, overfitting, generic outputs, model collapse,
    prompt fatigue, and weak dataset habits.
    """

    REQUIRED_DATASET_MARKERS = [
        "User:",
        "OpenDoor:",
        "Active Recall:",
        "<END>",
        "### EXAMPLE START",
    ]

    REQUIRED_OUTPUT_MARKERS = [
        "Door opened:",
        "Level:",
        "Learning Mode:",
        "First Lesson:",
        "Active Recall:",
    ]

    GENERIC_PHRASES = [
        "this topic",
        "beginner concepts",
        "in your own words",
        "first lesson",
        "learning mode",
        "active recall",
    ]

    @classmethod
    def inspect_dataset(cls, file_path: str) -> DatasetHealthReport:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        text = path.read_text(encoding="utf-8")

        if not text.strip():
            raise ValueError(f"Dataset file is empty: {path}")

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        repeated_line_count = cls.count_repeated_lines(lines)
        unique_words = cls.count_unique_words(text)

        user_examples = text.count("User:")
        opendoor_examples = text.count("OpenDoor:")
        active_recall_examples = text.count("Active Recall:")
        end_tokens = text.count("<END>")
        example_boundaries = text.count("### EXAMPLE START")

        average_example_length = cls.estimate_average_example_length(
            text=text,
            example_count=max(user_examples, 1),
        )

        warnings = []
        recommendations = []

        if user_examples < 50:
            warnings.append(
                "Dataset has fewer than 50 examples. The model may memorize instead of generalize."
            )
            recommendations.append(
                "Expand the dataset to at least 50 examples, then 100+ examples."
            )

        if user_examples != opendoor_examples:
            warnings.append(
                "User example count does not match OpenDoor example count."
            )
            recommendations.append(
                "Make sure every User prompt has a matching OpenDoor response."
            )

        if end_tokens < user_examples:
            warnings.append(
                "Some examples may be missing <END> tokens."
            )
            recommendations.append(
                "Add <END> to every training example so generation learns when to stop."
            )

        if example_boundaries < user_examples:
            warnings.append(
                "Some examples may be missing example boundaries."
            )
            recommendations.append(
                "Use ### EXAMPLE START before every training example."
            )

        if repeated_line_count > max(3, len(lines) * 0.1):
            warnings.append(
                "Dataset has many repeated lines. This can cause generic or circular output."
            )
            recommendations.append(
                "Rewrite repeated examples with more varied wording and topics."
            )

        if unique_words < 300:
            warnings.append(
                "Dataset vocabulary is small. Generated text may sound repetitive or broken."
            )
            recommendations.append(
                "Add more subjects, teaching styles, analogies, and response variations."
            )

        if average_example_length < 250:
            warnings.append(
                "Average example length is short. The model may not learn full lesson structure."
            )
            recommendations.append(
                "Add richer examples with lesson, analogy, quiz, and review sections."
            )

        return DatasetHealthReport(
            file_path=str(path),
            character_count=len(text),
            line_count=len(text.splitlines()),
            user_examples=user_examples,
            opendoor_examples=opendoor_examples,
            active_recall_examples=active_recall_examples,
            end_tokens=end_tokens,
            example_boundaries=example_boundaries,
            unique_words=unique_words,
            repeated_line_count=repeated_line_count,
            average_example_length=round(average_example_length, 2),
            warnings=warnings,
            recommendations=recommendations,
        )

    @classmethod
    def inspect_generation(cls, prompt: str, generated_text: str) -> GenerationHealthReport:
        warnings = []
        recommendations = []

        has_door_opened = "Door opened:" in generated_text
        has_level = "Level:" in generated_text
        has_learning_mode = "Learning Mode:" in generated_text
        has_first_lesson = "First Lesson:" in generated_text
        has_active_recall = "Active Recall:" in generated_text
        has_end_token = "<END>" in generated_text

        missing_markers = []

        for marker in cls.REQUIRED_OUTPUT_MARKERS:
            if marker not in generated_text:
                missing_markers.append(marker)

        if missing_markers:
            warnings.append(
                f"Generated output is missing expected OpenDoor markers: {missing_markers}"
            )
            recommendations.append(
                "Add more training examples using the full OpenDoor response structure."
            )

        repeated_phrase_warnings = cls.find_repeated_phrases(generated_text)

        if repeated_phrase_warnings:
            warnings.append(
                "Generated output contains repeated phrases or loop-like behavior."
            )
            recommendations.append(
                "Use lower temperature, add <END> stopping, and expand dataset variety."
            )

        if len(generated_text) < 100:
            warnings.append(
                "Generated output is very short."
            )
            recommendations.append(
                "Increase max-new-tokens or train on longer examples."
            )

        if cls.looks_garbled(generated_text):
            warnings.append(
                "Generated output appears garbled or contains many unnatural words."
            )
            recommendations.append(
                "Expand the dataset and consider moving from character-level to token-level training."
            )

        return GenerationHealthReport(
            prompt=prompt,
            output_length=len(generated_text),
            has_door_opened=has_door_opened,
            has_level=has_level,
            has_learning_mode=has_learning_mode,
            has_first_lesson=has_first_lesson,
            has_active_recall=has_active_recall,
            has_end_token=has_end_token,
            repeated_phrase_warnings=repeated_phrase_warnings,
            warnings=warnings,
            recommendations=recommendations,
        )

    @staticmethod
    def count_repeated_lines(lines: List[str]) -> int:
        seen = set()
        repeated = 0

        for line in lines:
            normalized = line.lower().strip()

            if normalized in seen:
                repeated += 1
            else:
                seen.add(normalized)

        return repeated

    @staticmethod
    def count_unique_words(text: str) -> int:
        words = re.findall(r"[A-Za-z']+", text.lower())
        return len(set(words))

    @staticmethod
    def estimate_average_example_length(text: str, example_count: int) -> float:
        if example_count <= 0:
            return 0.0

        return len(text) / example_count

    @staticmethod
    def find_repeated_phrases(text: str) -> List[str]:
        warnings = []
        lowered = text.lower()

        phrases = [
            "door opened",
            "learning mode",
            "active recall",
            "first lesson",
            "level",
        ]

        for phrase in phrases:
            count = lowered.count(phrase)

            if count > 3:
                warnings.append(f"Phrase repeated too often: {phrase} ({count} times)")

        return warnings

    @staticmethod
    def looks_garbled(text: str) -> bool:
        words = re.findall(r"[A-Za-z']+", text)

        if not words:
            return True

        long_weird_words = [
            word for word in words
            if len(word) > 12 and not word.lower().endswith(("tion", "ing", "ment", "ness"))
        ]

        short_fragments = [
            word for word in words
            if len(word) <= 2
        ]

        weird_ratio = len(long_weird_words) / max(len(words), 1)
        fragment_ratio = len(short_fragments) / max(len(words), 1)

        return weird_ratio > 0.08 or fragment_ratio > 0.35


def print_report(title: str, payload):
    print("")
    print(title)
    print("-" * len(title))
    print(json.dumps(asdict(payload), indent=2))


def run_demo():
    dataset_path = "data/training/opendoor_teaching_examples_v2.txt"

    if Path(dataset_path).exists():
        dataset_report = ModelHealthMonitor.inspect_dataset(dataset_path)
        print_report("Dataset Health Report", dataset_report)
    else:
        print(f"Dataset not found for demo: {dataset_path}")

    sample_prompt = "User: Teach me Python as a beginner.\nOpenDoor:"
    sample_output = (
        "OpenDoor:\n"
        "Door opened: Python Programming.\n"
        "Level: Beginner.\n"
        "Learning Mode: procedural_learning.\n"
        "First Lesson: Python is a programming language.\n"
        "Active Recall: Explain what a variable is.\n"
        "<END>"
    )

    generation_report = ModelHealthMonitor.inspect_generation(
        prompt=sample_prompt,
        generated_text=sample_output,
    )

    print_report("Generation Health Report", generation_report)


if __name__ == "__main__":
    run_demo()