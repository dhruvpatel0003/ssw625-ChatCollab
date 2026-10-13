"""View 15: System Diagnostics & Settings (Module M1)."""
import streamlit as st
import subprocess
from pathlib import Path
from ...core.database import Database
from ...core.ollama_client import OllamaClient
from ...core.config import DB_PATH, WORKSPACE_DIR
from ..components import render_header, render_kpi


def render(db: Database, ollama: OllamaClient, project_id: str):
    render_header("System Settings & Diagnostics", "Monitor local Ollama engine, Java environment, database health, and runtime paths")

    st.markdown("### 🔌 Ollama Local Server Diagnostics")
    c1, c2, c3 = st.columns(3)

    health = ollama.check_health()
    is_connected = health.get("status") == "connected"
    render_kpi(c1, "Server Status", "ONLINE" if is_connected else "OFFLINE", health.get("url", ""))
    render_kpi(c2, "Available Models", len(health.get("models", [])), "Locally Stored")
    render_kpi(c3, "Default Model", ollama.default_model, "Configured")

    with st.expander("Installed Models in Local Ollama", expanded=True):
        models = health.get("models", [])
        if models:
            for m in models:
                st.write(f"- `{m}`")
        else:
            st.warning("No models reported by Ollama. Ensure 'ollama serve' is active.")

    st.markdown("---")
    st.markdown("### ☕ Java 17 Development Kit Diagnostics")
    j1, j2 = st.columns(2)
    try:
        j_ver = subprocess.run(["javac", "-version"], capture_output=True, text=True, timeout=5)
        javac_ok = (j_ver.returncode == 0)
        ver_text = (j_ver.stdout or j_ver.stderr).strip()
    except Exception as e:
        javac_ok = False
        ver_text = str(e)

    render_kpi(j1, "Compiler (javac)", "AVAILABLE" if javac_ok else "MISSING", ver_text)
    render_kpi(j2, "Workspace Storage", str(WORKSPACE_DIR), "Isolated Sandboxes")

    st.markdown("---")
    st.markdown("### 🗄️ Persistence & Database Diagnostics")
    st.write(f"**Database Location:** `{DB_PATH}`")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        tables = ["projects", "events", "artifacts", "test_runs", "ipa_classifications", "experiment_runs"]
        counts = {}
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            counts[t] = cursor.fetchone()[0]

    d_cols = st.columns(len(tables))
    for i, (t, cnt) in enumerate(counts.items()):
        render_kpi(d_cols[i], t, cnt, "Records")

    st.markdown("---")
    st.markdown("### ⚠️ Session Reset & Maintenance")
    if st.button("Initialize Sample Benchmark Project", use_container_width=True):
        sample_id = "sample_tictactoe_benchmark"
        db.create_project(
            project_id=sample_id,
            name="Java Tic-Tac-Toe Benchmark Session",
            description="Develop a text-based, two-player Java Tic-Tac-Toe application with 3x3 board, Player X and O, input validation, win/draw detection, and replay loop.",
            persona="Baseline Institutional Knowledge",
            active_model=ollama.default_model
        )
        st.success(f"Sample project '{sample_id}' initialized! Select it from the sidebar.")
        st.rerun()
