import streamlit as st

from assignment_builder import build_assignment
from beta_config import get_beta_config
from beta_health_check import run_beta_health_check
from beta_logger import log_beta_error, log_beta_event, safe_error_message
from homework_grader import format_homework_review, review_homework_response
from intent_normalizer import normalize_intent
from learning_guard import check_profile_fields, check_text_safety, check_topic_request
from rag_retriever import retrieve_relevant_chunks
from student_profile import (
    build_profile,
    list_profiles,
    load_profile,
    save_profile,
)
from upload_manager import save_uploaded_file


st.set_page_config(
    page_title="OpenDoor Beta",
    page_icon="🚪",
    layout="wide",
)

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


def show_app_header():
    st.title("OpenDoor")
    st.caption("Open the door. Find your house.")

    st.info(
        "OpenDoor is an adaptive learning beta. Start with quick chat, build a learner profile, "
        "or generate a study plan with homework."
    )


def show_health_check():
    if not CONFIG.show_admin_diagnostics:
        return

    with st.expander("Admin Diagnostics", expanded=False):
        health = run_beta_health_check()

        if health.passed:
            st.success("Required beta folders are ready.")
        else:
            st.error("Beta health check failed.")

        for error in health.errors:
            st.error(error)

        for warning in health.warnings:
            st.warning(warning)


def show_new_user_sidebar():
    st.sidebar.header("Start Here")

    profile = get_active_profile()

    if profile:
        st.sidebar.success(f"Active profile: {profile.name}")
    else:
        st.sidebar.warning("No active profile yet.")
        st.sidebar.caption("Go to Profile and create one for personalized lessons.")

    st.sidebar.divider()
    st.sidebar.caption("Public beta. Debug details are hidden from normal users.")


def show_list(title: str, items):
    st.markdown(f"### {title}")

    if not items:
        st.info("Nothing here yet.")
        return

    for item in items:
        st.markdown(f"- {item}")


def quick_chat_answer(message: str) -> str:
    decision = check_text_safety(message)

    if not decision.allowed:
        restrictions = "\n".join(f"- {item}" for item in decision.restrictions)
        return f"I cannot help with that request.\n\nReason: {decision.reason}\n\n{restrictions}"

    intent = normalize_intent(message)
    profile = get_active_profile()

    profile_line = ""

    if profile:
        profile_line = (
            f"\n\nI am using your profile lightly here: level {profile.level}, "
            f"goals: {profile.goals or 'not set'}."
        )

    if intent.output_mode == "quick_chat":
        return (
            f"I read this as: {intent.clean_topic}.\n\n"
            f"Quick answer: {intent.learning_goal}\n\n"
            f"Boundary: {intent.safety_frame}"
            f"{profile_line}"
        )

    return (
        f"I read this as: {intent.clean_topic}.\n\n"
        f"Goal: {intent.learning_goal}\n\n"
        "Small answer: start with the core idea, then ask what decision or example matters most. "
        "If you want a full lesson, use Study + Homework."
        f"{profile_line}"
    )


def show_chat_page():
    st.header("Chat")
    st.caption("Ask quick questions without creating homework or a full course.")

    for entry in st.session_state["chat_history"]:
        with st.chat_message(entry["role"]):
            st.write(entry["content"])

    message = st.chat_input("Ask a quick question...")

    if message:
        st.session_state["chat_history"].append({"role": "user", "content": message})

        try:
            answer = quick_chat_answer(message)
            st.session_state["chat_history"].append({"role": "assistant", "content": answer})

            log_beta_event(
                event_type="chat_message",
                message="Chat prompt answered.",
                metadata={
                    "message_length": len(message),
                    "has_profile": get_active_profile() is not None,
                },
            )

            st.rerun()

        except Exception as error:
            log_beta_error(
                error=error,
                user_action="chat_message",
                metadata={"message_length": len(message)},
            )

            st.error(safe_error_message(error))

            if CONFIG.show_debug_errors:
                st.exception(error)


