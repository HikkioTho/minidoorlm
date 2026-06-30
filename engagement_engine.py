from dataclasses import dataclass
from typing import List, Optional

from intent_normalizer import normalize_intent


@dataclass
class OnboardingCard:
    title: str
    learner_reason: str
    starting_topic: str
    first_door: str
    delight_moment: str
    next_step: str


@dataclass
class MasteryNode:
    name: str
    status: str
    mastery: float
    forgetting_risk: float
    note: str


@dataclass
class SessionSummary:
    greeting: str
    since_last_session: List[str]
    forgetting_alerts: List[str]
    next_best_action: str
    door_unlocked: Optional[str]


@dataclass
class TransparencyCard:
    assigned: str
    why: str
    learner_model_used: List[str]
    source_note: str
    user_can_override: str


@dataclass
class CelebrationMoment:
    title: str
    message: str
    unlocked: Optional[str]
    next_hint: str


@dataclass
class MoodEnergyCheck:
    prompt: str
    options: List[str]
    use_for: str


def build_onboarding_card(
    name: str,
    learner_reason: str,
    starting_topic: str,
    level: str,
    analogy_preferences: str,
) -> OnboardingCard:
    seed_topic = starting_topic or learner_reason or "general learning"
    intent = normalize_intent(seed_topic)

    delight = (
        f"OpenDoor reads your starting direction as '{intent.clean_topic}'. "
        f"Your first door is not a random lesson. It is: {intent.first_door}."
    )

    if analogy_preferences:
        next_step = (
            f"Start with a {level.lower()} lesson using examples related to {analogy_preferences}. "
            f"Next action: {intent.next_best_action}"
        )
    else:
        next_step = f"Start with a {level.lower()} lesson. Next action: {intent.next_best_action}"

    return OnboardingCard(
        title=f"Welcome, {name or 'learner'}",
        learner_reason=learner_reason or "General learning",
        starting_topic=intent.clean_topic,
        first_door=intent.first_door,
        delight_moment=delight,
        next_step=next_step,
    )


def build_mood_energy_check() -> MoodEnergyCheck:
    return MoodEnergyCheck(
        prompt="What kind of session are we doing?",
        options=[
            "Quick review",
            "Normal lesson",
            "Deep work",
            "I feel stuck",
        ],
        use_for=(
            "This controls lesson length, difficulty, and whether OpenDoor should push forward "
            "or slow down and repair gaps."
        ),
    )


def build_mastery_map_preview(profile) -> List[MasteryNode]:
    weak_topics = getattr(profile, "weak_topics", []) or []
    strong_topics = getattr(profile, "strong_topics", []) or []
    goals = getattr(profile, "goals", "") or ""

    nodes: List[MasteryNode] = []

    if goals:
        intent = normalize_intent(goals)
        nodes.append(
            MasteryNode(
                name=intent.clean_topic,
                status="main path",
                mastery=0.25,
                forgetting_risk=0.5,
                note=f"Built from your goal. First door: {intent.first_door}",
            )
        )

    for topic in strong_topics[:4]:
        nodes.append(
            MasteryNode(
                name=topic,
                status="strength",
                mastery=0.75,
                forgetting_risk=0.25,
                note="Marked as a strength from your profile.",
            )
        )

    for topic in weak_topics[:4]:
        nodes.append(
            MasteryNode(
                name=topic,
                status="repair needed",
                mastery=0.35,
                forgetting_risk=0.65,
                note="Marked as a weak area. OpenDoor should repair this before harder work.",
            )
        )

    if not nodes:
        nodes.append(
            MasteryNode(
                name="Starting concept",
                status="not measured yet",
                mastery=0.0,
                forgetting_risk=1.0,
                note="Create a lesson or submit work to start measuring mastery.",
            )
        )

    return nodes


def build_session_summary(profile, assignment=None) -> SessionSummary:
    name = getattr(profile, "name", "learner")
    weak_topics = getattr(profile, "weak_topics", []) or []
    strong_topics = getattr(profile, "strong_topics", []) or []
    goals = getattr(profile, "goals", "") or ""

    since_last = []

    if goals:
        intent = normalize_intent(goals)
        since_last.append(f"Current path: {intent.clean_topic}.")
        since_last.append(f"First door: {intent.first_door}.")

    if strong_topics:
        since_last.append(f"Known strengths: {', '.join(strong_topics[:3])}.")

    if weak_topics:
        since_last.append(f"Current repair targets: {', '.join(weak_topics[:3])}.")

    if assignment:
        since_last.append(f"Last generated lesson: {assignment.topic}.")
        next_action = (
            f"Answer the learning questions for {assignment.topic}, then submit a Feynman explanation."
        )
        door = f"{assignment.topic} is now active in your learning path."
    else:
        next_action = "Build one lesson or paste homework so OpenDoor can update your learner model."
        door = None

    alerts = []

    for topic in weak_topics[:2]:
        alerts.append(
            f"{topic} is marked weak. Do a short repair task before harder related topics."
        )

    if not alerts:
        alerts.append("No forgetting alerts yet. OpenDoor needs more learning events first.")

    return SessionSummary(
        greeting=f"Welcome back, {name}.",
        since_last_session=since_last or ["No learning movement logged yet. Start with one small lesson."],
        forgetting_alerts=alerts,
        next_best_action=next_action,
        door_unlocked=door,
    )


