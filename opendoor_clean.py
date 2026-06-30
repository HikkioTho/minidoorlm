import os

import streamlit as st

from assignment_builder import build_assignment
from beta_config import get_beta_config
from homework_grader import format_homework_review, review_homework_response
from intent_normalizer import normalize_intent
from rag_retriever import retrieve_relevant_chunks
from student_profile import (
    build_profile,
    list_profiles,
    load_profile,
    save_profile,
)
from upload_manager import save_uploaded_file


def enforce_local_lab_only():
    allow_clean_lab = os.getenv("OPENDOOR_ALLOW_CLEAN_LAB", "").strip().lower()

    if allow_clean_lab not in {"1", "true", "yes", "local"}:
        st.error(
            "OpenDoor Clean Lab is disabled. "
            "This no-filter build is for local development only."
        )
        st.stop()


st.set_page_config(
    page_title="OpenDoor Clean Lab",
    page_icon="🚪",
    layout="wide",
)

enforce_local_lab_only()

CONFIG = get_beta_config()


def init_state():
    defaults = {
        "chat_history": [],
        "assignment": None,
        "retrieved_chunks": [],
        "last_topic": "",
        "profile": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_active_profile():
    return st.session_state.get("profile")


def show_clean_lab_notice():
    st.title("OpenDoor Clean Lab")
    st.warning(
        "LOCAL CLEAN LAB ONLY. OpenDoor safety, quality, and policy filters are bypassed here. "
        "Do not deploy this file publicly."
    )


def clean_chat_answer(message: str) -> str:
    intent = normalize_intent(message)
    profile = get_active_profile()

    profile_line = ""

    if profile:
        profile_line = (
            f"\n\nProfile context: {profile.name}, level {profile.level}, goals: {profile.goals}."
        )

    return (
        f"Clean lab read this as: {intent.clean_topic}\n\n"
        f"Goal: {intent.learning_goal}\n\n"
        "This is the unfiltered local lab path. Use this space to test raw behavior and rebuild rules."
        f"{profile_line}"
    )


def show_chat_page():
    st.header("Clean Chat")

    for entry in st.session_state["chat_history"]:
        with st.chat_message(entry["role"]):
            st.write(entry["content"])

    message = st.chat_input("Ask anything in clean lab...")

    if message:
        st.session_state["chat_history"].append({"role": "user", "content": message})
        st.session_state["chat_history"].append({"role": "assistant", "content": clean_chat_answer(message)})
        st.rerun()


def show_profile_page():
    st.header("Profile")

    existing_profiles = list_profiles()
    load_col, create_col = st.columns([1, 2])

    with load_col:
        st.subheader("Load")

        if existing_profiles:
            selected_name = st.selectbox("Saved profiles", existing_profiles)

            if st.button("Load Profile"):
                profile = load_profile(selected_name)
                st.session_state["profile"] = profile
                st.success(f"Loaded {profile.name}")
        else:
            st.info("No saved profiles yet.")

    with create_col:
        st.subheader("Create / Update")

        active_profile = get_active_profile()

        name = st.text_input("Name", value=getattr(active_profile, "name", "Clean Lab User"))
        level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])

        goals = st.text_area(
            "Goals",
            value=getattr(active_profile, "goals", ""),
        )

        analogy_preferences = st.text_area(
            "Analogy preferences",
            value=getattr(active_profile, "analogy_preferences", ""),
        )

        weak_topics = st.text_area(
            "Weak topics",
            value=", ".join(getattr(active_profile, "weak_topics", [])),
        )

        strong_topics = st.text_area(
            "Strong topics",
            value=", ".join(getattr(active_profile, "strong_topics", [])),
        )

        current_streak = st.number_input(
            "Current streak",
            min_value=0,
            value=int(getattr(active_profile, "current_streak", 0)),
        )

        last_review_date = st.text_input(
            "Last review date",
            value=getattr(active_profile, "last_review_date", "") or "",
        )

        if st.button("Save Profile", type="primary"):
            profile = build_profile(
                name=name or "Clean Lab User",
                level=level,
                goals=goals,
                analogy_preferences=analogy_preferences,
                weak_topics_raw=weak_topics,
                strong_topics_raw=strong_topics,
                current_streak=current_streak,
                last_review_date=last_review_date or None,
            )

            save_profile(profile)
            st.session_state["profile"] = profile
            st.success("Profile saved.")


