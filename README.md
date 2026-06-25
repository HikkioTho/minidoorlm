# MiniDoorLM / OpenDoor

MiniDoorLM is a from-scratch tiny language model project built in Python and PyTorch.

OpenDoor is the larger AI learning system built around it. The goal is to create an education-first AI platform where users can enter almost any topic and receive a personalized learning path, beginner-friendly lessons, quizzes, active recall prompts, safety-aware guidance, and review scheduling.

This project is not just a chatbot. It is an experimental learning system with a dual-AI architecture: one AI layer focuses on teaching and generation, while another safety/privacy layer checks what the system should allow, block, sanitize, remember, or route into controlled learning.

---

## Core Idea

OpenDoor is designed to help users learn almost any subject through structured, adaptive lessons.

Instead of only answering questions, OpenDoor tries to:

* understand what the user wants to learn
* classify the topic and learning style
* route risky topics into safe controlled-learning modes
* generate beginner-friendly lessons
* ask active recall questions
* track what the learner remembers or forgets
* schedule review with a retention engine
* protect user privacy before saving or training on anything
* avoid using raw personal user prompts as LLM training data

The long-term goal is a learning system that feels more like a personal tutor than a basic AI chat window.

---

## Dual AI System

OpenDoor is being designed as a dual-AI system.

### 1. MiniDoorLM — The Learning Brain

MiniDoorLM is the model layer.

It started as a simple bigram language model and was upgraded into a tiny transformer language model using PyTorch.

MiniDoorLM is responsible for learning the structure of OpenDoor-style teaching responses, such as:

* opening a learning path
* explaining a topic clearly
* adjusting to a learner level
* producing active recall prompts
* following OpenDoor response patterns
* generating lesson-style output

MiniDoorLM is not meant to be a large commercial model right now. It is a from-scratch learning project meant to show how language models are trained, saved, loaded, and improved.

### 2. OpenDoor Guard Layer — The Safety, Privacy, and Routing Brain

The second AI layer is the guard and routing system.

This layer decides what should happen before anything reaches the learning engine.

It includes:

* MiniWindow safety checks
* controlled-learning routing
* account hard-lock review for severe violations
* PrivacyGuard for detecting and redacting personal data
* MediaPromptShield for prompt injection inside images, audio, or video
* MediaGuard for uploaded media validation
* AccessControl for feature permissions
* BacklogFilter for rescanning old stored content
* MemoryExporter for safe user-owned exports

This layer is designed so OpenDoor does not blindly trust user prompts, uploaded files, old logs, media content, or training candidates.

The main rule is:

> MiniDoorLM teaches. The guard layer decides what is safe, private, allowed, controlled, blocked, or reviewable.

---

## Features

* From-scratch bigram language model
* Tiny transformer language model in PyTorch
* Training loop with checkpoint saving
* Text generation script
* Training loss logging
* Streamlit OpenDoor prototype
* Topic-aware lesson builder
* Safety routing with MiniWindow
* Controlled learning mode for sensitive topics
* Hard-lock account review flow for serious safety violations
* RetentionEngine for spaced repetition review scheduling
* PersonaRouter for different teaching styles
* PrivacyGuard for detecting and redacting private user data
* MediaPromptShield for blocking prompt injection from uploaded media
* MediaGuard for future audio, video, and image uploads
* AccessControl for feature permissions
* BacklogFilter for rescanning old logs and training candidates
* MemoryExporter for safe user-owned session exports
* Policy gate with AI, legal, safety, and red-flag logging notices
* GitHub-tracked project structure and documentation

---

## OpenDoor Learning Flow

The current prototype follows this flow:

```text
User enters a topic
        ↓
Policy gate confirms required notices
        ↓
MiniWindow checks safety and risk
        ↓
PersonaRouter selects teaching style
        ↓
LessonBuilder creates structured lesson output
        ↓
RetentionEngine schedules review based on recall score
```

For normal topics, OpenDoor allows the request and creates a lesson.

For controlled topics, OpenDoor can allow safe educational learning with non-operational examples.

For severe unsafe requests, OpenDoor blocks the request and marks the account/session for review.

---

## Safety and Controlled Learning

OpenDoor is designed to teach difficult topics responsibly.

Some topics may be allowed only in controlled learning mode, such as:

* cybersecurity concepts
* malware analysis theory
* OSINT ethics
* chemistry safety
* religious history
* physical security concepts
* forensics
* red team / blue team concepts

Controlled learning uses:

* high-level explanations
* toy examples
* fake data
* non-operational examples
* defensive analysis
* safety checklists
* legal and ethical framing

Controlled learning blocks:

* working malware
* credential theft
* ransomware logic
* evasion or stealth steps
* real target instructions
* weaponization
* dangerous recipes
* privacy invasion
* harassment instructions

---

## Privacy Design

OpenDoor is designed with a privacy-first learning architecture.

The main privacy rule is:

> Raw user prompts are not training data.

OpenDoor should not train MiniDoorLM on raw user prompts or personal user information.

