"""
Shared Event Timeline broker for ChatCollab Lab.
Implements the central event-driven communication bus inspired by ChatCollab.
All participants (Human Client, AI CEO, AI PM, AI Dev, AI QA) publish and consume
events through this timeline.
"""
from typing import List, Optional, Dict, Any
import time
from ..core.models import (
    TimelineEvent, RoleType, ParticipantType, EventType,
    WorkflowStage
)
from ..core.database import Database


class Timeline:
    def __init__(self, db: Database):
        self.db = db

    def publish_event(
        self,
        project_id: str,
        actor_id: str,
        actor_name: str,
        actor_role: RoleType,
        participant_type: ParticipantType,
        event_type: EventType,
        message: str,
        payload: Optional[Dict[str, Any]] = None,
        artifact_id: Optional[str] = None,
        parent_event_id: Optional[str] = None,
        stage: WorkflowStage = WorkflowStage.REQUIREMENTS,
        timestamp: Optional[float] = None
    ) -> TimelineEvent:
        """Publish a new event to the shared event timeline."""
        event = TimelineEvent(
            project_id=project_id,
            timestamp=timestamp or time.time(),
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=actor_role,
            participant_type=participant_type,
            event_type=event_type,
            message=message,
            payload=payload or {},
            artifact_id=artifact_id,
            parent_event_id=parent_event_id,
            stage=stage
        )
        self.db.add_event(event)
        return event

    def get_events(
        self,
        project_id: str,
        since_timestamp: float = 0.0,
        actor_name: Optional[str] = None,
        event_type: Optional[EventType] = None,
        stage: Optional[WorkflowStage] = None,
        limit: int = 500
    ) -> List[TimelineEvent]:
        """Query chronological events with optional filtering."""
        all_events = self.db.get_events(project_id, since_timestamp=since_timestamp, limit=limit)
        filtered = []
        for e in all_events:
            if actor_name and e.actor_name.lower() != actor_name.lower():
                continue
            if event_type and e.event_type != event_type:
                continue
            if stage and e.stage != stage:
                continue
            filtered.append(e)
        return filtered

    def get_unprocessed_events_for_agent(
        self,
        project_id: str,
        agent_name: str
    ) -> List[TimelineEvent]:
        """Fetch all events published since the agent last processed the timeline."""
        last_cursor = self.db.get_agent_cursor(project_id, agent_name)
        new_events = self.db.get_events(project_id, since_timestamp=last_cursor)
        # Filter out agent's own events from "newly incoming" triggers if desired
        return new_events

    def advance_agent_cursor(self, project_id: str, agent_name: str, timestamp: float):
        """Update agent's cursor after decision cycle."""
        self.db.set_agent_cursor(project_id, agent_name, timestamp)

    def format_recent_history_for_prompt(self, project_id: str, max_turns: int = 10) -> str:
        """Format recent timeline messages into Slack-style conversation transcript."""
        events = self.db.get_events(project_id)
        if not events:
            return "(No messages yet in the channel.)"

        # Prioritize conversational events and key milestone events
        relevant_types = {
            EventType.MESSAGE_POSTED,
            EventType.REQUIREMENTS_SUBMITTED,
            EventType.CLARIFICATION_REQUESTED,
            EventType.CLARIFICATION_ANSWERED,
            EventType.PRD_CREATED,
            EventType.PRD_APPROVED,
            EventType.PRD_REJECTED,
            EventType.CODE_GENERATED,
            EventType.QA_REVIEW_REQUESTED,
            EventType.DEFECT_REPORTED,
            EventType.CODE_REVISED,
            EventType.TEST_PASSED,
            EventType.TEST_FAILED,
            EventType.HUMAN_FEEDBACK,
            EventType.PROJECT_COMPLETED,
        }

        chat_events = [e for e in events if e.event_type in relevant_types][-max_turns:]
        formatted = []
        for e in chat_events:
            stage_tag = f"[{e.stage.value}]"
            actor_tag = f"{e.actor_name} ({e.actor_role.value})"
            # Include summary if message is long
            msg_snippet = e.message.strip()
            if len(msg_snippet) > 400:
                msg_snippet = msg_snippet[:400] + "... [truncated]"
            formatted.append(f"{stage_tag} {actor_tag} ({e.event_type.value}):\n{msg_snippet}")

        return "\n\n".join(formatted)
