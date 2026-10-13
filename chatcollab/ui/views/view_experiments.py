"""View 10: Experiment Lab (Module M13)."""
import streamlit as st
from pathlib import Path
import pandas as pd
from ...core.database import Database
from ...core.ollama_client import OllamaClient
from ...core.config import DATA_DIR
from ...analytics.experiments import ExperimentRunner, EXPERIMENT_CONDITIONS
from ..components import render_header, render_kpi


def render(db: Database, ollama: OllamaClient):
    render_header("Experiment Lab", "Execute and compare the 8 experimental conditions inspired by ChatCollab with CSV export")

    runner = ExperimentRunner(db, ollama)
    runs = db.list_experiment_runs()

    st.markdown("### Run Experimental Condition Trial")
    st.info("Systematically test team behavior under different behavioral personas and human role configurations.")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        cond_names = [f"{c['id']}: {c['name']}" for c in EXPERIMENT_CONDITIONS]
        sel_idx = st.selectbox("Select Condition to Run:", range(len(cond_names)), format_func=lambda i: cond_names[i])
        selected_cond = EXPERIMENT_CONDITIONS[sel_idx]
    with c2:
        run_num = st.number_input("Run Number (#):", min_value=1, max_value=10, value=1)
    with c3:
        st.write("")
        st.write("")
        run_btn = st.button("🚀 Run Condition Trial", use_container_width=True)

    st.caption(f"**Condition Details:** {selected_cond['description']}")

    if run_btn:
        with st.spinner(f"Running automated trial for {selected_cond['name']} (Ollama inference)..."):
            res = runner.run_condition_trial(
                condition_info=selected_cond,
                run_number=int(run_num)
            )
            st.success(f"Trial complete in {res['duration_seconds']}s! Created project `{res['id']}`.")
            st.rerun()

    st.markdown("---")
    st.markdown("### Recorded Experiment Runs")

    if not runs:
        st.info("No experiment trials have been run yet.")
    else:
        # KPI summary
        k1, k2, k3 = st.columns(3)
        render_kpi(k1, "Total Trials Executed", len(runs), "Multi-run History")
        render_kpi(k2, "Avg Trial Duration", f"{sum(r['duration_seconds'] for r in runs) / len(runs):.1f} s", "Execution Performance")
        render_kpi(k3, "Success Rate", f"{(sum(1 for r in runs if r['compilation_success']) / len(runs)) * 100:.0f}%", "Compilation Success")

        # Table
        rows = []
        for r in runs:
            rows.append({
                "Run ID": r["id"],
                "Condition": r["condition_name"],
                "Run #": r["run_number"],
                "Duration (s)": r["duration_seconds"],
                "Messages": r["message_count"],
                "Compile OK": "✅" if r["compilation_success"] else "❌",
                "Timestamp": r["created_at"]
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        # CSV Export
        csv_path = DATA_DIR / "experiment_runs_export.csv"
        runner.export_runs_to_csv(csv_path)
        with open(csv_path, "rb") as f:
            st.download_button(
                label="📥 Export All Experiment Runs to CSV",
                data=f.read(),
                file_name="chatcollab_experiment_runs.csv",
                mime="text/csv"
            )
