"""Unit tests for SQLite database layer."""
import pytest
from pathlib import Path
import tempfile
import time
from chatcollab.core.database import Database
from chatcollab.core.models import (
    TimelineEvent, RoleType, ParticipantType, EventType, WorkflowStage,
    BalesIPACategory, IPALabelRecord
)


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)
    db = Database(db_path=db_path)
    yield db
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass


def test_project_crud(temp_db):
    temp_db.create_project(
        project_id="test_p1",
        name="Test Project 1",
        description="Build TicTacToe in Java",
        persona="Baseline",
        active_model="llama3.1:latest"
    )

    proj = temp_db.get_project("test_p1")
    assert proj is not None
    assert proj["name"] == "Test Project 1"
    assert proj["stage"] == WorkflowStage.REQUIREMENTS.value

    temp_db.update_project_stage("test_p1", WorkflowStage.DEVELOPMENT)
    proj_updated = temp_db.get_project("test_p1")
    assert proj_updated["stage"] == WorkflowStage.DEVELOPMENT.value


def test_timeline_events_and_cursor(temp_db):
    temp_db.create_project("test_p2", "P2", "Desc", "Baseline", "llama3.1:latest")

    event = TimelineEvent(
        event_id="ev_1",
        project_id="test_p2",
        actor_id="agent_pm",
        actor_name="Boshen (Product Manager)",
        actor_role=RoleType.AI_PM,
        participant_type=ParticipantType.AI,
        event_type=EventType.MESSAGE_POSTED,
        message="Hello team, starting PRD drafting.",
        stage=WorkflowStage.REQUIREMENTS,
        timestamp=time.time()
    )
    temp_db.record_event(event)

    events = temp_db.get_events("test_p2")
    assert len(events) == 1
    assert events[0].actor_name == "Boshen (Product Manager)"
    assert events[0].message == "Hello team, starting PRD drafting."

    # Cursor
    temp_db.update_agent_cursor("test_p2", "agent_pm", 100.0)
    cursor_val = temp_db.get_agent_cursor("test_p2", "agent_pm")
    assert cursor_val == 100.0


def test_artifacts_crud(temp_db):
    temp_db.create_project("test_p3", "P3", "Desc", "Baseline", "llama3.1:latest")
    temp_db.save_artifact(
        artifact_id="prd_1",
        project_id="test_p3",
        artifact_type="PRD",
        title="TicTacToe PRD v1",
        content="# PRD v1",
        version=1,
        metadata={"approved": False}
    )

    arts = temp_db.list_artifacts("test_p3", "PRD")
    assert len(arts) == 1
    assert arts[0]["title"] == "TicTacToe PRD v1"
    assert arts[0]["metadata"]["approved"] is False


def test_test_runs_and_ipa_labels(temp_db):
    temp_db.create_project("test_p4", "P4", "Desc", "Baseline", "llama3.1:latest")
    temp_db.record_test_run(
        run_id="run_1",
        project_id="test_p4",
        artifact_id="code_1",
        compilation_passed=True,
        tests_passed=7,
        tests_failed=0,
        stdout="[PASS] test1\n[PASS] test2",
        stderr="",
        execution_time_ms=250.5
    )

    runs = temp_db.get_test_runs("test_p4")
    assert len(runs) == 1
    assert runs[0]["compilation_passed"] == 1
    assert runs[0]["tests_passed"] == 7

    # IPA label
    ipa_record = IPALabelRecord(
        project_id="test_p4",
        event_id="ev_test",
        message_text="I suggest we add tests.",
        actor_name="Peter",
        actor_role="AI_CEO",
        predicted_category=BalesIPACategory.GIVES_SUGGESTION,
        predicted_model="llama3.1",
        timestamp=time.time()
    )
    temp_db.save_ipa_label(ipa_record)
    labels = temp_db.get_ipa_labels("test_p4")
    assert len(labels) == 1
    assert labels[0]["predicted_category"] == BalesIPACategory.GIVES_SUGGESTION.value
