from pathlib import Path
from dataclasses import asdict

import streamlit as st

from lesson_builder import LessonBuilder, LessonBuilderInput
from miniwindow import MiniWindow
from persona_router import PersonaRouter
from retention_engine import RetentionEngine


def load_policy_text(file_path):
    path = Path(file_path)

    if not path.exists():
        return f"Missing policy file: {file_path}"

    return path.read_text(encoding="utf-8")


def initialize_session_state():
    defaults = {
        "policy_step": 0,
        "accepted_ai_disclaimer": False,
        "accepted_legal_notice": False,
        "accepted_red_flag_notice": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def policy_gate():
    policies = [
        {
            "key": "accepted_ai_disclaimer",
            "title": "Step 1: AI Disclaimer",
            "file": "policies/ai_disclaimer.md",
            "button": "I understand the AI disclaimer",
        },
        {
            "key": "accepted_legal_notice",
            "title": "Step 2: Legal and Safety Notice",
            "file": "policies/legal_safety_notice.md",
            "button": "I agree to the legal and safety notice",
        },
        {
            "key": "accepted_red_flag_notice",
            "title": "Step 3: Red-Flag Logging Notice",
            "file": "policies/red_flag_logging_notice.md",
            "button": "I understand the red-flag logging notice",
        },
    ]

    all_accepted = (
        st.session_state.accepted_ai_disclaimer
        and st.session_state.accepted_legal_notice
        and st.session_state.accepted_red_flag_notice
    )

    if all_accepted:
        with st.expander("Policy acknowledgments complete", expanded=False):
            st.success("All required OpenDoor notices have been accepted for this session.")

            if st.button("Reset policy acknowledgments"):
                st.session_state.accepted_ai_disclaimer = False
                st.session_state.accepted_legal_notice = False
                st.session_state.accepted_red_flag_notice = False
                st.session_state.policy_step = 0
                st.rerun()

        return True

    current_step = st.session_state.policy_step
    policy = policies[current_step]

    st.markdown("## Required OpenDoor Acknowledgment")

    progress_value = (current_step + 1) / len(policies)
    st.progress(progress_value)

    st.markdown(f"### {policy['title']}")

    with st.container(border=True):
        st.markdown(load_policy_text(policy["file"]))

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button(policy["button"]):
            st.session_state[policy["key"]] = True

            if current_step < len(policies) - 1:
                st.session_state.policy_step += 1

            st.rerun()

    with col2:
        st.info("You must accept each notice before using OpenDoor.")

    st.stop()


def render_retention_demo():
    st.subheader("RetentionEngine Demo")

    current_state = {
        "easiness_factor": 2.5,
        "repetitions": 1,
        "interval_days": 1,
    }

    quality_score = st.slider(
        "Pretend the AI scored your recall from 0 to 5",
        min_value=0,
        max_value=5,
        value=4,
    )

    updated_state = RetentionEngine.calculate_next_review(
        current_state=current_state,
        quality_score=quality_score,
    )

    st.json(updated_state)


initialize_session_state()

st.set_page_config(
    page_title="OpenDoor",
    page_icon="🚪",
    layout="wide",
)

st.title("🚪 OpenDoor")
st.caption("Open any subject. Learn it your way.")

policy_gate()

with st.sidebar:
    st.header("Learner Profile")

    user_id = st.text_input("User ID", value="demo_user")
    session_id = st.text_input("Session ID", value="demo_session")

    level = st.selectbox(
        "Current Level",
        ["5th Grade", "Beginner", "Intermediate", "Advanced", "Expert"],
    )

    category = st.selectbox(
        "Teaching Style",
        [
            "Conceptual",
            "Procedural",
            "Kinesthetic",
            "Exam",
            "Project",
            "Controlled",
            "Unknown",
        ],
    )

    interests_text = st.text_input(
        "Interests for analogies",
        value="gaming, cars, baking",
    )

    interests = [
        item.strip()
        for item in interests_text.split(",")
        if item.strip()
    ]

st.subheader("What do you want to learn?")

topic_request = st.text_area(
    "Enter a topic or learning request",
    value="Teach me quantum physics from beginner level.",
    height=120,
)

open_door = st.button("Open Door")

if open_door:
    user_profile = {
        "user_id": user_id,
        "level": level,
        "interests": interests,
    }

    decision = MiniWindow.review_request(
        user_request=topic_request,
        user_id=user_id,
        session_id=session_id,
    )

    decision_data = asdict(decision)

    st.subheader("MiniWindow Decision")

    risk_color = {
        "green": "🟢",
        "yellow": "🟡",
        "orange": "🟠",
        "red": "🔴",
    }.get(decision.risk_level, "⚪")

    st.write(f"{risk_color} **Risk Level:** `{decision.risk_level}`")
    st.write(f"**Decision:** `{decision.decision}`")
    st.write(f"**Learning Mode:** `{decision.learning_mode}`")
    st.write(f"**Example Safety Mode:** `{decision.example_safety_mode}`")
    st.write(f"**Reason:** {decision.reason}")

    if decision.requires_account_review:
        st.error(
            f"Account action: `{decision.account_action}` | "
            f"Review priority: `{decision.review_priority}`"
        )

    with st.expander("Full MiniWindow output"):
        st.json(decision_data)

    if decision.decision == "block_flag":
        st.error("This request was blocked by OpenDoor safety systems.")
        st.info(decision.safe_redirect)

        if decision.requires_account_review:
            st.warning(
                "This account/session has been flagged for immediate review. "
                "Further learning access should remain locked until reviewed by an authorized administrator."
            )

        st.stop()

    if decision.decision == "clarify":
        st.warning("MiniWindow needs more scope before generating a course.")
        st.info(decision.safe_redirect)
        st.stop()

    st.subheader("PersonaRouter Prompt")

    prompt = PersonaRouter.get_system_prompt_by_category(
        category=category,
        user_profile=user_profile,
        example_safety_mode=decision.example_safety_mode,
    )

    with st.expander("Generated system prompt"):
        st.write(prompt)

    st.subheader("OpenDoor Output")

    lesson_input = LessonBuilderInput(
        topic_request=topic_request,
        learner_level=level,
        teaching_style=category,
        learning_mode=decision.learning_mode,
        example_safety_mode=decision.example_safety_mode,
        interests=interests,
    )

    learning_output = LessonBuilder.build(lesson_input)

    st.markdown(learning_output)

    render_retention_demo()