#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("project_canvas_os.py")


def run_cmd(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run([sys.executable, str(SCRIPT), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode != 0:
        raise AssertionError(f"command failed: {args}\nstdout={result.stdout}\nstderr={result.stderr}")
    return result


class ProjectCanvasOSTest(unittest.TestCase):
    def test_init_validate_add_evidence_transition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            run_cmd("init", str(project), "--name", "Demo", "--goal", "Ship verified slices")
            self.assertTrue((project / "README.md").exists())
            self.assertTrue((project / "Project.canvas").exists())
            self.assertTrue((project / ".agents" / "canvas-protocol.md").exists())
            run_cmd("validate", str(project), "--strict")
            run_cmd("add-module", str(project), "--title", "Runtime", "--role", "executes agent queries")
            run_cmd("add-task", str(project), "--title", "Wire runtime", "--state", "Active", "--owner", "Codex", "--module", "Runtime")
            run_cmd("add-evidence", str(project), "--title", "Runtime tests", "--task", "Wire runtime", "--test", "pnpm test passed", "--set-task-verify")
            status = run_cmd("status", str(project)).stdout
            self.assertIn("Verify", status)
            denied = run_cmd("transition", str(project), "--task", "Wire runtime", "--state", "Done", check=False)
            self.assertNotEqual(denied.returncode, 0)
            self.assertIn("Done requires", denied.stderr)
            run_cmd("transition", str(project), "--task", "Wire runtime", "--state", "Done", "--gate", "human confirmed")
            run_cmd("validate", str(project), "--strict")
            data = json.loads((project / "Project.canvas").read_text())
            task_nodes = [n for n in data["nodes"] if n.get("type") == "text" and "Task: Wire runtime" in n.get("text", "")]
            self.assertEqual(len(task_nodes), 1)
            self.assertIn("State: Done", task_nodes[0]["text"])
            self.assertIn("Gate: human confirmed", task_nodes[0]["text"])

    def test_done_without_evidence_fails_strict_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            run_cmd("init", str(project))
            canvas = project / "Project.canvas"
            data = json.loads(canvas.read_text())
            for node in data["nodes"]:
                if node.get("type") == "text" and "Task: <first task>" in node.get("text", ""):
                    node["text"] = node["text"].replace("State: Proposed", "State: Done")
                    break
            canvas.write_text(json.dumps(data, indent=2))
            result = run_cmd("validate", str(project), "--strict", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("lacks concrete evidence", result.stderr)
    def test_docs_are_agent_knowledge_layer_not_sprawl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            run_cmd("init", str(project))
            docs = project / "docs"
            docs.mkdir()
            (docs / "architecture.md").write_text("# Architecture\n\nCanonical module overview.\n", encoding="utf-8")
            (docs / "runbook.md").write_text("# Runbook\n\nCanonical operator procedure.\n", encoding="utf-8")
            result = run_cmd("docs", str(project))
            self.assertIn("knowledge=3", result.stdout)
            self.assertNotIn("state/progress docs exist", result.stdout)
            stale = docs / "old-design.md"
            stale.write_text("# Old Design\n\nOUTDATED: replaced by architecture.md\n", encoding="utf-8")
            strict = run_cmd("docs", str(project), "--strict", check=False)
            self.assertNotEqual(strict.returncode, 0)
            self.assertIn("stale/deprecated markers", strict.stdout)


if __name__ == "__main__":
    unittest.main()
