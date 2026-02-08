from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Dict, Optional, Sequence


_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUE_VALUES


def tmux_enabled() -> bool:
    return not _env_truthy("CODEAGENT_NO_TMUX")


def resolve_codex_timeout_seconds(*, default_seconds: int = 7200, buffer_seconds: int = 300) -> int:
    """
    Resolve a safe subprocess timeout for invoking codeagent-wrapper.

    - Mirrors codeagent-wrapper's `CODEX_TIMEOUT` parsing:
      - values > 10000 are treated as milliseconds
      - otherwise treated as seconds
    - Adds a small buffer so the wrapper can exit cleanly.
    """
    raw = os.environ.get("CODEX_TIMEOUT", "").strip()
    timeout_seconds = default_seconds
    if raw:
        try:
            parsed = int(raw)
            if parsed > 0:
                timeout_seconds = parsed // 1000 if parsed > 10000 else parsed
        except ValueError:
            timeout_seconds = default_seconds
    return max(60, timeout_seconds) + max(0, buffer_seconds)


def _candidate_wrapper_names() -> Sequence[str]:
    if sys.platform.startswith("win"):
        return ("codeagent-wrapper.exe", "codeagent-wrapper")
    return ("codeagent-wrapper", "codeagent-wrapper.exe")


def _is_executable(path: Path) -> bool:
    if sys.platform.startswith("win"):
        return path.is_file()
    return path.is_file() and os.access(path, os.X_OK)


def resolve_codeagent_wrapper() -> str:
    override = os.environ.get("CODEAGENT_WRAPPER") or os.environ.get("CODEAGENT_WRAPPER_PATH")
    if override:
        candidate = Path(override).expanduser()
        if _is_executable(candidate):
            return str(candidate)
        raise FileNotFoundError(f"CODEAGENT_WRAPPER not found: {candidate}")

    found = shutil.which("codeagent-wrapper")
    if found:
        return found

    names = _candidate_wrapper_names()
    search_roots = [Path.cwd().resolve(), Path(__file__).resolve()]
    for root in search_roots:
        for base in (root, *root.parents):
            for name in names:
                for candidate in (
                    base / "codeagent-wrapper" / name,  # local build: repo/codeagent-wrapper/codeagent-wrapper(.exe)
                    base / "bin" / name,  # legacy layout: repo/bin/codeagent-wrapper(.exe)
                ):
                    if _is_executable(candidate):
                        return str(candidate)

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


def looks_like_tmux_connect_error(text: str) -> bool:
    lowered = (text or "").lower()
    if "tmux" not in lowered:
        return False
    return (
        "error connecting to /tmp/tmux" in lowered
        or "failed to connect to /tmp/tmux" in lowered
        or "operation not permitted" in lowered
        or "permission denied" in lowered
    )


def looks_like_tmux_missing(text: str) -> bool:
    lowered = (text or "").lower()
    if "tmux" not in lowered:
        return False
    return (
        "tmux: not found" in lowered
        or "command not found: tmux" in lowered
        or "executable file not found" in lowered
        or "no such file or directory" in lowered
    )


def ensure_tmux_tmpdir(env: Dict[str, str]) -> Optional[str]:
    current = env.get("TMUX_TMPDIR", "").strip()
    if current:
        return current
    tmpdir = os.path.join(os.path.expanduser("~"), ".tmux-tmp")
    try:
        os.makedirs(tmpdir, exist_ok=True)
        try:
            os.chmod(tmpdir, 0o700)
        except OSError:
            pass
    except OSError:
        return None
    env["TMUX_TMPDIR"] = tmpdir
    os.environ.setdefault("TMUX_TMPDIR", tmpdir)
    return tmpdir
