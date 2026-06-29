from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from learning_guard import should_require_safety_note
from student_profile import StudentProfile


@dataclass
class Assignment:
    topic: str
    level: str
    virtual_lesson: str
    warm_up: List[str]
    reading_task: List[str]
    starter_resources: List[str]
    ending_resources: List[str]
    practice_problems: List[str]
    active_recall: List[str]
    feynman_prompt: str
    mini_project: str
    review_schedule: List[str]
    safety_note: str


def normalize_topic(topic: str) -> str:
    return " ".join(str(topic or "").strip().split())


def topic_in_list(topic: str, topics: List[str]) -> bool:
    normalized_topic = topic.lower()

    for item in topics:
        if item.lower() in normalized_topic or normalized_topic in item.lower():
            return True

    return False


def choose_difficulty(profile: StudentProfile, topic: str) -> str:
    level = profile.level.lower().strip()

    if topic_in_list(topic, profile.weak_topics):
        return "supportive"

    if topic_in_list(topic, profile.strong_topics):
        if level == "beginner":
            return "beginner_plus"
        if level == "intermediate":
            return "challenge"
        return "advanced_challenge"

    if level in {"advanced", "expert"}:
        return "advanced"

    if level == "intermediate":
        return "intermediate"

    return "beginner"


def summarize_source_chunks(source_chunks: Optional[List[str]]) -> List[str]:
    if not source_chunks:
        return []

    summaries = []

    for chunk in source_chunks[:4]:
        clean = " ".join(chunk.split())

        if len(clean) > 220:
            clean = clean[:220].rstrip() + "..."

        summaries.append(clean)

    return summaries


def build_virtual_lesson(
    profile: StudentProfile,
    topic: str,
    difficulty: str,
    source_chunks: Optional[List[str]] = None,
) -> str:
    analogy = profile.analogy_preferences or "real-world examples"
    source_summaries = summarize_source_chunks(source_chunks)

    source_line = ""

    if source_summaries:
        source_line = (
            " Use the retrieved local study sources as grounding. "
            f"One relevant source idea is: {source_summaries[0]}"
        )

    if difficulty == "supportive":
        return (
            f"Today, {profile.name} will learn {topic} slowly and clearly. "
            f"We will start with the core idea, use {analogy} for analogies, "
            f"then practice one small skill at a time.{source_line}"
        )

    if difficulty in {"challenge", "advanced", "advanced_challenge"}:
        return (
            f"Today, {profile.name} will strengthen {topic} with a more challenging lesson. "
            f"We will connect the concept to {profile.goals}, use {analogy} when helpful, "
            f"and push beyond memorization into explanation and application.{source_line}"
        )

    return (
        f"Today, {profile.name} will learn the basics of {topic}. "
        f"The lesson will use {analogy} to make the idea easier to remember, "
        f"then end with practice and recall.{source_line}"
    )


def build_resources(
    topic: str,
    stage: str,
    source_chunks: Optional[List[str]] = None,
) -> List[str]:
    resources = [
        f"Find one beginner-friendly article, documentation page, or textbook section about {topic}.",
        f"Find one short visual explanation about {topic}.",
        f"Write down one question you still have about {topic}.",
        f"At the {stage} of the lesson, compare what you know now against your first question.",
    ]

    if source_chunks:
        resources.insert(
            0,
            "Review the retrieved local source chunks shown in the OpenDoor beta before using outside resources.",
        )

    return resources


def build_practice(
    profile: StudentProfile,
    topic: str,
    difficulty: str,
    source_chunks: Optional[List[str]] = None,
) -> List[str]:
    source_prompt = ""

    if source_chunks:
        source_prompt = " Use at least one retrieved local source idea in your answer."

    if difficulty == "supportive":
        return [
            f"Define {topic} in one sentence.{source_prompt}",
            f"List three words that seem important for {topic}.",
            f"Give one example of where {topic} appears in real life.",
        ]

    if difficulty == "beginner_plus":
        return [
            f"Explain {topic} using an analogy based on {profile.analogy_preferences or 'daily life'}.{source_prompt}",
            f"Create a small example problem about {topic} and solve it.",
            f"Identify one common beginner mistake related to {topic}.",
        ]

    if difficulty in {"challenge", "advanced", "advanced_challenge"}:
        return [
            f"Explain {topic} to a beginner without using jargon.{source_prompt}",
            f"Create a harder problem involving {topic} and solve it step by step.",
            f"Connect {topic} to {profile.goals} and explain why it matters.",
            f"Design a mini test that would prove someone understands {topic}.",
        ]

    return [
        f"Define {topic}.{source_prompt}",
        f"Give two examples of {topic}.",
        f"Explain why {topic} matters.",
        f"Create one practice question about {topic}.",
    ]


