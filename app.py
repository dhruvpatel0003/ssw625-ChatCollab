"""
ChatCollab: Human–AI Software Development Laboratory
Main Streamlit Application Entrypoint.
Faithfully inspired by ChatCollab (Klieger et al., 2024).
"""
import streamlit as st
import uuid
from chatcollab.core.database import Database
from chatcollab.core.ollama_client import OllamaClient
from chatcollab.engine.timeline import Timeline
from chatcollab.agents.roles import TeamManager
from chatcollab.engine.decision_engine import DecisionEngine
from chatcollab.engine.prd_manager import PRDManager
from chatcollab.engine.code_generator import CodeGenerator
from chatcollab.engine.sandbox import JavaSandbox
from chatcollab.engine.qa_engine import QAEngine
from chatcollab.ui.styles import CUSTOM_CSS

# View Modules
from chatcollab.ui.views import (
    view_dashboard,
    view_team,
    view_workspace,
    view_institutional_knowledge,
    view_prd,
    view_code,
    view_qa,
    view_timeline,
    view_analytics,
    view_experiments,
    view_human_coding,
    view_paper_vs_demo,
    view_strengths_weaknesses,
    view_presentation,
    view_diagnostics,
    view_tools_technologies
)

# Page configuration
st.set_page_config(
    page_title="ChatCollab Lab — Human-AI Software Engineering",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_resource
def get_database() -> Database:
    return Database()


@st.cache_resource
def get_ollama_client() -> OllamaClient:
    return OllamaClient()


# Initialize application session state
if "team_manager" not in st.session_state:
    st.session_state.team_manager = TeamManager()

db = get_database()
ollama = get_ollama_client()
timeline = Timeline(db)
team_manager = st.session_state.team_manager

decision_engine = DecisionEngine(db, timeline, ollama, team_manager)
prd_manager = PRDManager(db, timeline, ollama)
code_generator = CodeGenerator(db, timeline, ollama)
sandbox = JavaSandbox(db, timeline)
qa_engine = QAEngine(db, timeline, ollama)

# Ensure at least one default benchmark project exists
existing_projects = db.list_projects()
if not existing_projects:
    default_proj_id = "proj_tictactoe_benchmark"
    db.create_project(
        project_id=default_proj_id,
        name="Java Tic-Tac-Toe Benchmark",
        description="Develop a complete, text-based Java Tic-Tac-Toe application with 3x3 grid, alternating turns for Player X and Player O, row/col validation, win/draw detection, and replay loop.",
        persona="Baseline Institutional Knowledge",
        active_model=ollama.default_model
    )
    existing_projects = db.list_projects()

if "active_project_id" not in st.session_state or not st.session_state.active_project_id:
    st.session_state.active_project_id = existing_projects[0]["id"] if existing_projects else ""

# ----------------- SIDEBAR NAVIGATION -----------------
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 16px 0;">
        <span class="paper-badge">ChatCollab (Stanford)</span>
        <h2 style="margin: 6px 0 0 0; font-weight: 800; font-size: 1.3rem; letter-spacing: -0.5px;">Software Lab</h2>
        <p style="margin: 0; font-size: 0.8rem; color: #a4b0be;">Human–AI Collaborative Engineering</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Project Selector
    st.markdown("**📂 Active Project Session**")
    proj_options = {p["id"]: f"{p['name']} ({p['stage']})" for p in existing_projects}
    proj_ids = list(proj_options.keys())

    cur_idx = proj_ids.index(st.session_state.active_project_id) if st.session_state.active_project_id in proj_ids else 0
    selected_project_id = st.selectbox(
        "Select Session:",
        options=proj_ids,
        format_func=lambda pid: proj_options.get(pid, pid),
        index=cur_idx,
        label_visibility="collapsed"
    )
    st.session_state.active_project_id = selected_project_id

    # New Project Popover
    with st.popover("➕ New Project Session"):
        new_name = st.text_input("Project Name:", value="New Collaboration Experiment")
        new_desc = st.text_area("Requirements / Goal:", value="Develop a Java Tic-Tac-Toe game with OOP modularity and test suite.")
        if st.button("Create Project", use_container_width=True):
            new_id = f"proj_{uuid.uuid4().hex[:8]}"
            db.create_project(
                project_id=new_id,
                name=new_name,
                description=new_desc,
                persona="Baseline Institutional Knowledge",
                active_model=ollama.default_model
            )
            st.session_state.active_project_id = new_id
            st.success("Project created!")
            st.rerun()

    st.markdown("---")

    # Navigation Menu
    st.markdown("**🧭 Lab Navigation**")
    PAGE_LIST = [
        "1. Overview Dashboard",
        "2. Team Configuration & Roles",
        "3. Human–AI Collaboration Workspace",
        "4. Institutional Knowledge & Personas",
        "5. PRD & Approval Center",
        "6. Code & Artifact Explorer",
        "7. QA & Test Results",
        "8. Shared Event Timeline",
        "9. Collaboration Analytics",
        "10. Experiment Lab",
        "11. Human Coding & Agreement",
        "12. Paper vs. Demo Traceability",
        "13. Strengths, Weaknesses & Recommendations",
        "14. 5-Minute Presentation Mode",
        "15. System Settings & Diagnostics",
        "16. Tools & Technologies"
    ]

    selected_page = st.radio(
        "Go to page:",
        PAGE_LIST,
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")
    # Quick Status Indicators
    health = ollama.check_health()
    if health.get("status") == "connected":
        st.caption(f"🟢 **Ollama Online**: `{ollama.default_model}`")
    else:
        st.caption("🔴 **Ollama Offline** (Check server)")

# ----------------- PAGE ROUTING -----------------
active_pid = st.session_state.active_project_id

try:
    if selected_page.startswith("1. Overview"):
        view_dashboard.render(db, ollama, active_pid)
    elif selected_page.startswith("2. Team"):
        view_team.render(team_manager)
    elif selected_page.startswith("3. Human–AI"):
        view_workspace.render(
            db, timeline, ollama, decision_engine, team_manager,
            prd_manager, code_generator, sandbox, qa_engine, active_pid
        )
    elif selected_page.startswith("4. Institutional"):
        view_institutional_knowledge.render()
    elif selected_page.startswith("5. PRD"):
        view_prd.render(db, prd_manager, team_manager, active_pid)
    elif selected_page.startswith("6. Code"):
        view_code.render(db, active_pid)
    elif selected_page.startswith("7. QA"):
        view_qa.render(db, active_pid)
    elif selected_page.startswith("8. Shared"):
        view_timeline.render(db, active_pid)
    elif selected_page.startswith("9. Collaboration"):
        view_analytics.render(db, ollama, active_pid)
    elif selected_page.startswith("10. Experiment"):
        view_experiments.render(db, ollama)
    elif selected_page.startswith("11. Human"):
        view_human_coding.render(db, active_pid)
    elif selected_page.startswith("12. Paper"):
        view_paper_vs_demo.render()
    elif selected_page.startswith("13. Strengths"):
        view_strengths_weaknesses.render()
    elif selected_page.startswith("14. 5-Minute"):
        view_presentation.render(db, ollama, active_pid)
    elif selected_page.startswith("15. System"):
        view_diagnostics.render(db, ollama, active_pid)
    elif selected_page.startswith("16. Tools"):
        view_tools_technologies.render()
except Exception as e:
    st.error(f"Error rendering {selected_page}: {str(e)}")
    st.exception(e)
