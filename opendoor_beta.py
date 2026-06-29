import streamlit as st

from assignment_builder import build_assignment
from beta_config import get_beta_config
from beta_health_check import run_beta_health_check
from beta_logger import log_beta_error, log_beta_event, safe_error_message
from content_quality_guard import evaluate_content_quality, format_content_quality_report
from learning_guard import check_profile_fields, check_topic_request
from rag_retriever import retrieve_relevant_chunks
from student_profile import (
    build_profile,
    list_profiles,
    load_profile,
    save_profile,
)


st.set_page_config(
    page_title="OpenDoor Beta",
    page_icon="🚪",
    layout="wide",
)

CONFIG = get_beta_config()


def show_list(title: str, items):
    st.markdown(f"### {title}")

    if not items:
        st.info("None yet.")
        return

    for item in items:
        st.markdown(f"- {item}")


def show_health_check():
    with st.expander("Beta Health Check", expanded=False):
        health = run_beta_health_check()

        if health.passed:
            st.success("Required beta folders are ready.")
        else:
            st.error("Beta health check failed.")

        if health.errors:
            st.markdown("#### Errors")
            for error in health.errors:
                st.error(error)

        if health.warnings:
            st.markdown("#### Warnings")
            for warning in health.warnings:
                st.warning(warning)

        if not health.errors and not health.warnings:
            st.info("No warnings found.")


def show_disclosure():
    st.info(
        "OpenDoor Beta is an AI-assisted learning tool. "
        "It can help create lessons, homework, and review plans, but it is not a human teacher, "
        "doctor, lawyer, therapist, or emergency service. Do not enter passwords, secrets, "
        "private personal records, or sensitive data."
    )


def show_retrieved_sources(chunks):
    st.markdown("### Retrieved Study Sources")

    if not chunks:
        st.info("No local source chunks were retrieved. Add .txt or .md files to data/sources/ and run ingest_sources.py.")
        return

    for index, chunk in enumerate(chunks, start=1):
        with st.expander(f"Source {index}: {chunk.source_name} | score {chunk.score}"):
            st.caption(f"Chunk ID: {chunk.chunk_id}")
            st.write(chunk.text)


def show_assignment(assignment, retrieved_chunks):
    st.header("Virtual Lesson")
    st.write(assignment.virtual_lesson)

    if retrieved_chunks:
        st.markdown("### Grounding Note")
        st.write(
            "This lesson used local study-source chunks from the OpenDoor knowledge base. "
            "Review the retrieved sources before trusting the assignment fully."
        )

    if assignment.safety_note:
        st.warning(assignment.safety_note)

    left, right = st.columns(2)

    with left:
        show_list("Warm-Up", assignment.warm_up)
        show_list("Reading / Task", assignment.reading_task)
        show_list("Starter Resources", assignment.starter_resources)
        show_list("Practice Problems", assignment.practice_problems)

    with right:
        show_list("Active Recall", assignment.active_recall)

        st.markdown("### Feynman Explanation")
        st.write(assignment.feynman_prompt)

        st.markdown("### Mini Project")
        st.write(assignment.mini_project)

        show_list("Review Schedule", assignment.review_schedule)
        show_list("Ending Resources", assignment.ending_resources)

    show_retrieved_sources(retrieved_chunks)

    combined_text = "\n".join(
        [
            assignment.virtual_lesson,
            "\n".join(assignment.warm_up),
            "\n".join(assignment.reading_task),
            "\n".join(assignment.practice_problems),
            "\n".join(assignment.active_recall),
            assignment.feynman_prompt,
            assignment.mini_project,
        ]
    )

    quality = evaluate_content_quality(combined_text)

    with st.expander("Content Quality Guard", expanded=False):
        if quality.passed:
            st.success(f"Style check passed: {quality.label}")
        else:
            st.warning(f"Style review needed: {quality.label}")

        st.text(format_content_quality_report(quality))


