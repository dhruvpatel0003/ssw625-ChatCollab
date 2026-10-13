"""
Bales Interaction Process Analysis (IPA) Classifier for ChatCollab Lab.
Implements the 12 Bales categories + None of the Above.
Classifies collaboration transcript messages using local Ollama inference
with a window of +/- 2 conversational turns as defined in ChatCollab Section 4.
"""
from typing import List, Dict, Any, Optional
import time
import json
import re
from ..core.models import (
    BalesIPACategory, IPALabelRecord, TimelineEvent, EventType
)
from ..core.database import Database
from ..core.ollama_client import OllamaClient

IPA_DEFINITIONS = """
BALES' INTERACTION PROCESS ANALYSIS (IPA) CATEGORIES:
1. Shows Solidarity: raises other's status, gives help, reward, praise, warm greeting.
2. Shows Tension Release: jokes, laughs, shows satisfaction, relieves anxiety.
3. Agrees: shows passive acceptance, understands, concurs, complies, confirms.
4. Gives Suggestion: direction, proposing action, tactical advice, implying autonomy for other.
5. Gives Opinion: evaluation, analysis, expresses feeling, belief, reasoning, or wish.
6. Gives Orientation: information, repeats, clarifies, confirms facts, status update.
7. Asks for Orientation: asks for information, repetition, confirmation, status.
8. Asks for Opinion: asks for evaluation, analysis, viewpoint, expression of feeling.
9. Asks for Suggestion: asks for direction, possible ways of action, instructions.
10. Disagrees: shows passive rejection, formality, withholds help, skepticism.
11. Shows Tension: asks for help, withdraws out of field, expresses frustration.
12. Shows Antagonism: deflates other's status, defends or asserts self aggressively.
13. None of the Above: purely mechanical system message or unclassifiable text.
"""

IPA_CATEGORY_MAPPING = {
    "1": BalesIPACategory.SHOWS_SOLIDARITY,
    "2": BalesIPACategory.SHOWS_TENSION_RELEASE,
    "3": BalesIPACategory.AGREES,
    "4": BalesIPACategory.GIVES_SUGGESTION,
    "5": BalesIPACategory.GIVES_OPINION,
    "6": BalesIPACategory.GIVES_ORIENTATION,
    "7": BalesIPACategory.ASKS_FOR_ORIENTATION,
    "8": BalesIPACategory.ASKS_FOR_OPINION,
    "9": BalesIPACategory.ASKS_FOR_SUGGESTION,
    "10": BalesIPACategory.DISAGREES,
    "11": BalesIPACategory.SHOWS_TENSION,
    "12": BalesIPACategory.SHOWS_ANTAGONISM,
    "13": BalesIPACategory.NONE_OF_THE_ABOVE,
}


class BalesIPAClassifier:
    def __init__(self, db: Database, ollama: OllamaClient):
        self.db = db
        self.ollama = ollama

    def classify_message(
        self,
        project_id: str,
        target_event: TimelineEvent,
        preceding_turns: List[TimelineEvent],
        following_turns: List[TimelineEvent],
        model_name: Optional[str] = None
    ) -> IPALabelRecord:
        """
        Classify a single event using the target message and +/- 2 context turns.
        """
        context_lines = []
        if preceding_turns:
            context_lines.append("PRECEDING CONTEXT (up to 2 turns):")
            for e in preceding_turns[-2:]:
                context_lines.append(f"  [{e.actor_name} ({e.actor_role.value})]: {e.message[:200]}")

        context_lines.append(f"\nTARGET MESSAGE TO CLASSIFY:\n  Speaker: {target_event.actor_name} ({target_event.actor_role.value})\n  Message: \"{target_event.message}\"\n")

        if following_turns:
            context_lines.append("FOLLOWING CONTEXT (up to 2 turns):")
            for e in following_turns[:2]:
                context_lines.append(f"  [{e.actor_name} ({e.actor_role.value})]: {e.message[:200]}")

        prompt = f"""
{IPA_DEFINITIONS}

Analyze the TARGET MESSAGE in the conversational context below and classify it into EXACTLY ONE of the 13 categories.

=== CONVERSATION WINDOW ===
{chr(10).join(context_lines)}

INSTRUCTIONS:
Respond with a JSON object containing:
- "category_number": Integer 1 to 13
- "category_name": Exact name from the list above
- "rationale": Brief 1-sentence justification
"""
        selected_model = model_name or self.ollama.default_model
        res = self.ollama.generate(
            prompt=prompt,
            system="You are a social science coding specialist classifying team communication using Bales Interaction Process Analysis.",
            model=selected_model,
            temperature=0.1
        )

        predicted_cat = self._parse_category_response(res.get("text", ""), target_event)

        record = IPALabelRecord(
            project_id=project_id,
            event_id=target_event.event_id,
            message_text=target_event.message,
            actor_name=target_event.actor_name,
            actor_role=target_event.actor_role.value if hasattr(target_event.actor_role, 'value') else str(target_event.actor_role),
            predicted_category=predicted_cat,
            predicted_model=selected_model,
            prompt_version="v1_window_plus_minus_2",
            timestamp=time.time()
        )

        self.db.save_ipa_label(record)
        return record

    def classify_project_timeline(
        self,
        project_id: str,
        model_name: Optional[str] = None
    ) -> List[IPALabelRecord]:
        """
        Classify all conversational messages in the project timeline using +/- 2 turn context windows.
        """
        events = self.db.get_events(project_id)
        # Filter for conversational turns
        chat_events = [
            e for e in events
            if e.event_type in {
                EventType.MESSAGE_POSTED,
                EventType.REQUIREMENTS_SUBMITTED,
                EventType.CLARIFICATION_REQUESTED,
                EventType.CLARIFICATION_ANSWERED,
                EventType.PRD_APPROVED,
                EventType.PRD_REJECTED,
                EventType.DEFECT_REPORTED,
                EventType.HUMAN_FEEDBACK,
            }
        ]

        records = []
        for i, target in enumerate(chat_events):
            preceding = chat_events[max(0, i - 2):i]
            following = chat_events[i + 1:min(len(chat_events), i + 3)]
            rec = self.classify_message(project_id, target, preceding, following, model_name)
            records.append(rec)

        return records

    def _parse_category_response(self, text: str, event: TimelineEvent) -> BalesIPACategory:
        """Parse category name or number from model output with heuristic fallback."""
        text_lower = text.lower()

        # Check for category names directly
        for cat in BalesIPACategory:
            if cat.value.lower() in text_lower:
                return cat

        # Check for category numbers: 1 to 13
        num_match = re.search(r'"category_number":\s*(\d+)', text)
        if num_match:
            val = num_match.group(1)
            if val in IPA_CATEGORY_MAPPING:
                return IPA_CATEGORY_MAPPING[val]

        # Heuristic fallback based on event type if model output was ambiguous
        if event.event_type == EventType.CLARIFICATION_REQUESTED:
            return BalesIPACategory.ASKS_FOR_ORIENTATION
        elif event.event_type == EventType.PRD_APPROVED:
            return BalesIPACategory.AGREES
        elif event.event_type == EventType.PRD_REJECTED or event.event_type == EventType.DEFECT_REPORTED:
            return BalesIPACategory.DISAGREES
        elif event.event_type == EventType.REQUIREMENTS_SUBMITTED:
            return BalesIPACategory.GIVES_ORIENTATION

        return BalesIPACategory.GIVES_ORIENTATION