def build_transparency_card(profile, assignment, retrieved_chunks) -> TransparencyCard:
    learner_model_used = [
        f"Level: {getattr(profile, 'level', 'unknown')}",
        f"Goals: {getattr(profile, 'goals', 'not set') or 'not set'}",
    ]

    weak_topics = getattr(profile, "weak_topics", []) or []
    strong_topics = getattr(profile, "strong_topics", []) or []

    if weak_topics:
        learner_model_used.append(f"Weak topics: {', '.join(weak_topics[:3])}")

    if strong_topics:
        learner_model_used.append(f"Strong topics: {', '.join(strong_topics[:3])}")

    if getattr(profile, "analogy_preferences", ""):
        learner_model_used.append(f"Example style: {profile.analogy_preferences}")

    if retrieved_chunks:
        source_note = f"Used {len(retrieved_chunks)} retrieved local source chunk(s)."
    else:
        source_note = "No local source chunks were used. This came from OpenDoor's built-in lesson structure."

    return TransparencyCard(
        assigned=assignment.topic,
        why=(
            f"OpenDoor assigned this because your request was normalized into '{assignment.topic}' "
            f"and matched your current learner profile."
        ),
        learner_model_used=learner_model_used,
        source_note=source_note,
        user_can_override=(
            "If this feels wrong, mark it too easy, too hard, or not relevant in a later build."
        ),
    )


def detect_basic_frustration(response_text: str, rewrite_count: int = 0) -> Optional[str]:
    lowered = str(response_text or "").lower()

    frustration_terms = [
        "i don't get it",
        "i dont get it",
        "this makes no sense",
        "i'm confused",
        "im confused",
        "stuck",
        "frustrated",
        "too hard",
    ]

    if rewrite_count >= 3:
        return "Multiple rewrites detected. Next response should slow down and use a different explanation style."

    if any(term in lowered for term in frustration_terms):
        return "Frustration signal detected. Next response should slow down, shorten, and repair the prerequisite."

    return None


def build_celebration_moment(event_type: str, concept: str) -> CelebrationMoment:
    if event_type == "misconception_repaired":
        return CelebrationMoment(
            title="Misconception repaired",
            message=(
                f"You repaired a misunderstanding around {concept}. "
                "That is more valuable than just getting one question right."
            ),
            unlocked=f"{concept} is now more stable in your learner graph.",
            next_hint="Do one recall check tomorrow to keep it from coming back.",
        )

    if event_type == "door_unlocked":
        return CelebrationMoment(
            title="Door opened",
            message=f"You opened the first door into {concept}.",
            unlocked=f"{concept} is now active in your learning path.",
            next_hint="Answer the learning questions, then submit a short explanation.",
        )

    if event_type == "project_completed":
        return CelebrationMoment(
            title="Project completed",
            message=f"You completed a project connected to {concept}.",
            unlocked=f"{concept} mastery should increase after review.",
            next_hint="Submit a short explanation of what the project proved.",
        )

    return CelebrationMoment(
        title="Progress logged",
        message=f"OpenDoor logged progress on {concept}.",
        unlocked=None,
        next_hint="Keep going with one small review or practice task.",
    )


def build_lapse_recovery_message(days_away: int, weak_topics: List[str]) -> str:
    if days_away < 7:
        return "No lapse recovery needed yet."

    if weak_topics:
        return (
            f"You have been away for {days_away} days. "
            f"Start with a 5-minute warm-up on {weak_topics[0]} before adding new material."
        )

    return (
        f"You have been away for {days_away} days. "
        "Start with a 5-minute warm-up before continuing."
    )


def build_path_direction(topic: str) -> List[str]:
    intent = normalize_intent(topic)

    if intent.domain == "trades_plumbing":
        return [
            "Plumbing apprentice path",
            "Residential repair fundamentals",
            "Pipe systems and fixtures path",
            "Code and safety awareness path",
            "Maintenance technician path",
        ]

    if intent.domain == "electronics":
        return [
            "Electronics hobbyist",
            "Embedded systems beginner",
            "Robotics project path",
            "Hardware repair path",
        ]

    if intent.domain == "programming":
        return [
            "Python developer",
            "Automation scripting",
            "Web app builder",
            "Data tools beginner",
        ]

    if intent.domain == "cybersecurity":
        return [
            "Network security",
            "Linux security fundamentals",
            "SOC analyst path",
            "Defensive lab builder",
        ]

    if intent.domain == "mechanical_fuel":
        return [
            "Mechanical systems literacy",
            "Equipment maintenance basics",
            "Agricultural tech learning path",
            "Safety-first troubleshooting",
        ]

    return [
        "General foundations",
        "Project-based learning path",
        "Study and review path",
    ]