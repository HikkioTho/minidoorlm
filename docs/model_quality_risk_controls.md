# MiniDoorLM Model Quality and Risk Controls

## Purpose

MiniDoorLM is a from-scratch learning model, so quality control matters as much as model training.

The system must watch for:

- overfitting
- model collapse
- prompt fatigue
- generic output
- context loss
- hallucinated structure
- repeated phrases
- small-dataset memorization
- unsafe or private training data

---

## Model Collapse Risk

Model collapse can happen when a model is trained too heavily on AI-generated outputs or narrow repeated patterns.

MiniDoorLM should avoid training only on its own generated responses.

Preferred training sources:

- human-written examples
- reviewed synthetic examples
- source-grounded summaries
- sanitized and approved training candidates
- varied subject examples
- controlled-learning examples
- privacy-safe examples

Avoid:

- raw user prompts
- private user data
- unreviewed AI-generated examples
- repeated generic lesson shells
- unsafe red-flag logs
- unverified media-derived text

---

## Small Dataset Risk

MiniDoorLM currently learns structure faster than meaning.

Symptoms:

- fake words
- topic bleeding
- repeated sections
- garbled lesson text
- memorized examples
- validation loss rising while train loss falls

Fixes:

- expand dataset to 50+ examples
- use example boundaries
- use <END> tokens
- add more topics
- vary wording
- add better validation prompts
- save best validation checkpoint
- eventually move from character-level to token-level modeling

---

## Context Loss Risk

OpenDoor should not rely only on raw chat history.

Long-term learning should use structured memory:

- concept scores
- weak tags
- strong tags
- review dates
- difficulty level
- learning mode
- retention state

Raw private prompts should not be used as memory or training data by default.

---

## Prompt Fatigue Risk

If OpenDoor always outputs the same structure without real teaching value, users will stop trusting it.

To reduce prompt fatigue:

- vary teaching style
- adapt examples to user interests
- ask different active recall questions
- generate quizzes
- use projects
- use analogies
- use review scheduling
- use diagnostic checks
- track weak concepts

---

## Sycophancy Risk

OpenDoor should not blindly praise every user answer.

Future answer evaluation should include:

- what the user got right
- what is missing
- what is incorrect
- confidence level
- next best review step
- constructive correction

The system should be supportive but not fake.

---

## Quality Gate Rule

Before training data enters MiniDoorLM, it should pass:

1. PrivacyGuard
2. MiniWindow safety review
3. ModelHealthMonitor dataset check
4. human or admin review for generated examples
5. dataset lineage tagging

---

## Product Principle

MiniDoorLM should not become smarter by absorbing everything.

It should improve through clean, varied, reviewed, privacy-safe training data.