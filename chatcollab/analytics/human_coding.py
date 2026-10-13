"""
Human Coding and Inter-Rater Agreement Analytics for ChatCollab Lab.
Computes Pairwise Agreement percentage, Cohen's Kappa, and confusion matrices
between automated LLM classifications and human expert annotations.
"""
from typing import Dict, Any, List, Tuple, Optional
from ..core.models import BalesIPACategory
from ..core.database import Database


class HumanCodingAnalyzer:
    def __init__(self, db: Database):
        self.db = db

    def get_labeled_pairs(self, project_id: Optional[str] = None) -> List[Tuple[str, str]]:
        """Retrieve paired (predicted_category, human_category) for verified records."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute("""
                SELECT predicted_category, human_category FROM ipa_classifications
                WHERE project_id = ? AND is_verified = 1 AND human_category IS NOT NULL
                """, (project_id,))
            else:
                cursor.execute("""
                SELECT predicted_category, human_category FROM ipa_classifications
                WHERE is_verified = 1 AND human_category IS NOT NULL
                """)
            rows = cursor.fetchall()
            return [(r["predicted_category"], r["human_category"]) for r in rows]

    def compute_agreement(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Compute Pairwise Percentage Agreement and Cohen's Kappa on verified labels.
        Does NOT invent data: requires real verified records.
        """
        pairs = self.get_labeled_pairs(project_id)
        n = len(pairs)
        if n == 0:
            return {
                "sample_size": 0,
                "percentage_agreement": 0.0,
                "cohens_kappa": 0.0,
                "observed_agreement": 0.0,
                "expected_agreement": 0.0,
                "confusion_matrix": {},
                "categories": [c.value for c in BalesIPACategory],
                "message": "No human-verified labels available yet. Use the Human Coding interface to annotate messages."
            }

        # 1. Observed agreement (p_o)
        agreements = sum(1 for pred, human in pairs if pred == human)
        p_o = agreements / n

        # 2. Marginal distributions for expected agreement (p_e)
        all_cats = [c.value for c in BalesIPACategory]
        pred_counts = {c: 0 for c in all_cats}
        human_counts = {c: 0 for c in all_cats}

        # Matrix: matrix[pred][human]
        matrix = {p: {h: 0 for h in all_cats} for p in all_cats}

        for pred, human in pairs:
            if pred in pred_counts:
                pred_counts[pred] += 1
            if human in human_counts:
                human_counts[human] += 1
            if pred in matrix and human in matrix[pred]:
                matrix[pred][human] += 1

        p_e = sum((pred_counts[c] / n) * (human_counts[c] / n) for c in all_cats)

        # 3. Cohen's Kappa: (p_o - p_e) / (1 - p_e)
        if (1.0 - p_e) == 0:
            kappa = 1.0 if p_o == 1.0 else 0.0
        else:
            kappa = (p_o - p_e) / (1.0 - p_e)

        return {
            "sample_size": n,
            "percentage_agreement": round(p_o * 100.0, 2),
            "cohens_kappa": round(kappa, 3),
            "observed_agreement": round(p_o, 4),
            "expected_agreement": round(p_e, 4),
            "confusion_matrix": matrix,
            "categories": all_cats
        }
