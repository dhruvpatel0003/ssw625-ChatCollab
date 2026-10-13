"""View 7: QA & Test Results (Module M10)."""
import streamlit as st
from ...core.database import Database
from ..components import render_header, render_kpi


def render(db: Database, project_id: str):
    render_header("QA & Test Results", "Deterministic Java sandbox execution logs, unit test verification, and defect reports")

    test_runs = db.get_test_runs(project_id)
    qa_reports = db.list_artifacts(project_id, artifact_type="QA_REPORT")

    if not test_runs and not qa_reports:
        st.info("No test runs or QA evaluations recorded for this project yet. Use the Workspace to run 'Compile & Test' or 'QA Inspection'.")
        return

    # Latest Test Run
    if test_runs:
        latest = test_runs[0]
        st.markdown("### Deterministic Sandbox Execution Evidence")
        c1, c2, c3, c4 = st.columns(4)
        comp_ok = bool(latest["compilation_passed"])
        render_kpi(c1, "Compilation", "PASSED" if comp_ok else "FAILED", "javac 17")
        render_kpi(c2, "Unit Tests Passed", latest["tests_passed"], "Assertions")
        render_kpi(c3, "Unit Tests Failed", latest["tests_failed"], "Assertions")
        render_kpi(c4, "Execution Time", f"{latest['execution_time_ms']:.1f} ms", "Isolated Subprocess")

        with st.expander("Terminal Execution Console (stdout & stderr)", expanded=True):
            if latest["stdout"]:
                st.markdown("**stdout:**")
                st.code(latest["stdout"], language="text")
            if latest["stderr"]:
                st.markdown("**stderr:**")
                st.code(latest["stderr"], language="text")

    st.markdown("---")

    # QA Report Evaluation
    if qa_reports:
        latest_qa = qa_reports[0]
        meta = latest_qa.get("metadata", {})
        st.markdown(f"### {latest_qa['title']}")
        if meta.get("approved"):
            st.success("✅ QA Status: APPROVED — All functional and acceptance criteria verified.")
        else:
            st.error(f"❌ QA Status: REVISION REQUIRED — {meta.get('defect_count', 1)} defect(s) detected.")

        st.markdown(latest_qa["content"])
