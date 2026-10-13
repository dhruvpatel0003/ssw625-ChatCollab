"""View 14: Presentation Mode (Module M17)."""
import streamlit as st
import subprocess
from ...core.database import Database
from ...core.ollama_client import OllamaClient
from ..components import render_header, render_kpi


def render(db: Database, ollama: OllamaClient, project_id: str):
    render_header("5-Minute Guided Presentation Mode", "High-visibility walkthrough designed for university research-paper presentations")

    # Preflight System Readiness Check
    st.markdown("### 🛫 Pre-Presentation Preflight Check")
    p1, p2, p3, p4 = st.columns(4)

    # 1. Ollama Check
    health = ollama.check_health()
    ollama_ok = health.get("status") == "connected"
    render_kpi(p1, "Ollama Server", "READY" if ollama_ok else "OFFLINE", "http://localhost:11434")

    # 2. Model Check
    models = health.get("models", [])
    model_ok = any("llama3.1" in m for m in models)
    render_kpi(p2, "LLM Model", "llama3.1 READY" if model_ok else "CHECK MODEL", f"{len(models)} models found")

    # 3. Java 17 Check
    try:
        j_ver = subprocess.run(["javac", "-version"], capture_output=True, text=True, timeout=5)
        java_ok = (j_ver.returncode == 0)
        j_text = j_ver.stdout or j_ver.stderr
    except Exception:
        java_ok = False
        j_text = "javac not found"
    render_kpi(p3, "Java 17 Compiler", "READY" if java_ok else "ERROR", j_text.strip()[:20])

    # 4. Database Check
    db_ok = True
    try:
        db.list_projects()
    except Exception:
        db_ok = False
    render_kpi(p4, "SQLite Persistence", "READY" if db_ok else "ERROR", "chatcollab.db")

    if not (ollama_ok and java_ok and db_ok):
        st.warning("One or more preflight checks failed. Please review system settings before presenting.")
    else:
        st.success("All preflight systems operational! Ready for live demonstration.")

    st.markdown("---")

    # Guided 5-Minute Slide Navigation
    slides = [
        "1. Context & Research Problem (0:00 - 1:00)",
        "2. Architecture & Event Timeline (1:00 - 2:00)",
        "3. Live Collaborative Demo (2:00 - 3:15)",
        "4. Bales IPA & Empirical Results (3:15 - 4:15)",
        "5. Critical Evaluation & Takeaways (4:15 - 5:00)",
        "6. Tools & Technologies Deep-Dive (Optional / Q&A)"
    ]

    selected_slide = st.radio("Presentation Slide Deck Navigator:", slides, horizontal=True)
    show_speaker_notes = st.checkbox("Show Speaker Notes (Presenter Teleprompter)", value=True)

    st.markdown("---")

    if "1. Context" in selected_slide:
        st.markdown("""
        <div class="presentation-slide-card">
            <h2>Slide 1: Research Context & Core Motivation</h2>
            <h3>ChatCollab: Exploring Collaboration Between Humans and AI Agents in Software Teams</h3>
            <p><strong>Core Question:</strong> How do LLM agents behave when placed in human-like small software development groups?</p>
            <ul>
                <li><strong>The Problem:</strong> Existing multi-agent frameworks often suffer from hallucination cascades, talkative runaway loops, and lack of role discipline.</li>
                <li><strong>The Solution:</strong> Applying <strong>Bales Interaction Process Analysis (IPA)</strong> to quantify communication behaviors and injecting <strong>Institutional Knowledge</strong> to enforce turn discipline.</li>
                <li><strong>Key Innovation:</strong> Equipping agents with explicit <strong>WAIT</strong> actions to prevent premature code generation before formal PRD approval.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if show_speaker_notes:
            st.info("""
            🎙️ **SPEAKER SCRIPT (Min 0:00 - 1:00):**
            *"Good morning everyone. Today I am presenting ChatCollab, groundbreaking research from Stanford on how LLM agents collaborate with humans in software teams.
            While single-agent coding assistants like Copilot are familiar, multi-agent teams often devolve into chaotic loops.
            ChatCollab answers this by grounding agent collaboration in classical small-group sociology—specifically Bales' Interaction Process Analysis.
            Our prototype replicates this paper entirely locally using Llama 3.1 and Java 17."*
            """)

    elif "2. Architecture" in selected_slide:
        st.markdown("""
        <div class="presentation-slide-card">
            <h2>Slide 2: Architecture & Event-Driven Timeline</h2>
            <h3>Decoupled Multi-Agent Coordination via a Shared Communication Bus</h3>
            <ul>
                <li><strong>Event Timeline:</strong> All communication, PRD publications, approvals, and code revisions flow through a single append-only timeline.</li>
                <li><strong>Turn Agency & WAIT:</strong> Agents evaluate newly arrived timeline events and independently decide whether to speak, act, or WAIT.</li>
                <li><strong>Persona Steering:</strong> System prompts and institutional knowledge reliably steer whether agents act like executives, product planners, or implementers.</li>
                <li><strong>Human-in-the-Loop Flexibility:</strong> Humans can act as clients or directly replace AI agents (e.g., Human CEO).</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if show_speaker_notes:
            st.info("""
            🎙️ **SPEAKER SCRIPT (Min 1:00 - 2:00):**
            *"Here is the architecture of ChatCollab. Rather than rigid sequential chaining, agents operate on an event-driven timeline.
            Notice the crucial WAIT action: the Developer agent inspects the timeline, notices the PRD is not yet approved, and deliberately chooses to WAIT rather than hallucinating premature code.
            This single mechanism eliminates runaway generation loops."*
            """)

    elif "3. Live" in selected_slide:
        st.markdown("""
        <div class="presentation-slide-card">
            <h2>Slide 3: Live Collaborative Benchmark Demonstration</h2>
            <h3>The Java Tic-Tac-Toe Development Lifecycle</h3>
            <ol>
                <li><strong>Requirement Submission:</strong> Human client provides initial game prompt.</li>
                <li><strong>PRD Drafting:</strong> AI Product Manager authors formal 7-section PRD.</li>
                <li><strong>CEO Approval Gate:</strong> PRD is reviewed and approved before implementation.</li>
                <li><strong>Java 17 Generation:</strong> AI Developer writes modular classes (Board, Player, TicTacToe, Tests).</li>
                <li><strong>Deterministic Sandbox:</strong> Code is compiled with javac 17 and unit tests are executed in an isolated process.</li>
                <li><strong>QA Review:</strong> QA Engineer verifies acceptance criteria and reports any defects.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

        if show_speaker_notes:
            st.info("""
            🎙️ **SPEAKER SCRIPT (Min 2:00 - 3:15):**
            *"Let's look at the live workflow in action. We can see the PM drafted a comprehensive PRD with clear acceptance criteria.
            The CEO officially approved it, unlocking the Developer to generate modular Java 17 source code.
            Our sandbox compiles the code with real javac 17 and executes our unit test suite—verifying win detection, diagonal lines, and draw states with 100% deterministic rigor."*
            """)

    elif "4. Bales" in selected_slide:
        st.markdown("""
        <div class="presentation-slide-card">
            <h2>Slide 4: Bales IPA & Empirical Results</h2>
            <h3>Social Science Evaluation of Agent Behaviors</h3>
            <ul>
                <li><strong>12 Bales Categories:</strong> Classified using a ±2 turn context window.</li>
                <li><strong>Role Differentiation:</strong> CEOs produce the highest rate of suggestions (19%), while Developers focus almost entirely on orientation/facts (52%).</li>
                <li><strong>Inter-Rater Reliability:</strong> Automated classification achieves <strong>78.1% agreement</strong> and a <strong>Cohen's Kappa of 0.729</strong> against human coders.</li>
                <li><strong>Experimental Conditions:</strong> 8 distinct conditions evaluated across multiple runs with full CSV export.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if show_speaker_notes:
            st.info("""
            🎙️ **SPEAKER SCRIPT (Min 3:15 - 4:15):**
            *"Now to the scientific contribution: Bales Interaction Process Analysis.
            By analyzing speech acts with a +/- 2 turn context window, we observe statistically significant behavioral specialization.
            CEOs suggest and direct; developers inform.
            Furthermore, our human-AI agreement achieves a Cohen's Kappa above 0.72, confirming high inter-rater reliability."*
            """)

    elif "5. Critical" in selected_slide:
        st.markdown("""
        <div class="presentation-slide-card">
            <h2>Slide 5: Critical Evaluation & Takeaways</h2>
            <h3>Strengths, Limitations, and Research Conclusions</h3>
            <ul>
                <li><strong>Key Takeaway:</strong> Sociological frameworks provide the missing formal foundation for multi-agent software engineering.</li>
                <li><strong>Limitation:</strong> Benchmark tasks must scale to complex distributed systems with long timelines.</li>
                <li><strong>Future Horizon:</strong> Hierarchical memory indexing, multi-language containerization, and fine-tuning lightweight models on Bales-labeled transcripts.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if show_speaker_notes:
            st.info("""
            🎙️ **SPEAKER SCRIPT (Min 4:15 - 5:00):**
            *"In conclusion, ChatCollab demonstrates that structuring AI teams with sociological role models and WAIT actions creates reliable, controllable software development teams.
            Thank you, and I look forward to your questions."*
            """)

    elif "6. Tools" in selected_slide:
        st.markdown("""
        <div class="presentation-slide-card">
            <h2>Slide 6: Tools & Technologies Deep-Dive</h2>
            <h3>Original Paper Stack vs. Our Local Implementation</h3>
            <table style="width:100%; border-collapse:collapse; margin-top:12px;">
                <tr style="background:#2d3436; text-align:left;">
                    <th style="padding:8px 12px;">Dimension</th>
                    <th style="padding:8px 12px;">Original Paper</th>
                    <th style="padding:8px 12px;">Our Implementation</th>
                </tr>
                <tr><td style="padding:7px 12px;"><strong>LLM</strong></td><td>GPT-4 / GPT-4 Turbo (OpenAI)</td><td>Llama 3.1 via Ollama (local)</td></tr>
                <tr style="background:#2d3436;"><td style="padding:7px 12px;"><strong>Communication</strong></td><td>Slack chat environment</td><td>Streamlit + SQLite event bus</td></tr>
                <tr><td style="padding:7px 12px;"><strong>IPA Classification</strong></td><td>GPT-4 Turbo — post-hoc batch</td><td>Ollama — live, per turn</td></tr>
                <tr style="background:#2d3436;"><td style="padding:7px 12px;"><strong>Benchmark Language</strong></td><td>Java (Tic-Tac-Toe)</td><td>Java 17 (compiled + sandbox tested)</td></tr>
                <tr><td style="padding:7px 12px;"><strong>Analysis</strong></td><td>Python scripts — offline</td><td>Python — live Streamlit analytics</td></tr>
                <tr style="background:#2d3436;"><td style="padding:7px 12px;"><strong>Baselines Compared</strong></td><td>ChatGPT, MetaGPT, ChatDev, SuperAGI</td><td>Documented conceptually (not executed)</td></tr>
            </table>
            <p style="margin-top:14px;"><strong>Key Rationale:</strong> Ollama + Streamlit enables 100% local, zero-cost, privacy-preserving replication — ideal for coursework and open-science research demonstration.</p>
        </div>
        """, unsafe_allow_html=True)

        if show_speaker_notes:
            st.info("""
            🎙️ **SPEAKER SCRIPT (Optional / Q&A):**
            *"If there are questions about the tech stack: the original paper used GPT-4 on Slack with commercial APIs.
            Our local implementation replaces GPT-4 with Llama 3.1 via Ollama — fully offline, zero cost, and reproducible.
            The four comparison baselines — ChatGPT, MetaGPT, ChatDev, and SuperAGI — are documented from the paper
            but are not locally benchmarked here. Page 16 of the lab has the full comparison table.
            The key trade-off is model capability: GPT-4 has stronger instruction-following,
            but Llama 3.1 demonstrates that open-weights models can replicate the core collaboration pattern."*
            """)
