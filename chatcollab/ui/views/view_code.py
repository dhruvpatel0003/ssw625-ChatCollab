"""View 6: Code & Artifact Explorer (Module M9)."""
import streamlit as st
import io
import zipfile
from pathlib import Path
from ...core.database import Database
from ...core.config import WORKSPACE_DIR
from ..components import render_header


def render(db: Database, project_id: str):
    render_header("Code & Artifact Explorer", "Inspect generated Java 17 modular codebase, unit tests, and download deliverables")

    ws_dir = WORKSPACE_DIR / project_id / "src"
    if not ws_dir.exists():
        st.info("No workspace directory found for this project yet. Use the Workspace to generate code.")
        return

    java_files = list(ws_dir.glob("*.java"))
    if not java_files:
        st.info("No Java source files found in workspace yet.")
        return

    st.markdown(f"### Generated Java Files ({len(java_files)} files)")

    # Zip download preparation
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for jf in java_files:
            zip_file.writestr(jf.name, jf.read_text(encoding="utf-8"))
    zip_buffer.seek(0)

    st.download_button(
        label="📦 Download Complete Java Project (.zip)",
        data=zip_buffer,
        file_name=f"chatcollab_java_{project_id}.zip",
        mime="application/zip",
        use_container_width=True
    )

    st.markdown("---")

    tabs = st.tabs([f.name for f in java_files])
    for i, jf in enumerate(java_files):
        with tabs[i]:
            code_content = jf.read_text(encoding="utf-8")
            line_count = len(code_content.splitlines())
            st.caption(f"Path: `{jf}` | Lines: {line_count}")
            st.code(code_content, language="java")
