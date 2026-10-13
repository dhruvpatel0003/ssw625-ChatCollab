"""
Role Factory and Human Role Replacement configuration.
Handles agent creation, role configurations, and permissions.
"""
from typing import Dict, List, Optional
from ..core.models import RoleType, ParticipantType, PersonaType
from .base_agent import BaseAgent


def create_default_team(persona: PersonaType = PersonaType.BASELINE, model_name: Optional[str] = None) -> List[BaseAgent]:
    """Create the canonical 4-agent team (CEO, PM, Dev, QA) with the specified persona."""
    return [
        BaseAgent(
            agent_id="agent_ceo",
            name="Peter (CEO)",
            role=RoleType.AI_CEO,
            participant_type=ParticipantType.AI,
            persona=persona,
            model_name=model_name
        ),
        BaseAgent(
            agent_id="agent_pm",
            name="Boshen (Product Manager)",
            role=RoleType.AI_PM,
            participant_type=ParticipantType.AI,
            persona=persona,
            model_name=model_name
        ),
        BaseAgent(
            agent_id="agent_dev",
            name="David (Developer)",
            role=RoleType.AI_DEV,
            participant_type=ParticipantType.AI,
            persona=persona,
            model_name=model_name
        ),
        BaseAgent(
            agent_id="agent_qa",
            name="Quinn (QA Engineer)",
            role=RoleType.AI_QA,
            participant_type=ParticipantType.AI,
            persona=persona,
            model_name=model_name
        ),
    ]


class TeamManager:
    """Manages active participants, human role replacements, and execution permissions."""
    def __init__(self, agents: Optional[List[BaseAgent]] = None):
        self.agents: Dict[str, BaseAgent] = {}
        # Human participant
        self.human_name: str = "Dhruv (Human Client)"
        self.human_role: RoleType = RoleType.HUMAN_CLIENT
        self.replaced_role: Optional[RoleType] = None

        if agents:
            for a in agents:
                self.agents[a.agent_id] = a
        else:
            for a in create_default_team():
                self.agents[a.agent_id] = a

    def get_agent_by_role(self, role: RoleType) -> Optional[BaseAgent]:
        for a in self.agents.values():
            if a.role == role and a.is_enabled:
                return a
        return None

    def get_active_agents(self) -> List[BaseAgent]:
        return [a for a in self.agents.values() if a.is_enabled]

    def set_human_role_replacement(self, role_to_replace: Optional[RoleType]):
        """
        When human replaces an AI role (e.g. AI CEO or AI PM), disable that AI agent
        and delegate its authority to the Human user.
        """
        self.replaced_role = role_to_replace
        if role_to_replace is None:
            # Revert to standard Human Client
            self.human_role = RoleType.HUMAN_CLIENT
            # Re-enable all default agents
            for a in self.agents.values():
                a.is_enabled = True
        else:
            self.human_role = role_to_replace
            # Disable the replaced AI agent
            for a in self.agents.values():
                if a.role == role_to_replace:
                    a.is_enabled = False
                else:
                    a.is_enabled = True

    def is_human_turn_required(self, current_stage: str, prd_needs_approval: bool) -> bool:
        """Check if workflow is currently waiting for human input/approval."""
        if self.human_role == RoleType.AI_CEO and prd_needs_approval:
            return True
        return False
