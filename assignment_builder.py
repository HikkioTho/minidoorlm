from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from intent_normalizer import NormalizedIntent, normalize_intent
from learning_guard import should_require_safety_note
from learning_questions import LearningQuestionSet, build_learning_questions
from student_profile import StudentProfile


@dataclass
class Assignment:
    topic: str
    raw_topic: str
    level: str
    intent: NormalizedIntent
    learning_questions: LearningQuestionSet
    summary_card: str
    virtual_lesson: str
    why_this_matters: str
    prerequisite_check: List[str]
    practice_tasks: List[str]
    active_recall: List[str]
    feynman_prompt: str
    mini_project: str
    review_schedule: List[str]
    source_note: str
    safety_note: str


def normalize_topic(topic: str) -> str:
    return " ".join(str(topic or "").strip().split())


def topic_in_list(topic: str, topics: List[str]) -> bool:
    normalized_topic = topic.lower()

    for item in topics:
        item_lower = item.lower()

        if item_lower in normalized_topic or normalized_topic in item_lower:
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
        clean = " ".join(str(chunk or "").split())

        if len(clean) > 240:
            clean = clean[:240].rstrip() + "..."

        if clean:
            summaries.append(clean)

    return summaries


def build_summary_card(profile: StudentProfile, intent: NormalizedIntent, difficulty: str) -> str:
    return (
        f"OpenDoor reads your request as: {intent.clean_topic}.\n\n"
        f"Goal: {intent.learning_goal}\n\n"
        f"First door: {intent.first_door}.\n\n"
        f"Next best action: {intent.next_best_action}\n\n"
        f"Level route: {difficulty}.\n\n"
        f"Profile used: {profile.name}, {profile.level}, goal: {profile.goals or 'not set'}."
    )


def build_virtual_lesson(
    profile: StudentProfile,
    intent: NormalizedIntent,
    difficulty: str,
    source_chunks: Optional[List[str]] = None,
) -> str:
    topic = intent.clean_topic
    analogy = profile.analogy_preferences or "real-world examples"
    source_summaries = summarize_source_chunks(source_chunks)

    source_line = ""

    if source_summaries:
        source_line = (
            f"\n\nSource-grounded note: One retrieved source idea says: {source_summaries[0]}"
        )

    if intent.domain == "trades_plumbing":
        return (
            f"{topic} starts with understanding the system, not touching tools first. "
            "A beginner should learn the map: water supply brings clean water in, drainage carries waste water out, "
            "venting helps drains work correctly, fixtures are the visible endpoints, and shutoff valves control risk. "
            "The first safe move is observation: identify parts, learn names, understand what each part does, "
            "and know when code, permits, or a licensed plumber matter. "
            f"Use {analogy} as the explanation style where helpful."
            f"{source_line}"
        )

    if difficulty == "supportive":
        return (
            f"Start with the safe basic idea of {topic}. "
            "The point is not to memorize a definition. The point is to understand the decision points, "
            "common mistakes, and what someone should check before acting. "
            f"Use {analogy} where helpful."
            f"{source_line}"
        )

    if difficulty in {"challenge", "advanced", "advanced_challenge"}:
        return (
            f"For {topic}, do not stop at the surface explanation. "
            f"Connect the idea to {profile.goals}, identify constraints, and explain where beginners get it wrong. "
            f"Use {analogy} if it helps make the concept easier to reason about."
            f"{source_line}"
        )

    return (
        f"{topic} is the clean topic OpenDoor extracted from your request. "
        "The lesson should focus on what it means, why it matters, what can go wrong, "
        "and what first step a learner should take. "
        f"Use {analogy} where helpful."
        f"{source_line}"
    )


def build_why_this_matters(intent: NormalizedIntent, profile: StudentProfile) -> str:
    if intent.domain == "trades_plumbing":
        return (
            "This matters because plumbing mistakes can cause leaks, water damage, unsafe conditions, "
            "or code problems. Learning the system map first makes the hands-on work safer later."
        )

    if intent.domain == "mechanical_fuel":
        return (
            "This matters because fuel and engine compatibility are safety-sensitive. "
            "A learner needs to understand the options and risks before thinking about real changes."
        )

    if profile.goals:
        return f"This matters because it connects to your stated goal: {profile.goals}."

    return f"This matters because {intent.clean_topic} is easier to remember when you know where it is used."


def build_prerequisite_check(intent: NormalizedIntent) -> List[str]:
    if intent.domain == "trades_plumbing":
        return [
            "Can you identify supply, drain, vent, fixture, trap, and shutoff valve?",
            "Do you know where the main water shutoff is before any real work?",
            "Do you understand that real plumbing work can involve local code, permits, and licensing?",
        ]

    if intent.domain == "mechanical_fuel":
        return [
            "Do you know what type of engine the tractor uses?",
            "Do you have the manufacturer manual or fuel recommendation?",
            "Do you understand the difference between learning options and modifying equipment?",
        ]

    if intent.domain == "electronics":
        return [
            "Do you know the basic vocabulary for this topic?",
            "Can you point to where this appears in a real circuit?",
            "Can you explain one beginner mistake before practicing?",
        ]

    if intent.domain == "programming":
        return [
            "Do you know the basic terms needed for this topic?",
            "Can you explain what problem this solves?",
            "Can you trace one simple example?",
        ]

    return [
        "Can you explain the topic in one sentence?",
        "Can you name one real example?",
        "Can you name one thing beginners usually misunderstand?",
    ]