def show_profile_sidebar():
    st.sidebar.header("Profile")

    existing_profiles = list_profiles()
    profile_mode = st.sidebar.radio(
        "Profile Mode",
        ["Create / Update Profile", "Load Existing Profile"],
    )

    if profile_mode == "Load Existing Profile" and existing_profiles:
        selected_name = st.sidebar.selectbox("Choose profile", existing_profiles)

        if st.sidebar.button("Load Profile"):
            try:
                profile = load_profile(selected_name)
                st.session_state["profile"] = profile
                st.sidebar.success(f"Loaded profile: {profile.name}")

                log_beta_event(
                    event_type="profile_loaded",
                    message="Profile loaded.",
                    metadata={"name": profile.name},
                )

            except Exception as error:
                log_beta_error(
                    error=error,
                    user_action="load_profile",
                    metadata={"selected_name": selected_name},
                )
                st.sidebar.error(safe_error_message(error))

                if CONFIG.show_debug_errors:
                    st.sidebar.exception(error)

    st.sidebar.divider()

    active_profile = st.session_state.get("profile")

    name = st.sidebar.text_input(
        "Name",
        value=getattr(active_profile, "name", ""),
    )

    level_options = ["Beginner", "Intermediate", "Advanced"]
    active_level = getattr(active_profile, "level", "Beginner")

    try:
        level_index = level_options.index(active_level)
    except ValueError:
        level_index = 0

    level = st.sidebar.selectbox(
        "Level",
        level_options,
        index=level_index,
    )

    goals = st.sidebar.text_area(
        "Goals",
        value=getattr(active_profile, "goals", ""),
        placeholder="Example: Learn electronics, Python, Linux, and robotics.",
    )

    analogy_preferences = st.sidebar.text_area(
        "Preferred learning style / things to use for analogies",
        value=getattr(active_profile, "analogy_preferences", ""),
        placeholder="Example: gaming, cars, kitchens, chess, electronics, sports.",
    )

    weak_topics = st.sidebar.text_area(
        "Weak topics",
        value=", ".join(getattr(active_profile, "weak_topics", [])),
        placeholder="Example: algebra, Linux permissions, circuits",
    )

    strong_topics = st.sidebar.text_area(
        "Strong topics",
        value=", ".join(getattr(active_profile, "strong_topics", [])),
        placeholder="Example: taxes, Python basics, networking",
    )

    current_streak = st.sidebar.number_input(
        "Current streak",
        min_value=0,
        value=int(getattr(active_profile, "current_streak", 0)),
    )

    last_review_date = st.sidebar.text_input(
        "Last review date",
        value=getattr(active_profile, "last_review_date", "") or "",
        placeholder="Optional, example: 2026-06-27",
    )

    if st.sidebar.button("Save Profile"):
        try:
            decision = check_profile_fields(
                name=name,
                level=level,
                goals=goals,
                analogy_preferences=analogy_preferences,
                weak_topics=weak_topics,
                strong_topics=strong_topics,
            )

            if not decision.allowed:
                log_beta_event(
                    event_type="profile_rejected",
                    message=decision.reason,
                    metadata={"risk_level": decision.risk_level},
                )

                st.sidebar.error(decision.reason)

                for restriction in decision.restrictions:
                    st.sidebar.warning(restriction)

                return

            profile = build_profile(
                name=name,
                level=level,
                goals=goals,
                analogy_preferences=analogy_preferences,
                weak_topics_raw=weak_topics,
                strong_topics_raw=strong_topics,
                current_streak=current_streak,
                last_review_date=last_review_date or None,
            )

            if CONFIG.allow_profile_saving:
                path = save_profile(profile)
                st.sidebar.success(f"Saved profile: {path}")
            else:
                path = None
                st.sidebar.info("Profile saving is disabled in this environment.")

            st.session_state["profile"] = profile

            log_beta_event(
                event_type="profile_saved",
                message="Profile created or updated.",
                metadata={
                    "name": profile.name,
                    "level": profile.level,
                    "saved_path": str(path) if path else None,
                },
            )

            if decision.risk_level == "yellow":
                st.sidebar.warning(decision.reason)

                for restriction in decision.restrictions:
                    st.sidebar.info(restriction)

        except Exception as error:
            log_beta_error(
                error=error,
                user_action="save_profile",
                metadata={"name": name},
            )

            st.sidebar.error(safe_error_message(error))

            if CONFIG.show_debug_errors:
                st.sidebar.exception(error)


def show_active_profile(profile):
    st.subheader(f"Active Profile: {profile.name}")

    profile_col_1, profile_col_2 = st.columns(2)

    with profile_col_1:
        st.write(f"**Level:** {profile.level}")
        st.write(f"**Goals:** {profile.goals}")
        st.write(f"**Analogy Preferences:** {profile.analogy_preferences}")

    with profile_col_2:
        st.write(f"**Weak Topics:** {', '.join(profile.weak_topics) or 'None'}")
        st.write(f"**Strong Topics:** {', '.join(profile.strong_topics) or 'None'}")
        st.write(f"**Current Streak:** {profile.current_streak}")
        st.write(f"**Last Review Date:** {profile.last_review_date or 'None'}")


