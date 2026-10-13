"""View 16: Tools & Technologies Comparison (Module M18)."""
import streamlit as st
import pandas as pd
from ..components import render_header

# ── Framework & methodology technologies from the paper ──────────────────────
FRAMEWORK_TECH = [
    {
        "Technology": "ChatCollab Framework",
        "Category": "Multi-Agent Framework",
        "Purpose in Paper": "Central experimental framework; structured human–AI software teams with shared timeline, role assignment, institutional knowledge, and WAIT actions.",
        "Our Equivalent": "This Streamlit Laboratory (chatcollab/ package)",
        "Reproduction Status": "✅ Reproduced",
        "Paper Section": "Section 3",
    },
    {
        "Technology": "Slack",
        "Category": "Communication Platform",
        "Purpose in Paper": "Shared communication environment where human and AI agents exchanged messages, simulating real team chat.",
        "Our Equivalent": "Streamlit Event Timeline + SQLite append-only bus (Page 8)",
        "Reproduction Status": "🟡 Adapted",
        "Paper Section": "Section 3 / Figure 1",
    },
    {
        "Technology": "GPT-4",
        "Category": "Large Language Model",
        "Purpose in Paper": "Primary LLM powering all AI agents (CEO, PM, Developer, QA) during collaboration experiments.",
        "Our Equivalent": "Ollama llama3.1:latest (local open-weights inference)",
        "Reproduction Status": "🟡 Adapted",
        "Paper Section": "Section 3.1",
    },
    {
        "Technology": "GPT-4 Turbo",
        "Category": "Large Language Model",
        "Purpose in Paper": "Used specifically for automated Bales IPA speech-act classification of conversation transcripts.",
        "Our Equivalent": "Same Ollama llama3.1 instance via structured JSON prompt (bales_ipa.py)",
        "Reproduction Status": "🟡 Adapted",
        "Paper Section": "Section 4",
    },
    {
        "Technology": "Python",
        "Category": "Programming Language",
        "Purpose in Paper": "Transcript processing, experimental pipeline, Bales IPA scoring, statistical analysis, and Cohen's Kappa computation.",
        "Our Equivalent": "Python 3.11+ (entire chatcollab/ backend and analytics)",
        "Reproduction Status": "✅ Reproduced",
        "Paper Section": "Methodology",
    },
    {
        "Technology": "Bales IPA",
        "Category": "Research Methodology",
        "Purpose in Paper": "12-category interaction analysis scheme from small-group sociology; used to classify and quantify agent speech acts across collaboration sessions.",
        "Our Equivalent": "bales_ipa.py — 12-category + None classifier with ±2 turn context window",
        "Reproduction Status": "✅ Reproduced",
        "Paper Section": "Section 4 / Table 1",
    },
    {
        "Technology": "Java",
        "Category": "Benchmark Programming Language",
        "Purpose in Paper": "Language used for the Tic-Tac-Toe software benchmark task that agents collaboratively implemented.",
        "Our Equivalent": "Java 17 (JDK Temurin) — generated, compiled, and tested via javac sandbox",
        "Reproduction Status": "✅ Reproduced",
        "Paper Section": "Section 5",
    },
]

# ── Comparison baseline systems from the paper ────────────────────────────────
BASELINE_SYSTEMS = [
    {
        "System": "ChatGPT (OpenAI)",
        "Type": "Single-Agent / Conversational AI",
        "Role in Paper": "Baseline comparison: human-led development assisted by a single conversational LLM, without multi-agent role structure.",
        "Locally Available?": "❌ Not Installed",
        "Note": "OpenAI commercial API required. Not benchmarked in this local implementation.",
    },
    {
        "System": "MetaGPT",
        "Type": "Multi-Agent Software Framework",
        "Role in Paper": "Comparison system: structured role-based agents (PM, Engineer, QA) using sequential message passing without a shared event timeline.",
        "Locally Available?": "❌ Not Installed",
        "Note": "Open-source Python package, but not integrated here. Compared conceptually only.",
    },
    {
        "System": "ChatDev",
        "Type": "Multi-Agent Software Framework",
        "Role in Paper": "Comparison system: LLM-powered virtual software company with role-play dialogue between agents.",
        "Locally Available?": "❌ Not Installed",
        "Note": "Open-source. Role-play based, lacks autonomous WAIT mechanism. Not locally executed.",
    },
    {
        "System": "SuperAGI",
        "Type": "Autonomous Agent Platform",
        "Role in Paper": "Evaluated as a general-purpose autonomous agent baseline lacking domain-specific role grounding.",
        "Locally Available?": "❌ Not Installed",
        "Note": "Cloud-hosted platform. Included in paper's evaluation table; not replicated locally.",
    },
]

