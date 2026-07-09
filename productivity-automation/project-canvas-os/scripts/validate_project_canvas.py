#!/usr/bin/env python3
"""Compatibility wrapper for Project Canvas OS validation.

Usage:
  python3 validate_project_canvas.py Project.canvas
  python3 validate_project_canvas.py /path/to/project-dir --strict
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_canvas_os import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["validate", *sys.argv[1:]]))
