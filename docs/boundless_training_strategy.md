# OpenDoor Boundless Training Strategy

## Core Idea

OpenDoor is not limited to a fixed list of subjects.

The goal is not to support only math, science, coding, baking, cybersecurity, or school topics. Those are only examples.

OpenDoor should support any learnable domain by dynamically understanding:

- what the user wants to learn
- the learner's current level
- the skill type
- the risk level
- the prerequisites
- the best teaching style
- the right practice format
- the safest way to teach the topic

The user should be able to say:

> I want to learn this.

And OpenDoor should figure out how to open that door.

---

## What Boundless Training Means

Boundless training does not mean the system provides anything without limits.

It means OpenDoor is not restricted to hardcoded subject categories.

The system should not ask:

> Is this one of our approved subjects?

It should ask:

> What kind of learning is this, and how can it be taught responsibly?

---

## Boundless Learning, Not Boundless Harm

OpenDoor should teach hard topics.

OpenDoor should not enable harm.

The correct balance is:

- broad learning scope
- dynamic routing
- controlled learning for risky topics
- source verification
- non-operational examples for dual-use subjects
- refusal only for clearly harmful requests

---

## System Layers

OpenDoor is made of multiple cooperating systems.

### MiniDoorLM

MiniDoorLM is the from-scratch model layer.

Its purpose is to learn how to generate text, structure lessons, ask questions, summarize, and eventually teach.

MiniDoorLM does not need to memorize every fact in the world.

It should learn how to teach.

### Source Pool

The source pool provides knowledge.

It should include trusted materials such as:

- open textbooks
- open courses
- official documentation
- public education resources
- research papers
- user-uploaded learning material
- vetted reference content

The source pool keeps OpenDoor current and reduces hallucinations.

### MiniWindow

MiniWindow checks scope, safety, and risk.

It routes requests into:

- allow
- clarify
- controlled_allow
- block_flag

MiniWindow does not exist to block hard topics. It exists to preserve learning while preventing harm.

### RetentionEngine

RetentionEngine tracks memory.

It schedules reviews based on concept-level performance using a spaced repetition approach.

It tracks:

- easiness factor
- repetitions
- interval days
- last reviewed time
- next review due

### PersonaRouter

PersonaRouter chooses the teaching style.

It can route or blend modes such as:

- Socratic Tutor
- Technical Code Reviewer
- Master Artisan
- Exam Coach
- Project Mentor
- Controlled Learning Instructor

These are not fixed subject categories. They are teaching patterns.

---

## Dynamic Classification

OpenDoor should classify learning requests across multiple dimensions.

Example dimensions:

- conceptual
- procedural
- kinesthetic
- visual
- analytical
- creative
- technical
- physical
- social
- exam-based
- project-based
- lab-based
- controlled
- source-verified

A single topic can have multiple dimensions.

Example:

> Teach me how to bake bread.

Classification:

- kinesthetic
- practical
- sensory feedback
- beginner friendly
- low risk

Example:

> Teach me quantum physics.

Classification:

- conceptual
- mathematical
- abstract
- source verified
- beginner to advanced pathway

Example:

> Teach me malware analysis for a college sandbox.

Classification:

- technical
- procedural
- controlled learning
- lab based
- non-operational examples
- defensive framing

---

## Dataset Strategy

OpenDoor should not train one model on everything in the world directly.

Instead:

MiniDoorLM learns teaching behavior.

The source pool provides facts.

The verifier checks factual claims.

MiniWindow checks risk.

RetentionEngine tracks user memory.

This avoids turning MiniDoorLM into a frozen, outdated encyclopedia.

---

## Teaching Behavior Dataset

The first major dataset should teach OpenDoor how to act.

It should include examples of:

- building learning paths
- explaining concepts clearly
- adjusting for grade level
- asking active recall questions
- scoring Feynman explanations
- giving micro-lessons
- generating quizzes
- adapting difficulty
- using analogies
- diagnosing tactile skills
- handling controlled learning safely

---

## Source Pool Dataset

The source pool should contain reference material.

This material should be organized by:

- domain
- topic
- concept
- difficulty
- source type
- trust level
- freshness
- license
- safety level

OpenDoor should retrieve relevant chunks when teaching.

---

## Controlled Learning

Controlled learning is for topics that are useful but risky or dual-use.

Examples:

- ethical hacking
- malware analysis
- OSINT
- chemistry
- biofuels
- physical security
- lockpicking
- forensics
- red team concepts

Controlled learning should use:

- theory
- fake data
- toy examples
- pseudocode
- non-runnable snippets
- detection logic
- defensive analysis
- safety checklists
- legal and ethical framing

Controlled learning should not provide:

- copy-paste harmful code
- working malware
- evasion steps
- credential theft
- real target instructions
- hazardous recipes
- illegal procedures
- weaponization steps

---

## Learning Loop

The ideal OpenDoor loop is:

1. User selects a topic.
2. OpenDoor classifies the topic.
3. MiniWindow checks risk.
4. Source pool retrieves trusted material.
5. PersonaRouter chooses teaching style.
6. OpenDoor creates a learning path.
7. User completes a micro-lesson.
8. User answers or explains in their own words.
9. AI evaluates the answer.
10. RetentionEngine schedules review.
11. Difficulty adjusts.
12. Next concept unlocks.

---

## Project Principle

OpenDoor should not be a generic chatbot.

OpenDoor should be a learning system.

It should teach broadly, adapt personally, verify information, remember what the user forgets, and route difficult topics responsibly.