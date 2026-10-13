"""
Experiment Lab Module for ChatCollab Lab.
Executes systematic comparisons across the 8 experimental conditions inspired by
ChatCollab (Klieger et al., 2024), collects empirical transcripts, logs metrics,
and exports results to CSV.
"""
from typing import Dict, Any, List, Optional
import uuid
import time
import json
from pathlib import Path
import pandas as pd
from ..core.models import (
    PersonaType, RoleType, ParticipantType, EventType, WorkflowStage
)
from ..core.database import Database
from ..core.ollama_client import OllamaClient
from ..engine.timeline import Timeline
from ..engine.prd_manager import PRDManager
from ..engine.code_generator import CodeGenerator
from ..engine.sandbox import JavaSandbox
from ..engine.qa_engine import QAEngine
from ..agents.roles import TeamManager, create_default_team
from .bales_ipa import BalesIPAClassifier

EXPERIMENT_CONDITIONS = [
    {
        "id": "C1_BASELINE",
        "name": "Baseline Institutional Knowledge",
        "persona": PersonaType.BASELINE,
        "description": "Standard professional cooperative defaults without behavioral bias."
    },
    {
        "id": "C2_AGREEABLE",
        "name": "Frequently Agreeable Persona",
        "persona": PersonaType.FREQUENTLY_AGREEABLE,
        "description": "Agents frequently express praise, agreement, and solidarity."
    },
    {
        "id": "C3_DISAGREEABLE",
        "name": "Frequently Disagreeable Persona",
        "persona": PersonaType.FREQUENTLY_DISAGREEABLE,
        "description": "Agents frequently challenge assumptions, point out flaws, and express skepticism."
    },
    {
        "id": "C4_SUGGESTION",
        "name": "Suggestion-Oriented Persona",
        "persona": PersonaType.SUGGESTION_ORIENTED,
        "description": "Agents proactively propose concrete tactics, recommendations, and action steps."
    },
    {
        "id": "C5_OPINION_SEEKING",
        "name": "Opinion-Seeking Persona",
        "persona": PersonaType.OPINION_SEEKING,
        "description": "Agents actively ask teammates for evaluations, viewpoints, and sentiment."
    },
    {
        "id": "C6_ORIENTATION_FOCUSED",
        "name": "Orientation-Focused Persona",
        "persona": PersonaType.ORIENTATION_FOCUSED,
        "description": "Agents focus strictly on status reporting, facts, and technical coordinates."
    },
    {
        "id": "C7_SOLIDARITY_FOCUSED",
        "name": "Solidarity-Focused Persona",
        "persona": PersonaType.BASELINE,  # with solidarity custom instruction
        "custom_instruction": "Show strong solidarity, warm mutual appreciation, and positive encouragement.",
        "description": "Agents prioritize social cohesion, team encouragement, and mutual support."
    },
    {
        "id": "C8_HUMAN_CEO",
        "name": "Human CEO Replacement Condition",
        "persona": PersonaType.HUMAN_CEO_REPLACEMENT,
        "human_replaces_ceo": True,
        "description": "Human replaces AI CEO; agents coordinate with Human for all milestone approvals."
    }
]


