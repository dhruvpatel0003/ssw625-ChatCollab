"""
Autonomous Agent Decision Engine and Scheduler for ChatCollab Lab.
Coordinates the event-driven turn cycle, runs agent decisions, enforces
preconditions and approvals, and publishes resulting timeline events.
"""
from typing import List, Dict, Any, Optional, Tuple
import time
from ..core.models import (
    TimelineEvent, RoleType, ParticipantType, EventType,
    WorkflowStage, DecisionAction, AgentDecision
)
from ..core.database import Database
from ..core.ollama_client import OllamaClient
from ..agents.roles import TeamManager, BaseAgent
from .timeline import Timeline


class DecisionEngine:
    def __init__(
        self,
        db: Database,
        timeline: Timeline,
        ollama_client: OllamaClient,
        team_manager: TeamManager
    ):
        self.db = db
        self.timeline = timeline
        self.ollama = ollama_client
        self.team = team_manager
        self.is_paused = False

    def step_agent(
        self,
        project_id: str,
        agent: BaseAgent,
        institutional_knowledge: Optional[str] = None
    ) -> Optional[TimelineEvent]:
        """
        Execute one decision step for a single AI agent.
        Returns the published event, or None if agent chose to WAIT or is disabled.
        """
        if not agent.is_enabled or self.is_paused:
            return None

        project = self.db.get_project(project_id)
        if not project:
            return None

        current_stage = WorkflowStage(project["stage"])
        unprocessed = self.timeline.get_unprocessed_events_for_agent(project_id, agent.name)
        history_text = self.timeline.format_recent_history_for_prompt(project_id, max_turns=8)

        # Artifact inspection
        prd_artifacts = self.db.list_artifacts(project_id, artifact_type="PRD")
        code_artifacts = self.db.list_artifacts(project_id, artifact_type="CODE")
        qa_artifacts = self.db.list_artifacts(project_id, artifact_type="QA_REPORT")

        prd_status = "Approved" if any(a["metadata"].get("approved") for a in prd_artifacts) else (
            "Pending Approval" if prd_artifacts else "Not Created"
        )
        code_status = f"Generated ({len(code_artifacts)} files)" if code_artifacts else "Not Generated"

        # Ask agent for structured decision
        decision: AgentDecision = agent.decide(
            client=self.ollama,
            project_name=project["name"],
            requirements_text=project["description"] or "Build Java Tic-Tac-Toe",
            current_stage=current_stage,
            timeline_history=history_text,
            prd_status=prd_status,
            code_status=code_status,
            unprocessed_events_count=len(unprocessed),
            institutional_knowledge=institutional_knowledge,
            model_override=project.get("active_model")
        )

        # Update cursor timestamp
        self.timeline.advance_agent_cursor(project_id, agent.name, time.time())

        # Execute decision action and publish corresponding event
        return self._execute_decision(project_id, agent, decision, current_stage)

    def _execute_decision(
        self,
        project_id: str,
        agent: BaseAgent,
        decision: AgentDecision,
        current_stage: WorkflowStage
    ) -> Optional[TimelineEvent]:
        """Translate structured AgentDecision into concrete event and state transition."""
        action = decision.action
        msg = decision.message.strip()

        if action == DecisionAction.WAIT:
            # Publish low-priority AGENT_WAITING event (recorded in DB for observability)
            return self.timeline.publish_event(
                project_id=project_id,
                actor_id=agent.agent_id,
                actor_name=agent.name,
                actor_role=agent.role,
                participant_type=agent.participant_type,
                event_type=EventType.AGENT_WAITING,
                message=f"[WAIT] {msg}",
                payload={"reasoning": decision.reasoning},
                stage=current_stage
            )

        elif action == DecisionAction.ASK_QUESTION:
            return self.timeline.publish_event(
                project_id=project_id,
                actor_id=agent.agent_id,
                actor_name=agent.name,
                actor_role=agent.role,
                participant_type=agent.participant_type,
                event_type=EventType.CLARIFICATION_REQUESTED,
                message=msg,
                payload={"target_recipient": decision.target_recipient, "reasoning": decision.reasoning},
                stage=current_stage
            )

        elif action == DecisionAction.SEND_MESSAGE:
            return self.timeline.publish_event(
                project_id=project_id,
                actor_id=agent.agent_id,
                actor_name=agent.name,
                actor_role=agent.role,
                participant_type=agent.participant_type,
                event_type=EventType.MESSAGE_POSTED,
                message=msg,
                payload={"target_recipient": decision.target_recipient, "reasoning": decision.reasoning},
                stage=current_stage
            )

        elif action == DecisionAction.APPROVE_ARTIFACT:
            if agent.role == RoleType.AI_CEO or agent.role == RoleType.HUMAN_CLIENT:
                # Approve PRD
                self.db.update_project_stage(project_id, WorkflowStage.DEVELOPMENT)
                # Mark latest PRD as approved
                prds = self.db.list_artifacts(project_id, artifact_type="PRD")
                if prds:
                    latest = prds[0]
                    meta = latest["metadata"]
                    meta["approved"] = True
                    self.db.save_artifact(
                        latest["artifact_id"], project_id, "PRD", latest["title"],
                        latest["content"], latest["version"], meta
                    )
                return self.timeline.publish_event(
                    project_id=project_id,
                    actor_id=agent.agent_id,
                    actor_name=agent.name,
                    actor_role=agent.role,
                    participant_type=agent.participant_type,
                    event_type=EventType.PRD_APPROVED,
                    message=msg or "Product Requirements Document is APPROVED. Developer is authorized to proceed with Java implementation.",
                    payload={"reasoning": decision.reasoning},
                    stage=WorkflowStage.DEVELOPMENT
                )
            elif agent.role == RoleType.AI_QA:
                # QA approves software
                return self.timeline.publish_event(
                    project_id=project_id,
                    actor_id=agent.agent_id,
                    actor_name=agent.name,
                    actor_role=agent.role,
                    participant_type=agent.participant_type,
                    event_type=EventType.TEST_PASSED,
                    message=msg or "All QA criteria and test cases have PASSED.",
                    payload={"reasoning": decision.reasoning},
                    stage=current_stage
                )

        elif action == DecisionAction.REJECT_ARTIFACT:
            if agent.role == RoleType.AI_CEO or agent.role == RoleType.HUMAN_CLIENT:
                self.db.update_project_stage(project_id, WorkflowStage.PRD_CREATION)
                return self.timeline.publish_event(
                    project_id=project_id,
                    actor_id=agent.agent_id,
                    actor_name=agent.name,
                    actor_role=agent.role,
                    participant_type=agent.participant_type,
                    event_type=EventType.PRD_REJECTED,
                    message=msg,
                    payload={"feedback": msg, "reasoning": decision.reasoning},
                    stage=WorkflowStage.PRD_CREATION
                )

        elif action == DecisionAction.REPORT_DEFECT:
            self.db.update_project_stage(project_id, WorkflowStage.REVISION)
            return self.timeline.publish_event(
                project_id=project_id,
                actor_id=agent.agent_id,
                actor_name=agent.name,
                actor_role=agent.role,
                participant_type=agent.participant_type,
                event_type=EventType.DEFECT_REPORTED,
                message=msg,
                payload={"defect_details": decision.artifact_payload, "reasoning": decision.reasoning},
                stage=WorkflowStage.REVISION
            )

        elif action == DecisionAction.COMPLETE_TASK:
            self.db.update_project_stage(project_id, WorkflowStage.COMPLETED)
            return self.timeline.publish_event(
                project_id=project_id,
                actor_id=agent.agent_id,
                actor_name=agent.name,
                actor_role=agent.role,
                participant_type=agent.participant_type,
                event_type=EventType.PROJECT_COMPLETED,
                message=msg or "Project successfully delivered and accepted!",
                payload={"reasoning": decision.reasoning},
                stage=WorkflowStage.COMPLETED
            )

        # Default fallback to message posted
        return self.timeline.publish_event(
            project_id=project_id,
            actor_id=agent.agent_id,
            actor_name=agent.name,
            actor_role=agent.role,
            participant_type=agent.participant_type,
            event_type=EventType.MESSAGE_POSTED,
            message=msg,
            payload={"action": action.value},
            stage=current_stage
        )

    def run_collaboration_turn(
        self,
        project_id: str,
        institutional_knowledge: Optional[str] = None
    ) -> List[TimelineEvent]:
        """
        Run one round-robin pass over eligible active agents.
        Returns all non-WAIT published events.
        """
        published = []
        for agent in self.team.get_active_agents():
            event = self.step_agent(project_id, agent, institutional_knowledge)
            if event and event.event_type != EventType.AGENT_WAITING:
                published.append(event)
        return published