def show_profile_page():
    st.header("Profile")
    st.caption("Create or load the learner profile. This is what lets OpenDoor adapt.")

    existing_profiles = list_profiles()

    load_col, create_col = st.columns([1, 2])

    with load_col:
        st.subheader("Load")

        if existing_profiles:
            selected_name = st.selectbox("Saved profiles", existing_profiles)

            if st.button("Load Profile"):
                try:
                    profile = load_profile(selected_name)
                    st.session_state["profile"] = profile
                    st.success(f"Loaded {profile.name}")

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
                    st.error(safe_error_message(error))
        else:
            st.info("No saved profiles yet.")

    with create_col:
        st.subheader("Create / Update")

        active_profile = get_active_profile()

        name = st.text_input("Name or nickname", value=getattr(active_profile, "name", ""))
        level_options = ["Beginner", "Intermediate", "Advanced"]
        active_level = getattr(active_profile, "level", "Beginner")

        try:
            level_index = level_options.index(active_level)
        except ValueError:
            level_index = 0

        level = st.selectbox("Current level", level_options, index=level_index)

        goals = st.text_area(
            "Why are you here?",
            value=getattr(active_profile, "goals", ""),
            placeholder="Example: I want to learn electronics and build small projects.",
        )

        analogy_preferences = st.text_area(
            "What examples help you learn?",
            value=getattr(active_profile, "analogy_preferences", ""),
            placeholder="Example: gaming, cars, electronics, real projects, money examples.",
        )

        weak_topics = st.text_area(
            "Weak topics",
            value=", ".join(getattr(active_profile, "weak_topics", [])),
            placeholder="Example: algebra, circuits, Linux permissions",
        )

        strong_topics = st.text_area(
            "Strong topics",
            value=", ".join(getattr(active_profile, "strong_topics", [])),
            placeholder="Example: Python basics, networking, hands-on work",
        )

        current_streak = st.number_input(
            "Current streak",
            min_value=0,
            value=int(getattr(active_profile, "current_streak", 0)),
        )

        last_review_date = st.text_input(
            "Last review date",
            value=getattr(active_profile, "last_review_date", "") or "",
            placeholder="Optional. Example: 2026-06-29",
        )

        if st.button("Save Profile", type="primary"):
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
                    st.error(decision.reason)

                    for restriction in decision.restrictions:
                        st.warning(restriction)

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
                    save_profile(profile)
                    st.success("Profile saved.")
                else:
                    st.info("Profile saving is disabled in this environment.")

                st.session_state["profile"] = profile

                log_beta_event(
                    event_type="profile_saved",
                    message="Profile created or updated.",
                    metadata={
                        "name": profile.name,
                        "level": profile.level,
                    },
                )

            except Exception as error:
                log_beta_error(
                    error=error,
                    user_action="save_profile",
                    metadata={"name": name},
                )

                st.error(safe_error_message(error))

                if CONFIG.show_debug_errors:
                    st.exception(error)

    profile = get_active_profile()

    if profile:
        st.divider()
        st.subheader("Your starting point")

        st.write(f"**Learner:** {profile.name}")
        st.write(f"**Level:** {profile.level}")
        st.write(f"**Goal:** {profile.goals or 'Not set yet'}")
        st.write(f"**Examples that help:** {profile.analogy_preferences or 'Not set yet'}")

        if profile.weak_topics:
            st.write(f"**Things to repair:** {', '.join(profile.weak_topics)}")

        if profile.strong_topics:
            st.write(f"**Strengths:** {', '.join(profile.strong_topics)}")


def show_source_note(assignment, retrieved_chunks):
    if retrieved_chunks:
        with st.expander("Sources used", expanded=False):
            for index, chunk in enumerate(retrieved_chunks, start=1):
                st.markdown(f"**Source {index}: {chunk.source_name}**")
                st.caption(f"Chunk ID: {chunk.chunk_id}")
                st.write(chunk.text)
    else:
        st.info(assignment.source_note)


def show_lesson_card(assignment, retrieved_chunks):
    st.header("Lesson Card")

    if assignment.safety_note:
        st.warning(assignment.safety_note)

    st.subheader("What OpenDoor understood")
    st.write(assignment.summary_card)

    st.subheader("Why this matters")
    st.write(assignment.why_this_matters)

    with st.expander("Learn", expanded=True):
        st.write(assignment.virtual_lesson)

    with st.expander("Check before going deeper", expanded=True):
        for item in assignment.prerequisite_check:
            st.markdown(f"- {item}")

    with st.expander("Learning questions", expanded=True):
        st.markdown("**Comprehension**")
        for item in assignment.learning_questions.comprehension:
            st.markdown(f"- {item}")

        st.markdown("**Misconception checks**")
        for item in assignment.learning_questions.misconception_checks:
            st.markdown(f"- {item}")

        st.markdown("**Application**")
        for item in assignment.learning_questions.application:
            st.markdown(f"- {item}")

    with st.expander("Practice", expanded=True):
        for item in assignment.practice_tasks:
            st.markdown(f"- {item}")

    with st.expander("Active recall", expanded=False):
        for item in assignment.active_recall:
            st.markdown(f"- {item}")

        st.markdown("**Feynman prompt**")
        st.write(assignment.feynman_prompt)

    with st.expander("Mini project and review", expanded=False):
        st.markdown("**Mini project**")
        st.write(assignment.mini_project)

        st.markdown("**Review schedule**")
        for item in assignment.review_schedule:
            st.markdown(f"- {item}")

    show_source_note(assignment, retrieved_chunks)


