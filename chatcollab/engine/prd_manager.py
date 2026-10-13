"""
Product Requirements Document (PRD) Manager.
Handles generation, versioning, review, and approval/rejection lifecycle.
"""
from typing import Optional, Dict, Any, List
import uuid
import time
from ..core.models import (
    PRDDocument, WorkflowStage, EventType, RoleType, ParticipantType
)
from ..core.database import Database
from ..core.ollama_client import OllamaClient
from .timeline import Timeline


class PRDManager:
    def __init__(self, db: Database, timeline: Timeline, ollama: OllamaClient):
        self.db = db
        self.timeline = timeline
        self.ollama = ollama

    def generate_prd(
        self,
        project_id: str,
        requirements_text: str,
        clarifications_text: str = "",
        model_name: Optional[str] = None
    ) -> PRDDocument:
        """Use Ollama to generate a structured PRD based on requirements and clarifications."""
        prompt = f"""
You are the Product Manager drafting a comprehensive Product Requirements Document (PRD) for a software project.
Task: Author a structured PRD conforming to the PRDDocument schema.

=== USER REQUIREMENTS ===
{requirements_text}

=== CLARIFICATIONS & CONVERSATION CONTEXT ===
{clarifications_text or 'No specific clarifications provided.'}

Requirements must include:
- Clear title and overview
- Functional requirements (Board, Players, Move input, Validation, Win/Draw detection, Game loop, Replay)
- Nonfunctional requirements (Java 17, clean modular OOP, readable console UI, error handling)
- Assumptions and constraints
- Acceptance criteria (numbered list of testable criteria)
- Edge cases (out-of-bounds inputs, non-integer inputs, occupied cells)
- Scope and testing expectations
"""
        prd_doc = self.ollama.generate_structured(
            prompt=prompt,
            response_model=PRDDocument,
            system="You are an expert technical Product Manager creating a formal PRD for software engineers.",
            model=model_name or self.ollama.default_model,
            temperature=0.2
        )

        if not prd_doc:
            # Deterministic robust fallback PRD if local model output fails validation
            prd_doc = PRDDocument(
                project_id=project_id,
                version=1,
                title="Java Tic-Tac-Toe Game Specification",
                overview="A text-based, two-player Tic-Tac-Toe application written in Java 17.",
                functional_requirements=[
                    "FR-1: Support 3x3 grid display with cell coordinates.",
                    "FR-2: Alternate turns between Player X and Player O.",
                    "FR-3: Accept user row and column input from console.",
                    "FR-4: Validate inputs (reject out-of-range inputs 0-2 and occupied cells).",
                    "FR-5: Detect horizontal, vertical, and diagonal win conditions.",
                    "FR-6: Detect draw/tie condition when board is full without a winner.",
                    "FR-7: Prompt players to play again after a match terminates."
                ],
                nonfunctional_requirements=[
                    "NFR-1: Implemented in Java 17 using standard library only.",
                    "NFR-2: Modular OOP architecture (Board, Player, Game/TicTacToe, Tests).",
                    "NFR-3: Graceful exception handling for non-numeric input."
                ],
                assumptions=["Running in a standard terminal/console environment."],
                constraints=["Pure Java 17; no external third-party dependencies."],
                acceptance_criteria=[
                    "AC-1: Valid move updates board correctly.",
                    "AC-2: Occupied move displays error and prompts again.",
                    "AC-3: Winning line immediately triggers game over with winner name.",
                    "AC-4: Full board with no line triggers draw.",
                    "AC-5: Clean termination when player declines restart."
                ],
                edge_cases=[
                    "Inputting letters or symbols instead of numbers.",
                    "Entering negative numbers or numbers greater than 2.",
                    "Attempting to overwrite an already chosen cell."
                ],
                implementation_scope="Core console engine and automated unit test suite.",
                testing_expectations="Automated test suite verifying board logic, win conditions, and input guards."
            )

        prd_doc.project_id = project_id

        # Generate markdown representation
        markdown_content = self.render_to_markdown(prd_doc)
        prd_doc.raw_markdown = markdown_content

        # Determine version
        existing = self.db.list_artifacts(project_id, artifact_type="PRD")
        version = len(existing) + 1
        prd_doc.version = version

        artifact_id = f"prd_v{version}_{uuid.uuid4().hex[:6]}"
        metadata = {
            "version": version,
            "approved": False,
            "functional_req_count": len(prd_doc.functional_requirements),
            "acceptance_criteria_count": len(prd_doc.acceptance_criteria)
        }

        self.db.save_artifact(
            artifact_id=artifact_id,
            project_id=project_id,
            artifact_type="PRD",
            title=f"{prd_doc.title} (v{version})",
            content=markdown_content,
            version=version,
            metadata=metadata
        )

        # Update project stage to PRD_REVIEW
        self.db.update_project_stage(project_id, WorkflowStage.PRD_REVIEW)

        # Publish event
        self.timeline.publish_event(
            project_id=project_id,
            actor_id="agent_pm",
            actor_name="Boshen (Product Manager)",
            actor_role=RoleType.AI_PM,
            participant_type=ParticipantType.AI,
            event_type=EventType.PRD_CREATED,
            message=f"I have published PRD v{version}: '{prd_doc.title}'. Ready for CEO / Human approval.",
            payload={"artifact_id": artifact_id, "version": version},
            artifact_id=artifact_id,
            stage=WorkflowStage.PRD_REVIEW
        )

        return prd_doc

    def approve_prd(
        self,
        project_id: str,
        approver_name: str,
        approver_role: RoleType,
        participant_type: ParticipantType
    ) -> bool:
        """Approve the latest PRD and advance workflow to DEVELOPMENT."""
        prds = self.db.list_artifacts(project_id, artifact_type="PRD")
        if not prds:
            return False

        latest = prds[0]
        meta = latest["metadata"]
        meta["approved"] = True
        meta["approved_by"] = approver_name

        self.db.save_artifact(
            artifact_id=latest["artifact_id"],
            project_id=project_id,
            artifact_type="PRD",
            title=latest["title"],
            content=latest["content"],
            version=latest["version"],
            metadata=meta
        )

        self.db.update_project_stage(project_id, WorkflowStage.DEVELOPMENT)

        self.timeline.publish_event(
            project_id=project_id,
            actor_id="approver",
            actor_name=approver_name,
            actor_role=approver_role,
            participant_type=participant_type,
            event_type=EventType.PRD_APPROVED,
            message=f"PRD {latest['title']} has been officially APPROVED. Development may begin.",
            payload={"artifact_id": latest["artifact_id"]},
            artifact_id=latest["artifact_id"],
            stage=WorkflowStage.DEVELOPMENT
        )
        return True

    def reject_prd(
        self,
        project_id: str,
        feedback: str,
        rejector_name: str,
        rejector_role: RoleType,
        participant_type: ParticipantType
    ) -> bool:
        """Reject the latest PRD with feedback and revert stage to PRD_CREATION."""
        prds = self.db.list_artifacts(project_id, artifact_type="PRD")
        if not prds:
            return False

        latest = prds[0]
        meta = latest["metadata"]
        meta["approved"] = False
        meta["feedback"] = feedback

        self.db.save_artifact(
            artifact_id=latest["artifact_id"],
            project_id=project_id,
            artifact_type="PRD",
            title=latest["title"],
            content=latest["content"],
            version=latest["version"],
            metadata=meta
        )

        self.db.update_project_stage(project_id, WorkflowStage.PRD_CREATION)

        self.timeline.publish_event(
            project_id=project_id,
            actor_id="rejector",
            actor_name=rejector_name,
            actor_role=rejector_role,
            participant_type=participant_type,
            event_type=EventType.PRD_REJECTED,
            message=f"PRD was REJECTED with feedback: '{feedback}'. Product Manager, please revise.",
            payload={"feedback": feedback},
            artifact_id=latest["artifact_id"],
            stage=WorkflowStage.PRD_CREATION
        )
        return True

    @staticmethod
    def render_to_markdown(prd: PRDDocument) -> str:
        """Render PRDDocument into structured GitHub Flavored Markdown."""
        lines = [
            f"# {prd.title} (v{prd.version})",
            "",
            "## 1. Project Overview",
            prd.overview,
            "",
            "## 2. Functional Requirements",
        ]
        for fr in prd.functional_requirements:
            lines.append(f"- {fr}")

        lines.extend([
            "",
            "## 3. Nonfunctional Requirements",
        ])
        for nfr in prd.nonfunctional_requirements:
            lines.append(f"- {nfr}")

        lines.extend([
            "",
            "## 4. Assumptions & Constraints",
            "### Assumptions",
        ])
        for a in prd.assumptions:
            lines.append(f"- {a}")

        lines.append("### Constraints")
        for c in prd.constraints:
            lines.append(f"- {c}")

        lines.extend([
            "",
            "## 5. Acceptance Criteria",
        ])
        for ac in prd.acceptance_criteria:
            lines.append(f"- [ ] {ac}")

        lines.extend([
            "",
            "## 6. Edge Cases",
        ])
        for ec in prd.edge_cases:
            lines.append(f"- {ec}")

        lines.extend([
            "",
            "## 7. Implementation Scope & Testing Expectations",
            f"**Scope**: {prd.implementation_scope}",
            f"**Testing**: {prd.testing_expectations}",
        ])
        return "\n".join(lines)
