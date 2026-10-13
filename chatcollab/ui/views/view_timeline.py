"""View 8: Shared Event Timeline (Module M4)."""
import streamlit as st
import pandas as pd
from ...core.database import Database
from ...core.models import EventType, RoleType, WorkflowStage
from ..components import render_header, render_event_timeline


def render(db: Database, project_id: str):
    render_header("Shared Event Timeline", "Filter, inspect, and analyze all events in the event-driven communication bus")

    events = db.get_events(project_id)
    if not events:
        st.info("No events recorded for this project yet.")
        return

    # Filter Toolbar
    c1, c2, c3 = st.columns(3)
    with c1:
        roles = ["All"] + list(set([e.actor_role.value if hasattr(e.actor_role, 'value') else str(e.actor_role) for e in events]))
        sel_role = st.selectbox("Filter by Role:", roles)
    with c2:
        event_types = ["All"] + list(set([e.event_type.value if hasattr(e.event_type, 'value') else str(e.event_type) for e in events]))
        sel_type = st.selectbox("Filter by Event Type:", event_types)
    with c3:
        search_query = st.text_input("Search Message Text:", "")

    filtered = events
    if sel_role != "All":
        filtered = [e for e in filtered if (e.actor_role.value if hasattr(e.actor_role, 'value') else str(e.actor_role)) == sel_role]
    if sel_type != "All":
        filtered = [e for e in filtered if (e.event_type.value if hasattr(e.event_type, 'value') else str(e.event_type)) == sel_type]
    if search_query.strip():
        filtered = [e for e in filtered if search_query.lower() in e.message.lower()]

    st.write(f"Showing **{len(filtered)}** of **{len(events)}** events.")

    view_mode = st.radio("View Format:", ["Chat Bubbles", "Tabular Data Grid"], horizontal=True)
    if view_mode == "Chat Bubbles":
        render_event_timeline(filtered, max_events=100)
    else:
        rows = []
        for e in filtered:
            rows.append({
                "Timestamp": e.timestamp,
                "Actor": e.actor_name,
                "Role": e.actor_role.value if hasattr(e.actor_role, 'value') else str(e.actor_role),
                "Type": e.event_type.value if hasattr(e.event_type, 'value') else str(e.event_type),
                "Stage": e.stage.value if hasattr(e.stage, 'value') else str(e.stage),
                "Message": e.message
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
