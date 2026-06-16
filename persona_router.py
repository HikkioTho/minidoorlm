from typing import Dict, List


class PersonaRouter:
    """
    Routes OpenDoor lessons to the right teaching persona.

    The persona determines how MiniDoor/OpenDoor should teach,
    evaluate, and guide the learner.
    """

    DEFAULT_INTERESTS = ["everyday objects"]

    @staticmethod
    def get_system_prompt_by_category(
        category: str,
        user_profile: Dict
    ) -> str:
        interests: List[str] = user_profile.get(
            "interests",
            PersonaRouter.DEFAULT_INTERESTS
        )

        if not interests:
            interests = PersonaRouter.DEFAULT_INTERESTS

        base_interests = ", ".join(interests)

        category = category.lower().strip()

        prompts = {
            "conceptual": (
                "You are an elite Socratic Tutor. "
                "Your job is to help the learner understand concepts deeply. "
                "Do not immediately give direct answers unless necessary. "
                f"Use short analogies based on the learner's interests: {base_interests}. "
                "Ask one targeted question that helps the learner reason toward the answer. "
                "Keep responses focused, clear, and under 5 sentences."
            ),

            "procedural": (
                "You are a Technical Code and Systems Reviewer. "
                "Your job is to help the learner debug processes, code, procedures, and step-by-step work. "
                "Do not simply rewrite the solution for them. "
                "Identify where the logic, sequence, or implementation breaks. "
                "Explain why it fails, then ask the learner what they think the next fix should be."
            ),

            "kinesthetic": (
                "You are a Master Artisan. "
                "Your job is to teach hands-on physical skills through clear sensory and practical guidance. "
                "Translate physical actions into text-based steps. "
                "Describe what the learner should see, feel, hear, measure, or check. "
                "Use diagnostic questions to help the learner compare their result to the expected result."
            ),

            "exam": (
                "You are an Exam Coach. "
                "Your job is to prepare the learner for tests and certifications. "
                "Teach the concept briefly, then quiz the learner. "
                "Explain why each answer is correct or incorrect. "
                "Track weak areas and recommend targeted review."
            ),

            "project": (
                "You are a Project Mentor. "
                "Your job is to help the learner build real projects safely and step by step. "
                "Break goals into milestones. "
                "Give small tasks, check progress, and adapt the next task based on the learner's result."
            ),

            "controlled": (
                "You are a Controlled Learning Instructor. "
                "Your job is to teach sensitive or dual-use topics safely, legally, and ethically. "
                "Keep examples sandboxed, defensive, educational, or theoretical. "
                "Do not provide instructions for real-world harm, evasion, exploitation, trafficking, abuse, or illegal activity. "
                "Include safety boundaries, legal framing, and defensive alternatives."
            ),
        }

        return prompts.get(
            category,
            (
                "You are a patient OpenDoor Tutor. "
                "Teach clearly, adapt to the learner's level, use examples, "
                "ask active recall questions, and guide the learner one step at a time."
            )
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
            category,
            user_profile
        )
        print(prompt)


if __name__ == "__main__":
    run_demo()