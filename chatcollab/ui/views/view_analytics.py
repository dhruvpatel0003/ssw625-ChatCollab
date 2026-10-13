"""View 9: Collaboration Analytics & Bales IPA Breakdown (Modules M11, M12)."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from ...core.database import Database
from ...core.ollama_client import OllamaClient
from ...analytics.bales_ipa import BalesIPAClassifier
from ...analytics.metrics import CollaborationMetrics, PAPER_REFERENCE_BENCHMARKS
from ..components import render_header, render_kpi


def render(db: Database, ollama: OllamaClient, project_id: str):
    render_header("Collaboration Analytics", "Bales IPA classification distributions, participation rates, and research paper comparisons")

    classifier = BalesIPAClassifier(db, ollama)
    metrics_calc = CollaborationMetrics(db)
    summary = metrics_calc.get_summary_metrics(project_id)
    ipa_labels = db.get_ipa_labels(project_id)

    # Classification Trigger
    c1, c2 = st.columns([3, 1])
    with c1:
        st.write(f"Classified Messages in Timeline: **{len(ipa_labels)}**")
    with c2:
        if st.button("🏷️ Run Bales IPA Classification", use_container_width=True, help="Analyze timeline messages using Ollama +/- 2 turn window"):
            with st.spinner("Classifying messages with local Ollama model..."):
                recs = classifier.classify_project_timeline(project_id)
                st.success(f"Classified {len(recs)} messages!")
                st.rerun()

    st.markdown("---")

    # Visualizations Row 1: Participation & Roles
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Participation by Role")
        role_dist = summary.get("role_message_distribution", {})
        if role_dist:
            df_roles = pd.DataFrame(list(role_dist.items()), columns=["Role", "Messages"])
            fig_roles = px.pie(
                df_roles, values="Messages", names="Role",
                title="Message Share by Role",
                color_discrete_sequence=["#6c5ce7", "#0984e3", "#00b894", "#e17055", "#00cec9"]
            )
            fig_roles.update_layout(template="plotly_dark", margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_roles, use_container_width=True)
        else:
            st.info("No message distribution data available.")

    with col_right:
        st.subheader("Bales IPA Category Distribution")
        ipa_dist = summary.get("ipa_category_distribution", {})
        if ipa_dist:
            df_ipa = pd.DataFrame(list(ipa_dist.items()), columns=["Category", "Count"]).sort_values("Count", ascending=True)
            fig_ipa = px.bar(
                df_ipa, x="Count", y="Category", orientation="h",
                title="Bales IPA Communication Behaviors",
                color="Count", color_continuous_scale="Purples"
            )
            fig_ipa.update_layout(template="plotly_dark", margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_ipa, use_container_width=True)
        else:
            st.info("No IPA classifications available yet. Click 'Run Bales IPA Classification' above.")

    st.markdown("---")

    # Research Paper Benchmark Comparison Section
    st.subheader("Comparison Against Research Paper Reference (ChatCollab 2024)")
    st.markdown("""
    <div class="paper-insight-box">
        <strong>Paper Finding:</strong> In ChatCollab, specialized role prompts led to stark behavioral differentiation:
        CEOs accounted for the highest rate of <em>Giving Suggestions</em> (19%), Product Managers led in initial orientation and questions,
        and Developers focused primarily on <em>Giving Orientation</em> (52%) while offering very few suggestions (4.5%).
    </div>
    """, unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns(4)
    render_kpi(b1, "Paper Total Messages", PAPER_REFERENCE_BENCHMARKS["primary_experiment_messages"], "Primary Study")
    render_kpi(b2, "Paper Agreement", f"{PAPER_REFERENCE_BENCHMARKS['human_ai_coding_agreement']}%", "Human-AI Coding")
    render_kpi(b3, "Paper Cohen's Kappa", PAPER_REFERENCE_BENCHMARKS["cohens_kappa"], "High Inter-Rater Reliability")
    render_kpi(b4, "Paper Conditions", PAPER_REFERENCE_BENCHMARKS["experimental_conditions_count"], "3 Runs per Condition")
