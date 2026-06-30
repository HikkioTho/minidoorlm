# OpenDoor

**Open the door. Find your house.**

OpenDoor is an adaptive AI learning engine. It is not meant to be just another chatbot.

The goal is to model how a learner learns, then use that model to generate personalized lessons, homework, learning questions, review schedules, projects, and next-best-action recommendations.

## Current beta

The public beta includes:

- Quick chat
- Learner profile creation
- Study and homework generation
- Intent normalization
- Learning questions
- Homework response review
- Local source retrieval when a knowledge base exists
- Guarded public beta mode
- Separate local-only clean lab mode

## Core idea

Most AI tutors answer questions.

OpenDoor should model the learner.

The system is being built around:

- learner profiles
- concept graphs
- misconception tracking
- retention scheduling
- source-grounded learning
- project-based assessment
- next-best-action learning paths

## Public beta vs clean lab

`opendoor_beta.py` is the guarded public beta.

`opendoor_clean.py` is a local-only no-filter clean lab used for development and rebuilding. It should not be deployed publicly.

To run clean lab locally:

```powershell
$env:OPENDOOR_ALLOW_CLEAN_LAB="local"
streamlit run opendoor_clean.py --server.port 8503