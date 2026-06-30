from dataclasses import dataclass


QUESTION_STARTERS = [
    "how would i",
    "how do i",
    "how can i",
    "what is",
    "what are",
    "why does",
    "why do",
    "can you teach me",
    "teach me",
    "explain",
    "i want to learn",
    "help me learn",
]


@dataclass
class NormalizedIntent:
    raw_input: str
    clean_topic: str
    learning_goal: str
    safety_frame: str
    output_mode: str
    domain: str
    user_facing_summary: str


def clean_sentence(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def remove_question_starter(text: str) -> str:
    stripped = text.strip(" ?.!").strip()
    lowered = stripped.lower()

    for starter in QUESTION_STARTERS:
        if lowered.startswith(starter):
            return stripped[len(starter):].strip(" ?.!").strip()

    return stripped


def infer_domain(raw_input: str) -> str:
    lowered = raw_input.lower()

    if any(word in lowered for word in ["tractor", "engine", "fuel", "diesel", "biodiesel", "mechanic"]):
        return "mechanical_fuel"

    if any(word in lowered for word in ["cyber", "malware", "exploit", "network", "linux", "packet", "firewall"]):
        return "cybersecurity"

    if any(word in lowered for word in ["solder", "resistor", "circuit", "arduino", "esp32", "voltage", "current"]):
        return "electronics"

    if any(word in lowered for word in ["python", "function", "class", "code", "programming", "javascript"]):
        return "programming"

    if any(word in lowered for word in ["algebra", "calculus", "equation", "geometry", "statistics"]):
        return "math"

    if any(word in lowered for word in ["bake", "muffin", "cook", "recipe"]):
        return "food"

    return "general"


def infer_clean_topic(raw_input: str) -> str:
    raw = clean_sentence(raw_input)
    lowered = raw.lower()

    if "tractor" in lowered and any(word in lowered for word in ["fuel", "natural", "biodiesel", "diesel"]):
        return "Alternative tractor fuel options"

    if "muffin" in lowered or "bake" in lowered:
        return "Basic baking timing and food preparation"

    if "cidr" in lowered:
        return "CIDR notation"

    if "solder" in lowered:
        return "Soldering basics"

    if "resistor" in lowered:
        return "Resistors and current limiting"

    if "python" in lowered and "function" in lowered:
        return "Python functions"

    stripped = remove_question_starter(raw)

    if not stripped:
        return "General learning request"

    return stripped[:1].upper() + stripped[1:]


def infer_safety_frame(raw_input: str, clean_topic: str, domain: str) -> str:
    lowered = f"{raw_input} {clean_topic}".lower()

    if domain == "mechanical_fuel":
        return (
            "Use a high-level, safety-focused explanation. Discuss engine type, fuel compatibility, "
            "mechanical risk, environmental/legal considerations, manuals, and professional inspection. "
            "Avoid dangerous step-by-step fuel production recipes or unsafe engine modification instructions."
        )

    if domain == "cybersecurity":
        return (
            "Use defensive, legal, educational framing. Avoid credential theft, evasion, persistence, "
            "malware deployment, exploit execution steps, or instructions that enable harm."
        )

    if any(word in lowered for word in ["medical", "legal", "financial", "tax"]):
        return (
            "Use educational framing. Do not pretend to be a professional advisor. "
            "Encourage qualified professional review for decisions with real consequences."
        )

    return "Use normal educational framing."


def infer_learning_goal(raw_input: str, clean_topic: str) -> str:
    lowered = raw_input.lower()

    if lowered.startswith(("how", "can")):
        return f"Understand the safe practical options, decision points, and limits around {clean_topic}."

    if lowered.startswith(("what", "why")):
        return f"Understand the meaning, purpose, examples, and common mistakes around {clean_topic}."

    return f"Build a beginner-friendly understanding of {clean_topic}."


def infer_output_mode(raw_input: str) -> str:
    lowered = raw_input.lower()

    if any(word in lowered for word in ["homework", "assignment", "grade", "review my answer"]):
        return "homework_review"

    if any(word in lowered for word in ["quick", "short", "simple answer"]):
        return "quick_chat"

    return "lesson"


def normalize_intent(raw_input: str) -> NormalizedIntent:
    raw = clean_sentence(raw_input)
    domain = infer_domain(raw)
    clean_topic = infer_clean_topic(raw)
    learning_goal = infer_learning_goal(raw, clean_topic)
    safety_frame = infer_safety_frame(raw, clean_topic, domain)
    output_mode = infer_output_mode(raw)

    user_facing_summary = (
        f"I read this as: learn about {clean_topic}. "
        f"Goal: {learning_goal}"
    )

    return NormalizedIntent(
        raw_input=raw,
        clean_topic=clean_topic,
        learning_goal=learning_goal,
        safety_frame=safety_frame,
        output_mode=output_mode,
        domain=domain,
        user_facing_summary=user_facing_summary,
    )