def show_study_page():
    st.header("Study + Homework")
    st.caption("Generate lessons, learning questions, practice, and homework review.")

    profile = get_active_profile()

    if not profile:
        st.warning("Create or load a profile first for personalized lessons.")
        return

    topic = st.text_input(
        "What do you want to learn?",
        value=st.session_state.get("last_topic", ""),
        placeholder="Example: soldering basics, CIDR notation, Python functions",
    )

    use_rag = st.checkbox(
        "Use local source library if available",
        value=True,
        help="Uses approved local source chunks when the knowledge base exists.",
    )

    if st.button("Build my lesson", type="primary"):
        try:
            if not topic.strip():
                st.error("Enter a topic first.")
                return

            st.session_state["last_topic"] = topic

            decision = check_topic_request(
                topic=topic,
                profile_goals=profile.goals,
            )

            if not decision.allowed:
                st.error(decision.reason)

                for restriction in decision.restrictions:
                    st.warning(restriction)

                return

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

            log_beta_event(
                event_type="assignment_created",
                message="Assignment created.",
                metadata={
                    "raw_topic": topic,
                    "clean_topic": assignment.topic,
                    "profile": profile.name,
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
        st.divider()
        show_lesson_card(assignment, retrieved_chunks)

    st.divider()
    st.header("Upload study material or homework")

    uploaded_file = st.file_uploader(
        "Upload notes, homework, screenshot, PDF, image, or video.",
        type=["txt", "md", "csv", "json", "pdf", "png", "jpg", "jpeg", "webp", "mp4", "mov"],
    )

    if uploaded_file:
        try:
            saved_upload = save_uploaded_file(uploaded_file)

            st.success("File uploaded.")

            if CONFIG.show_admin_diagnostics:
                st.caption(f"Saved to: {saved_upload.display_path}")

            st.caption(f"Size: {saved_upload.size_bytes} bytes")

            if saved_upload.readable_as_text and saved_upload.text_preview:
                with st.expander("Text preview", expanded=True):
                    st.text(saved_upload.text_preview)
            else:
                st.info("File saved for beta review. Deeper image/PDF/video grading comes later.")

            log_beta_event(
                event_type="file_uploaded",
                message="User uploaded file.",
                metadata={
                    "filename": saved_upload.original_name,
                    "extension": saved_upload.extension,
                    "size_bytes": saved_upload.size_bytes,
                },
            )

        except Exception as error:
            log_beta_error(
                error=error,
                user_action="file_upload",
                metadata={"filename": getattr(uploaded_file, "name", None)},
            )

            st.error(safe_error_message(error))

            if CONFIG.show_debug_errors:
                st.exception(error)

    st.divider()
    st.header("Review my answer")

    assignment_topic = ""
    if assignment:
        assignment_topic = assignment.topic

    review_topic = st.text_input(
        "Homework topic",
        value=assignment_topic,
        placeholder="Example: soldering basics",
    )

    response = st.text_area(
        "Paste homework answer or Feynman explanation",
        placeholder="Explain the topic in your own words...",
    )

    if st.button("Review response"):
        try:
            if not response.strip():
                st.error("Paste a response first.")
                return

            if len(response) > CONFIG.max_submission_chars:
                st.error(f"Submission is too long. Limit: {CONFIG.max_submission_chars} characters.")
                return

            decision = check_text_safety(response)

            if not decision.allowed:
                st.error(decision.reason)

                for restriction in decision.restrictions:
                    st.warning(restriction)

                return

            review = review_homework_response(
                topic=review_topic,
                response=response,
            )

            st.text(format_homework_review(review))

            log_beta_event(
                event_type="homework_reviewed",
                message="Homework response reviewed.",
                metadata={
                    "topic": review_topic,
                    "label": review.label,
                    "score": review.score,
                    "word_count": len(response.split()),
                },
            )

        except Exception as error:
            log_beta_error(
                error=error,
                user_action="homework_review",
                metadata={"topic": review_topic},
            )

            st.error(safe_error_message(error))

            if CONFIG.show_debug_errors:
                st.exception(error)


def main():
    init_state()
    show_app_header()
    show_health_check()
    show_new_user_sidebar()

    page = st.sidebar.radio(
        "Navigation",
        [
            "Chat",
            "Profile",
            "Study + Homework",
        ],
    )

    if page == "Chat":
        show_chat_page()
    elif page == "Profile":
        show_profile_page()
    elif page == "Study + Homework":
        show_study_page()


if __name__ == "__main__":
    main()