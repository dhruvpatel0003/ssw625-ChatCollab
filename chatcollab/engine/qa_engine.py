"""
QA Review Engine for ChatCollab Lab.
Reviews software implementation against the PRD acceptance criteria,
incorporates deterministic compilation/test evidence, produces structured QA reports,
and coordinates code revision cycles.
"""
from typing import Dict, Any, List, Optional
import uuid
from ..core.models import (
    QAReport, QADefect, WorkflowStage, EventType, RoleType, ParticipantType
)
from ..core.database import Database
from ..core.ollama_client import OllamaClient
from .timeline import Timeline


class QAEngine:
    def __init__(self, db: Database, timeline: Timeline, ollama: OllamaClient):
        self.db = db
        self.timeline = timeline
        self.ollama = ollama

    def review_implementation(
        self,
        project_id: str,
        artifact_id: str,
        prd_text: str,
        code_text: str,
        test_results: Dict[str, Any],
        model_name: Optional[str] = None
    ) -> QAReport:
        """
        Produce a structured QA evaluation report combining deterministic test evidence
        with LLM code analysis against PRD acceptance criteria.
        """
        compilation_passed = test_results.get("compilation_passed", False)
        tests_passed = test_results.get("tests_passed", 0)
        tests_failed = test_results.get("tests_failed", 0)
        stdout = test_results.get("stdout", "")
        stderr = test_results.get("stderr", "")

        prompt = f"""
You are Quinn, the AI QA Engineer reviewing the Java Tic-Tac-Toe implementation against the PRD.

=== PRD ACCEPTANCE CRITERIA ===
{prd_text}

=== DETERMINISTIC COMPILATION & TEST EXECUTION EVIDENCE ===
Compilation Passed: {compilation_passed}
Tests Passed: {tests_passed}
Tests Failed: {tests_failed}
Compiler/Runtime Output:
{stdout}
{stderr}

=== GENERATED SOURCE CODE (EXCERPT) ===
{code_text[:3000]}

Evaluate the implementation.
If compilation failed or tests failed, log specific defects with severity Critical or High.
If all tests passed and code meets criteria, log 0 defects and set approved to true.
Conform strictly to the QAReport schema.
"""
        qa_report = self.ollama.generate_structured(
            prompt=prompt,
            response_model=QAReport,
            system="You are an uncompromising, detail-oriented QA Engineer inspecting Java software against formal requirements.",
            model=model_name or self.ollama.default_model,
            temperature=0.2
        )

        if not qa_report:
            # Deterministic fallback based directly on real execution evidence
            all_ok = compilation_passed and tests_failed == 0 and tests_passed > 0
            defects = []
            if not compilation_passed:
                defects.append(QADefect(
                    requirement_id="NFR-1",
                    description="Java source code failed compilation with javac 17.",
                    severity="Critical",
                    evidence=stderr[:200] if stderr else "Compilation error",
                    recommended_correction="Fix syntax or type errors identified by javac."
                ))
            elif tests_failed > 0:
                defects.append(QADefect(
                    requirement_id="FR-5",
                    description=f"{tests_failed} automated unit test assertions failed.",
                    severity="High",
                    evidence=stdout[:200],
                    recommended_correction="Verify win detection algorithms and coordinate checks."
                ))

            qa_report = QAReport(
                project_id=project_id,
                artifact_id=artifact_id,
                version=1,
                summary="Deterministic QA evaluation: " + ("All checks passed." if all_ok else "Defects detected."),
                compilation_passed=compilation_passed,
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                defects=defects,
                approved=all_ok,
                raw_output=stdout
            )

        # Enforce consistency with physical test execution
        qa_report.project_id = project_id
        qa_report.artifact_id = artifact_id
        qa_report.compilation_passed = compilation_passed
        qa_report.tests_passed = tests_passed
        qa_report.tests_failed = tests_failed

        if not compilation_passed or tests_failed > 0:
            qa_report.approved = False

        # Determine version & save artifact
        existing_reports = self.db.list_artifacts(project_id, artifact_type="QA_REPORT")
        version = len(existing_reports) + 1
        qa_report.version = version

        report_md = self.render_to_markdown(qa_report)
        qa_artifact_id = f"qa_v{version}_{uuid.uuid4().hex[:6]}"

        self.db.save_artifact(
            artifact_id=qa_artifact_id,
            project_id=project_id,
            artifact_type="QA_REPORT",
            title=f"QA Evaluation Report (v{version})",
            content=report_md,
            version=version,
            metadata={
                "compilation_passed": compilation_passed,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "defect_count": len(qa_report.defects),
                "approved": qa_report.approved
            }
        )

        # Publish timeline events
        if qa_report.approved:
            self.db.update_project_stage(project_id, WorkflowStage.COMPLETED)
            self.timeline.publish_event(
                project_id=project_id,
                actor_id="agent_qa",
                actor_name="Quinn (QA Engineer)",
                actor_role=RoleType.AI_QA,
                participant_type=ParticipantType.AI,
                event_type=EventType.TEST_PASSED,
                message=f"QA Evaluation Complete (v{version}): Code compiled cleanly and all {tests_passed} test cases PASSED. Recommending project completion to CEO.",
                payload={"artifact_id": qa_artifact_id, "approved": True},
                artifact_id=qa_artifact_id,
                stage=WorkflowStage.COMPLETED
            )
        else:
            self.db.update_project_stage(project_id, WorkflowStage.REVISION)
            defect_summary = "; ".join([d.description for d in qa_report.defects])
            self.timeline.publish_event(
                project_id=project_id,
                actor_id="agent_qa",
                actor_name="Quinn (QA Engineer)",
                actor_role=RoleType.AI_QA,
                participant_type=ParticipantType.AI,
                event_type=EventType.DEFECT_REPORTED,
                message=f"QA Review (v{version}) found {len(qa_report.defects)} defect(s): {defect_summary}. Requesting Developer revision.",
                payload={"artifact_id": qa_artifact_id, "defects": [d.model_dump() for d in qa_report.defects]},
                artifact_id=qa_artifact_id,
                stage=WorkflowStage.REVISION
            )

        return qa_report

    @staticmethod
    def render_to_markdown(report: QAReport) -> str:
        status_badge = "**STATUS: APPROVED**" if report.approved else "**STATUS: REVISION REQUIRED**"
        lines = [
            f"# QA Evaluation Report (v{report.version})",
            f"{status_badge}",
            "",
            "## Summary",
            report.summary,
            "",
            "## Deterministic Verification Evidence",
            f"- **Compilation Passed**: {'Yes' if report.compilation_passed else 'No'}",
            f"- **Automated Tests Passed**: {report.tests_passed}",
            f"- **Automated Tests Failed**: {report.tests_failed}",
            "",
            "## Defect Log"
        ]
        if not report.defects:
            lines.append("No defects identified. All acceptance criteria satisfied.")
        else:
            for d in report.defects:
                lines.extend([
                    f"### Defect {d.defect_id} [{d.severity}] - Req {d.requirement_id}",
                    f"- **Description**: {d.description}",
                    f"- **Evidence**: `{d.evidence}`",
                    f"- **Recommended Correction**: {d.recommended_correction}",
                    ""
                ])
        return "\n".join(lines)