def build_active_recall(topic: str, difficulty: str) -> List[str]:
    questions = [
        f"Without notes, explain the main idea of {topic}.",
        f"What is one mistake someone might make when learning {topic}?",
        f"What is one example of {topic} in a real situation?",
    ]

    if difficulty in {"challenge", "advanced", "advanced_challenge"}:
        questions.append(
            f"How would you teach {topic} to someone who thinks they already understand it?"
        )

    return questions


def build_review_schedule(profile: StudentProfile) -> List[str]:
    now = datetime.now(timezone.utc)

    if profile.current_streak >= 5:
        intervals = [1, 3, 7, 14]
    elif profile.current_streak >= 2:
        intervals = [1, 2, 5, 10]
    else:
        intervals = [1, 2, 4, 7]

    schedule = []

    for days in intervals:
        due_date = now + timedelta(days=days)
        schedule.append(
            f"Review in {days} day(s): {due_date.date().isoformat()}"
        )

    return schedule


def build_assignment(
    profile: StudentProfile,
    topic: str,
    source_chunks: Optional[List[str]] = None,
) -> Assignment:
    clean_topic = normalize_topic(topic)
    difficulty = choose_difficulty(profile, clean_topic)

    source_chunks = source_chunks or []

    safety_note = ""

    if should_require_safety_note(clean_topic):
        safety_note = (
            "Safety Boundary: This assignment must stay educational, defensive, "
            "legal, and authorized. Do not create operational harm instructions."
        )

    virtual_lesson = build_virtual_lesson(
        profile=profile,
        topic=clean_topic,
        difficulty=difficulty,
        source_chunks=source_chunks,
    )

    warm_up = [
        f"What do you already know about {clean_topic}?",
        f"What do you think will be difficult about {clean_topic}?",
        f"How does {clean_topic} connect to your goal: {profile.goals}?",
    ]

    if source_chunks:
        warm_up.append(
            "Before answering, read the retrieved local source chunks and mark one idea that seems important."
        )

    starter_resources = build_resources(
        topic=clean_topic,
        stage="start",
        source_chunks=source_chunks,
    )

    ending_resources = build_resources(
        topic=clean_topic,
        stage="end",
        source_chunks=source_chunks,
    )

    reading_task = [
        f"Before practice, read or watch one beginner-friendly explanation of {clean_topic}.",
        "Write down three key terms.",
        "Write one sentence explaining why this topic matters.",
    ]

    if source_chunks:
        reading_task.insert(
            0,
            "Read the retrieved local source chunks first. Treat them as the starting study material.",
        )

    practice_problems = build_practice(
        profile=profile,
        topic=clean_topic,
        difficulty=difficulty,
        source_chunks=source_chunks,
    )

    active_recall = build_active_recall(
        topic=clean_topic,
        difficulty=difficulty,
    )

    feynman_prompt = (
        f"Explain {clean_topic} like you are teaching a smart 12-year-old. "
        "Use plain language, one analogy, and one example. "
        "Then list what still feels unclear."
    )

    if source_chunks:
        feynman_prompt += (
            " Include one idea from the retrieved local source chunks, but explain it in your own words."
        )

    mini_project = (
        f"Create a small artifact that proves you understand {clean_topic}. "
        "This could be notes, a diagram, code, a solved example, a short demo, "
        "or a one-page explanation."
    )

    review_schedule = build_review_schedule(profile)

    return Assignment(
        topic=clean_topic,
        level=profile.level,
        virtual_lesson=virtual_lesson,
        warm_up=warm_up,
        reading_task=reading_task,
        starter_resources=starter_resources,
        ending_resources=ending_resources,
        practice_problems=practice_problems,
        active_recall=active_recall,
        feynman_prompt=feynman_prompt,
        mini_project=mini_project,
        review_schedule=review_schedule,
        safety_note=safety_note,
    )