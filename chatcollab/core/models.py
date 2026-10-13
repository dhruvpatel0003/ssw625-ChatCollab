"""
Pydantic data models and schemas for ChatCollab Lab.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import time
import uuid


class RoleType(str, Enum):
    HUMAN_CLIENT = "Human Client"
    AI_CEO = "AI CEO"
    AI_PM = "AI Product Manager"
    AI_DEV = "AI Developer"
    AI_QA = "AI QA Engineer"


class ParticipantType(str, Enum):
    HUMAN = "HUMAN"
    AI = "AI"


class WorkflowStage(str, Enum):
    REQUIREMENTS = "REQUIREMENTS"
    PRD_CREATION = "PRD_CREATION"
    PRD_REVIEW = "PRD_REVIEW"
    DEVELOPMENT = "DEVELOPMENT"
    QA_TESTING = "QA_TESTING"
    REVISION = "REVISION"
    COMPLETED = "COMPLETED"


class EventType(str, Enum):
    MESSAGE_POSTED = "MESSAGE_POSTED"
    REQUIREMENTS_SUBMITTED = "REQUIREMENTS_SUBMITTED"
    CLARIFICATION_REQUESTED = "CLARIFICATION_REQUESTED"
    CLARIFICATION_ANSWERED = "CLARIFICATION_ANSWERED"
    PRD_CREATED = "PRD_CREATED"
    PRD_APPROVED = "PRD_APPROVED"
    PRD_REJECTED = "PRD_REJECTED"
    DEVELOPMENT_STARTED = "DEVELOPMENT_STARTED"
    CODE_GENERATED = "CODE_GENERATED"
    QA_REVIEW_REQUESTED = "QA_REVIEW_REQUESTED"
    DEFECT_REPORTED = "DEFECT_REPORTED"
    CODE_REVISED = "CODE_REVISED"
    TEST_EXECUTED = "TEST_EXECUTED"
    TEST_FAILED = "TEST_FAILED"
    TEST_PASSED = "TEST_PASSED"
    AGENT_WAITING = "AGENT_WAITING"
    HUMAN_FEEDBACK = "HUMAN_FEEDBACK"
    PROJECT_COMPLETED = "PROJECT_COMPLETED"
    ERROR = "ERROR"


class DecisionAction(str, Enum):
    SEND_MESSAGE = "SEND_MESSAGE"
    ASK_QUESTION = "ASK_QUESTION"
    CREATE_ARTIFACT = "CREATE_ARTIFACT"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"
    APPROVE_ARTIFACT = "APPROVE_ARTIFACT"
    REJECT_ARTIFACT = "REJECT_ARTIFACT"
    REVIEW_ARTIFACT = "REVIEW_ARTIFACT"
    REPORT_DEFECT = "REPORT_DEFECT"
    REVISE_ARTIFACT = "REVISE_ARTIFACT"
    WAIT = "WAIT"
    COMPLETE_TASK = "COMPLETE_TASK"


class PersonaType(str, Enum):
    BASELINE = "Baseline Institutional Knowledge"
    FREQUENTLY_AGREEABLE = "Frequently Agreeable"
    FREQUENTLY_DISAGREEABLE = "Frequently Disagreeable"
    SUGGESTION_ORIENTED = "Suggestion-Oriented"
    OPINION_SEEKING = "Opinion-Seeking"
    ORIENTATION_FOCUSED = "Orientation-Focused"
    HUMAN_CEO_REPLACEMENT = "Human CEO Replacement"


class BalesIPACategory(str, Enum):
    SHOWS_SOLIDARITY = "Shows Solidarity"
    SHOWS_TENSION_RELEASE = "Shows Tension Release"
    AGREES = "Agrees"
    GIVES_SUGGESTION = "Gives Suggestion"
    GIVES_OPINION = "Gives Opinion"
    GIVES_ORIENTATION = "Gives Orientation"
    ASKS_FOR_ORIENTATION = "Asks for Orientation"
    ASKS_FOR_OPINION = "Asks for Opinion"
    ASKS_FOR_SUGGESTION = "Asks for Suggestion"
    DISAGREES = "Disagrees"
    SHOWS_TENSION = "Shows Tension"
    SHOWS_ANTAGONISM = "Shows Antagonism"
    NONE_OF_THE_ABOVE = "None of the Above"


class TimelineEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    timestamp: float = Field(default_factory=time.time)
    actor_id: str
    actor_name: str
    actor_role: RoleType
    participant_type: ParticipantType
    event_type: EventType
    message: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    artifact_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    stage: WorkflowStage = WorkflowStage.REQUIREMENTS


class AgentDecision(BaseModel):
    action: DecisionAction
    message: str = Field(description="Message text to post or reason for action/waiting")
    target_recipient: Optional[str] = Field(default=None, description="Target agent name or None for all")
    artifact_type: Optional[str] = Field(default=None, description="'PRD' or 'CODE' or 'QA_REPORT' or None")
    artifact_payload: Optional[Dict[str, Any]] = Field(default=None, description="Artifact content or details")
    reasoning: Optional[str] = Field(default=None, description="Internal agent justification for this decision")


class PRDDocument(BaseModel):
    project_id: str
    version: int = 1
    title: str = "Tic-Tac-Toe Game Specification"
    overview: str
    functional_requirements: List[str]
    nonfunctional_requirements: List[str]
    assumptions: List[str]
    constraints: List[str]
    acceptance_criteria: List[str]
    edge_cases: List[str]
    implementation_scope: str
    testing_expectations: str
    raw_markdown: Optional[str] = None


class QADefect(BaseModel):
    defect_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    requirement_id: str
    description: str
    severity: str = "Medium"  # Critical, High, Medium, Low
    evidence: str
    recommended_correction: str


class QAReport(BaseModel):
    project_id: str
    artifact_id: str
    version: int = 1
    summary: str
    compilation_passed: bool
    tests_passed: int
    tests_failed: int
    defects: List[QADefect] = Field(default_factory=list)
    approved: bool = False
    raw_output: Optional[str] = None


class IPALabelRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    event_id: str
    message_text: str
    actor_name: str
    actor_role: str
    predicted_category: BalesIPACategory
    predicted_model: str
    prompt_version: str = "v1"
    timestamp: float = Field(default_factory=time.time)
    human_category: Optional[BalesIPACategory] = None
    human_coder: Optional[str] = None
    is_verified: bool = False