def build_practice_tasks(
    profile: StudentProfile,
    intent: NormalizedIntent,
    difficulty: str,
    source_chunks: Optional[List[str]] = None,
) -> List[str]:
    topic = intent.clean_topic
    source_task = ""

    if source_chunks:
        source_task = " Use one retrieved source idea in your answer."

    if intent.domain == "trades_plumbing":
        return [
            "Look at one sink without changing anything. Identify the supply lines, shutoff valves, trap, and drain path.",
            "Write a 5-item safety checklist a beginner should complete before attempting any minor plumbing task.",
            "Explain why a leak, clog, or slow drain might have more than one possible cause.",
            "Find your local rules for plumbing work and write down when a licensed plumber is required.",
        ]

    if intent.domain == "mechanical_fuel":
        return [
            "Make a safe checklist of what to verify before considering any tractor fuel change.",
            "Explain why diesel, gasoline, and alternative fuels cannot be treated as interchangeable.",
            "List 3 questions you would ask a qualified mechanic or check in the manual.",
        ]

    if difficulty == "supportive":
        return [
            f"Explain {topic} in one plain sentence.{source_task}",
            f"List three important terms connected to {topic}.",
            f"Give one real-world example of {topic}.",
        ]

    if difficulty in {"challenge", "advanced", "advanced_challenge"}:
        return [
            f"Explain {topic} to a beginner without jargon.{source_task}",
            f"Create a harder example involving {topic} and solve or explain it.",
            f"Connect {topic} to {profile.goals}.",
            f"Design a mini test that proves someone understands {topic}.",
        ]

    return [
        f"Define {topic} in plain language.{source_task}",
        f"Give two examples of {topic}.",
        f"Explain why {topic} matters.",
        f"Create one practice question about {topic}.",
    ]


def build_active_recall(intent: NormalizedIntent) -> List[str]:
    topic = intent.clean_topic

    if intent.domain == "trades_plumbing":
        return [
            "Without notes, explain how water enters and leaves a house.",
            "What is the purpose of a shutoff valve?",
            "Why does a trap exist under a sink?",
            "What is one reason plumbing work may require code or licensing?",
        ]

    return [
        f"Without notes, explain the main idea of {topic}.",
        f"What is one mistake someone might make when learning {topic}?",
        f"What is one practical example of {topic}?",
        "What should you check before moving to a harder version of this topic?",
    ]


def build_review_schedule(profile: StudentProfile) -> List[str]:
    now = datetime.now(timezone.utc)

    if getattr(profile, "current_streak", 0) >= 5:
        intervals = [1, 3, 7, 14]
    elif getattr(profile, "current_streak", 0) >= 2:
        intervals = [1, 2, 5, 10]
    else:
        intervals = [1, 2, 4, 7]

    schedule = []

    for days in intervals:
        due_date = now + timedelta(days=days)
        schedule.append(f"Review in {days} day(s): {due_date.date().isoformat()}")

    return schedule


def build_source_note(source_chunks: Optional[List[str]]) -> str:
    if source_chunks:
        return "This lesson used retrieved local source chunks. Review the source section before trusting details."

    return (
        "No source library is connected for this topic yet. "
        "This lesson is using OpenDoor's built-in lesson structure."
    )


def build_safety_note(intent: NormalizedIntent) -> str:
    if should_require_safety_note(intent.clean_topic):
        return "Controlled topic note: this should stay educational, defensive, legal, and safe."

    if intent.safety_frame != "Use normal educational framing.":
        return intent.safety_frame

    return ""


def build_assignment(
    profile: StudentProfile,
    topic: str,
    source_chunks: Optional[List[str]] = None,
) -> Assignment:
    intent = normalize_intent(topic)
    clean_topic = normalize_topic(intent.clean_topic)
    source_chunks = source_chunks or []
    difficulty = choose_difficulty(profile, clean_topic)
    questions = build_learning_questions(intent)

    return Assignment(
        topic=clean_topic,
        raw_topic=intent.raw_input,
        level=profile.level,
        intent=intent,
        learning_questions=questions,
        summary_card=build_summary_card(profile, intent, difficulty),
        virtual_lesson=build_virtual_lesson(
            profile=profile,
            intent=intent,
            difficulty=difficulty,
            source_chunks=source_chunks,
        ),
        why_this_matters=build_why_this_matters(intent, profile),
        prerequisite_check=build_prerequisite_check(intent),
        practice_tasks=build_practice_tasks(
            profile=profile,
            intent=intent,
            difficulty=difficulty,
            source_chunks=source_chunks,
        ),
        active_recall=build_active_recall(intent),
        feynman_prompt=questions.feynman,
        mini_project=questions.next_step,
        review_schedule=build_review_schedule(profile),
        source_note=build_source_note(source_chunks),
        safety_note=build_safety_note(intent),
    )