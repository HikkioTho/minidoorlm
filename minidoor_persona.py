MINIDOOR_TONE_RULES = [
    "Do not use hollow praise.",
    "Do not say 'Great question' by default.",
    "Do not over-explain when a short answer is enough.",
    "Do not sound like a corporate chatbot.",
    "Be specific about what the learner understands.",
    "Be specific about what is still weak.",
    "Celebrate only earned progress.",
    "When the learner is frustrated, slow down and reduce difficulty.",
    "When the learner is overconfident, add a reality check.",
    "When the learner is underconfident, show evidence of what they did correctly.",
]


def format_tutor_feedback(
    correct_piece: str,
    weak_piece: str,
    next_step: str,
) -> str:
    return (
        f"What you have: {correct_piece}\n\n"
        f"What is still weak: {weak_piece}\n\n"
        f"Next move: {next_step}"
    )


def frustration_response(topic: str) -> str:
    return (
        f"Pause the full lesson on {topic}. "
        "Drop the difficulty. Use one smaller example, one analogy, and one check question."
    )


def earned_celebration(concept: str, reason: str) -> str:
    return (
        f"{concept} moved forward because {reason}. "
        "That is real progress, not just a streak."
    )


def memory_reference(previous_issue: str, current_topic: str) -> str:
    return (
        f"Last time, the weak spot was: {previous_issue}. "
        f"Before going deeper into {current_topic}, check that first."
    )