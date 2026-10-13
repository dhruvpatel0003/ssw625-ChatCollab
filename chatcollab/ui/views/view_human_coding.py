"""View 11: Human Coding and Inter-Rater Agreement (Module M14)."""
import streamlit as st
import pandas as pd
from ...core.database import Database
from ...core.models import BalesIPACategory
from ...analytics.human_coding import HumanCodingAnalyzer
from ...analytics.metrics import PAPER_REFERENCE_BENCHMARKS
from ..components import render_header, render_kpi


def render(db: Database, project_id: str):
    render_header("Human Coding & Agreement", "Label messages as a human annotator, calculate Pairwise Agreement, and evaluate Cohen's Kappa")

    analyzer = HumanCodingAnalyzer(db)
    metrics = analyzer.compute_agreement(project_id)

    st.markdown("### Inter-Rater Agreement Metrics")
    k1, k2, k3, k4 = st.columns(4)
    render_kpi(k1, "Observed Agreement", f"{metrics['percentage_agreement']}%", f"Sample: {metrics['sample_size']} items")
    render_kpi(k2, "Cohen's Kappa (κ)", metrics["cohens_kappa"], "Inter-Rater Reliability")
    render_kpi(k3, "Paper Reference Agreement", f"{PAPER_REFERENCE_BENCHMARKS['human_ai_coding_agreement']}%", "ChatCollab Benchmark")
    render_kpi(k4, "Paper Reference Kappa", PAPER_REFERENCE_BENCHMARKS["cohens_kappa"], "Substantial Agreement")

    st.markdown("---")
    st.markdown("### Annotate / Verify Transcript Messages")

    labels = db.get_ipa_labels(project_id)
    if not labels:
        st.info("No messages have been classified yet. Run Bales IPA Classification in Collaboration Analytics first.")
        return

    # Annotation Table
    categories = [c.value for c in BalesIPACategory]

    with st.expander("Annotate Messages", expanded=True):
        for item in labels[:15]:
            with st.container():
                st.markdown(f"**[{item['actor_role']}] {item['actor_name']}**: *\"{item['message_text']}\"*")
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.caption(f"🤖 **Model Predicted**: `{item['predicted_category']}`")
                with c2:
                    current_human = item["human_category"] or item["predicted_category"]
                    selected_human = st.selectbox(
                        "Human Annotation:",
                        categories,
                        index=categories.index(current_human) if current_human in categories else 0,
                        key=f"anno_{item['id']}"
                    )
                with c3:
                    st.write("")
                    if st.button("Save", key=f"btn_save_{item['id']}"):
                        db.update_ipa_human_label(item["id"], selected_human)
                        st.success("Saved!")
                        st.rerun()
                st.markdown("---")

    if metrics["sample_size"] > 0:
        st.markdown("### Confusion Matrix (Predicted vs Human)")
        st.dataframe(pd.DataFrame(metrics["confusion_matrix"]), use_container_width=True)
