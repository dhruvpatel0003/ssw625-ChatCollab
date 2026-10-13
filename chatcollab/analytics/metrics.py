"""
Collaboration Metrics Aggregator and Research Reference Data.
Computes participation rates, role distributions, IPA category ratios,
and provides original paper reference numbers for comparison.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
from ..core.models import (
    TimelineEvent, RoleType, ParticipantType, EventType, BalesIPACategory
)
from ..core.database import Database

# Ground truth baseline statistics reported in ChatCollab (Klieger et al., 2024)
PAPER_REFERENCE_BENCHMARKS = {
    "title": "ChatCollab: Exploring Collaboration Between Humans and AI Agents in Software Teams (Klieger et al., 2024)",
    "primary_experiment_messages": 237,
    "experimental_conditions_count": 8,
    "runs_per_condition": 3,
    "human_ai_coding_agreement": 78.1,  # %
    "cohens_kappa": 0.729,
    "role_suggestion_percentages": {
        "CEO": 19.0,
        "Product Manager": 11.0,
        "Developer": 4.5,
    },
    "role_orientation_percentages": {
        "Product Manager": 45.0,
        "Developer": 52.0,
        "CEO": 30.0,
    },
    "key_findings": [
        "Specialized role prompts significantly steer agent communicative behaviors.",
        "CEOs exhibit higher rates of giving suggestions and opinions.",
        "Developers exhibit high rates of giving orientation (technical facts) and lowest suggestions.",
        "Product Managers dominate the initial requirement clarification and PRD drafting stages.",
        "Human participants seamlessly coordinate as team peers when agents exhibit role awareness."
    ]
}


class CollaborationMetrics:
    def __init__(self, db: Database):
        self.db = db

    def get_summary_metrics(self, project_id: str) -> Dict[str, Any]:
        """Aggregate collaboration metrics for a specific project session."""
        events = self.db.get_events(project_id)
        artifacts = self.db.list_artifacts(project_id)
        test_runs = self.db.get_test_runs(project_id)
        ipa_labels = self.db.get_ipa_labels(project_id)

        chat_events = [
            e for e in events
            if e.event_type not in {EventType.AGENT_WAITING}
        ]
        waiting_events = [
            e for e in events
            if e.event_type == EventType.AGENT_WAITING
        ]

        # Messages per actor and role
        actor_counts = {}
        role_counts = {}
        for e in chat_events:
            actor_counts[e.actor_name] = actor_counts.get(e.actor_name, 0) + 1
            role_val = e.actor_role.value if hasattr(e.actor_role, 'value') else str(e.actor_role)
            role_counts[role_val] = role_counts.get(role_val, 0) + 1

        # IPA category distribution
        ipa_counts = {}
        for l in ipa_labels:
            cat = l["predicted_category"]
            ipa_counts[cat] = ipa_counts.get(cat, 0) + 1

        # Test stats
        latest_test = test_runs[0] if test_runs else None

        return {
            "total_events": len(events),
            "chat_messages_count": len(chat_events),
            "waiting_actions_count": len(waiting_events),
            "artifacts_count": len(artifacts),
            "test_runs_count": len(test_runs),
            "actor_message_distribution": actor_counts,
            "role_message_distribution": role_counts,
            "ipa_category_distribution": ipa_counts,
            "latest_test_status": {
                "compiled": bool(latest_test["compilation_passed"]) if latest_test else False,
                "passed": latest_test["tests_passed"] if latest_test else 0,
                "failed": latest_test["tests_failed"] if latest_test else 0,
            } if latest_test else None,
            "paper_references": PAPER_REFERENCE_BENCHMARKS
        }

    def get_timeline_dataframe(self, project_id: str) -> pd.DataFrame:
        """Convert timeline events to pandas DataFrame for interactive charts."""
        events = self.db.get_events(project_id)
        if not events:
            return pd.DataFrame()

        rows = []
        for e in events:
            rows.append({
                "Timestamp": pd.to_datetime(e.timestamp, unit="s"),
                "Actor": e.actor_name,
                "Role": e.actor_role.value if hasattr(e.actor_role, 'value') else str(e.actor_role),
                "Participant": e.participant_type.value if hasattr(e.participant_type, 'value') else str(e.participant_type),
                "EventType": e.event_type.value if hasattr(e.event_type, 'value') else str(e.event_type),
                "Stage": e.stage.value if hasattr(e.stage, 'value') else str(e.stage),
                "MessageSnippet": (e.message[:80] + "...") if len(e.message) > 80 else e.message
            })
        return pd.DataFrame(rows)
