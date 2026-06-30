from dataclasses import dataclass
from typing import List

from intent_normalizer import NormalizedIntent


@dataclass
class LearningQuestionSet:
    comprehension: List[str]
    misconception_checks: List[str]
    application: List[str]
    feynman: str
    next_step: str


def build_learning_questions(intent: NormalizedIntent) -> LearningQuestionSet:
    topic = intent.clean_topic
    domain = intent.domain

    if domain == "mechanical_fuel":
        return LearningQuestionSet(
            comprehension=[
                "What type of engine are we talking about: diesel, gasoline, or something else?",
                "Why does engine type matter before considering alternative fuels?",
                "What does fuel compatibility mean in simple terms?",
            ],
            misconception_checks=[
                "Why is it unsafe to assume any natural or homemade fuel will work in an engine?",
                "What could go wrong if fuel viscosity, combustion behavior, or filtration is wrong?",
            ],
            application=[
                "Make a safe decision checklist someone should complete before changing anything about a tractor fuel system.",
            ],
            feynman=(
                "Explain alternative tractor fuel options to a smart beginner. "
                "Keep it high-level, focus on safety, and explain why manuals or mechanics matter."
            ),
            next_step=(
                "Identify the tractor engine type and find the manufacturer fuel recommendations before learning anything deeper."
            ),
        )

    if domain == "electronics":
        return LearningQuestionSet(
            comprehension=[
                f"What is the basic purpose of {topic}?",
                f"What are the most important parts or terms inside {topic}?",
                f"Where would you see {topic} in a real electronics project?",
            ],
            misconception_checks=[
                f"What is one beginner mistake people make with {topic}?",
                f"What would someone misunderstand if they only memorized the definition of {topic}?",
            ],
            application=[
                f"Describe one small hands-on project that would prove someone understands {topic}.",
            ],
            feynman=f"Explain {topic} using plain language and one electronics example.",
            next_step=f"Create one small practice task that uses {topic} in a real project.",
        )

    if domain == "programming":
        return LearningQuestionSet(
            comprehension=[
                f"What problem does {topic} solve?",
                f"What are the core terms someone must know before using {topic}?",
                f"What is a tiny code example where {topic} would appear?",
            ],
            misconception_checks=[
                f"What is one common beginner bug related to {topic}?",
                f"What would someone misunderstand if they copied code using {topic} without explaining it?",
            ],
            application=[
                f"Write or describe a small program that proves you understand {topic}.",
            ],
            feynman=f"Explain {topic} to someone who has written a few lines of code but is still new.",
            next_step=f"Build a small example using {topic}, then explain each line.",
        )

    if domain == "cybersecurity":
        return LearningQuestionSet(
            comprehension=[
                f"What is {topic} used for in defensive or educational work?",
                f"What terms do you need before learning {topic}?",
                f"What is one safe lab-style example of {topic}?",
            ],
            misconception_checks=[
                f"What is the difference between learning {topic} defensively and using it irresponsibly?",
                f"What boundary should a learner not cross when studying {topic}?",
            ],
            application=[
                f"Create a safe study lab checklist for learning {topic}.",
            ],
            feynman=f"Explain {topic} safely and defensively to a beginner.",
            next_step=f"Pick one legal lab or documentation source to study {topic} safely.",
        )

    return LearningQuestionSet(
        comprehension=[
            f"What is {topic} in plain language?",
            f"Why does {topic} matter?",
            f"What are the 3 most important words or ideas connected to {topic}?",
        ],
        misconception_checks=[
            f"What is one thing beginners often misunderstand about {topic}?",
            f"What is the difference between knowing the definition of {topic} and actually using it?",
        ],
        application=[
            f"Give one real-world example where {topic} matters.",
        ],
        feynman=f"Explain {topic} to a smart beginner using one analogy and one example.",
        next_step=f"Create one small task that proves you understand {topic}.",
    )