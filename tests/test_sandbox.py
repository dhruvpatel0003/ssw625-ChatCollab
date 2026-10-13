"""Integration test for Java Code Generation and Sandbox javac compilation & execution."""
import pytest
import tempfile
import subprocess
from pathlib import Path
from chatcollab.core.database import Database
from chatcollab.engine.timeline import Timeline
from chatcollab.engine.code_generator import CodeGenerator
from chatcollab.engine.sandbox import JavaSandbox


@pytest.fixture
def temp_env():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)
    db = Database(db_path=db_path)
    tl = Timeline(db)
    yield db, tl
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass


def test_java_sandbox_compilation_and_execution(temp_env):
    db, tl = temp_env
    project_id = "test_sandbox_proj"
    db.create_project(project_id, "Sandbox Proj", "Desc", "Baseline", "llama3.1")

    # Generate canonical Java solution
    code_gen = CodeGenerator(db, tl, None)
    files = code_gen._get_canonical_java_solution()

    ws_dir = code_gen.get_project_workspace(project_id)
    for fname, content in files.items():
        with open(ws_dir / fname, "w", encoding="utf-8") as f:
            f.write(content)

    sandbox = JavaSandbox(db, tl)
    result = sandbox.compile_and_test(project_id)

    # Validate deterministic execution
    assert result["compilation_passed"] is True, f"Compilation failed: {result['stderr']}"
    assert result["tests_passed"] == 11, f"Expected 11 passed assertions, got: {result['tests_passed']}"
    assert result["tests_failed"] == 0, f"Expected 0 failed tests, got: {result['tests_failed']}"
    assert result["execution_time_ms"] > 0
    assert "[PASS] Row 0 win detected for X" in result["stdout"]
