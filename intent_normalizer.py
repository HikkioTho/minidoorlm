from dataclasses import dataclass
from difflib import get_close_matches


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


KNOWN_TOPIC_ALIASES = {
    "plumbing": [
        "plumbing",
        "plumber",
        "plumming",
        "pluming",
        "pipes",
        "pipe fitting",
    ],
    "conlang": [
        "conlang",
        "conlanging",
        "constructed language",
        "constructed languages",
        "language design",
    ],
    "coding": [
        "coding",
        "programming",
        "code",
        "python",
        "javascript",
    ],
    "electronics": [
        "electronics",
        "circuits",
        "resistor",
        "soldering",
        "arduino",
        "esp32",
    ],
    "cybersecurity": [
        "cybersecurity",
        "network security",
        "linux security",
        "cidr",
        "firewall",
    ],
    "math": [
        "math",
        "algebra",
        "calculus",
        "statistics",
        "geometry",
    ],
}


COMMON_TYPOS = {
    "conlnog": "conlang",
    "cohlnong": "conlang",
    "conlong": "conlang",
    "conlanging": "conlanging",
    "plumming": "plumbing",
    "pluming": "plumbing",
    "pyhton": "python",
    "phyton": "python",
    "javscript": "javascript",
    "maths": "math",
}


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
    confidence: float
    needs_clarification: bool
    clarification_question: str
    suggested_topics: list[str]


