"""
Reusable UI Components for Streamlit in ChatCollab Lab.
"""
import streamlit as st
import datetime
from typing import Optional, Dict, Any, List
from ..core.models import (
    TimelineEvent, RoleType, EventType, WorkflowStage
)
from .styles import get_role_color


def render_header(title: str, subtitle: Optional[str] = None):
    """Render consistent research-grade top header."""
    st.markdown("""
    <div>
        <span class="paper-badge">ChatCollab (Stanford 2024)</span>
        <span class="prototype-tag">Research Prototype & Laboratory</span>
    </div>
    """, unsafe_allow_html=True)
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.markdown("---")


def render_kpi(col, title: str, value: Any, subtitle: str = ""):
    """Render high-contrast metric card in a column."""
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div style="font-size:0.75rem; color:#747d8c; margin-top:2px;">{subtitle}</div>
        </div>
        """, unsafe_allow_html=True)


def render_event_timeline(events: List[TimelineEvent], max_events: int = 100):
    """Render Slack-style chronological event transcript with role styling."""
    if not events:
        st.info("No events in this project timeline yet.")
        return

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for event in events[-max_events:]:
        role_val = event.actor_role.value if hasattr(event.actor_role, 'value') else str(event.actor_role)
        bubble_cls = "chat-system"
        role_cls = "role-system"

        if "ceo" in role_val.lower():
            bubble_cls = "chat-ceo"
            role_cls = "role-ceo"
        elif "product" in role_val.lower() or "pm" in role_val.lower():
            bubble_cls = "chat-pm"
            role_cls = "role-pm"
        elif "dev" in role_val.lower():
            bubble_cls = "chat-dev"
            role_cls = "role-dev"
        elif "qa" in role_val.lower():
            bubble_cls = "chat-qa"
            role_cls = "role-qa"
        elif "human" in role_val.lower():
            bubble_cls = "chat-human"
            role_cls = "role-human"

        time_str = datetime.datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")

        st.markdown(f"""
        <div class="chat-bubble {bubble_cls}">
            <div class="actor-header">
                <span>{event.actor_name}</span>
                <span class="role-badge {role_cls}">{role_val}</span>
                <span class="timestamp-text">{time_str}</span>
                <span class="event-type-tag">{event.event_type.value}</span>
            </div>
            <div style="font-size: 0.95rem; white-space: pre-wrap;">{event.message}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
