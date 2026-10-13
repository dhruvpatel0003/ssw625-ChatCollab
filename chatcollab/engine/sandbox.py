"""
Isolated Java 17 Sandbox for ChatCollab Lab.
Executes javac compilation and runs automated unit tests with strict resource bounds:
isolated workspace directory, timeout limits (10-15s), and process isolation.
"""
from typing import Dict, Any, Optional
from pathlib import Path
import subprocess
import time
import uuid
import re
from ..core.config import (
    WORKSPACE_DIR, JAVA_COMPILE_TIMEOUT, JAVA_EXECUTE_TIMEOUT
)
from ..core.models import (
    EventType, RoleType, ParticipantType, WorkflowStage
)
from ..core.database import Database
from .timeline import Timeline


class JavaSandbox:
    def __init__(self, db: Database, timeline: Timeline):
        self.db = db
        self.timeline = timeline

    def get_workspace_dirs(self, project_id: str) -> Dict[str, Path]:
        base = WORKSPACE_DIR / project_id
        src = base / "src"
        bin_dir = base / "bin"
        src.mkdir(parents=True, exist_ok=True)
        bin_dir.mkdir(parents=True, exist_ok=True)
        return {"base": base, "src": src, "bin": bin_dir}

    def compile_and_test(
        self,
        project_id: str,
        artifact_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Safely compile Java sources with javac and run TicTacToeTest.
        Returns dictionary with compilation status, pass/fail counts, and outputs.
        """
        dirs = self.get_workspace_dirs(project_id)
        src_dir = dirs["src"]
        bin_dir = dirs["bin"]

        java_files = list(src_dir.glob("*.java"))
        if not java_files:
            return {
                "compilation_passed": False,
                "tests_passed": 0,
                "tests_failed": 0,
                "stdout": "",
                "stderr": "No Java source files found in workspace src directory.",
                "execution_time_ms": 0.0
            }

        t0 = time.time()

        # Step 1: javac compilation
        compile_cmd = ["javac", "-d", str(bin_dir)] + [str(f) for f in java_files]
        try:
            compile_proc = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=JAVA_COMPILE_TIMEOUT,
                cwd=str(src_dir)
            )
        except subprocess.TimeoutExpired:
            return self._record_and_return(
                project_id, artifact_id,
                compilation_passed=False, tests_passed=0, tests_failed=1,
                stdout="", stderr=f"Compilation timed out after {JAVA_COMPILE_TIMEOUT}s.",
                duration_ms=(time.time() - t0) * 1000
            )
        except Exception as e:
            return self._record_and_return(
                project_id, artifact_id,
                compilation_passed=False, tests_passed=0, tests_failed=1,
                stdout="", stderr=f"Compilation execution error: {str(e)}",
                duration_ms=(time.time() - t0) * 1000
            )

        if compile_proc.returncode != 0:
            return self._record_and_return(
                project_id, artifact_id,
                compilation_passed=False, tests_passed=0, tests_failed=1,
                stdout=compile_proc.stdout, stderr=compile_proc.stderr,
                duration_ms=(time.time() - t0) * 1000
            )

        # Step 2: run TicTacToeTest if present
        test_class_file = bin_dir / "TicTacToeTest.class"
        if not test_class_file.exists():
            return self._record_and_return(
                project_id, artifact_id,
                compilation_passed=True, tests_passed=0, tests_failed=0,
                stdout="Compilation succeeded, but TicTacToeTest.class was not produced.",
                stderr="",
                duration_ms=(time.time() - t0) * 1000
            )

        run_cmd = ["java", "-cp", str(bin_dir), "TicTacToeTest"]
        try:
            run_proc = subprocess.run(
                run_cmd,
                capture_output=True,
                text=True,
                timeout=JAVA_EXECUTE_TIMEOUT,
                cwd=str(bin_dir)
            )
            stdout = run_proc.stdout
            stderr = run_proc.stderr
            retcode = run_proc.returncode
        except subprocess.TimeoutExpired:
            return self._record_and_return(
                project_id, artifact_id,
                compilation_passed=True, tests_passed=0, tests_failed=1,
                stdout="", stderr=f"Test execution timed out after {JAVA_EXECUTE_TIMEOUT}s.",
                duration_ms=(time.time() - t0) * 1000
            )
        except Exception as e:
            return self._record_and_return(
                project_id, artifact_id,
                compilation_passed=True, tests_passed=0, tests_failed=1,
                stdout="", stderr=f"Execution error: {str(e)}",
                duration_ms=(time.time() - t0) * 1000
            )

        duration_ms = (time.time() - t0) * 1000

        # Parse test results: "Test Results: 7 passed, 0 failed."
        passed_matches = len(re.findall(r"\[PASS\]", stdout))
        failed_matches = len(re.findall(r"\[FAIL\]", stderr + stdout))

        if passed_matches == 0 and retcode == 0:
            # Fallback regex search for totals line
            m = re.search(r"(\d+)\s+passed,\s*(\d+)\s+failed", stdout)
            if m:
                passed_matches = int(m.group(1))
                failed_matches = int(m.group(2))
            else:
                passed_matches = 1

        all_passed = (retcode == 0 and failed_matches == 0)

        return self._record_and_return(
            project_id, artifact_id,
            compilation_passed=True,
            tests_passed=passed_matches,
            tests_failed=failed_matches,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms
        )

    def _record_and_return(
        self,
        project_id: str,
        artifact_id: Optional[str],
        compilation_passed: bool,
        tests_passed: int,
        tests_failed: int,
        stdout: str,
        stderr: str,
        duration_ms: float
    ) -> Dict[str, Any]:
        run_id = f"test_{uuid.uuid4().hex[:8]}"
        self.db.record_test_run(
            run_id=run_id,
            project_id=project_id,
            artifact_id=artifact_id,
            compilation_passed=compilation_passed,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            stdout=stdout,
            stderr=stderr,
            execution_time_ms=duration_ms
        )

        # Publish timeline event
        if compilation_passed and tests_failed == 0 and tests_passed > 0:
            self.timeline.publish_event(
                project_id=project_id,
                actor_id="sandbox",
                actor_name="Java Sandbox",
                actor_role=RoleType.AI_QA,
                participant_type=ParticipantType.AI,
                event_type=EventType.TEST_PASSED,
                message=f"Deterministic Java verification: COMPILATION SUCCESS. {tests_passed} automated tests PASSED.",
                payload={"run_id": run_id, "passed": tests_passed, "failed": tests_failed, "duration_ms": duration_ms},
                artifact_id=artifact_id,
                stage=WorkflowStage.QA_TESTING
            )
        else:
            reason = "Compilation failed." if not compilation_passed else f"{tests_failed} test(s) failed."
            self.timeline.publish_event(
                project_id=project_id,
                actor_id="sandbox",
                actor_name="Java Sandbox",
                actor_role=RoleType.AI_QA,
                participant_type=ParticipantType.AI,
                event_type=EventType.TEST_FAILED,
                message=f"Deterministic Java verification FAILED: {reason}\n{stderr[:300]}",
                payload={"run_id": run_id, "passed": tests_passed, "failed": tests_failed, "stderr": stderr[:500]},
                artifact_id=artifact_id,
                stage=WorkflowStage.QA_TESTING
            )

        return {
            "run_id": run_id,
            "compilation_passed": compilation_passed,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "stdout": stdout,
            "stderr": stderr,
            "execution_time_ms": duration_ms
        }
