"""
Core configuration settings for ChatCollab Lab.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "chatcollab.db"
WORKSPACE_DIR = BASE_DIR / "workspaces"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("DEFAULT_OLLAMA_MODEL", "llama3.1:latest")

# Timeout limits
OLLAMA_REQUEST_TIMEOUT = 120  # seconds
JAVA_COMPILE_TIMEOUT = 15     # seconds
JAVA_EXECUTE_TIMEOUT = 10     # seconds
MAX_AGENT_TURNS_PER_CYCLE = 12
