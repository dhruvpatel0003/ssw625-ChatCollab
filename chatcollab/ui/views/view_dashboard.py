"""View 1: Overview Dashboard (Module M1)."""
import streamlit as st
from ...core.database import Database
from ...core.ollama_client import OllamaClient
from ...engine.sandbox import JavaSandbox
from ...analytics.metrics import CollaborationMetrics
from ..components import render_header, render_kpi


def render(db: Database, ollama: OllamaClient, project_id: str):
    render_header("Overview Dashboard", "Real-time state of the Human–AI Software Development Laboratory")

    project = db.get_project(project_id) if project_id else None
    metrics_calc = CollaborationMetrics(db)
    metrics = metrics_calc.get_summary_metrics(project_id) if project_id else {}

    # System Status Row
    c1, c2, c3, c4 = st.columns(4)
    health = ollama.check_health()
    ollama_ok = health.get("status") == "connected"
    render_kpi(c1, "Ollama Server", "Connected" if ollama_ok else "Offline", health.get("url", ""))
    render_kpi(c2, "Active Model", project.get("active_model", ollama.default_model) if project else ollama.default_model, "Local Inference")
    render_kpi(c3, "Workflow Stage", project.get("stage", "REQUIREMENTS") if project else "No Project", "Current Phase")
    render_kpi(c4, "Timeline Events", metrics.get("total_events", 0), "Total Events Logged")

    st.markdown("### Active Collaboration Metrics")
    m1, m2, m3, m4 = st.columns(4)
    render_kpi(m1, "Chat Messages", metrics.get("chat_messages_count", 0), "Conversational Turns")
    render_kpi(m2, "Agent WAITs", metrics.get("waiting_actions_count", 0), "Autonomy Decisions")
    render_kpi(m3, "Artifacts Created", metrics.get("artifacts_count", 0), "PRDs & Code Files")
    render_kpi(m4, "Test Runs", metrics.get("test_runs_count", 0), "Sandbox Executions")

    if project:
        st.markdown("### Project Overview")
        with st.container():
            st.info(f"**Project**: {project['name']} | **Persona Condition**: {project.get('persona', 'Baseline')}")
            st.write(f"**Goal**: {project.get('description', 'Tic-Tac-Toe Benchmark')}")
    else:
        st.warning("No active project session selected. Use the sidebar to create or select a project.")
