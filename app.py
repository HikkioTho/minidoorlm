import streamlit as st
from dataclasses import asdict

from miniwindow import MiniWindow
from persona_router import PersonaRouter
from retention_engine import RetentionEngine


st.set_page_config(
    page_title="OpenDoor",
    page_icon="🚪",
    layout="wide",
)

st.title("🚪 OpenDoor")
st.caption("Open any subject. Learn it your way.")

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

    with st.expander("Full MiniWindow output"):
        st.json(decision_data)

    if decision.decision == "block_flag":
        st.error("This request was blocked and logged as a red-flag event.")
        st.info(decision.safe_redirect)

    elif decision.decision == "clarify":
        st.warning("MiniWindow needs more scope before generating a course.")
        st.info(decision.safe_redirect)

    else:
        st.subheader("PersonaRouter Prompt")

        prompt = PersonaRouter.get_system_prompt_by_category(
            category=category,
            user_profile=user_profile,
            example_safety_mode=decision.example_safety_mode,
        )

        with st.expander("Generated system prompt"):
            st.write(prompt)

        st.subheader("Prototype Learning Path")

        st.markdown(
            f"""
### Door opened: {topic_request.replace("Teach me", "").strip()}

**Level:** {level}  
**Teaching Style:** {category}  
**Learning Mode:** {decision.learning_mode}

#### Starter Path

1. Find your current level with a quick diagnostic.
2. Break the topic into small concepts.
3. Teach the first concept with an analogy.
4. Ask an active recall question.
5. Score the answer using the Feynman method.
6. Schedule review with the RetentionEngine.
7. Unlock the next concept when ready.

#### First Active Recall Prompt

Explain the main idea of this topic in your own words.
            """
        )

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