_STATUS_LEGEND = {
    "✅ Reproduced": "Identical capability — same methodology, different (local) tooling.",
    "🟡 Adapted": "Functionally equivalent; local open-source alternative used.",
    "🔵 Conceptual": "Demonstrated conceptually; not a full technical replication.",
    "🔴 Not Implemented": "Acknowledged in paper but absent from local implementation.",
}

_FLOW_CARD = """
<div style="
    background: {bg};
    border: 1px solid {border};
    border-radius: 12px;
    padding: 20px 24px;
    height: 100%;
">
    <h4 style="margin-top:0; color:{title_color};">{title}</h4>
    <div style="display:flex; flex-direction:column; gap:8px; margin-top:12px;">
        {steps}
    </div>
</div>
"""

_STEP = """
<div style="display:flex; align-items:center; gap:10px;">
    <div style="
        background:{color};
        border-radius:8px;
        padding:6px 14px;
        font-size:0.82rem;
        font-weight:600;
        white-space:nowrap;
        color:#fff;
    ">{label}</div>
    {arrow}
</div>
"""

_ARROW = '<div style="font-size:1.2rem; color:#636e72;">↓</div>'


def _build_flow(steps: list[tuple[str, str]], last: bool = False) -> str:
    html_steps = ""
    for i, (label, color) in enumerate(steps):
        arrow = "" if i == len(steps) - 1 else _ARROW
        html_steps += _STEP.format(label=label, color=color, arrow=arrow)
    return html_steps