def clean_sentence(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def remove_question_starter(text: str) -> str:
    stripped = text.strip(" ?.!").strip()
    lowered = stripped.lower()

    for starter in QUESTION_STARTERS:
        if lowered.startswith(starter):
            return stripped[len(starter):].strip(" ?.!").strip()

    return stripped


def normalize_typos(text: str) -> str:
    words = text.split()
    fixed_words = []

    for word in words:
        clean_word = word.lower().strip(" ?.!,")

        if clean_word in COMMON_TYPOS:
            fixed_words.append(COMMON_TYPOS[clean_word])
        else:
            fixed_words.append(word)

    return " ".join(fixed_words)


def all_aliases() -> list[str]:
    aliases = []

    for values in KNOWN_TOPIC_ALIASES.values():
        aliases.extend(values)

    return aliases


def find_alias_topic(text: str) -> str | None:
    lowered = text.lower()

    for canonical, aliases in KNOWN_TOPIC_ALIASES.items():
        for alias in aliases:
            if alias in lowered:
                return canonical

    words = lowered.replace("?", "").replace(".", "").replace(",", "").split()

    for word in words:
        match = get_close_matches(word, all_aliases(), n=1, cutoff=0.82)

        if match:
            matched_alias = match[0]

            for canonical, aliases in KNOWN_TOPIC_ALIASES.items():
                if matched_alias in aliases:
                    return canonical

    return None


def infer_domain(raw_input: str, alias_topic: str | None) -> str:
    lowered = raw_input.lower()

    if alias_topic == "plumbing":
        return "trades_plumbing"

    if alias_topic == "conlang":
        return "creative_language"

    if alias_topic == "coding":
        return "programming"

    if alias_topic == "electronics":
        return "electronics"

    if alias_topic == "cybersecurity":
        return "cybersecurity"

    if alias_topic == "math":
        return "math"

    if any(word in lowered for word in ["career", "job", "apprentice", "apprenticeship", "certification", "trade school"]):
        return "career_path"

    if any(word in lowered for word in ["tractor", "engine", "fuel", "diesel", "biodiesel", "mechanic"]):
        return "mechanical_fuel"

    if any(word in lowered for word in ["bake", "muffin", "cook", "recipe"]):
        return "food"

    return "general"


def infer_clean_topic(raw_input: str, alias_topic: str | None) -> str:
    raw = clean_sentence(raw_input)
    lowered = raw.lower()

    if alias_topic == "plumbing":
        if any(word in lowered for word in ["career", "job", "begin", "start", "apprentice", "apprenticeship"]):
            return "Starting a plumbing career"
        return "Plumbing fundamentals"

    if alias_topic == "conlang":
        return "Conlanging basics"

    if alias_topic == "coding":
        if "python" in lowered:
            return "Python programming"
        return "Programming fundamentals"

    if alias_topic == "electronics":
        if "solder" in lowered:
            return "Soldering basics"
        if "resistor" in lowered:
            return "Resistors and current limiting"
        return "Electronics fundamentals"

    if alias_topic == "cybersecurity":
        if "cidr" in lowered:
            return "CIDR notation"
        return "Cybersecurity fundamentals"

    if alias_topic == "math":
        return "Math fundamentals"

    if "tractor" in lowered and any(word in lowered for word in ["fuel", "natural", "biodiesel", "diesel"]):
        return "Alternative tractor fuel options"

    if "muffin" in lowered or "bake" in lowered:
        return "Basic baking timing and food preparation"

    stripped = remove_question_starter(raw)

    if not stripped:
        return "General learning request"

    return stripped[:1].upper() + stripped[1:]


def is_unclear_request(raw_input: str, clean_topic: str, alias_topic: str | None) -> bool:
    lowered = raw_input.lower().strip()
    stripped = remove_question_starter(lowered)

    if alias_topic:
        return False

    if len(stripped) <= 3:
        return True

    known_single_word_topics = {
        "math",
        "coding",
        "plumbing",
        "electronics",
        "cybersecurity",
        "python",
        "cidr",
        "conlang",
        "conlanging",
    }

    if len(stripped.split()) == 1 and stripped not in known_single_word_topics:
        return True

    nonsense_signals = [
        "asdf",
        "qwer",
        "idk",
        "stuff",
        "things",
    ]

    if any(signal == stripped for signal in nonsense_signals):
        return True

    if clean_topic.lower() in {"general learning request", "begin", "start", "learn"}:
        return True

    return False


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

    if domain == "creative_language":
        return (
            "Learn how to create a constructed language by starting with sounds, grammar rules, basic words, "
            "and simple sentence patterns."
        )

    if domain == "mechanical_fuel":
        return f"Understand the safe practical options, decision points, and limits around {clean_topic}."

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

    if domain == "creative_language":
        return "Conlang basics: sounds, grammar, core words, and simple sentences"

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

    if domain == "creative_language":
        return "Choose the sound style first, then create 10 root words and one basic sentence rule."

    if domain == "mechanical_fuel":
        return "Identify the engine type and manufacturer fuel requirements before learning deeper options."

    if domain == "electronics":
        return "Do one small explanation task, then one hands-on practice task."

    if domain == "programming":
        return "Write one tiny example, run it, then explain each line."

    return f"Learn the core idea of {clean_topic}, answer one check question, then do one small practice task."


def suggested_topics_for(raw_input: str) -> list[str]:
    lowered = raw_input.lower()

    if "con" in lowered or "lang" in lowered:
        return [
            "Conlanging basics",
            "Creative writing worldbuilding",
            "Language design basics",
        ]

    if "plumb" in lowered or "pipe" in lowered:
        return [
            "Starting a plumbing career",
            "Plumbing fundamentals",
            "Basic pipe and drain systems",
        ]

    return [
        "Programming fundamentals",
        "Plumbing fundamentals",
        "Electronics fundamentals",
        "Math fundamentals",
    ]


def build_clarification_question(raw_input: str, suggestions: list[str]) -> str:
    options = ", ".join(suggestions[:3])

    return (
        f"I am not confident I understood '{raw_input}'. "
        f"Did you mean one of these: {options}? "
        "Rephrase it like 'teach me plumbing basics' or 'build a lesson on conlanging basics'."
    )


def normalize_intent(raw_input: str) -> NormalizedIntent:
    raw = clean_sentence(raw_input)
    typo_fixed = normalize_typos(raw)
    alias_topic = find_alias_topic(typo_fixed)
    domain = infer_domain(typo_fixed, alias_topic)
    clean_topic = infer_clean_topic(typo_fixed, alias_topic)
    unclear = is_unclear_request(typo_fixed, clean_topic, alias_topic)
    suggestions = suggested_topics_for(typo_fixed)

    if unclear:
        confidence = 0.25
        clarification_question = build_clarification_question(raw, suggestions)
    elif alias_topic:
        confidence = 0.92
        clarification_question = ""
    else:
        confidence = 0.65
        clarification_question = ""

    learning_goal = infer_learning_goal(typo_fixed, clean_topic, domain)
    safety_frame = infer_safety_frame(typo_fixed, clean_topic, domain)
    output_mode = infer_output_mode(typo_fixed)
    first_door = infer_first_door(clean_topic, domain)
    next_best_action = infer_next_best_action(clean_topic, domain)

    if unclear:
        user_facing_summary = clarification_question
    else:
        user_facing_summary = f"I read this as: {clean_topic}. Goal: {learning_goal}"

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
        confidence=confidence,
        needs_clarification=unclear,
        clarification_question=clarification_question,
        suggested_topics=suggestions,
    )