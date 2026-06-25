from dataclasses import dataclass
from typing import List


@dataclass
class LessonBuilderInput:
    topic_request: str
    learner_level: str
    teaching_style: str
    learning_mode: str
    example_safety_mode: str
    interests: List[str]


class LessonBuilder:
    @staticmethod
    def clean_topic(topic_request: str) -> str:
        topic = topic_request.strip()

        lower_topic = topic.lower()

        starters = [
            "teach me how to",
            "teach me about",
            "teach me",
            "i want to learn how to",
            "i want to learn about",
            "i want to learn",
            "learn how to",
            "learn about",
        ]

        for starter in starters:
            if lower_topic.startswith(starter):
                topic = topic[len(starter):].strip()
                break

        if not topic:
            return "this topic"

        return topic

    @staticmethod
    def detect_topic_family(topic: str) -> str:
        topic_lower = topic.lower()

        if any(word in topic_lower for word in ["telescope", "lens", "mirror", "optics"]):
            return "optics_telescope"

        if any(word in topic_lower for word in ["python", "code", "programming", "javascript", "app"]):
            return "coding"

        if any(word in topic_lower for word in ["bake", "cooking", "bread", "cake", "pie"]):
            return "cooking"

        if any(word in topic_lower for word in ["math", "fractions", "algebra", "geometry"]):
            return "math"

        if any(word in topic_lower for word in ["physics", "quantum", "force", "energy", "motion"]):
            return "physics"

        return "general"

    @staticmethod
    def interests_text(interests: List[str]) -> str:
        if not interests:
            return "real-world examples"

        return ", ".join(interests)

    @classmethod
    def build(cls, lesson_input: LessonBuilderInput) -> str:
        topic = cls.clean_topic(lesson_input.topic_request)
        topic_family = cls.detect_topic_family(topic)
        interests = cls.interests_text(lesson_input.interests)

        if lesson_input.example_safety_mode == "non_operational":
            safety_note = """
> **Controlled Learning Note:** This topic is being taught with safety boundaries. OpenDoor will use high-level, simulated, defensive, or non-operational examples only.
"""
        else:
            safety_note = ""

        if topic_family == "optics_telescope":
            return cls._build_telescope_lesson(topic, lesson_input, interests, safety_note)

        if topic_family == "coding":
            return cls._build_coding_lesson(topic, lesson_input, interests, safety_note)

        if topic_family == "cooking":
            return cls._build_cooking_lesson(topic, lesson_input, interests, safety_note)

        if topic_family == "math":
            return cls._build_math_lesson(topic, lesson_input, interests, safety_note)

        if topic_family == "physics":
            return cls._build_physics_lesson(topic, lesson_input, interests, safety_note)

        return cls._build_general_lesson(topic, lesson_input, interests, safety_note)

    @staticmethod
    def _header(topic: str, lesson_input: LessonBuilderInput, interests: str, safety_note: str) -> str:
        return f"""
# OpenDoor Learning Output

## Topic

**{topic}**

## Learning Setup

**Learner Level:** {lesson_input.learner_level}  
**Teaching Style:** {lesson_input.teaching_style}  
**Learning Mode:** {lesson_input.learning_mode}  
**Example Safety Mode:** {lesson_input.example_safety_mode}  
**Analogy Interests:** {interests}

{safety_note}
---
"""

    @classmethod
    def _build_telescope_lesson(
        cls,
        topic: str,
        lesson_input: LessonBuilderInput,
        interests: str,
        safety_note: str,
    ) -> str:
        return cls._header(topic, lesson_input, interests, safety_note) + """
## First Lesson: What a Telescope Actually Does

A telescope is a tool that **collects light** from faraway objects and **focuses that light** so your eye can see a clearer, brighter, or larger image.

The key idea is not “zoom” first.

The key idea is:

> A telescope gathers more light than your eye can gather on its own.

Your eye has a small opening. A telescope has a larger lens or mirror, so it can collect more light from faint or distant objects.

---

## Core Parts of a Basic Telescope

A beginner telescope usually has these parts:

1. **Objective lens or primary mirror**  
   This is the main light-collecting part.

2. **Tube or body**  
   This holds the parts at the right distance and blocks extra stray light.

3. **Eyepiece**  
   This magnifies the focused image.

4. **Focuser**  
   This moves the eyepiece slightly so the image becomes sharp.

5. **Mount or tripod**  
   This keeps the telescope steady.

A shaky telescope is almost useless, even if the optics are decent.

---

## The Three Concepts You Need First

### 1. Aperture

Aperture means the width of the main lens or mirror.

Bigger aperture means:

- more light collected
- brighter image
- better detail
- better viewing of dim objects

### 2. Focal Length

Focal length is the distance needed for the lens or mirror to bring light into focus.

Longer focal length usually means more magnification potential.

### 3. Magnification

Magnification depends on the telescope focal length and eyepiece focal length.

At this stage, do not chase huge magnification. A stable, clear image is better than a giant blurry one.

---

## Simple Analogy

Think of a telescope like a gaming graphics setting.

Aperture is like increasing brightness and detail because you are collecting more information.

Focus is like sharpening the image.

The eyepiece is like changing your field of view.

A good telescope is not just “more zoom.” It is better light collection plus stable focus.

---

## Beginner Build Path

A safe beginner path would be:

1. Learn how lenses focus light.
2. Compare refractor telescopes and reflector telescopes.
3. Understand aperture and focal length.
4. Sketch a simple telescope layout.
5. Learn why alignment matters.
6. Build or simulate a simple refractor design.
7. Test focus using distant safe objects during the day.
8. Learn safe viewing rules before observing the sky.

Important safety note: never point a telescope at the Sun without proper certified solar equipment.

---

## Active Recall Question

Explain what a telescope does in your own words.

Try to include:

1. what part collects light
2. what part magnifies the image
3. why focus matters
4. why bigger magnification is not always better

---

## Mini Quiz

1. What does aperture control?
2. Why does a telescope need a stable mount?
3. What does the eyepiece do?
4. Why is focus important?
5. Why should you not point a telescope at the Sun without proper equipment?

---

## Feynman Check

A strong answer should sound simple, like:

> A telescope uses a lens or mirror to collect more light than my eye can. It focuses that light into an image, and the eyepiece helps me view it larger. If the parts are not aligned or focused, the image looks blurry.

---

## Next Step

Next, OpenDoor should teach **how lenses bend light** using a simple diagram and a hands-on safe example.
"""

    @classmethod
    def _build_coding_lesson(
        cls,
        topic: str,
        lesson_input: LessonBuilderInput,
        interests: str,
        safety_note: str,
    ) -> str:
        return cls._header(topic, lesson_input, interests, safety_note) + f"""
## First Lesson: Understanding the Coding Goal

To learn **{topic}**, start by separating the goal into three layers:

1. **What should the program do?**
2. **What inputs does it need?**
3. **What output should it produce?**

Most beginners get stuck because they jump straight into syntax before understanding the flow.

---

## Core Concepts

You usually need:

- variables
- conditionals
- loops
- functions
- data structures
- debugging
- testing

---

## Simple Analogy

Think of code like a recipe.

Variables are ingredients.  
Functions are reusable cooking steps.  
Conditionals are decisions like “if the oven is hot, put the tray in.”  
Loops are repeated actions like “stir 10 times.”

---

## Active Recall Question

Explain what you want the program to do without using code.

Then list:

1. the input
2. the process
3. the output

---

## Mini Quiz

1. What is a variable?
2. Why do functions help?
3. What is a loop?
4. Why should you test small pieces before building the whole app?

---

## Next Step

Next, OpenDoor should turn your goal into pseudocode before writing real code.
"""

    @classmethod
    def _build_cooking_lesson(
        cls,
        topic: str,
        lesson_input: LessonBuilderInput,
        interests: str,
        safety_note: str,
    ) -> str:
        return cls._header(topic, lesson_input, interests, safety_note) + f"""
## First Lesson: Understanding the Skill

To learn **{topic}**, you need to understand the process, not just memorize steps.

Cooking skills usually depend on:

- ingredients
- timing
- temperature
- texture
- smell
- visual cues
- safe handling

---

## Core Beginner Concepts

Start with:

1. what each ingredient does
2. what tools are needed
3. what can go wrong
4. what signs show progress
5. how to fix common mistakes

---

## Simple Analogy

Cooking is like tuning a game character build.

Each ingredient changes the final result. Too much of one thing can throw off the whole balance.

---

## Active Recall Question

Explain the process in your own words.

Try to include:

1. what the main ingredients do
2. what texture or smell you expect
3. one mistake to avoid
4. one safety rule

---

## Next Step

Next, OpenDoor should give a beginner-safe checklist and ask a diagnostic question.
"""

    @classmethod
    def _build_math_lesson(
        cls,
        topic: str,
        lesson_input: LessonBuilderInput,
        interests: str,
        safety_note: str,
    ) -> str:
        return cls._header(topic, lesson_input, interests, safety_note) + f"""
## First Lesson: Build the Idea Before the Formula

For **{topic}**, the goal is to understand the idea before memorizing procedures.

Math gets easier when you can answer:

> What is this measuring, comparing, or changing?

---

## Core Beginner Concepts

Start with:

1. vocabulary
2. visual model
3. simple example
4. practice problem
5. explanation in your own words

---

## Simple Analogy

Math is like a game system.

The rules are strict, but once you understand the rules, you can predict what happens next.

---

## Active Recall Question

Explain **{topic}** without using a formula first.

Then give one example.

---

## Mini Quiz

1. What does this concept help you figure out?
2. What is one visual way to represent it?
3. What mistake do beginners usually make?
4. How would you explain it to a younger student?

---

## Next Step

Next, OpenDoor should generate a simple worked example and then a practice problem.
"""

    @classmethod
    def _build_physics_lesson(
        cls,
        topic: str,
        lesson_input: LessonBuilderInput,
        interests: str,
        safety_note: str,
    ) -> str:
        return cls._header(topic, lesson_input, interests, safety_note) + f"""
## First Lesson: Physics Is About Relationships

To learn **{topic}**, start by asking:

> What things are affecting each other?

Physics is usually about relationships between quantities like motion, force, energy, time, mass, charge, light, or waves.

---

## Core Beginner Concepts

Start with:

1. what objects or systems are involved
2. what quantities can change
3. what stays constant
4. what cause-and-effect relationship exists
5. what real-world example shows the idea

---

## Simple Analogy

Physics is like understanding the rules behind a game engine.

Objects move, collide, accelerate, slow down, transfer energy, and respond to forces based on rules.

---

## Active Recall Question

Explain **{topic}** as a relationship between two or more things.

Try to include:

1. what changes
2. what causes the change
3. one real-world example
4. one question you still have

---

## Mini Quiz

1. What quantities are involved?
2. What causes change in the system?
3. What is one everyday example?
4. What would you measure if you wanted to test it?

---

## Next Step

Next, OpenDoor should create a simple diagram and one beginner practice question.
"""

    @classmethod
    def _build_general_lesson(
        cls,
        topic: str,
        lesson_input: LessonBuilderInput,
        interests: str,
        safety_note: str,
    ) -> str:
        return cls._header(topic, lesson_input, interests, safety_note) + f"""
## First Lesson: Build a Mental Map

To learn **{topic}**, start by building a mental map.

A good first lesson should answer:

1. What is it?
2. Why does it matter?
3. What are the beginner building blocks?
4. What should I learn first?
5. How will I know I understand it?

---

## Core Beginner Concepts

The first learning path should include:

1. a plain-English definition
2. key vocabulary
3. one simple example
4. common mistakes
5. a short practice task
6. an active recall question

---

## Simple Analogy

Using your interests in **{interests}**, OpenDoor should connect this topic to something familiar so the first idea sticks.

---

## Active Recall Question

Explain **{topic}** in your own words as if you were teaching it to someone younger than you.

Try to include:

1. what it is
2. why it matters
3. one example
4. one thing you still find confusing

---

## Mini Quiz

1. What is the simplest definition of this topic?
2. Why would someone learn it?
3. What is one example?
4. What is one beginner mistake?
5. What should you learn next?

---

## Feynman Check

A good explanation should be clear enough that a younger student could understand it.

If the explanation uses too much jargon, OpenDoor should simplify the lesson and try again.

---

## Next Step

Next, OpenDoor should create a diagnostic question to check your current level.
"""