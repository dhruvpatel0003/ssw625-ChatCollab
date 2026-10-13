"""Unit tests for Timeline and Agent roles/decision logic."""
import pytest
import tempfile
from pathlib import Path
from chatcollab.core.database import Database
from chatcollab.core.models import (
    RoleType, ParticipantType, PersonaType, WorkflowStage,
    DecisionAction, AgentDecision, EventType
)
from chatcollab.engine.timeline import Timeline
from chatcollab.agents.roles import TeamManager, create_default_team
from chatcollab.agents.base_agent import BaseAgent


@pytest.fixture
def temp_timeline():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)
    db = Database(db_path=db_path)
    tl = Timeline(db)
    yield db, tl
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass


def test_team_manager_roles_and_replacement():
    team = TeamManager(create_default_team())
    assert len(team.get_active_agents()) == 4

    ceo_agent = team.get_agent_by_role(RoleType.AI_CEO)
    assert ceo_agent is not None
    assert ceo_agent.is_enabled is True

    # Test Human replacing CEO
    team.set_human_role_replacement(RoleType.AI_CEO)
    assert team.human_role == RoleType.AI_CEO
    assert ceo_agent.is_enabled is False
    assert len(team.get_active_agents()) == 3

    # Revert
    team.set_human_role_replacement(None)
    assert team.human_role == RoleType.HUMAN_CLIENT
    assert ceo_agent.is_enabled is True
    assert len(team.get_active_agents()) == 4


def test_timeline_event_publishing_and_unprocessed(temp_timeline):
    db, tl = temp_timeline
    db.create_project("p_tl", "Timeline Proj", "Desc", "Baseline", "llama3.1")

    ev1 = tl.publish_event(
        project_id="p_tl",
        actor_id="human",
        actor_name="Dhruv",
        actor_role=RoleType.HUMAN_CLIENT,
        participant_type=ParticipantType.HUMAN,
        event_type=EventType.REQUIREMENTS_SUBMITTED,
        message="Please build TicTacToe",
        stage=WorkflowStage.REQUIREMENTS
    )
    assert ev1 is not None

    unprocessed = tl.get_unprocessed_events_for_agent("p_tl", "Peter (CEO)")
    assert len(unprocessed) == 1

    tl.advance_agent_cursor("p_tl", "Peter (CEO)", ev1.timestamp + 1.0)
    unprocessed_after = tl.get_unprocessed_events_for_agent("p_tl", "Peter (CEO)")
    assert len(unprocessed_after) == 0


def test_agent_loop_prevention():
    agent = BaseAgent(
        agent_id="test_agent",
        name="Test Dev",
        role=RoleType.AI_DEV,
        persona=PersonaType.BASELINE
    )

    # Simulate fake ollama client returning identical action repeatedly
    class MockOllama:
        default_model = "llama3.1"
        def generate_structured(self, **kwargs):
            return AgentDecision(
                action=DecisionAction.SEND_MESSAGE,
                message="Repetitive message",
                reasoning="Testing loop"
            )

    mock_client = MockOllama()

    # Step 1
    d1 = agent.decide(mock_client, "P", "Req", WorkflowStage.DEVELOPMENT, "Hist", "App", "Gen", 0)
    assert d1.action == DecisionAction.SEND_MESSAGE

    # Step 2
    d2 = agent.decide(mock_client, "P", "Req", WorkflowStage.DEVELOPMENT, "Hist", "App", "Gen", 0)
    assert d2.action == DecisionAction.SEND_MESSAGE

    # Step 3 -> Loop guard triggers WAIT
    d3 = agent.decide(mock_client, "P", "Req", WorkflowStage.DEVELOPMENT, "Hist", "App", "Gen", 0)
    assert d3.action == DecisionAction.WAIT
    assert "Repetition guard triggered" in d3.reasoning
