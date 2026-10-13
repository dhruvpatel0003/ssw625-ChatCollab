"""
Base Agent class for ChatCollab Lab.
Encapsulates role identity, institutional knowledge, context assembling,
Ollama structured inference, loop prevention, and WAIT decision handling.
"""
from typing import Optional, Dict, Any, List
import time
from ..core.models import (
    RoleType, ParticipantType, PersonaType, WorkflowStage,
    AgentDecision, DecisionAction, TimelineEvent
)
from ..core.ollama_client import OllamaClient
from .prompts import (
    ROLE_SYSTEM_PROMPTS, PERSONA_MODIFIERS, DEFAULT_INSTITUTIONAL_KNOWLEDGE
)


class BaseAgent:
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: RoleType,
        participant_type: ParticipantType = ParticipantType.AI,
        persona: PersonaType = PersonaType.BASELINE,
        custom_instructions: str = "",
        model_name: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.participant_type = participant_type
        self.persona = persona
        self.custom_instructions = custom_instructions
        self.model_name = model_name
        self.is_enabled = True

        # Loop and repetition guard tracking
        self.last_action: Optional[DecisionAction] = None
        self.consecutive_identical_actions = 0
        self.total_decisions_made = 0

    def assemble_system_prompt(self, institutional_knowledge: Optional[str] = None) -> str:
        """Combine role prompt, persona traits, and institutional knowledge."""
        base_role_prompt = ROLE_SYSTEM_PROMPTS.get(self.role, "")
        persona_prompt = PERSONA_MODIFIERS.get(self.persona, "")
        ik_prompt = institutional_knowledge or DEFAULT_INSTITUTIONAL_KNOWLEDGE

        parts = [
            f"You are '{self.name}', acting as '{self.role.value}'.",
            base_role_prompt.strip(),
            persona_prompt.strip(),
            ik_prompt.strip()
        ]
        if self.custom_instructions:
            parts.append(f"ADDITIONAL GUIDELINES:\n{self.custom_instructions.strip()}")

        return "\n\n".join(parts)

    def assemble_context_prompt(
        self,
        project_name: str,
        requirements_text: str,
        current_stage: WorkflowStage,
        timeline_history: str,
        prd_status: str,
        code_status: str,
        unprocessed_events_count: int
    ) -> str:
        """Create prompt describing the current environment state and decisions available."""
        prompt = f"""
=== CURRENT ENVIRONMENT STATE ===
Project: {project_name}
Current Workflow Stage: {current_stage.value}
PRD Status: {prd_status}
Code Status: {code_status}
Unprocessed New Events: {unprocessed_events_count}

=== ORIGINAL REQUIREMENTS ===
{requirements_text}

=== RECENT SHARED TIMELINE (SLACK-LIKE TRANSCRIPT) ===
{timeline_history}

=== YOUR TASK & AVAILABLE ACTIONS ===
As {self.name} ({self.role.value}), evaluate the recent timeline and project state.
Choose ONE action from:
- SEND_MESSAGE: Post an update, observation, agreement, or guidance to the team.
- ASK_QUESTION: Ask a targeted question to a teammate or client.
- CREATE_ARTIFACT: Create a PRD or code document (only if you are PM or Dev at the appropriate stage).
- REQUEST_APPROVAL: Request review/approval for an artifact.
- APPROVE_ARTIFACT: Approve a PRD (CEO only) or test/QA deliverable (QA only).
- REJECT_ARTIFACT: Reject PRD with feedback (CEO only) or reject code (QA only).
- REPORT_DEFECT: Log a specific defect or missing acceptance criterion (QA only).
- REVISE_ARTIFACT: Submit updated PRD (PM) or updated Java code (Dev).
- WAIT: If it is not your turn, or prerequisites are missing, or another agent is currently responding, CHOOSE WAIT.
- COMPLETE_TASK: CEO only, when QA has verified all criteria and game is complete.

Provide your decision as valid JSON conforming to the AgentDecision schema.
"""
        return prompt

    def decide(
        self,
        client: OllamaClient,
        project_name: str,
        requirements_text: str,
        current_stage: WorkflowStage,
        timeline_history: str,
        prd_status: str,
        code_status: str,
        unprocessed_events_count: int,
        institutional_knowledge: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> AgentDecision:
        """Obtain a structured decision from the local Ollama model with safeguards."""
        system_prompt = self.assemble_system_prompt(institutional_knowledge)
        user_prompt = self.assemble_context_prompt(
            project_name=project_name,
            requirements_text=requirements_text,
            current_stage=current_stage,
            timeline_history=timeline_history,
            prd_status=prd_status,
            code_status=code_status,
            unprocessed_events_count=unprocessed_events_count
        )

        selected_model = model_override or self.model_name or client.default_model

        decision = client.generate_structured(
            prompt=user_prompt,
            response_model=AgentDecision,
            system=system_prompt,
            model=selected_model,
            temperature=0.2,
            max_retries=2
        )

        if not decision:
            # Fallback to safe WAIT if LLM fails
            decision = AgentDecision(
                action=DecisionAction.WAIT,
                message=f"{self.name} is waiting for clear next events.",
                reasoning="Fallback decision due to empty or unparseable model response."
            )

        # Loop and repetition guard
        if decision.action == self.last_action and decision.action != DecisionAction.WAIT:
            self.consecutive_identical_actions += 1
            if self.consecutive_identical_actions >= 3:
                # Force WAIT to break infinite loop
                decision = AgentDecision(
                    action=DecisionAction.WAIT,
                    message=f"{self.name} is waiting to avoid repetitive actions.",
                    reasoning="Repetition guard triggered: 3 identical actions detected."
                )
        else:
            self.consecutive_identical_actions = 1

        self.last_action = decision.action
        self.total_decisions_made += 1
        return decision