class ExperimentRunner:
    def __init__(self, db: Database, ollama: OllamaClient):
        self.db = db
        self.ollama = ollama

    def run_condition_trial(
        self,
        condition_info: Dict[str, Any],
        run_number: int = 1,
        task_requirements: str = "Develop a text-based Java Tic-Tac-Toe game with 3x3 board, 2 players X and O, input validation, win/draw detection, and replay.",
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute one end-to-end trial for an experimental condition.
        Logs real Ollama conversations, PRD creation, code generation, sandbox tests,
        and Bales IPA classification.
        """
        experiment_run_id = f"exp_{condition_info['id']}_run{run_number}_{uuid.uuid4().hex[:6]}"
        project_id = f"proj_exp_{experiment_run_id}"

        # Initialize project in SQLite
        self.db.create_project(
            project_id=project_id,
            name=f"Exp: {condition_info['name']} (Run #{run_number})",
            description=task_requirements,
            persona=condition_info["name"],
            active_model=model_name or self.ollama.default_model
        )

        timeline = Timeline(self.db)
        team_manager = TeamManager(create_default_team(
            persona=condition_info["persona"],
            model_name=model_name
        ))

        if condition_info.get("human_replaces_ceo"):
            team_manager.set_human_role_replacement(RoleType.AI_CEO)

        prd_mgr = PRDManager(self.db, timeline, self.ollama)
        code_gen = CodeGenerator(self.db, timeline, self.ollama)
        sandbox = JavaSandbox(self.db, timeline)
        qa_engine = QAEngine(self.db, timeline, self.ollama)
        ipa_classifier = BalesIPAClassifier(self.db, self.ollama)

        t0 = time.time()

        # Step 1: Submit requirements event
        timeline.publish_event(
            project_id=project_id,
            actor_id="human_client",
            actor_name="Human Client" if not condition_info.get("human_replaces_ceo") else "Dhruv (Human CEO)",
            actor_role=RoleType.HUMAN_CLIENT if not condition_info.get("human_replaces_ceo") else RoleType.AI_CEO,
            participant_type=ParticipantType.HUMAN,
            event_type=EventType.REQUIREMENTS_SUBMITTED,
            message=task_requirements,
            stage=WorkflowStage.REQUIREMENTS
        )

        # Step 2: PM generates PRD
        prd = prd_mgr.generate_prd(
            project_id=project_id,
            requirements_text=task_requirements,
            model_name=model_name
        )

        # Step 3: Approve PRD (CEO or Human CEO)
        approver_name = "Dhruv (Human CEO)" if condition_info.get("human_replaces_ceo") else "Peter (CEO)"
        approver_role = RoleType.AI_CEO
        p_type = ParticipantType.HUMAN if condition_info.get("human_replaces_ceo") else ParticipantType.AI

        prd_mgr.approve_prd(
            project_id=project_id,
            approver_name=approver_name,
            approver_role=approver_role,
            participant_type=p_type
        )

        # Step 4: Dev generates Java source code
        java_files = code_gen.generate_code_from_prd(
            project_id=project_id,
            prd_text=prd.raw_markdown or "Java Tic-Tac-Toe specification",
            model_name=model_name
        )

        # Step 5: Sandbox compile and test
        code_artifacts = self.db.list_artifacts(project_id, artifact_type="CODE")
        art_id = code_artifacts[0]["artifact_id"] if code_artifacts else "code_1"
        test_res = sandbox.compile_and_test(project_id, artifact_id=art_id)

        # Step 6: QA review
        code_combined = "\n\n".join(java_files.values())
        qa_rep = qa_engine.review_implementation(
            project_id=project_id,
            artifact_id=art_id,
            prd_text=prd.raw_markdown or "",
            code_text=code_combined,
            test_results=test_res,
            model_name=model_name
        )

        duration = time.time() - t0

        # Step 7: Classify transcript with Bales IPA
        ipa_records = ipa_classifier.classify_project_timeline(project_id, model_name=model_name)

        events = self.db.get_events(project_id)
        chat_events = [e for e in events if e.event_type != EventType.AGENT_WAITING]

        # Aggregate metrics
        ipa_distribution = {}
        for r in ipa_records:
            cat = r.predicted_category.value if hasattr(r.predicted_category, 'value') else str(r.predicted_category)
            ipa_distribution[cat] = ipa_distribution.get(cat, 0) + 1

        run_record = {
            "id": experiment_run_id,
            "experiment_id": condition_info["id"],
            "condition_name": condition_info["name"],
            "run_number": run_number,
            "model_name": model_name or self.ollama.default_model,
            "task_spec": task_requirements,
            "status": "COMPLETED",
            "duration_seconds": round(duration, 2),
            "message_count": len(chat_events),
            "agreement_score": 0.0,
            "compilation_success": test_res.get("compilation_passed", False),
            "results_json": {
                "tests_passed": test_res.get("tests_passed", 0),
                "tests_failed": test_res.get("tests_failed", 0),
                "qa_approved": qa_rep.approved,
                "ipa_distribution": ipa_distribution
            }
        }

        self.db.save_experiment_run(run_record)
        return run_record

    def export_runs_to_csv(self, output_path: Path) -> Path:
        """Export all recorded experiment trials to CSV."""
        runs = self.db.list_experiment_runs()
        rows = []
        for r in runs:
            res_json = json.loads(r["results_json"] or "{}")
            rows.append({
                "Run ID": r["id"],
                "Condition ID": r["experiment_id"],
                "Condition Name": r["condition_name"],
                "Run Number": r["run_number"],
                "Model": r["model_name"],
                "Status": r["status"],
                "Duration (s)": r["duration_seconds"],
                "Message Count": r["message_count"],
                "Compilation Success": bool(r["compilation_success"]),
                "Tests Passed": res_json.get("tests_passed", 0),
                "Tests Failed": res_json.get("tests_failed", 0),
                "QA Approved": res_json.get("qa_approved", False),
                "Created At": r["created_at"]
            })
        df = pd.DataFrame(rows)
        df.to_csv(str(output_path), index=False)
        return output_path