def show_lesson_card(assignment, retrieved_chunks):
    st.header("Clean Lab Lesson")
    st.subheader("What OpenDoor understood")
    st.write(assignment.summary_card)

    st.subheader("Lesson")
    st.write(assignment.virtual_lesson)

    st.subheader("Learning questions")

    st.markdown("**Comprehension**")
    for item in assignment.learning_questions.comprehension:
        st.markdown(f"- {item}")

    st.markdown("**Misconception checks**")
    for item in assignment.learning_questions.misconception_checks:
        st.markdown(f"- {item}")

    st.markdown("**Application**")
    for item in assignment.learning_questions.application:
        st.markdown(f"- {item}")

    st.subheader("Practice")
    for item in assignment.practice_tasks:
        st.markdown(f"- {item}")

    st.subheader("Feynman prompt")
    st.write(assignment.feynman_prompt)

    st.subheader("Mini project")
    st.write(assignment.mini_project)

    st.subheader("Review schedule")
    for item in assignment.review_schedule:
        st.markdown(f"- {item}")

    if retrieved_chunks:
        with st.expander("Retrieved sources", expanded=False):
            for index, chunk in enumerate(retrieved_chunks, start=1):
                st.markdown(f"**Source {index}: {chunk.source_name}**")
                st.write(chunk.text)


def show_study_page():
    st.header("Study + Homework")

    profile = get_active_profile()

    if not profile:
        st.warning("Create or load a profile first.")
        return

    topic = st.text_input(
        "What do you want to learn?",
        value=st.session_state.get("last_topic", ""),
    )

    use_rag = st.checkbox("Use local source library if available", value=True)

    if st.button("Build clean lab lesson", type="primary"):
        if not topic.strip():
            st.error("Enter a topic first.")
            return

        st.session_state["last_topic"] = topic

        retrieved_chunks = []

        if use_rag:
            retrieved_chunks = retrieve_relevant_chunks(
                query=topic,
                limit=4,
                knowledge_file=CONFIG.knowledge_file,
            )

        assignment = build_assignment(
            profile=profile,
            topic=topic,
            source_chunks=[chunk.text for chunk in retrieved_chunks],
        )

        st.session_state["assignment"] = assignment
        st.session_state["retrieved_chunks"] = retrieved_chunks

    assignment = st.session_state.get("assignment")
    retrieved_chunks = st.session_state.get("retrieved_chunks", [])

    if assignment:
        show_lesson_card(assignment, retrieved_chunks)

    st.divider()
    st.header("Upload")

    uploaded_file = st.file_uploader(
        "Upload study material or homework",
        type=["txt", "md", "csv", "json", "pdf", "png", "jpg", "jpeg", "webp", "mp4", "mov"],
    )

    if uploaded_file:
        saved_upload = save_uploaded_file(uploaded_file)
        st.success("File uploaded.")
        st.caption(f"Saved to: {saved_upload.display_path}")

        if saved_upload.readable_as_text and saved_upload.text_preview:
            with st.expander("Text preview", expanded=True):
                st.text(saved_upload.text_preview)

    st.divider()
    st.header("Review response")

    review_topic = st.text_input(
        "Homework topic",
        value=assignment.topic if assignment else "",
    )

    response = st.text_area("Paste homework answer or Feynman explanation")

    if st.button("Review response"):
        if not response.strip():
            st.error("Paste a response first.")
            return

        review = review_homework_response(
            topic=review_topic,
            response=response,
        )

        st.text(format_homework_review(review))


def main():
    init_state()
    show_clean_lab_notice()

    page = st.sidebar.radio(
        "Clean Lab Navigation",
        [
            "Chat",
            "Profile",
            "Study + Homework",
        ],
    )

    profile = get_active_profile()

    if profile:
        st.sidebar.success(f"Active profile: {profile.name}")
    else:
        st.sidebar.warning("No active profile")

    if page == "Chat":
        show_chat_page()
    elif page == "Profile":
        show_profile_page()
    elif page == "Study + Homework":
        show_study_page()


if __name__ == "__main__":
    main()