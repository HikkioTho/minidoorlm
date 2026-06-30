from dataclasses import dataclass


QUESTION_STARTERS = [
    "how would i",
    "how do i",
    "how can i",
    "where do i start with",
    "where should i start with",
    "how do i start with",
    "how do i start",
    "how do i begin",
    "how can i begin",
    "what is",
    "what are",
    "why does",
    "why do",
    "can you teach me",
    "teach me",
    "explain",
    "i want to learn",
    "help me learn",
    "start with",
    "begin with",
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
    first_door: str
    next_best_action: str


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

    if any(word in lowered for word in ["plumbing", "plumber", "pipe", "pipes", "water heater", "drain", "fixture"]):
        return "trades_plumbing"

    if any(word in lowered for word in ["career", "job", "apprentice", "apprenticeship", "certification", "trade school"]):
        return "career_path"

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

    if any(word in lowered for word in ["plumbing", "plumber"]):
        if any(word in lowered for word in ["career", "job", "begin", "start", "apprentice", "apprenticeship"]):
            return "Starting a plumbing career"
        return "Plumbing fundamentals"

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

    if domain == "trades_plumbing":
        return (
            "Use educational and safety-aware framing. Explain concepts, tools, career steps, "
            "and basic troubleshooting at a high level. For real plumbing work, mention local code, "
            "permits, licensing rules, and qualified supervision."
        )

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


def infer_learning_goal(raw_input: str, clean_topic: str, domain: str) -> str:
    lowered = raw_input.lower()

    if domain == "trades_plumbing":
        if any(word in lowered for word in ["career", "job", "begin", "start", "apprentice", "apprenticeship"]):
            return (
                "Understand the first safe steps toward plumbing: basic concepts, tools, code awareness, "
                "apprenticeship options, and beginner practice areas."
            )

        return (
            "Build a practical beginner understanding of plumbing systems, basic components, tools, "
            "safety, and when to call a licensed professional."
        )

    if domain == "mechanical_fuel":
        return (
            f"Understand the safe practical options, decision points, and limits around {clean_topic}."
        )

    if lowered.startswith(("how", "can", "where")):
        return f"Understand the practical starting path, decision points, and safe next steps around {clean_topic}."

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


def infer_first_door(clean_topic: str, domain: str) -> str:
    if domain == "trades_plumbing":
        return "Plumbing basics: water supply, drainage, tools, safety, and code awareness"

    if domain == "mechanical_fuel":
        return "Engine type and manufacturer fuel requirements"

    if domain == "electronics":
        return "Core vocabulary and one safe hands-on example"

    if domain == "programming":
        return "Small working example plus explanation"

    if domain == "cybersecurity":
        return "Safe lab framing and defensive vocabulary"

    return f"Basic understanding of {clean_topic}"


def infer_next_best_action(clean_topic: str, domain: str) -> str:
    if domain == "trades_plumbing":
        return (
            "Start with the plumbing system map: supply, drain, vent, fixtures, shutoff valves, "
            "basic tools, and local licensing/code awareness. Then pick one tiny practice topic."
        )

    if domain == "mechanical_fuel":
        return "Identify the engine type and manufacturer fuel requirements before learning deeper options."

    if domain == "electronics":
        return "Do one small explanation task, then one hands-on practice task."

    if domain == "programming":
        return "Write one tiny example, run it, then explain each line."

    return f"Learn the core idea of {clean_topic}, answer one check question, then do one small practice task."


def normalize_intent(raw_input: str) -> NormalizedIntent:
    raw = clean_sentence(raw_input)
    domain = infer_domain(raw)
    clean_topic = infer_clean_topic(raw)
    learning_goal = infer_learning_goal(raw, clean_topic, domain)
    safety_frame = infer_safety_frame(raw, clean_topic, domain)
    output_mode = infer_output_mode(raw)
    first_door = infer_first_door(clean_topic, domain)
    next_best_action = infer_next_best_action(clean_topic, domain)

    user_facing_summary = (
        f"I read this as: {clean_topic}. "
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
        first_door=first_door,
        next_best_action=next_best_action,
    )