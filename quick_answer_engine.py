import ast
import operator
import re
from dataclasses import dataclass
from typing import Optional

from intent_normalizer import normalize_intent


@dataclass
class QuickAnswer:
    answer_type: str
    title: str
    answer: str
    next_step: str


SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


SPELLING_FIXES = {
    "whats": "what is",
    "what's": "what is",
    "1st": "first",
    "2nd": "second",
    "3rd": "third",
    "therodnynamics": "thermodynamics",
    "thermodynmics": "thermodynamics",
    "thermodnamics": "thermodynamics",
    "thermo dynamics": "thermodynamics",
    "ohms": "ohm's",
    "ohms law": "ohm's law",
    "conlnog": "conlang",
    "cohlnong": "conlang",
    "conlong": "conlang",
    "plumming": "plumbing",
    "pluming": "plumbing",
}


def normalize_question_text(message: str) -> str:
    text = " ".join(str(message or "").lower().strip().split())

    for wrong, right in SPELLING_FIXES.items():
        text = text.replace(wrong, right)

    text = text.replace("?", "").strip()

    return text


def safe_eval_math(expression: str) -> float:
    def eval_node(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPERATORS:
            return SAFE_OPERATORS[type(node.op)](
                eval_node(node.left),
                eval_node(node.right),
            )

        if isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPERATORS:
            return SAFE_OPERATORS[type(node.op)](eval_node(node.operand))

        raise ValueError("Unsupported math expression.")

    parsed = ast.parse(expression, mode="eval")
    return eval_node(parsed.body)


def extract_math_expression(message: str) -> str:
    text = normalize_question_text(message)

    replacements = {
        "what is": "",
        "calculate": "",
        "solve": "",
        "equals": "=",
        "x": "*",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.strip()

    if "=" in text:
        text = text.split("=")[0].strip()

    allowed = re.findall(r"[0-9\.\+\-\*\/\%\(\)\s]+", text)
    expression = "".join(allowed).strip()

    return expression


def looks_like_math(message: str) -> bool:
    text = normalize_question_text(message)

    if re.search(r"\d+\s*[\+\-\*\/]\s*\d+", text):
        return True

    if text.startswith(("what is", "calculate", "solve")) and any(char.isdigit() for char in text):
        return True

    return False


def answer_math(message: str) -> QuickAnswer:
    expression = extract_math_expression(message)

    if not expression:
        raise ValueError("No math expression found.")

    result = safe_eval_math(expression)

    if isinstance(result, float) and result.is_integer():
        result_text = str(int(result))
    else:
        result_text = str(result)

    return QuickAnswer(
        answer_type="math",
        title="Math answer",
        answer=f"{expression} = {result_text}",
        next_step="Ask another quick question or build a lesson if you want practice problems.",
    )


def answer_known_fact(message: str) -> Optional[QuickAnswer]:
    lowered = normalize_question_text(message)

    if "first law" in lowered and "thermodynamics" in lowered:
        return QuickAnswer(
            answer_type="known_fact",
            title="First law of thermodynamics",
            answer=(
                "The first law of thermodynamics says energy cannot be created or destroyed, "
                "only transferred or changed from one form to another. A system's energy changes "
                "when heat enters or leaves and when work is done by or on the system."
            ),
            next_step=(
                "Check your understanding: if heat is added to gas in a piston and the piston moves upward, "
                "some energy became work and some may remain as internal energy."
            ),
        )

    if "second law" in lowered and "thermodynamics" in lowered:
        return QuickAnswer(
            answer_type="known_fact",
            title="Second law of thermodynamics",
            answer=(
                "The second law of thermodynamics says entropy tends to increase in a closed system. "
                "In plain language, energy spreads out and systems naturally move toward less usable energy "
                "unless work is done to maintain order."
            ),
            next_step="Compare useful energy, wasted heat, and entropy in an engine.",
        )

    if "ohm's law" in lowered or "ohm law" in lowered:
        return QuickAnswer(
            answer_type="known_fact",
            title="Ohm's Law",
            answer=(
                "Ohm's Law says voltage equals current times resistance. Formula: V = I × R. "
                "Voltage is the push, current is the flow, and resistance limits that flow."
            ),
            next_step="Try this: if voltage is 5V and resistance is 220 ohms, calculate current.",
        )

    if "cidr" in lowered:
        return QuickAnswer(
            answer_type="known_fact",
            title="CIDR notation",
            answer=(
                "CIDR notation is a compact way to describe an IP network and how many bits are used "
                "for the network part. For example, /24 means the first 24 bits identify the network, "
                "leaving 8 bits for host addresses."
            ),
            next_step="Compare /24, /25, and /26 to see how network size changes.",
        )

    if "resistor" in lowered and ("what" in lowered or "do" in lowered):
        return QuickAnswer(
            answer_type="known_fact",
            title="Resistor",
            answer=(
                "A resistor limits current in a circuit. It does not simply use up electricity. "
                "It controls how much current can flow, often protecting parts like LEDs from too much current."
            ),
            next_step="A good first task is calculating the resistor needed for an LED.",
        )

    if "shutoff valve" in lowered:
        return QuickAnswer(
            answer_type="known_fact",
            title="Shutoff valve",
            answer=(
                "A shutoff valve controls water flow to a fixture or section of plumbing. "
                "Knowing where shutoff valves are matters because you can stop water before a leak or repair gets worse."
            ),
            next_step="Find the shutoff valves under one sink and identify which line is hot and which is cold.",
        )

    return None


def answer_racing(message: str) -> Optional[QuickAnswer]:
    lowered = normalize_question_text(message)

    racing_terms = [
        "stock car",
        "nascar",
        "car racing",
        "racing",
        "race car",
    ]

    if not any(term in lowered for term in racing_terms):
        return None

    if "first rule" in lowered or "1st rule" in lowered:
        return QuickAnswer(
            answer_type="sports_racing",
            title="First rule of stock car racing",
            answer=(
                "The practical first rule is safety and control. Know the rules of the track, keep control of the car, "
                "respect flags and officials, and do not drive in a way that puts other drivers, crews, or spectators at risk. "
                "Speed matters, but controlled driving comes first."
            ),
            next_step=(
                "First door: learn the flag system, basic racing line, passing rules, and what to do when something goes wrong."
            ),
        )

    return QuickAnswer(
        answer_type="sports_racing",
        title="Stock car racing basics",
        answer=(
            "Stock car racing is built around controlled speed, racecraft, track awareness, car setup, and safety rules. "
            "Beginners should learn flags, the racing line, braking points, passing etiquette, and basic vehicle control first."
        ),
        next_step="Start with flags, track safety, and the racing line before studying advanced strategy.",
    )


def answer_plumbing_start(message: str) -> Optional[QuickAnswer]:
    lowered = normalize_question_text(message)

    if "plumbing" not in lowered and "plumber" not in lowered:
        return None

    if any(word in lowered for word in ["career", "job", "start", "begin", "apprentice", "apprenticeship"]):
        return QuickAnswer(
            answer_type="career_path",
            title="Starting a plumbing career",
            answer=(
                "Start by learning the basic plumbing system map: water supply, drainage, venting, fixtures, traps, "
                "and shutoff valves. Then look up your local apprenticeship or trade-school path, because plumbing "
                "is code and license driven. A smart first step is not doing repairs yet. It is learning parts, tools, "
                "safety, and the rules in your area."
            ),
            next_step=(
                "First door: map one sink. Identify the supply lines, shutoff valves, trap, and drain path. "
                "Then look up plumbing apprentice requirements in your state."
            ),
        )

    return QuickAnswer(
        answer_type="trade_basics",
        title="Plumbing basics",
        answer=(
            "Plumbing is the system that brings clean water in, moves waste water out, and uses venting so drains "
            "work correctly. The first things to learn are supply lines, drain lines, vent lines, traps, fixtures, "
            "shutoff valves, and basic safety."
        ),
        next_step="First door: identify the parts under one sink without changing anything.",
    )


def answer_conlang(message: str) -> Optional[QuickAnswer]:
    lowered = normalize_question_text(message)

    if "conlang" not in lowered and "constructed language" not in lowered and "conlanging" not in lowered:
        return None

    return QuickAnswer(
        answer_type="creative_language",
        title="Conlanging basics",
        answer=(
            "Conlanging means creating a constructed language. Start with the sound system, then decide simple grammar rules, "
            "make a small set of root words, and test the language by writing tiny sentences. Do not start by inventing thousands "
            "of words. Start with the rules that make the language feel consistent."
        ),
        next_step="First door: choose 10 sounds, make 10 root words, then write 3 simple sentences.",
    )


def answer_basic_science(message: str) -> Optional[QuickAnswer]:
    lowered = normalize_question_text(message)

    if "photosynthesis" in lowered:
        return QuickAnswer(
            answer_type="known_fact",
            title="Photosynthesis",
            answer=(
                "Photosynthesis is how plants use sunlight, carbon dioxide, and water to make sugar for energy. "
                "Oxygen is released as a byproduct."
            ),
            next_step="A good check question is: where do the carbon atoms in plant sugar come from?",
        )

    if "gravity" in lowered:
        return QuickAnswer(
            answer_type="known_fact",
            title="Gravity",
            answer=(
                "Gravity is the attractive force between objects with mass. On Earth, it pulls objects toward the ground. "
                "On a larger scale, gravity keeps planets, moons, and stars moving in orbits."
            ),
            next_step="Next, compare weight and mass because people often mix them up.",
        )

    return None


def build_unknown_quick_answer(message: str) -> QuickAnswer:
    intent = normalize_intent(message)

    if intent.needs_clarification:
        return QuickAnswer(
            answer_type="clarification",
            title="I need one clarification",
            answer=intent.clarification_question,
            next_step="Pick one of the suggested topics or rephrase the request.",
        )

    return QuickAnswer(
        answer_type="unknown_quick_answer",
        title="Not in quick-answer mode yet",
        answer=(
            f"I can route this as a learning topic: {intent.clean_topic}.\n\n"
            "But I do not have a direct quick-answer card for this yet. "
            "Use Build lesson if you want OpenDoor to turn it into a learning path."
        ),
        next_step=f"Switch to Build lesson for: {intent.clean_topic}.",
    )


def build_quick_answer(message: str) -> QuickAnswer:
    clean_message = message.strip()

    if not clean_message:
        return QuickAnswer(
            answer_type="empty",
            title="No question",
            answer="Type a question first.",
            next_step="Ask something like: what is CIDR? or how do I start plumbing?",
        )

    normalized_message = normalize_question_text(clean_message)

    if looks_like_math(normalized_message):
        try:
            return answer_math(normalized_message)
        except Exception:
            pass

    quick_answer_routes = [
        answer_known_fact,
        answer_racing,
        answer_plumbing_start,
        answer_conlang,
        answer_basic_science,
    ]

    for route in quick_answer_routes:
        answer = route(normalized_message)

        if answer:
            return answer

    return build_unknown_quick_answer(clean_message)


def format_quick_answer(answer: QuickAnswer, profile=None) -> str:
    profile_line = ""

    if profile and answer.answer_type not in {"math", "known_fact"}:
        profile_line = (
            f"\n\nProfile used: {profile.name}, level {profile.level}, goal: {profile.goals or 'not set'}."
        )

    return (
        f"**{answer.title}**\n\n"
        f"{answer.answer}\n\n"
        f"**Next step:** {answer.next_step}"
        f"{profile_line}"
    )