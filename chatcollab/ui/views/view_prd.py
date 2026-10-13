"""View 5: PRD and Approval Center (Module M7)."""
import streamlit as st
from ...core.database import Database
from ...engine.prd_manager import PRDManager
from ...agents.roles import TeamManager
from ...core.models import ParticipantType
from ..components import render_header


def render(db: Database, prd_manager: PRDManager, team_manager: TeamManager, project_id: str):
    render_header("PRD & Approval Center", "Manage structured Product Requirements Documents and milestone approval gates")

    prds = db.list_artifacts(project_id, artifact_type="PRD")
    if not prds:
        st.info("No Product Requirements Document (PRD) has been generated for this project yet. Use the Workspace to prompt the AI Product Manager.")
        return

    latest = prds[0]
    meta = latest.get("metadata", {})
    is_approved = meta.get("approved", False)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"{latest['title']}")
    with col2:
        if is_approved:
            st.success("✅ APPROVED")
        else:
            st.warning("⏳ PENDING APPROVAL")

    st.markdown("---")

    # Review & Approval Actions
    st.markdown("### Approval Gate")
    st.write(f"**Current User Role**: `{team_manager.human_role.value}`")

    a_col, r_col = st.columns(2)
    with a_col:
        if not is_approved:
            if st.button("✅ Officially Approve PRD", use_container_width=True):
                prd_manager.approve_prd(
                    project_id=project_id,
                    approver_name=f"Dhruv ({team_manager.human_role.value})",
                    approver_role=team_manager.human_role,
                    participant_type=ParticipantType.HUMAN
                )
                st.success("PRD approved! Stage set to DEVELOPMENT.")
                st.rerun()
        else:
            st.info(f"Approved by: {meta.get('approved_by', 'Peter (CEO)')}")

    with r_col:
        with st.popover("❌ Reject PRD with Feedback"):
            fb = st.text_input("Reason / Revision Request:", value="Please add more edge cases.")
            if st.button("Submit Rejection"):
                prd_manager.reject_prd(
                    project_id=project_id,
                    feedback=fb,
                    rejector_name=f"Dhruv ({team_manager.human_role.value})",
                    rejector_role=team_manager.human_role,
                    participant_type=ParticipantType.HUMAN
                )
                st.warning("PRD rejected. Feedback posted to team timeline.")
                st.rerun()

    st.markdown("---")
    st.markdown("### Document Content (Markdown)")
    st.markdown(latest["content"])

    st.download_button(
        label="📥 Download PRD (.md)",
        data=latest["content"],
        file_name=f"PRD_v{latest['version']}.md",
        mime="text/markdown"
    )

    if len(prds) > 1:
        st.markdown("---")
        st.markdown("### Version History")
        for p in prds[1:]:
            with st.expander(f"Version {p['version']} - Created {p['created_at']}"):
                st.markdown(p["content"])
