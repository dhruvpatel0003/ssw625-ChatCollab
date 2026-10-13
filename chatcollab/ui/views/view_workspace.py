"""View 3: Human–AI Collaboration Workspace (Modules M4, M6)."""
import streamlit as st
import time
from ...core.models import (
    WorkflowStage, EventType, RoleType, ParticipantType
)
from ...core.database import Database
from ...core.ollama_client import OllamaClient
from ...engine.timeline import Timeline
from ...engine.decision_engine import DecisionEngine
from ...engine.prd_manager import PRDManager
from ...engine.code_generator import CodeGenerator
from ...engine.sandbox import JavaSandbox
from ...engine.qa_engine import QAEngine
from ...agents.roles import TeamManager
from ..components import render_header, render_event_timeline


def render(
    db: Database,
    timeline: Timeline,
    ollama: OllamaClient,
    decision_engine: DecisionEngine,
    team_manager: TeamManager,
    prd_manager: PRDManager,
    code_generator: CodeGenerator,
    sandbox: JavaSandbox,
    qa_engine: QAEngine,
    project_id: str
):
    render_header("Human–AI Collaboration Workspace", "Shared event-driven Slack-like workspace for Human and AI team members")

    project = db.get_project(project_id)
    if not project:
        st.warning("Please select or initialize a project in the sidebar.")
        return

    current_stage = WorkflowStage(project["stage"])

    # Stage progress indicator
    stages = [
        WorkflowStage.REQUIREMENTS,
        WorkflowStage.PRD_CREATION,
        WorkflowStage.PRD_REVIEW,
        WorkflowStage.DEVELOPMENT,
        WorkflowStage.QA_TESTING,
        WorkflowStage.COMPLETED
    ]
    st.markdown("#### Workflow Progression")
    stage_cols = st.columns(len(stages))
    for i, s in enumerate(stages):
        is_active = (s == current_stage)
        color = "#6c5ce7" if is_active else "#636e72"
        badge = f"**[{s.value}]**" if is_active else s.value
        stage_cols[i].markdown(f"<div style='text-align:center; padding:6px; border-radius:8px; border: 1px solid {color}; color:{color}; font-size:0.78rem;'>{badge}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Action Toolbar
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("▶ Step Agent Turn", use_container_width=True, help="Trigger next autonomous AI turn cycle"):
            with st.spinner("Agents evaluating timeline..."):
                events = decision_engine.run_collaboration_turn(project_id)
                if events:
                    st.success(f"{len(events)} agent action(s) published!")
                else:
                    st.info("All agents chose to WAIT or preconditions not met.")
                st.rerun()

    with col2:
        if st.button("📄 Draft / Revise PRD", use_container_width=True, help="AI Product Manager authors PRD"):
            with st.spinner("Product Manager generating PRD with Ollama..."):
                req_text = project["description"] or "Java Tic-Tac-Toe"
                history_text = timeline.format_recent_history_for_prompt(project_id)
                prd_manager.generate_prd(project_id, req_text, history_text, project.get("active_model"))
                st.success("PRD generated and submitted for review!")
                st.rerun()

    with col3:
        if st.button("💻 Implement Code", use_container_width=True, help="Developer writes Java 17 code"):
            prds = db.list_artifacts(project_id, "PRD")
            if not prds:
                st.error("Cannot implement code: PRD has not been generated yet!")
            elif not prds[0]["metadata"].get("approved") and current_stage != WorkflowStage.DEVELOPMENT:
                st.warning("Warning: PRD has not been officially approved yet. Developer policy is to wait for approval.")
            else:
                with st.spinner("AI Developer generating modular Java 17 code..."):
                    code_generator.generate_code_from_prd(project_id, prds[0]["content"], model_name=project.get("active_model"))
                    db.update_project_stage(project_id, WorkflowStage.DEVELOPMENT)
                    st.success("Java source files generated and saved in workspace!")
                    st.rerun()

    with col4:
        if st.button("⚙️ Compile & Test", use_container_width=True, help="Compile with javac 17 and run unit tests"):
            code_arts = db.list_artifacts(project_id, "CODE")
            art_id = code_arts[0]["artifact_id"] if code_arts else None
            with st.spinner("Compiling with javac and executing unit tests..."):
                res = sandbox.compile_and_test(project_id, artifact_id=art_id)
                db.update_project_stage(project_id, WorkflowStage.QA_TESTING)
                if res["compilation_passed"] and res["tests_failed"] == 0:
                    st.success(f"Compilation SUCCESS! {res['tests_passed']} unit tests passed.")
                else:
                    st.error("Compilation or test failure detected in sandbox.")
                st.rerun()

    with col5:
        if st.button("🔍 QA Inspection", use_container_width=True, help="AI QA reviews code against PRD"):
            prds = db.list_artifacts(project_id, "PRD")
            code_arts = db.list_artifacts(project_id, "CODE")
            test_runs = db.get_test_runs(project_id)
            if not prds or not code_arts:
                st.error("Need both PRD and code artifacts before QA inspection.")
            else:
                latest_test = test_runs[0] if test_runs else {"compilation_passed": False, "tests_passed": 0, "tests_failed": 1, "stdout": "", "stderr": "No tests run"}
                with st.spinner("QA Engineer inspecting implementation against PRD..."):
                    qa_engine.review_implementation(
                        project_id=project_id,
                        artifact_id=code_arts[0]["artifact_id"],
                        prd_text=prds[0]["content"],
                        code_text=code_arts[0]["content"],
                        test_results=latest_test,
                        model_name=project.get("active_model")
                    )
                    st.success("QA report published to timeline!")
                    st.rerun()

    st.markdown("---")

    # Main layout: Left = Live Timeline, Right = Human Input & Context
    t_col, input_col = st.columns([3, 2])

    with t_col:
        st.subheader("Shared Event Timeline (Slack-like Transcript)")
        events = db.get_events(project_id)
        # Filter toggle for WAIT events
        show_waits = st.checkbox("Show low-level AGENT_WAITING events", value=False)
        display_events = events if show_waits else [e for e in events if e.event_type != EventType.AGENT_WAITING]
        render_event_timeline(display_events, max_events=40)

    with input_col:
        st.subheader("Human Participant Console")
        st.markdown(f"**Acting As**: `{team_manager.human_role.value}`")

        with st.form("human_msg_form", clear_on_submit=True):
            user_msg = st.text_area("Your Message / Steering Input:", placeholder="Clarify requirements, answer agent questions, or direct priorities...", height=120)
            target = st.selectbox("Direct Message to (Optional):", ["Everyone", "AI Product Manager", "AI Developer", "AI QA Engineer", "AI CEO"])
            submitted = st.form_submit_button("Send Message to Team", use_container_width=True)

            if submitted and user_msg.strip():
                timeline.publish_event(
                    project_id=project_id,
                    actor_id="human_user",
                    actor_name="Dhruv (Human)",
                    actor_role=team_manager.human_role,
                    participant_type=ParticipantType.HUMAN,
                    event_type=EventType.HUMAN_FEEDBACK,
                    message=user_msg.strip(),
                    payload={"target": target},
                    stage=current_stage
                )
                st.success("Message posted to timeline!")
                st.rerun()

        # Quick Actions for Approval if Human is CEO or PRD is pending
        prds = db.list_artifacts(project_id, "PRD")
        if prds and not prds[0]["metadata"].get("approved"):
            st.markdown("#### PRD Approval Action")
            st.warning("PRD is awaiting approval!")
            ap_col, rej_col = st.columns(2)
            with ap_col:
                if st.button("Approve PRD", use_container_width=True):
                    prd_manager.approve_prd(project_id, "Dhruv (Human Approver)", team_manager.human_role, ParticipantType.HUMAN)
                    st.success("PRD approved! Stage advanced to DEVELOPMENT.")
                    st.rerun()
            with rej_col:
                if st.button("Reject PRD", use_container_width=True):
                    prd_manager.reject_prd(project_id, "Needs revisions for clarity", "Dhruv (Human Approver)", team_manager.human_role, ParticipantType.HUMAN)
                    st.warning("PRD rejected. PM will revise.")
                    st.rerun()
