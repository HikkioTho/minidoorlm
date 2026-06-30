import streamlit as st

from assignment_builder import build_assignment
from beta_config import get_beta_config
from beta_health_check import run_beta_health_check
from beta_logger import log_beta_error, log_beta_event, safe_error_message
from engagement_engine import (
    build_celebration_moment,
    build_mastery_map_preview,
    build_mood_energy_check,
    build_onboarding_card,
    build_path_direction,
    build_session_summary,
    build_transparency_card,
    detect_basic_frustration,
)
from homework_grader import format_homework_review, review_homework_response
from intent_normalizer import normalize_intent
from learning_guard import check_profile_fields, check_text_safety, check_topic_request
from minidoor_persona import format_tutor_feedback
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
        "onboarding_card": None,
        "celebration": None,
        "session_energy": "Normal lesson",
        "home_input": "",
        "home_review_text": "",
        "active_page": "Home",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_active_profile():
    return st.session_state.get("profile")


def inject_clean_css():
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 4rem;
            max-width: 1120px;
        }

        div[data-testid="stAlert"] {
            border-radius: 14px;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        .od-hero {
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 18px;
            padding: 1.25rem 1.35rem;
            margin: 0.75rem 0 1rem 0;
            background: rgba(255,255,255,0.035);
        }

        .od-card {
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 16px;
            padding: 1.05rem 1.15rem;
            margin: 0.75rem 0;
            background: rgba(255,255,255,0.03);
        }

        .od-muted {
            color: rgba(255,255,255,0.68);
            font-size: 0.92rem;
        }

        .od-pill {
            display: inline-block;
            border: 1px solid rgba(255,255,255,0.16);
            border-radius: 999px;
            padding: 0.25rem 0.7rem;
            margin: 0.2rem 0.25rem 0.2rem 0;
            font-size: 0.88rem;
        }

        .od-big-label {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_app_header():
    st.title("OpenDoor")
    st.caption("Open the door. Find your house.")


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


def show_sidebar():
    st.sidebar.header("OpenDoor")

    profile = get_active_profile()

    if profile:
        st.sidebar.success(f"Active profile: {profile.name}")
    else:
        st.sidebar.warning("No profile yet")
        st.sidebar.caption("Quick chat still works. Create a profile for adaptive lessons.")

    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigation",
        [
            "Home",
            "Chat",
            "Profile",
            "Study + Homework",
        ],
        index=[
            "Home",
            "Chat",
            "Profile",
            "Study + Homework",
        ].index(st.session_state.get("active_page", "Home")),
    )

    st.session_state["active_page"] = page

    st.sidebar.divider()
    st.sidebar.caption("Public beta. Debug details are hidden from normal users.")

    return page


def run_quick_answer(message: str) -> str:
    decision = check_text_safety(message)

    if not decision.allowed:
        restrictions = "\n".join(f"- {item}" for item in decision.restrictions)
        return f"I cannot help with that request.\n\nReason: {decision.reason}\n\n{restrictions}"

    intent = normalize_intent(message)
    profile = get_active_profile()

    profile_line = ""

    if profile:
        profile_line = (
            f"\n\nProfile used: {profile.name}, level {profile.level}, goal: {profile.goals or 'not set'}."
        )

    if intent.domain == "trades_plumbing":
        return (
            f"I read this as: {intent.clean_topic}.\n\n"
            f"First door: {intent.first_door}.\n\n"
            "Start here:\n"
            "1. Learn the system map: supply, drain, vent, fixtures, traps, and shutoff valves.\n"
            "2. Learn tool names before using tools.\n"
            "3. Learn safety and local code boundaries.\n"
            "4. Do observation first: map one sink without changing anything.\n"
            "5. If this is career-focused, look into apprenticeship routes and licensing rules in your area.\n\n"
            f"Next best action: {intent.next_best_action}"
            f"{profile_line}"
        )

    return (
        f"I read this as: {intent.clean_topic}.\n\n"
        f"First door: {intent.first_door}.\n\n"
        f"Quick answer: {intent.learning_goal}\n\n"
        f"Next best action: {intent.next_best_action}"
        f"{profile_line}"
    )


def build_lesson_from_topic(topic: str, use_rag: bool = True):
    profile = get_active_profile()

    if not profile:
        st.warning("Create a profile for full adaptive lesson generation. Quick answers still work without one.")
        return None, []

    decision = check_topic_request(
        topic=topic,
        profile_goals=profile.goals,
    )

    if not decision.allowed:
        st.error(decision.reason)

        for restriction in decision.restrictions:
            st.warning(restriction)

        return None, []

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
    st.session_state["last_topic"] = topic
    st.session_state["celebration"] = build_celebration_moment(
        event_type="door_unlocked",
        concept=assignment.topic,
    )

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

    return assignment, retrieved_chunks


def show_home_action_center():
    st.markdown(
        """
        <div class="od-hero">
            <h3>Start here</h3>
            <p class="od-muted">
            Ask a quick question, build a lesson, or paste homework. OpenDoor will route it.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_input = st.text_area(
        "What do you want to learn, ask, or review?",
        value=st.session_state.get("home_input", ""),
        placeholder="Example: how do I start a plumbing career?",
        height=110,
        key="home_input_box",
    )

    st.session_state["home_input"] = user_input

    action = st.radio(
        "What should OpenDoor do?",
        [
            "Quick answer",
            "Build lesson",
            "Review homework",
        ],
        horizontal=True,
    )

    use_rag = st.checkbox(
        "Use source library if available",
        value=True,
        help="Uses approved local source chunks when a knowledge base exists.",
    )

    if action == "Review homework":
        review_text = st.text_area(
            "Paste the homework answer or Feynman explanation here",
            value=st.session_state.get("home_review_text", ""),
            height=160,
            key="home_review_box",
        )
        st.session_state["home_review_text"] = review_text

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        run_button = st.button("Run OpenDoor", type="primary", use_container_width=True)

    with col2:
        clear_button = st.button("Clear", use_container_width=True)

    if clear_button:
        st.session_state["home_input"] = ""
        st.session_state["home_review_text"] = ""
        st.rerun()

    if not run_button:
        return

    if not user_input.strip():
        st.error("Type what you want to learn, ask, or review first.")
        return

    try:
        if action == "Quick answer":
            answer = run_quick_answer(user_input)
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            st.session_state["chat_history"].append({"role": "assistant", "content": answer})

            with st.container(border=True):
                st.markdown("### Quick answer")
                st.write(answer)

            log_beta_event(
                event_type="home_quick_answer",
                message="Home quick answer created.",
                metadata={"message_length": len(user_input)},
            )

        elif action == "Build lesson":
            assignment, retrieved_chunks = build_lesson_from_topic(user_input, use_rag=use_rag)

            if assignment:
                st.success("Lesson built. Scroll down or open Study + Homework to keep working.")
                show_lesson_card(assignment, retrieved_chunks)

        elif action == "Review homework":
            review_text = st.session_state.get("home_review_text", "")

            if not review_text.strip():
                st.error("Paste the homework answer before reviewing.")
                return

            decision = check_text_safety(review_text)

            if not decision.allowed:
                st.error(decision.reason)

                for restriction in decision.restrictions:
                    st.warning(restriction)

                return

            intent = normalize_intent(user_input)
            review = review_homework_response(
                topic=intent.clean_topic,
                response=review_text,
            )

            with st.container(border=True):
                st.markdown("### Homework review")
                st.text(format_homework_review(review))

            frustration_signal = detect_basic_frustration(review_text)

            if frustration_signal:
                st.warning(frustration_signal)
                st.info(
                    format_tutor_feedback(
                        correct_piece="You submitted enough text for OpenDoor to inspect your reasoning.",
                        weak_piece="The response shows signs that the current explanation may not be landing.",
                        next_step="Try a shorter explanation style or ask OpenDoor to explain it another way.",
                    )
                )

            log_beta_event(
                event_type="home_homework_review",
                message="Home homework review completed.",
                metadata={
                    "topic": intent.clean_topic,
                    "label": review.label,
                    "score": review.score,
                },
            )

    except Exception as error:
        log_beta_error(
            error=error,
            user_action="home_action_center",
            metadata={"action": action, "input_length": len(user_input)},
        )

        st.error(safe_error_message(error))

        if CONFIG.show_debug_errors:
            st.exception(error)


def show_home_page():
    st.header("Home")
    st.caption("One place to start. Ask, learn, or review.")

    show_home_action_center()

    st.divider()

    profile = get_active_profile()
    assignment = st.session_state.get("assignment")
    retrieved_chunks = st.session_state.get("retrieved_chunks", [])

    if not profile:
        with st.container(border=True):
            st.markdown("### No profile yet")
            st.write("Quick answers work now. Create a profile when you want OpenDoor to adapt to your goals, level, and weak spots.")
            st.write("Go to Profile when ready.")
        return

    summary = build_session_summary(profile, assignment)

    st.subheader("Your learner model")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### Since last session")
            for item in summary.since_last_session:
                st.markdown(f"- {item}")

    with col2:
        with st.container(border=True):
            st.markdown("### Next best action")
            st.write(summary.next_best_action)

            if summary.door_unlocked:
                st.success(summary.door_unlocked)

    with st.expander("Forgetting and repair alerts", expanded=False):
        for item in summary.forgetting_alerts:
            st.markdown(f"- {item}")

    with st.expander("Mastery map preview", expanded=False):
        mastery_nodes = build_mastery_map_preview(profile)

        for node in mastery_nodes:
            with st.container(border=True):
                st.markdown(f"**{node.name}**")
                st.caption(f"Status: {node.status}")
                st.progress(min(max(node.mastery, 0.0), 1.0))
                st.caption(f"Forgetting risk: {node.forgetting_risk:.0%}")
                st.write(node.note)

    mood = build_mood_energy_check()

    with st.expander("Session mode", expanded=False):
        selected_energy = st.radio(
            mood.prompt,
            mood.options,
            horizontal=True,
        )
        st.caption(mood.use_for)
        st.session_state["session_energy"] = selected_energy

    if assignment:
        with st.expander("Why this was assigned", expanded=False):
            transparency = build_transparency_card(profile, assignment, retrieved_chunks)

            st.write(f"**Assigned:** {transparency.assigned}")
            st.write(transparency.why)
            st.markdown("**Learner model used:**")

            for item in transparency.learner_model_used:
                st.markdown(f"- {item}")

            st.caption(transparency.source_note)
            st.caption(transparency.user_can_override)

        with st.expander("Where this could go", expanded=False):
            for path in build_path_direction(assignment.topic):
                st.markdown(f"- {path}")


def show_chat_page():
    st.header("Chat")
    st.caption("Ask quick questions without creating homework or a full course.")

    prompt = st.text_input(
        "Quick question",
        placeholder="Example: what is a shutoff valve?",
    )

    if st.button("Ask", type="primary"):
        if not prompt.strip():
            st.error("Type a question first.")
            return

        try:
            answer = run_quick_answer(prompt)
            st.session_state["chat_history"].append({"role": "user", "content": prompt})
            st.session_state["chat_history"].append({"role": "assistant", "content": answer})
            st.rerun()

        except Exception as error:
            log_beta_error(
                error=error,
                user_action="chat_message",
                metadata={"message_length": len(prompt)},
            )

            st.error(safe_error_message(error))

            if CONFIG.show_debug_errors:
                st.exception(error)

    if st.session_state["chat_history"]:
        st.divider()
        st.subheader("Conversation")

    for entry in st.session_state["chat_history"]:
        with st.chat_message(entry["role"]):
            st.write(entry["content"])


def show_profile_page():
    st.header("Profile")
    st.caption("Create the learner model. This is what lets OpenDoor adapt.")

    existing_profiles = list_profiles()

    with st.container(border=True):
        st.subheader("Guided start")

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
            placeholder="Example: I want to start a plumbing career, learn electronics, or pass Security+.",
        )

        analogy_preferences = st.text_area(
            "What examples help you learn?",
            value=getattr(active_profile, "analogy_preferences", ""),
            placeholder="Example: gaming, cars, electronics, real projects, money examples.",
        )

        weak_topics = st.text_area(
            "What feels weak or confusing?",
            value=", ".join(getattr(active_profile, "weak_topics", [])),
            placeholder="Example: algebra, tools, circuits, networking, code errors",
        )

        strong_topics = st.text_area(
            "What do you already feel good at?",
            value=", ".join(getattr(active_profile, "strong_topics", [])),
            placeholder="Example: Python basics, hands-on work, troubleshooting",
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

                seed_topic = profile.weak_topics[0] if profile.weak_topics else profile.goals

                onboarding_card = build_onboarding_card(
                    name=profile.name,
                    learner_reason=profile.goals,
                    starting_topic=seed_topic,
                    level=profile.level,
                    analogy_preferences=profile.analogy_preferences,
                )

                st.session_state["onboarding_card"] = onboarding_card

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

    if existing_profiles:
        with st.expander("Load existing profile", expanded=False):
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

    profile = get_active_profile()

    if profile:
        st.divider()
        st.subheader("Your starting point")

        with st.container(border=True):
            st.write(f"**Learner:** {profile.name}")
            st.write(f"**Level:** {profile.level}")
            st.write(f"**Goal:** {profile.goals or 'Not set yet'}")
            st.write(f"**Examples that help:** {profile.analogy_preferences or 'Not set yet'}")

            if profile.weak_topics:
                st.write(f"**Things to repair:** {', '.join(profile.weak_topics)}")

            if profile.strong_topics:
                st.write(f"**Strengths:** {', '.join(profile.strong_topics)}")

        onboarding_card = st.session_state.get("onboarding_card")

        if onboarding_card:
            st.subheader("Your first door")

            with st.container(border=True):
                st.markdown(f"### {onboarding_card.first_door}")
                st.write(onboarding_card.delight_moment)
                st.write(onboarding_card.next_step)


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

    with st.container(border=True):
        st.subheader("What OpenDoor understood")
        st.write(assignment.summary_card)

    celebration = st.session_state.get("celebration")

    if celebration:
        with st.container(border=True):
            st.markdown(f"### {celebration.title}")
            st.write(celebration.message)

            if celebration.unlocked:
                st.success(celebration.unlocked)

            st.caption(celebration.next_hint)

    with st.container(border=True):
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
    st.caption("Turn a topic into a lesson, learning questions, practice, and review.")

    profile = get_active_profile()

    if not profile:
        st.warning("Create or load a profile first for personalized lessons.")
        st.info("Quick answers still work from Home or Chat.")
        return

    topic = st.text_input(
        "What do you want to learn?",
        value=st.session_state.get("last_topic", ""),
        placeholder="Example: how do I start a plumbing career?",
    )

    use_rag = st.checkbox(
        "Use local source library if available",
        value=True,
        help="Uses approved local source chunks when the knowledge base exists.",
    )

    if st.button("Build my lesson", type="primary"):
        if not topic.strip():
            st.error("Enter a topic first.")
            return

        try:
            assignment, retrieved_chunks = build_lesson_from_topic(topic, use_rag=use_rag)

            if assignment:
                st.success("Lesson built.")

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
        placeholder="Example: plumbing fundamentals",
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

            frustration_signal = detect_basic_frustration(response)

            if frustration_signal:
                st.warning(frustration_signal)
                st.info(
                    format_tutor_feedback(
                        correct_piece="You submitted enough text for OpenDoor to inspect your reasoning.",
                        weak_piece="The response shows signs that the current explanation may not be landing.",
                        next_step="Try a shorter explanation style or ask OpenDoor to explain it another way.",
                    )
                )

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
    inject_clean_css()
    show_app_header()
    show_health_check()

    page = show_sidebar()

    if page == "Home":
        show_home_page()
    elif page == "Chat":
        show_chat_page()
    elif page == "Profile":
        show_profile_page()
    elif page == "Study + Homework":
        show_study_page()


if __name__ == "__main__":
    main()