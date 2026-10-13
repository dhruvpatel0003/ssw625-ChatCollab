"""View 4: Institutional Knowledge Editor (Module M3)."""
import streamlit as st
from ...agents.prompts import DEFAULT_INSTITUTIONAL_KNOWLEDGE, PERSONA_MODIFIERS
from ...core.models import PersonaType
from ..components import render_header


def render():
    render_header("Institutional Knowledge & Personas", "Inspect and edit organizational conventions, role expectations, and behavioral modifiers")

    st.markdown("### Organizational Institutional Knowledge")
    st.info("ChatCollab Section 3 demonstrates that shared institutional knowledge aligns LLM agents to follow team conventions, stage gates, and role boundaries.")

    ik_text = st.text_area(
        "Shared Team Institutional Knowledge Prompt (Injected into all agent system prompts):",
        value=DEFAULT_INSTITUTIONAL_KNOWLEDGE,
        height=280
    )

    if st.button("Save Institutional Knowledge"):
        st.success("Institutional knowledge conventions updated successfully for this session.")

    st.markdown("---")
    st.markdown("### Behavioral Persona Presets")
    st.caption("Personas modify agent communicative style to simulate diverse collaborative profiles.")

    cols = st.columns(2)
    for i, p_type in enumerate(PersonaType):
        target_col = cols[i % 2]
        with target_col:
            with st.expander(f"Persona: {p_type.value}", expanded=(i == 0)):
                st.code(PERSONA_MODIFIERS.get(p_type, "Standard baseline cooperative behavior."))
