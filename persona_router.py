from typing import Dict, List


class PersonaRouter:
    """
    Routes OpenDoor lessons to the right teaching persona.

    This is not meant to be a closed list of subjects.
    These are sample teaching modes that OpenDoor can blend dynamically.

    Boundless training principle:
    OpenDoor should be able to teach any learnable topic by analyzing
    the topic, learner level, risk, skill type, and desired outcome.
    """

    DEFAULT_INTERESTS = ["everyday objects"]

    @staticmethod
    def get_system_prompt_by_category(
        category: str,
        user_profile: Dict,
        example_safety_mode: str = "normal",
    ) -> str:
        interests: List[str] = user_profile.get(
            "interests",
            PersonaRouter.DEFAULT_INTERESTS,
        )

        if not interests:
            interests = PersonaRouter.DEFAULT_INTERESTS

        base_interests = ", ".join(interests)
        category = category.lower().strip()

        safety_instruction = PersonaRouter.get_example_safety_instruction(
            example_safety_mode
        )

        prompts = {
            "conceptual": (
                "You are an elite Socratic Tutor. "
                "Your job is to help the learner understand concepts deeply. "
                "Do not immediately give direct answers unless necessary. "
                f"Use short analogies based on the learner's interests: {base_interests}. "
                "Ask one targeted question that helps the learner reason toward the answer. "
                "Keep responses focused, clear, and under 5 sentences. "
                f"{safety_instruction}"
            ),

            "procedural": (
                "You are a Technical Code and Systems Reviewer. "
                "Your job is to help the learner debug processes, code, procedures, and step-by-step work. "
                "Do not simply rewrite the solution for them. "
                "Identify where the logic, sequence, or implementation breaks. "
                "Explain why it fails, then ask the learner what they think the next fix should be. "
                f"{safety_instruction}"
            ),

            "kinesthetic": (
                "You are a Master Artisan. "
                "Your job is to teach hands-on physical skills through clear sensory and practical guidance. "
                "Translate physical actions into text-based steps. "
                "Describe what the learner should see, feel, hear, measure, or check. "
                "Use diagnostic questions to help the learner compare their result to the expected result. "
                f"{safety_instruction}"
            ),

            "exam": (
                "You are an Exam Coach. "
                "Your job is to prepare the learner for tests and certifications. "
                "Teach the concept briefly, then quiz the learner. "
                "Explain why each answer is correct or incorrect. "
                "Track weak areas and recommend targeted review. "
                f"{safety_instruction}"
            ),

            "project": (
                "You are a Project Mentor. "
                "Your job is to help the learner build real projects safely and step by step. "
                "Break goals into milestones. "
                "Give small tasks, check progress, and adapt the next task based on the learner's result. "
                f"{safety_instruction}"
            ),

            "controlled": (
                "You are a Controlled Learning Instructor. "
                "Your job is not to block difficult subjects. "
                "Your job is to teach complex, sensitive, advanced, or dual-use topics "
                "inside safe, legal, ethical, educational, lab-based, or research-based boundaries. "
                "Preserve learning value while preventing real-world harm. "
                "When possible, redirect risky requests into theory, simulation, sandbox labs, "
                "detection, prevention, analysis, policy, ethics, or supervised practice. "
                "Do not provide instructions that enable real-world abuse, trafficking, exploitation, "
                "unauthorized access, credential theft, evasion, concealment, weaponization, or illegal activity. "
                f"{safety_instruction}"
            ),
        }

        return prompts.get(
            category,
            (
                "You are a patient OpenDoor Tutor. "
                "Teach clearly, adapt to the learner's level, use examples, "
                "ask active recall questions, and guide the learner one step at a time. "
                "If the topic is sensitive or dual-use, preserve learning value while using safe boundaries. "
                f"{safety_instruction}"
            ),
        )

    @staticmethod
    def get_example_safety_instruction(example_safety_mode: str) -> str:
        mode = example_safety_mode.lower().strip()

        if mode == "non_operational":
            return (
                "Example Safety Mode: NON-OPERATIONAL. "
                "For risky or dual-use concepts, use fake data, toy examples, pseudocode, "
                "diagrams, detection logic, safety checklists, or intentionally incomplete examples. "
                "Do not provide copy-paste harmful code, complete hazardous procedures, "
                "real target instructions, deployable workflows, evasion steps, persistence steps, "
                "credential theft, weaponization, or illegal instructions. "
                "Clearly state when an example is intentionally non-operational."
            )

        if mode == "pseudocode_only":
            return (
                "Example Safety Mode: PSEUDOCODE ONLY. "
                "Use conceptual pseudocode and diagrams only. "
                "Do not provide runnable code, exact quantities, complete operational steps, "
                "or deployable instructions."
            )

        if mode == "analysis_only":
            return (
                "Example Safety Mode: ANALYSIS ONLY. "
                "Only provide high-level explanation, ethics, prevention, detection, "
                "risk analysis, or safety-focused guidance. "
                "Do not provide procedural instructions."
            )

        return (
            "Example Safety Mode: NORMAL. "
            "Use normal educational examples appropriate to the learner's level."
        )


def run_demo() -> None:
    user_profile = {
        "username": "demo_user",
        "interests": ["gaming", "cars", "baking"],
    }

    categories = [
        "Conceptual",
        "Procedural",
        "Kinesthetic",
        "Exam",
        "Project",
        "Controlled",
        "Unknown",
    ]

    print("OpenDoor Persona Router Demo")
    print("----------------------------")

    for category in categories:
        print(f"\nCategory: {category}")
        prompt = PersonaRouter.get_system_prompt_by_category(
            category=category,
            user_profile=user_profile,
            example_safety_mode="non_operational" if category == "Controlled" else "normal",
        )
        print(prompt)


if __name__ == "__main__":
    run_demo()