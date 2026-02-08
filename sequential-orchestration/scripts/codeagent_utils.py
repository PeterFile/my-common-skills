"""
Codeagent Wrapper Utilities

Helper functions for resolving and invoking codeagent-wrapper.
Self-contained - no external skill dependencies.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Optional, Sequence


_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUE_VALUES


def tmux_enabled() -> bool:
    """Check if tmux is enabled (not disabled via CODEAGENT_NO_TMUX)."""
    return not _env_truthy("CODEAGENT_NO_TMUX")


def _candidate_wrapper_names() -> Sequence[str]:
    if sys.platform.startswith("win"):
        return ("codeagent-wrapper.exe", "codeagent-wrapper")
    return ("codeagent-wrapper", "codeagent-wrapper.exe")


def _is_executable(path: Path) -> bool:
    if sys.platform.startswith("win"):
        return path.is_file()
    return path.is_file() and os.access(path, os.X_OK)


def resolve_codeagent_wrapper() -> str:
    """
    Resolve path to codeagent-wrapper executable.
    
    Search order:
    1. CODEAGENT_WRAPPER / CODEAGENT_WRAPPER_PATH env var
    2. System PATH
    3. Local bin directories (cwd, repo root)
    4. Home directories (~/.claude/bin, ~/.local/bin, ~/bin)
    
    Raises:
        FileNotFoundError: If wrapper cannot be found
    """
    # Check env override
    override = os.environ.get("CODEAGENT_WRAPPER") or os.environ.get("CODEAGENT_WRAPPER_PATH")
    if override:
        candidate = Path(override).expanduser()
        if _is_executable(candidate):
            return str(candidate)
        raise FileNotFoundError(f"CODEAGENT_WRAPPER not found: {candidate}")

    # Check PATH
    found = shutil.which("codeagent-wrapper")
    if found:
        return found

    # Search local directories
    names = _candidate_wrapper_names()
    search_roots = [Path.cwd().resolve(), Path(__file__).resolve()]
    for root in search_roots:
        for base in (root, *root.parents):
            for name in names:
                for candidate in (
                    base / "codeagent-wrapper" / name,
                    base / "bin" / name,
                ):
                    if _is_executable(candidate):
                        return str(candidate)

    # Check home directories
    home_bins = [
        Path.home() / ".claude" / "bin",
        Path.home() / ".local" / "bin",
        Path.home() / "bin",
    ]
    for bin_dir in home_bins:
        for name in names:
            candidate = bin_dir / name
            if _is_executable(candidate):
                return str(candidate)

    raise FileNotFoundError("codeagent-wrapper not found (set CODEAGENT_WRAPPER or add it to PATH)")


def looks_like_tmux_error(text: str) -> bool:
    """Check if error text suggests tmux issues."""
    lowered = (text or "").lower()
    if "tmux" not in lowered:
        return False
    return (
        "error connecting to /tmp/tmux" in lowered
        or "failed to connect to /tmp/tmux" in lowered
        or "operation not permitted" in lowered
        or "permission denied" in lowered
        or "tmux: not found" in lowered
        or "command not found: tmux" in lowered
        or "executable file not found" in lowered
        or "no such file or directory" in lowered
    )
