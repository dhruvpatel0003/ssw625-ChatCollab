"""View 12: Paper vs Demo Traceability Matrix (Module M16)."""
import streamlit as st
import pandas as pd
from ..components import render_header

TRACEABILITY_DATA = [
    {
        "Paper Concept": "Shared Communication Timeline",
        "Paper Reference": "Section 3 & Figure 1",
        "Implementation in Demo": "Event-driven SQLite bus with chronological message and action log",
        "Status": "Direct Implementation"
    },
    {
        "Paper Concept": "Autonomous Agent Turns & WAIT actions",
        "Paper Reference": "Section 3.1 & Appendix A.2",
        "Implementation in Demo": "Pydantic AgentDecision schema with explicit DecisionAction.WAIT support",
        "Status": "Direct Implementation"
    },
    {
        "Paper Concept": "Institutional Knowledge Injection",
        "Paper Reference": "Section 3.2 & Appendix A.1",
        "Implementation in Demo": "Default conventions injected into prompts with interactive editable override",
        "Status": "Direct Implementation"
    },
    {
        "Paper Concept": "Bales IPA 12-Category Coding",
        "Paper Reference": "Section 4 & Table 1",
        "Implementation in Demo": "12 Bales categories + None with +/- 2 context window inference",
        "Status": "Direct Implementation"
    },
    {
        "Paper Concept": "Human-AI Inter-Rater Agreement",
        "Paper Reference": "Section 4.1",
        "Implementation in Demo": "Human Coding interface with Pairwise Agreement and Cohen's Kappa (κ)",
        "Status": "Direct Implementation"
    },
    {
        "Paper Concept": "Java Tic-Tac-Toe Benchmark",
        "Paper Reference": "Section 5 & Experiment Tasks",
        "Implementation in Demo": "Modular Java 17 OOP implementation (Board, Player, TicTacToe, Tests)",
        "Status": "Direct Implementation"
    },
    {
        "Paper Concept": "Isolated Sandbox Execution",
        "Paper Reference": "Engineering Extension",
        "Implementation in Demo": "Deterministic javac compilation and unit test execution in workspace",
        "Status": "Laboratory Extension"
    },
    {
        "Paper Concept": "Automated PRD & QA Defect Cycle",
        "Paper Reference": "Engineering Extension",
        "Implementation in Demo": "Structured PRD generation, CEO approval gates, and QA defect tracking",
        "Status": "Laboratory Extension"
    },
    {
        "Paper Concept": "Local Ollama LLM Inference",
        "Paper Reference": "Architecture Extension",
        "Implementation in Demo": "Strictly local llama3.1 inference without external API keys or cloud cost",
        "Status": "Laboratory Extension"
    }
]


def render():
    render_header("Paper vs. Demo Traceability", "Comprehensive matrix mapping research paper claims to our laboratory implementation")

    st.markdown("""
    <div class="paper-insight-box">
        This matrix provides full academic transparency for presentation reviewers, distinguishing between
        <strong>direct paper implementations</strong> (faithfully replicating the Stanford research) and
        <strong>laboratory extensions</strong> (added for interactive demonstration, sandboxing, and local inference).
    </div>
    """, unsafe_allow_html=True)

    df = pd.DataFrame(TRACEABILITY_DATA)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("Key Architectural Distinctions")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🏛️ Original ChatCollab Paper")
        st.markdown("""
        - Relied on proprietary commercial LLM APIs.
        - Primary focus on conversational interaction transcripts.
        - Manual or batch post-hoc analysis of Bales categories.
        - Human evaluation conducted via simulated MTurk / student trials.
        """)
    with col2:
        st.markdown("#### 🔬 Our Laboratory Implementation")
        st.markdown("""
        - 100% Local Inference powered by Ollama (`llama3.1`).
        - Real-time interactive Streamlit laboratory with step-by-step turns.
        - Integrated deterministic Java 17 compilation & sandbox testing.
        - Live human-in-the-loop coding, approval gates, and Cohen's Kappa calculator.
        """)