def render():
    render_header(
        "Tools & Technologies",
        "Original ChatCollab paper technologies vs. our local implementation — with research baselines",
    )

    # ── 1. Architecture flow comparison ──────────────────────────────────────
    st.markdown("### 🔄 Architecture Pipeline Comparison")
    st.caption("Side-by-side view of the original paper's tech stack vs. our local adaptation.")

    col_orig, col_local = st.columns(2)

    orig_steps = [
        ("👥 Human + AI Team", "#6c5ce7"),
        ("💬 Slack  (Chat Platform)", "#0984e3"),
        ("🤖 GPT-4 Agents  (OpenAI API)", "#00b894"),
        ("📦 Software Artifacts", "#fdcb6e"),
        ("📊 Bales IPA  (GPT-4 Turbo)", "#e17055"),
    ]
    local_steps = [
        ("👥 Human + AI Team", "#6c5ce7"),
        ("📋 Streamlit + SQLite Timeline", "#0984e3"),
        ("🦙 Ollama  llama3.1  (Local)", "#00b894"),
        ("☕ Java 17 Artifacts + Sandbox", "#fdcb6e"),
        ("📊 Ollama-Based IPA Analysis", "#e17055"),
    ]

    with col_orig:
        steps_html = _build_flow(orig_steps)
        st.markdown(
            _FLOW_CARD.format(
                bg="#1e1e2e",
                border="#6c5ce7",
                title_color="#a29bfe",
                title="🏛️ Original ChatCollab Paper",
                steps=steps_html,
            ),
            unsafe_allow_html=True,
        )

    with col_local:
        steps_html = _build_flow(local_steps)
        st.markdown(
            _FLOW_CARD.format(
                bg="#1e2e1e",
                border="#00b894",
                title_color="#55efc4",
                title="🔬 Our Local Implementation",
                steps=steps_html,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("")  # spacer

    # ── 2. Legend ─────────────────────────────────────────────────────────────
    with st.expander("📖 Reproduction Status Legend", expanded=False):
        for badge, desc in _STATUS_LEGEND.items():
            st.markdown(f"**{badge}** — {desc}")

    st.markdown("---")

    # ── 3. Framework technologies table ───────────────────────────────────────
    st.markdown("### 🛠️ Framework & Methodology Technologies")
    st.caption(
        "All technologies below are directly part of the ChatCollab paper's framework or evaluation methodology."
    )

    df_fw = pd.DataFrame(FRAMEWORK_TECH)
    st.dataframe(
        df_fw,
        use_container_width=True,
        column_config={
            "Technology": st.column_config.TextColumn("Technology", width="medium"),
            "Category": st.column_config.TextColumn("Category", width="medium"),
            "Purpose in Paper": st.column_config.TextColumn("Purpose in Paper", width="large"),
            "Our Equivalent": st.column_config.TextColumn("Our Equivalent", width="large"),
            "Reproduction Status": st.column_config.TextColumn("Status", width="small"),
            "Paper Section": st.column_config.TextColumn("Paper §", width="small"),
        },
    )

    st.markdown("---")

    # ── 4. Research baselines ─────────────────────────────────────────────────
    st.markdown("### 🧪 Research Comparison Baselines")

    st.info(
        "⚠️ **Transparency Notice:** The four systems below were evaluated as comparison baselines in the "
        "original paper. They are **not installed, executed, or benchmarked** in this local implementation. "
        "They are documented here for academic completeness and to facilitate discussion during presentation."
    )

    df_bl = pd.DataFrame(BASELINE_SYSTEMS)
    st.dataframe(
        df_bl,
        use_container_width=True,
        column_config={
            "System": st.column_config.TextColumn("System", width="medium"),
            "Type": st.column_config.TextColumn("Type", width="medium"),
            "Role in Paper": st.column_config.TextColumn("Role in Paper", width="large"),
            "Locally Available?": st.column_config.TextColumn("Local?", width="small"),
            "Note": st.column_config.TextColumn("Note", width="large"),
        },
    )

    st.markdown("---")

    # ── 5. Strengths, weaknesses, recommendations ─────────────────────────────
    st.markdown("### ⚖️ Why Ollama + Streamlit Instead of GPT-4 + Slack?")

    sw1, sw2 = st.columns(2)

    with sw1:
        st.markdown("#### ✅ Strengths of Our Local Approach")
        st.markdown("""
**1. Zero Cost & Full Privacy**
All inference runs locally via Ollama — no OpenAI API keys, no usage fees, no data leaves the machine. Ideal for coursework and sensitive research contexts.

**2. Full Reproducibility**
A deterministic seed and local model guarantees identical conditions across experimental runs, eliminating cloud-side variability from rate limits or model updates.

**3. Research Contribution: Open-Weights LLMs**
Testing whether Bales IPA classification and WAIT-action discipline transfer to open-weights models (Llama 3.1) is itself a novel research angle not covered by the original paper.

**4. Integrated Execution Sandbox**
The Java 17 compilation and unit-test sandbox goes beyond the paper, adding engineering rigor that proves agent-generated code is actually correct — not just plausible.
        """)

    with sw2:
        st.markdown("#### ⚠️ Trade-offs vs. Original Paper")
        st.markdown("""
**1. Model Capability Gap**
GPT-4 significantly outperforms Llama 3.1 on instruction following, schema adherence, and nuanced judgment. Some agent turns may require additional retries or fallback WAIT actions.

**2. No Slack Integration**
Slack's real-time threading would more authentically replicate enterprise team communication. Our SQLite timeline is functionally equivalent but lacks rich UI threading features.

**3. Baseline Systems Not Executed**
ChatGPT, MetaGPT, ChatDev, and SuperAGI are compared conceptually only. A true replicated experiment would require running each system on the same Tic-Tac-Toe benchmark.

**4. Context Window Limits**
Ollama's effective context is shorter than GPT-4 Turbo's 128K tokens, making very long collaboration histories more susceptible to prompt truncation.
        """)

    st.markdown("---")
    st.markdown("#### 🚀 Recommendations")
    st.markdown("""
- **Upgrade model**: Swap to `llama3.1:70b` or `mistral-large` for closer GPT-4 parity once hardware allows.
- **Add Slack webhook**: Post timeline events to a real Slack channel for a hybrid demo that mirrors the original paper's setup.
- **Containerize baselines**: Package MetaGPT and ChatDev in Docker and run the same Tic-Tac-Toe benchmark for a genuine local comparison table.
- **Fine-tune on Bales transcripts**: Train a small adapter on Bales IPA-labeled data to specialize a local model for higher-accuracy speech-act classification.
    """)
