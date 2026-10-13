"""Unit tests for Bales IPA classification and Human Coding Inter-Rater Agreement."""
import pytest
import tempfile
import time
from pathlib import Path
from chatcollab.core.database import Database
from chatcollab.core.models import BalesIPACategory, IPALabelRecord
from chatcollab.analytics.human_coding import HumanCodingAnalyzer


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


def test_cohens_kappa_calculation(temp_db):
    analyzer = HumanCodingAnalyzer(temp_db)
    project_id = "test_kappa_proj"
    temp_db.create_project(project_id, "Kappa Proj", "Desc", "Baseline", "llama3.1")

    # When no verified pairs exist
    empty_res = analyzer.compute_agreement(project_id)
    assert empty_res["sample_size"] == 0
    assert empty_res["percentage_agreement"] == 0.0
    assert empty_res["cohens_kappa"] == 0.0

    # Insert mock verified labels:
    # 4 agreements: 2 Gives Suggestion, 2 Gives Orientation
    # 1 disagreement: predicted Gives Suggestion, human coded Gives Opinion
    items = [
        (BalesIPACategory.GIVES_SUGGESTION, BalesIPACategory.GIVES_SUGGESTION),
        (BalesIPACategory.GIVES_SUGGESTION, BalesIPACategory.GIVES_SUGGESTION),
        (BalesIPACategory.GIVES_ORIENTATION, BalesIPACategory.GIVES_ORIENTATION),
        (BalesIPACategory.GIVES_ORIENTATION, BalesIPACategory.GIVES_ORIENTATION),
        (BalesIPACategory.GIVES_SUGGESTION, BalesIPACategory.GIVES_OPINION),
    ]

    for i, (pred, human) in enumerate(items):
        rec = IPALabelRecord(
            project_id=project_id,
            event_id=f"ev_{i}",
            message_text=f"Message {i}",
            actor_name="Agent",
            actor_role="Role",
            predicted_category=pred,
            predicted_model="llama3.1",
            human_category=human,
            is_verified=True,
            timestamp=time.time()
        )
        temp_db.save_ipa_label(rec)

    res = analyzer.compute_agreement(project_id)
    assert res["sample_size"] == 5
    assert res["percentage_agreement"] == 80.0  # 4 out of 5
    assert res["cohens_kappa"] > 0.6  # High agreement
    assert res["confusion_matrix"][BalesIPACategory.GIVES_SUGGESTION.value][BalesIPACategory.GIVES_SUGGESTION.value] == 2
    assert res["confusion_matrix"][BalesIPACategory.GIVES_SUGGESTION.value][BalesIPACategory.GIVES_OPINION.value] == 1