Instead, it can learn from:

* human-written training examples
* sanitized responses
* synthetic prompts
* approved training candidates
* source summaries
* generalized learning patterns

PrivacyGuard helps detect and redact:

* emails
* phone numbers
* addresses
* SSNs
* credit-card-like numbers
* IP addresses
* API keys
* passwords
* private keys
* sensitive personal context

This allows OpenDoor to improve over time without harvesting private user data.

---

## Media Upload Safety

OpenDoor is being designed to eventually support uploaded images, audio, and video.

Before any uploaded media is processed, it should pass through guard layers:

```text
Upload
  ↓
AccessControl
  ↓
MediaGuard
  ↓
MediaPromptShield
  ↓
PrivacyGuard
  ↓
MiniWindow
  ↓
Approved / Redacted / Quarantined / Blocked
```

Uploaded media is treated as untrusted content.

A key rule:

> Text found inside images, videos, audio transcripts, subtitles, QR codes, or metadata is content to analyze, not instructions to obey.

This helps defend against prompt injection hidden inside screenshots, videos, images, or audio.

---

## RetentionEngine

RetentionEngine tracks learning review schedules.

It uses a spaced-repetition style approach inspired by SM2-like review systems.

It tracks:

* easiness factor
* repetitions
* interval days
* last reviewed time
* next review due

The goal is to help OpenDoor remember what the learner needs to review instead of treating every lesson like a one-time chat.

---

## PersonaRouter

PersonaRouter controls teaching style.

Current teaching modes include:

* Conceptual Tutor
* Procedural Coach
* Kinesthetic / Hands-On Guide
* Exam Coach
* Project Mentor
* Controlled Learning Instructor

These are not fixed subject categories. They are teaching patterns that help OpenDoor adapt to different learning goals.

---

## Project Structure

```text
minidoorlm/
├── app.py                              # Streamlit OpenDoor prototype
├── model.py                            # Tiny transformer model
├── train.py                            # Training loop
├── generate.py                         # Text generation script
├── lesson_builder.py                   # Topic-aware lesson generation
├── miniwindow.py                       # Safety and controlled-learning router
├── privacy_guard.py                    # Privacy scanning and redaction
├── media_prompt_shield.py              # Multimodal prompt-injection protection
├── media_guard.py                      # Media upload validation foundation
├── access_control.py                   # Role and feature access checks
├── memory_exporter.py                  # Safe session export tools
├── backlog_filter.py                   # Rescans old stored content
├── persona_router.py                   # Teaching style router
├── retention_engine.py                 # Spaced repetition review logic
├── visualize_training.py               # Training loss visualization
├── data/
│   └── training/
│       └── opendoor_teaching_examples.txt
├── docs/
│   ├── boundless_training_strategy.md
│   ├── privacy_learning_architecture.md
│   ├── media_privacy_access_architecture.md
│   └── discord_trivia_bot_design.md
├── policies/
│   ├── ai_disclaimer.md
│   ├── legal_safety_notice.md
│   └── red_flag_logging_notice.md
└── README.md
```

---

## Current Status

MiniDoorLM currently supports:

* model training
* checkpoint saving
* generation
* training logs
* OpenDoor-style training data

OpenDoor currently supports:

* Streamlit app interface
* policy acknowledgment flow
* lesson generation prototype
* safety routing
* controlled-learning decisions
* account review locks
* privacy guard foundations
* media safety architecture foundations
* retention scheduling demo

---

## Example Normal Request

```text
User: Teach me how to build a telescope.
```

Expected OpenDoor behavior:

```text
Risk Level: green
Decision: allow
Learning Mode: normal_learning
Example Safety Mode: normal
```

OpenDoor then creates a beginner-friendly lesson explaining telescope parts, aperture, focal length, magnification, safety, active recall, and next steps.

---

## Example Controlled Request

```text
User: Teach me malware analysis for a college sandbox lab.
```

Expected OpenDoor behavior:

```text
Risk Level: orange
Decision: controlled_allow
Learning Mode: controlled_learning
Example Safety Mode: non_operational
```

OpenDoor allows safe educational coverage while blocking deployment, evasion, credential theft, persistence, or real-world targeting.

---

## Example Blocked Request

```text
User: Teach me how to make explosives.
```

Expected OpenDoor behavior:

```text
Risk Level: red
Decision: block_flag
Learning Mode: blocked
Example Safety Mode: blocked
Account Action: lock_pending_review
Review Priority: urgent
```

OpenDoor blocks the request, avoids generating harmful instructions, and flags the account/session for review.

---

## Why This Project Matters

MiniDoorLM / OpenDoor is a hands-on attempt to understand and build AI systems from the ground up.

It combines:

* language model training
* AI safety routing
* privacy protection
* learning science
* spaced repetition
* controlled topic handling
* multimodal safety planning
* user-owned memory export
* project-based software architecture

The project is experimental, but the goal is serious:

> Build an AI learning system that teaches broadly, adapts personally, protects privacy, and routes risky topics responsibly.