def show_submission_checker(assignment):
    st.divider()
    st.header("Student Submission Test")

    submission = st.text_area(
        "Paste the student's Feynman explanation or homework response here.",
        placeholder="Explain the topic in your own words...",
    )

    if st.button("Basic Submission Check"):
        try:
            if not submission.strip():
                st.error("Paste a response first.")
                return

            if len(submission) > 5000:
                st.error("Submission is too long for the beta checker.")
                return

            if len(submission.split()) < 25:
                st.warning("Response is short. Ask for more explanation, examples, or corrections.")
            else:
                st.success("Response has enough length for a beta review.")

                if assignment.topic.lower() in submission.lower():
                    st.info("The response mentions the topic directly.")
                else:
                    st.warning(
                        "The response does not mention the topic directly. "
                        "Ask the learner to connect back to the lesson."
                    )

            log_beta_event(
                event_type="submission_checked",
                message="Student submission checked.",
                metadata={
                    "topic": assignment.topic,
                    "word_count": len(submission.split()),
                },
            )

        except Exception as error:
            log_beta_error(
                error=error,
                user_action="submission_check",
                metadata={"topic": getattr(assignment, "topic", None)},
            )

            st.error(safe_error_message(error))

            if CONFIG.show_debug_errors:
                st.exception(error)


def main():
    st.title(CONFIG.app_name)
    st.caption(f"Environment: {CONFIG.environment}")

    show_disclosure()
    show_health_check()
    show_profile_sidebar()

    profile = st.session_state.get("profile")

    if not profile:
        st.info("Create or load a profile to begin.")
        return

    show_active_profile(profile)

    st.divider()
    st.header("Create Lesson + Homework")

    topic = st.text_input(
        "What should OpenDoor teach?",
        placeholder="Example: soldering basics, algebra for taxes, Linux nice and renice",
    )

    use_rag = st.checkbox(
        "Use local RAG knowledge base",
        value=True,
        help="Retrieves local .txt/.md source chunks from data/knowledge/knowledge_chunks.json.",
    )

    if st.button("Generate Virtual Lesson and Assignment"):
        try:
            if not topic.strip():
                st.error("Enter a topic first.")
                return

            decision = check_topic_request(
                topic=topic,
                profile_goals=profile.goals,
            )

            if not decision.allowed:
                log_beta_event(
                    event_type="topic_rejected",
                    message=decision.reason,
                    metadata={
                        "topic": topic,
                        "risk_level": decision.risk_level,
                        "profile": profile.name,
                    },
                )

                st.error(decision.reason)

                for restriction in decision.restrictions:
                    st.warning(restriction)

                return

            if decision.risk_level == "yellow":
                st.warning(decision.reason)

                for restriction in decision.restrictions:
                    st.info(restriction)

            retrieved_chunks = []

            if use_rag:
                retrieved_chunks = retrieve_relevant_chunks(
                    query=topic,
                    limit=4,
                )

            assignment = build_assignment(
                profile=profile,
                topic=topic,
                source_chunks=[chunk.text for chunk in retrieved_chunks],
            )

            st.session_state["assignment"] = assignment
            st.session_state["retrieved_chunks"] = retrieved_chunks

            log_beta_event(
                event_type="assignment_created",
                message="Assignment created.",
                metadata={
                    "topic": topic,
                    "profile": profile.name,
                    "risk_level": decision.risk_level,
                    "rag_chunks": len(retrieved_chunks),
                },
            )

        except Exception as error:
            log_beta_error(
                error=error,
                user_action="generate_assignment",
                metadata={
                    "topic": topic,
                    "profile": getattr(profile, "name", None),
                },
            )

            st.error(safe_error_message(error))

            if CONFIG.show_debug_errors:
                st.exception(error)

    assignment = st.session_state.get("assignment")
    retrieved_chunks = st.session_state.get("retrieved_chunks", [])

    if assignment:
        show_assignment(assignment, retrieved_chunks)
        show_submission_checker(assignment)


if __name__ == "__main__":
    main()