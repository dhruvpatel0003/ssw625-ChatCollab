"""
SQLite Database Layer for ChatCollab Lab.
Manages persistent storage for projects, agents, timeline events, artifacts,
sandbox test runs, Bales IPA classifications, and experimental conditions.
"""
import sqlite3
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from .config import DB_PATH
from .models import (
    TimelineEvent, RoleType, ParticipantType, EventType,
    WorkflowStage, BalesIPACategory, IPALabelRecord
)


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                stage TEXT NOT NULL DEFAULT 'REQUIREMENTS',
                persona TEXT NOT NULL DEFAULT 'Baseline Institutional Knowledge',
                active_model TEXT NOT NULL DEFAULT 'llama3.1:latest',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                participant_type TEXT NOT NULL,
                prompt_template TEXT,
                persona_traits TEXT,
                is_enabled INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                actor_id TEXT NOT NULL,
                actor_name TEXT NOT NULL,
                actor_role TEXT NOT NULL,
                participant_type TEXT NOT NULL,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                payload TEXT,
                artifact_id TEXT,
                parent_event_id TEXT,
                stage TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_events_project_time ON events(project_id, timestamp);
            CREATE INDEX IF NOT EXISTS idx_events_actor ON events(project_id, actor_name);
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(project_id, event_type);

            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                artifact_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS test_runs (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                artifact_id TEXT,
                compilation_passed INTEGER NOT NULL,
                tests_passed INTEGER NOT NULL,
                tests_failed INTEGER NOT NULL,
                stdout TEXT,
                stderr TEXT,
                execution_time_ms REAL NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ipa_classifications (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                message_text TEXT NOT NULL,
                actor_name TEXT NOT NULL,
                actor_role TEXT NOT NULL,
                predicted_category TEXT NOT NULL,
                predicted_model TEXT NOT NULL,
                prompt_version TEXT NOT NULL DEFAULT 'v1',
                timestamp REAL NOT NULL,
                human_category TEXT,
                human_coder TEXT,
                is_verified INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_ipa_project ON ipa_classifications(project_id);

            CREATE TABLE IF NOT EXISTS experiment_runs (
                id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                condition_name TEXT NOT NULL,
                run_number INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                task_spec TEXT,
                status TEXT NOT NULL,
                duration_seconds REAL,
                message_count INTEGER,
                agreement_score REAL,
                compilation_success INTEGER,
                results_json TEXT,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_cursors (
                project_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                last_processed_timestamp REAL NOT NULL DEFAULT 0.0,
                PRIMARY KEY (project_id, agent_name)
            );
            """)
            conn.commit()

    # --- Project Management ---
    def create_project(self, project_id: str, name: str, description: str = "",
                       persona: str = "Baseline Institutional Knowledge",
                       active_model: str = "llama3.1:latest") -> str:
        now = time.time()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO projects (id, name, description, stage, persona, active_model, created_at, updated_at)
            VALUES (?, ?, ?, 'REQUIREMENTS', ?, ?, ?, ?)
            """, (project_id, name, description, persona, active_model, now, now))
            conn.commit()
        return project_id

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_projects(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
            return [dict(r) for r in cursor.fetchall()]

    def update_project_stage(self, project_id: str, stage: WorkflowStage):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE projects SET stage = ?, updated_at = ? WHERE id = ?
            """, (stage.value if hasattr(stage, 'value') else stage, time.time(), project_id))
            conn.commit()

    def update_project_model(self, project_id: str, model_name: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE projects SET active_model = ?, updated_at = ? WHERE id = ?
            """, (model_name, time.time(), project_id))
            conn.commit()

    # --- Events ---
    def add_event(self, event: TimelineEvent):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO events (
                event_id, project_id, timestamp, actor_id, actor_name, actor_role,
                participant_type, event_type, message, payload, artifact_id, parent_event_id, stage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.project_id,
                event.timestamp,
                event.actor_id,
                event.actor_name,
                event.actor_role.value if hasattr(event.actor_role, 'value') else str(event.actor_role),
                event.participant_type.value if hasattr(event.participant_type, 'value') else str(event.participant_type),
                event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
                event.message,
                json.dumps(event.payload),
                event.artifact_id,
                event.parent_event_id,
                event.stage.value if hasattr(event.stage, 'value') else str(event.stage)
            ))
            # Also touch updated_at on project
            cursor.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (event.timestamp, event.project_id))
            conn.commit()

    def record_event(self, event: TimelineEvent):
        """Alias for add_event."""
        return self.add_event(event)

    def get_events(self, project_id: str, since_timestamp: float = 0.0,
                   limit: int = 500) -> List[TimelineEvent]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM events
            WHERE project_id = ? AND timestamp > ?
            ORDER BY timestamp ASC LIMIT ?
            """, (project_id, since_timestamp, limit))
            rows = cursor.fetchall()

            events = []
            for r in rows:
                events.append(TimelineEvent(
                    event_id=r["event_id"],
                    project_id=r["project_id"],
                    timestamp=r["timestamp"],
                    actor_id=r["actor_id"],
                    actor_name=r["actor_name"],
                    actor_role=RoleType(r["actor_role"]),
                    participant_type=ParticipantType(r["participant_type"]),
                    event_type=EventType(r["event_type"]),
                    message=r["message"],
                    payload=json.loads(r["payload"] or "{}"),
                    artifact_id=r["artifact_id"],
                    parent_event_id=r["parent_event_id"],
                    stage=WorkflowStage(r["stage"])
                ))
            return events

    # --- Agent Cursors ---
    def get_agent_cursor(self, project_id: str, agent_name: str) -> float:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT last_processed_timestamp FROM agent_cursors
            WHERE project_id = ? AND agent_name = ?
            """, (project_id, agent_name))
            row = cursor.fetchone()
            return row["last_processed_timestamp"] if row else 0.0

    def set_agent_cursor(self, project_id: str, agent_name: str, timestamp: float):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO agent_cursors (project_id, agent_name, last_processed_timestamp)
            VALUES (?, ?, ?)
            """, (project_id, agent_name, timestamp))
            conn.commit()

    def update_agent_cursor(self, project_id: str, agent_name: str, timestamp: float):
        """Alias for set_agent_cursor."""
        return self.set_agent_cursor(project_id, agent_name, timestamp)

    # --- Artifacts ---
    def save_artifact(self, artifact_id: str, project_id: str, artifact_type: str,
                      title: str, content: str, version: int = 1,
                      metadata: Optional[Dict[str, Any]] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO artifacts (
                artifact_id, project_id, version, artifact_type, title, content, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                artifact_id, project_id, version, artifact_type, title, content,
                json.dumps(metadata or {}), time.time()
            ))
            conn.commit()

    def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "artifact_id": r["artifact_id"],
                "project_id": r["project_id"],
                "version": r["version"],
                "artifact_type": r["artifact_type"],
                "title": r["title"],
                "content": r["content"],
                "metadata": json.loads(r["metadata"] or "{}"),
                "created_at": r["created_at"]
            }

    def list_artifacts(self, project_id: str, artifact_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if artifact_type:
                cursor.execute("""
                SELECT * FROM artifacts WHERE project_id = ? AND artifact_type = ? ORDER BY version DESC
                """, (project_id, artifact_type))
            else:
                cursor.execute("""
                SELECT * FROM artifacts WHERE project_id = ? ORDER BY created_at DESC
                """, (project_id,))
            rows = cursor.fetchall()
            return [
                {
                    "artifact_id": r["artifact_id"],
                    "project_id": r["project_id"],
                    "version": r["version"],
                    "artifact_type": r["artifact_type"],
                    "title": r["title"],
                    "content": r["content"],
                    "metadata": json.loads(r["metadata"] or "{}"),
                    "created_at": r["created_at"]
                }
                for r in rows
            ]

    # --- Test Runs ---
    def record_test_run(self, run_id: str, project_id: str, artifact_id: Optional[str],
                        compilation_passed: bool, tests_passed: int, tests_failed: int,
                        stdout: str, stderr: str, execution_time_ms: float):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO test_runs (
                id, project_id, artifact_id, compilation_passed, tests_passed, tests_failed,
                stdout, stderr, execution_time_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id, project_id, artifact_id, 1 if compilation_passed else 0,
                tests_passed, tests_failed, stdout, stderr, execution_time_ms, time.time()
            ))
            conn.commit()

    def get_test_runs(self, project_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test_runs WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
            return [dict(r) for r in cursor.fetchall()]

    # --- Bales IPA Classifications ---
    def save_ipa_label(self, label: IPALabelRecord):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO ipa_classifications (
                id, project_id, event_id, message_text, actor_name, actor_role,
                predicted_category, predicted_model, prompt_version, timestamp,
                human_category, human_coder, is_verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                label.id, label.project_id, label.event_id, label.message_text,
                label.actor_name, label.actor_role,
                label.predicted_category.value if hasattr(label.predicted_category, 'value') else label.predicted_category,
                label.predicted_model, label.prompt_version, label.timestamp,
                label.human_category.value if label.human_category and hasattr(label.human_category, 'value') else (label.human_category or None),
                label.human_coder, 1 if label.is_verified else 0
            ))
            conn.commit()

    def update_human_ipa_label(self, record_id: str, human_category: BalesIPACategory, coder_name: str = "Human Reviewer"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE ipa_classifications
            SET human_category = ?, human_coder = ?, is_verified = 1
            WHERE id = ?
            """, (human_category.value if hasattr(human_category, 'value') else human_category, coder_name, record_id))
            conn.commit()

    def update_ipa_human_label(self, record_id: str, human_category: BalesIPACategory, coder_name: str = "Human Reviewer"):
        """Alias for update_human_ipa_label."""
        return self.update_human_ipa_label(record_id, human_category, coder_name)

    def get_ipa_labels(self, project_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ipa_classifications WHERE project_id = ? ORDER BY timestamp ASC", (project_id,))
            return [dict(r) for r in cursor.fetchall()]

    # --- Experiments ---
    def save_experiment_run(self, run_dict: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO experiment_runs (
                id, experiment_id, condition_name, run_number, model_name, task_spec,
                status, duration_seconds, message_count, agreement_score, compilation_success,
                results_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_dict["id"], run_dict["experiment_id"], run_dict["condition_name"],
                run_dict["run_number"], run_dict["model_name"], run_dict.get("task_spec", ""),
                run_dict["status"], run_dict.get("duration_seconds", 0.0),
                run_dict.get("message_count", 0), run_dict.get("agreement_score", 0.0),
                1 if run_dict.get("compilation_success") else 0,
                json.dumps(run_dict.get("results_json", {})), time.time()
            ))
            conn.commit()

    def list_experiment_runs(self, experiment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if experiment_id:
                cursor.execute("SELECT * FROM experiment_runs WHERE experiment_id = ? ORDER BY created_at DESC", (experiment_id,))
            else:
                cursor.execute("SELECT * FROM experiment_runs ORDER BY created_at DESC")
            return [dict(r) for r in cursor.fetchall()]
