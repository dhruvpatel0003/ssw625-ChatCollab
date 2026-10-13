"""View 2: Team Configuration and Human Role Replacement (Module M2)."""
import streamlit as st
from ...core.models import RoleType, PersonaType
from ...agents.roles import TeamManager
from ..components import render_header


def render(team_manager: TeamManager):
    render_header("Team Configuration & Roles", "Inspect agent personas, configure models, and assign human role replacements")

    st.markdown("### Human Participant Role Assignment")
    st.info("The ChatCollab paper explores replacing AI roles with human participants to analyze mixed-initiative collaboration dynamics.")

    current_rep = team_manager.replaced_role.value if team_manager.replaced_role else "None (Human is Client)"
    role_options = ["None (Human is Client)", RoleType.AI_CEO.value, RoleType.AI_PM.value, RoleType.AI_DEV.value]

    sel_role = st.selectbox(
        "Select Role for Human Participant to Replace:",
        options=role_options,
        index=role_options.index(current_rep) if current_rep in role_options else 0
    )

    if st.button("Apply Role Assignment"):
        if sel_role == "None (Human is Client)":
            team_manager.set_human_role_replacement(None)
            st.success("Human set as Product Sponsor / Client. All AI agents active.")
        else:
            rt = RoleType(sel_role)
            team_manager.set_human_role_replacement(rt)
            st.success(f"Human now replaces {sel_role}! The corresponding AI agent has been deactivated.")
        st.rerun()

    st.markdown("---")
    st.markdown("### Active Agents & Personas")

    for agent_id, agent in team_manager.agents.items():
        with st.expander(f"{agent.name} — {'ENABLED' if agent.is_enabled else 'DEACTIVATED (Replaced by Human)'}", expanded=agent.is_enabled):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write(f"**Role**: `{agent.role.value}`")
                st.write(f"**Participant**: `{agent.participant_type.value}`")
                st.write(f"**Active Persona**: `{agent.persona.value}`")
                st.write(f"**Model**: `{agent.model_name or 'Default Project Model'}`")
                st.write(f"**Decisions Made**: `{agent.total_decisions_made}`")
            with c2:
                st.markdown("**Role System Prompt:**")
                st.text_area(f"Prompt for {agent.name}", agent.assemble_system_prompt(), height=160, disabled=True, key=f"prompt_{agent_id}")
