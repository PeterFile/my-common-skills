#!/usr/bin/env python3
"""Project Canvas OS command-line tool.

Zero-dependency operations for README.md + Project.canvas projects.

Examples:
  python3 project_canvas_os.py init /path/to/repo --name "My Project" --goal "Ship X"
  python3 project_canvas_os.py validate /path/to/repo --strict
  python3 project_canvas_os.py status /path/to/repo
  python3 project_canvas_os.py add-task /path/to/repo --title "Wire provider runtime" --state Active --owner Codex
  python3 project_canvas_os.py add-evidence /path/to/repo --title "Provider tests" --task "Wire provider" --test "pnpm test passed" --set-task-verify
  python3 project_canvas_os.py transition /path/to/repo --task "Wire provider" --state Done --evidence "Provider tests" --gate "human confirmed"
"""
from __future__ import annotations

import argparse
import json
import re
import secrets
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

VALID_NODE_TYPES = {"text", "file", "link", "group"}
VALID_SIDES = {"top", "right", "bottom", "left"}
VALID_ENDS = {"none", "arrow"}
VALID_STATES = {"Proposed", "Active", "Verify", "Done", "Blocked"}
CARD_KINDS = {"Goal", "Module", "Task", "Evidence", "Risk", "Decision"}
HEX16_RE = re.compile(r"^[0-9a-f]{16}$")
CARD_PREFIX_RE = re.compile(r"^(Goal|Module|Task|Evidence|Risk|Decision):\s*(.+)$", re.M)
STATE_RE = re.compile(r"^State:\s*(Proposed|Active|Verify|Done|Blocked)\s*$", re.M)
FIELD_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 _/-]*):\s*(.*)$")
DOC_STATE_RE = re.compile(r"(?i)(progress|summary|handoff|status|latest-status|dev-log|implementation-log|task-log).*(\.md|\.mdx)$")
DOC_KNOWLEDGE_RE = re.compile(r"(?i)(readme|docs?/|architecture|design|domain|model|adr|decision|runbook|operations|api|schema|testing|validation|setup|install|contributing|agent|protocol|spec).*(\.md|\.mdx)$")
STALE_DOC_RE = re.compile(r"(?i)\b(outdated|stale|deprecated|obsolete|superseded)\b|过时|已废弃|不再维护")
MARKDOWN_EXTS = {".md", ".mdx"}
IGNORED_DOC_PARTS = {".git", "node_modules", ".worktrees", ".tmp", ".venv", "venv", "dist", "build", "coverage"}

STATE_COLORS = {
    "Proposed": "6",
    "Active": "5",
    "Verify": "3",
    "Done": "4",
    "Blocked": "1",
}
KIND_COLORS = {
    "Goal": "6",
    "Module": "5",
    "Task": "6",
    "Evidence": "4",
    "Risk": "1",
    "Decision": "2",
}
REGIONS = {
    "Goal": {"x": 0, "y": 0, "width": 720, "height": 360},
    "System Structure": {"x": 760, "y": 0, "width": 920, "height": 360},
    "Current Work": {"x": 0, "y": 420, "width": 1680, "height": 420},
    "Evidence": {"x": 0, "y": 900, "width": 820, "height": 420},
    "Risks & Decisions": {"x": 860, "y": 900, "width": 820, "height": 420},
}
CARD_REGION = {
    "Goal": "Goal",
    "Module": "System Structure",
    "Task": "Current Work",
    "Evidence": "Evidence",
    "Risk": "Risks & Decisions",
    "Decision": "Risks & Decisions",
}
TASK_LANE_X = {
    "Proposed": 40,
    "Active": 360,
    "Verify": 680,
    "Blocked": 1000,
    "Done": 1320,
}


@dataclass(frozen=True)
class Card:
    node: dict[str, Any]
    kind: str
    title: str
    state: str | None = None

    @property
    def id(self) -> str:
        return str(self.node["id"])


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def template_path(name: str) -> Path:
    return skill_root() / "templates" / name


def reference_path(name: str) -> Path:
    return skill_root() / "references" / name


def resolve_project(arg: str | Path) -> Path:
    path = Path(arg).expanduser().resolve()
    if path.suffix == ".canvas":
        return path.parent
    return path


def resolve_canvas(arg: str | Path) -> Path:
    path = Path(arg).expanduser().resolve()
    if path.suffix == ".canvas":
        return path
    return path / "Project.canvas"


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"FAIL: missing canvas: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"FAIL: invalid JSON at {path}:{exc.lineno}:{exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        raise SystemExit("FAIL: top-level canvas JSON must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def nodes(data: dict[str, Any]) -> list[dict[str, Any]]:
    value = data.setdefault("nodes", [])
    if not isinstance(value, list):
        raise SystemExit("FAIL: top-level nodes must be an array")
    return value


def edges(data: dict[str, Any]) -> list[dict[str, Any]]:
    value = data.setdefault("edges", [])
    if not isinstance(value, list):
        raise SystemExit("FAIL: top-level edges must be an array")
    return value


def existing_ids(data: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for node in nodes(data):
        if isinstance(node, dict) and isinstance(node.get("id"), str):
            ids.add(node["id"])
    for edge in edges(data):
        if isinstance(edge, dict) and isinstance(edge.get("id"), str):
            ids.add(edge["id"])
    return ids


def new_id(data: dict[str, Any]) -> str:
    used = existing_ids(data)
    while True:
        value = secrets.token_hex(8)
        if value not in used:
            return value


def parse_card(node: dict[str, Any]) -> Card | None:
    if node.get("type") != "text" or not isinstance(node.get("text"), str):
        return None
    text = node["text"]
    match = CARD_PREFIX_RE.search(text)
    if not match:
        return None
    state_match = STATE_RE.search(text)
    return Card(node=node, kind=match.group(1), title=match.group(2).strip(), state=state_match.group(1) if state_match else None)


def all_cards(data: dict[str, Any]) -> list[Card]:
    out: list[Card] = []
    for node in nodes(data):
        if isinstance(node, dict):
            card = parse_card(node)
            if card:
                out.append(card)
    return out


def card_summary(card: Card) -> str:
    state = f" [{card.state}]" if card.state else ""
    return f"{card.id} {card.kind}:{card.title}{state}"


def find_card(data: dict[str, Any], query: str, kind: str | None = None) -> Card:
    cards = all_cards(data)
    if kind:
        cards = [c for c in cards if c.kind == kind]
    exact_id = [c for c in cards if c.id == query]
    if len(exact_id) == 1:
        return exact_id[0]
    exact_title = [c for c in cards if c.title.lower() == query.lower()]
    if len(exact_title) == 1:
        return exact_title[0]
    partial = [c for c in cards if query.lower() in c.title.lower()]
    if len(partial) == 1:
        return partial[0]
    if not exact_id and not exact_title and not partial:
        raise SystemExit(f"FAIL: no matching card for {query!r}" + (f" kind={kind}" if kind else ""))
    candidates = exact_id or exact_title or partial
    listing = "\n".join("  " + card_summary(c) for c in candidates[:10])
    raise SystemExit(f"FAIL: ambiguous card query {query!r}:\n{listing}")


def parse_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        m = FIELD_RE.match(line.strip())
        if m:
            fields[m.group(1)] = m.group(2)
    return fields


def is_noneish(value: str | None) -> bool:
    if value is None:
        return True
    stripped = value.strip().lower()
    return stripped in {"", "none", "n/a", "unknown"} or (stripped.startswith("<") and stripped.endswith(">"))


def evidence_is_concrete(card: Card) -> bool:
    if card.kind != "Evidence":
        return False
    fields = parse_fields(str(card.node.get("text", "")))
    for key in ("commit", "test", "build", "manual", "artifact"):
        if not is_noneish(fields.get(key)):
            return True
    return False


def replace_field(text: str, field: str, value: str) -> str:
    lines = text.splitlines()
    prefix = f"{field}:"
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = f"{prefix} {value}"
            return "\n".join(lines)
    lines.append(f"{prefix} {value}")
    return "\n".join(lines)


def region_for(kind: str) -> str:
    return CARD_REGION.get(kind, "Current Work")


def next_position(data: dict[str, Any], kind: str, state: str | None = None, exclude_id: str | None = None) -> tuple[int, int, int, int]:
    # Width/height are deliberately compact. The map should be readable at a glance.
    if kind == "Task":
        lane = state or "Proposed"
        x = TASK_LANE_X.get(lane, TASK_LANE_X["Proposed"])
        existing = [c for c in all_cards(data) if c.kind == "Task" and c.state == lane and c.id != exclude_id]
        return x, 500 + 240 * len(existing), 280, 200
    if kind == "Goal":
        existing = [c for c in all_cards(data) if c.kind == "Goal" and c.id != exclude_id]
        return 40, 60 + 220 * len(existing), 620, 200
    if kind == "Module":
        existing = [c for c in all_cards(data) if c.kind == "Module" and c.id != exclude_id]
        col = len(existing) % 2
        row = len(existing) // 2
        return 800 + col * 430, 60 + row * 220, 380, 180
    if kind == "Evidence":
        existing = [c for c in all_cards(data) if c.kind == "Evidence" and c.id != exclude_id]
        col = len(existing) % 2
        row = len(existing) // 2
        return 40 + col * 400, 980 + row * 220, 360, 180
    if kind in {"Risk", "Decision"}:
        existing = [c for c in all_cards(data) if c.kind == kind and c.id != exclude_id]
        base_x = 900 if kind == "Risk" else 1300
        return base_x, 980 + 220 * len(existing), 360, 180
    return 40, 500, 320, 180


def make_card_text(kind: str, title: str, **kwargs: str) -> str:
    if kind == "Goal":
        return "\n".join([
            f"Goal: {title}",
            f"Success: {kwargs.get('success', '<observable success condition>')}",
            f"Constraints: {kwargs.get('constraints', '<hard constraints>')}",
        ])
    if kind == "Module":
        return "\n".join([
            f"Module: {title}",
            f"Role: {kwargs.get('role', '<what it owns>')}",
            f"Inputs: {kwargs.get('inputs', '<sources>')}",
            f"Outputs: {kwargs.get('outputs', '<interfaces>')}",
        ])
    if kind == "Task":
        return "\n".join([
            f"Task: {title}",
            f"State: {kwargs.get('state', 'Proposed')}",
            f"Owner: {kwargs.get('owner', 'Hermes')}",
            f"Depends: {kwargs.get('depends', 'none')}",
            f"Evidence: {kwargs.get('evidence', 'none')}",
            f"Risk: {kwargs.get('risk', 'none')}",
        ])
    if kind == "Evidence":
        return "\n".join([
            f"Evidence: {title}",
            f"commit: {kwargs.get('commit', 'none')}",
            f"test: {kwargs.get('test', 'none')}",
            f"build: {kwargs.get('build', 'none')}",
            f"manual: {kwargs.get('manual', 'none')}",
            f"artifact: {kwargs.get('artifact', 'none')}",
        ])
    if kind == "Risk":
        return "\n".join([
            f"Risk: {title}",
            f"Impact: {kwargs.get('impact', '<what breaks>')}",
            f"Mitigation: {kwargs.get('mitigation', '<next check>')}",
            f"Status: {kwargs.get('status', 'Open')}",
        ])
    if kind == "Decision":
        return "\n".join([
            f"Decision: {title}",
            f"Rationale: {kwargs.get('rationale', '<why>')}",
            f"Impact: {kwargs.get('impact', '<what changes>')}",
            f"Evidence: {kwargs.get('evidence', 'none')}",
        ])
    raise ValueError(kind)


def add_text_card(data: dict[str, Any], kind: str, title: str, **kwargs: str) -> Card:
    state = kwargs.get("state") if kind == "Task" else None
    x, y, width, height = next_position(data, kind, state)
    node = {
        "id": new_id(data),
        "type": "text",
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "color": STATE_COLORS.get(state or "", KIND_COLORS.get(kind, "6")),
        "text": make_card_text(kind, title, **kwargs),
    }
    nodes(data).append(node)
    card = parse_card(node)
    assert card is not None
    return card


def add_edge(data: dict[str, Any], from_id: str, to_id: str, label: str, color: str | None = None) -> dict[str, Any]:
    for edge in edges(data):
        if edge.get("fromNode") == from_id and edge.get("toNode") == to_id and edge.get("label") == label:
            return edge
    edge: dict[str, Any] = {
        "id": new_id(data),
        "fromNode": from_id,
        "toNode": to_id,
        "toEnd": "arrow",
        "label": label,
    }
    if color:
        edge["color"] = color
    edges(data).append(edge)
    return edge


def validate_data(data: dict[str, Any], strict: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    ns = data.get("nodes")
    es = data.get("edges")
    if not isinstance(ns, list):
        errors.append("top-level nodes must be an array")
        ns = []
    if not isinstance(es, list):
        errors.append("top-level edges must be an array")
        es = []

    node_ids: list[str] = []
    edge_ids: list[str] = []
    cards: list[Card] = []
    card_labels: list[str] = []

    for idx, raw in enumerate(ns):
        if not isinstance(raw, dict):
            errors.append(f"nodes[{idx}] is not an object")
            continue
        node = raw
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"nodes[{idx}] missing string id")
            continue
        node_ids.append(node_id)
        if not HEX16_RE.match(node_id):
            warnings.append(f"node {node_id} id is not 16 lowercase hex chars")
        typ = node.get("type")
        if typ not in VALID_NODE_TYPES:
            errors.append(f"node {node_id} invalid type {typ!r}")
            continue
        for key in ("x", "y", "width", "height"):
            if not isinstance(node.get(key), int):
                errors.append(f"node {node_id} missing integer {key}")
        if typ == "text":
            text = node.get("text")
            if not isinstance(text, str):
                errors.append(f"text node {node_id} missing string text")
            else:
                card = parse_card(node)
                if card:
                    cards.append(card)
                    card_labels.append(f"{card.kind}:{card.title}")
                    if card.kind == "Task" and card.state not in VALID_STATES:
                        warnings.append(f"task {node_id} has no valid State line")
                    if len([ln for ln in text.splitlines() if ln.strip()]) > 8:
                        warnings.append(f"card {node_id} is longer than 8 lines; split it")
        elif typ == "file" and not isinstance(node.get("file"), str):
            errors.append(f"file node {node_id} missing string file")
        elif typ == "link" and not isinstance(node.get("url"), str):
            errors.append(f"link node {node_id} missing string url")
        elif typ == "group" and "label" in node and not isinstance(node.get("label"), str):
            errors.append(f"group node {node_id} label must be string when present")

    node_id_set = set(node_ids)
    for dup, count in Counter(node_ids).items():
        if count > 1:
            errors.append(f"duplicate node id {dup}")

    for idx, raw in enumerate(es):
        if not isinstance(raw, dict):
            errors.append(f"edges[{idx}] is not an object")
            continue
        edge = raw
        edge_id = edge.get("id")
        if not isinstance(edge_id, str) or not edge_id:
            errors.append(f"edges[{idx}] missing string id")
            continue
        edge_ids.append(edge_id)
        if not HEX16_RE.match(edge_id):
            warnings.append(f"edge {edge_id} id is not 16 lowercase hex chars")
        for endpoint in ("fromNode", "toNode"):
            value = edge.get(endpoint)
            if value not in node_id_set:
                errors.append(f"edge {edge_id} {endpoint} references missing node {value!r}")
        for side in ("fromSide", "toSide"):
            if side in edge and edge[side] not in VALID_SIDES:
                errors.append(f"edge {edge_id} invalid {side} {edge[side]!r}")
        for end in ("fromEnd", "toEnd"):
            if end in edge and edge[end] not in VALID_ENDS:
                errors.append(f"edge {edge_id} invalid {end} {edge[end]!r}")

    for dup, count in Counter(edge_ids).items():
        if count > 1:
            errors.append(f"duplicate edge id {dup}")
    for dup in set(node_ids).intersection(edge_ids):
        errors.append(f"id reused by node and edge {dup}")
    for dup, count in Counter(card_labels).items():
        if count > 1:
            warnings.append(f"duplicate card label {dup}")

    concrete_evidence_ids = {c.id for c in cards if c.kind == "Evidence" and evidence_is_concrete(c)}
    concrete_evidence_titles = {c.title.strip().lower() for c in cards if c.kind == "Evidence" and evidence_is_concrete(c)}
    outgoing_to_concrete_evidence: dict[str, int] = defaultdict(int)
    for edge in es:
        if isinstance(edge, dict) and edge.get("toNode") in concrete_evidence_ids:
            outgoing_to_concrete_evidence[str(edge.get("fromNode"))] += 1

    for card in cards:
        if card.kind != "Task":
            continue
        fields = parse_fields(str(card.node.get("text", "")))
        evidence_field = fields.get("Evidence", "none").strip().lower()
        has_named_evidence = evidence_field in concrete_evidence_titles
        has_evidence = has_named_evidence or outgoing_to_concrete_evidence.get(card.id, 0) > 0
        if card.state in {"Verify", "Done"} and not has_evidence:
            msg = f"task {card.id} state={card.state} lacks concrete evidence"
            (errors if strict else warnings).append(msg)
        if card.state == "Done" and not has_evidence:
            errors.append(f"Done task {card.id} has no concrete evidence")

    return errors, warnings


def cmd_init(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    project.mkdir(parents=True, exist_ok=True)
    readme = project / "README.md"
    canvas = project / "Project.canvas"
    agents_dir = project / ".agents"
    protocol = agents_dir / "canvas-protocol.md"

    changed: list[str] = []
    if args.force or not readme.exists():
        content = template_path("README.md").read_text(encoding="utf-8")
        content = content.replace("# Project Name", f"# {args.name or project.name}")
        if args.goal:
            content = content.replace("One sentence describing the project objective and success condition.", args.goal)
        readme.write_text(content, encoding="utf-8")
        changed.append(str(readme))
    if args.force or not canvas.exists():
        shutil.copyfile(template_path("Project.canvas"), canvas)
        changed.append(str(canvas))
    if args.agent_rules and (args.force or not protocol.exists()):
        agents_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(reference_path("canvas-protocol.md"), protocol)
        changed.append(str(protocol))

    if args.name or args.goal:
        data = read_json(canvas)
        goal_cards = [c for c in all_cards(data) if c.kind == "Goal"]
        if goal_cards:
            card = goal_cards[0]
            text = str(card.node.get("text", ""))
            if args.goal:
                text = replace_field(text, "Goal", args.goal)
            card.node["text"] = text
            write_json(canvas, data)
            if str(canvas) not in changed:
                changed.append(str(canvas))

    errors, warnings = validate_data(read_json(canvas), strict=True)
    if errors:
        for msg in errors:
            print(f"FAIL: {msg}", file=sys.stderr)
        return 1
    for msg in warnings:
        print(f"WARN: {msg}")
    print("OK: initialized Project Canvas OS")
    for path in changed:
        print(f"  {path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    path = resolve_canvas(args.project)
    data = read_json(path)
    errors, warnings = validate_data(data, strict=args.strict)
    for msg in warnings:
        print(f"WARN: {msg}")
    if errors:
        for msg in errors:
            print(f"FAIL: {msg}", file=sys.stderr)
        return 1
    print(f"OK: {path} nodes={len(nodes(data))} edges={len(edges(data))} warnings={len(warnings)}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    path = resolve_canvas(args.project)
    data = read_json(path)
    cards = all_cards(data)
    by_kind = Counter(c.kind for c in cards)
    by_state = Counter(c.state for c in cards if c.kind == "Task" and c.state)
    errors, warnings = validate_data(data, strict=False)
    print(f"Canvas: {path}")
    print("Cards: " + ", ".join(f"{k}={by_kind[k]}" for k in sorted(by_kind)) if by_kind else "Cards: none")
    print("Tasks: " + ", ".join(f"{s}={by_state[s]}" for s in ["Proposed", "Active", "Verify", "Blocked", "Done"] if by_state[s]) if by_state else "Tasks: none")
    for state in ["Active", "Verify", "Blocked"]:
        selected = [c for c in cards if c.kind == "Task" and c.state == state]
        if selected:
            print(f"\n{state}:")
            for card in selected:
                fields = parse_fields(str(card.node.get("text", "")))
                ev = fields.get("Evidence", "none")
                risk = fields.get("Risk", "none")
                print(f"  - {card.title} ({card.id}) evidence={ev} risk={risk}")
    if warnings:
        print("\nWarnings:")
        for msg in warnings:
            print(f"  - {msg}")
    if errors:
        print("\nErrors:")
        for msg in errors:
            print(f"  - {msg}")
        return 1
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    data = read_json(resolve_canvas(args.project))
    cards = all_cards(data)
    if args.kind:
        cards = [c for c in cards if c.kind == args.kind]
    if args.state:
        cards = [c for c in cards if c.state == args.state]
    for card in cards:
        print(card_summary(card))
    return 0


def save_after_change(project: str, data: dict[str, Any], strict: bool = True) -> int:
    path = resolve_canvas(project)
    errors, warnings = validate_data(data, strict=strict)
    if errors:
        for msg in errors:
            print(f"FAIL: {msg}", file=sys.stderr)
        return 1
    write_json(path, data)
    for msg in warnings:
        print(f"WARN: {msg}")
    print(f"OK: updated {path}")
    return 0


def cmd_add_goal(args: argparse.Namespace) -> int:
    data = read_json(resolve_canvas(args.project))
    card = add_text_card(data, "Goal", args.title, success=args.success, constraints=args.constraints)
    print(card_summary(card))
    return save_after_change(args.project, data)


def cmd_add_module(args: argparse.Namespace) -> int:
    data = read_json(resolve_canvas(args.project))
    card = add_text_card(data, "Module", args.title, role=args.role, inputs=args.inputs, outputs=args.outputs)
    print(card_summary(card))
    return save_after_change(args.project, data)


def cmd_add_task(args: argparse.Namespace) -> int:
    if args.state not in VALID_STATES - {"Done"}:
        raise SystemExit("FAIL: add-task may not create Done tasks")
    data = read_json(resolve_canvas(args.project))
    card = add_text_card(data, "Task", args.title, state=args.state, owner=args.owner, depends=args.depends or "none", risk=args.risk or "none")
    if args.module:
        module = find_card(data, args.module, kind="Module")
        add_edge(data, module.id, card.id, "enables", color="5")
    for dep_query in args.depends_card or []:
        dep = find_card(data, dep_query)
        add_edge(data, dep.id, card.id, "depends", color="6")
    if args.risk_card:
        risk = find_card(data, args.risk_card, kind="Risk")
        add_edge(data, risk.id, card.id, "may block", color="1")
    print(card_summary(card))
    return save_after_change(args.project, data)


def cmd_add_evidence(args: argparse.Namespace) -> int:
    data = read_json(resolve_canvas(args.project))
    card = add_text_card(data, "Evidence", args.title, commit=args.commit, test=args.test, build=args.build, manual=args.manual, artifact=args.artifact)
    if args.task:
        task = find_card(data, args.task, kind="Task")
        add_edge(data, task.id, card.id, "evidence", color="4")
        task.node["text"] = replace_field(str(task.node.get("text", "")), "Evidence", card.title)
        if args.set_task_verify:
            task.node["text"] = replace_field(str(task.node.get("text", "")), "State", "Verify")
            task.node["color"] = STATE_COLORS["Verify"]
            x, y, w, h = next_position(data, "Task", "Verify", exclude_id=task.id)
            task.node.update({"x": x, "y": y, "width": w, "height": h})
    print(card_summary(card))
    return save_after_change(args.project, data)


def cmd_add_risk(args: argparse.Namespace) -> int:
    data = read_json(resolve_canvas(args.project))
    card = add_text_card(data, "Risk", args.title, impact=args.impact, mitigation=args.mitigation, status=args.status)
    if args.task:
        task = find_card(data, args.task, kind="Task")
        add_edge(data, card.id, task.id, "may block", color="1")
        task.node["text"] = replace_field(str(task.node.get("text", "")), "Risk", card.title)
    print(card_summary(card))
    return save_after_change(args.project, data, strict=False)


def cmd_add_decision(args: argparse.Namespace) -> int:
    data = read_json(resolve_canvas(args.project))
    card = add_text_card(data, "Decision", args.title, rationale=args.rationale, impact=args.impact, evidence=args.evidence)
    if args.evidence_card:
        evidence = find_card(data, args.evidence_card, kind="Evidence")
        add_edge(data, evidence.id, card.id, "supports", color="4")
    print(card_summary(card))
    return save_after_change(args.project, data)


def cmd_link(args: argparse.Namespace) -> int:
    data = read_json(resolve_canvas(args.project))
    src = find_card(data, args.from_card)
    dst = find_card(data, args.to_card)
    edge = add_edge(data, src.id, dst.id, args.label, color=args.color)
    print(f"{edge['id']} {src.kind}:{src.title} -> {dst.kind}:{dst.title} label={args.label}")
    return save_after_change(args.project, data)


def task_has_evidence(data: dict[str, Any], task: Card, evidence_query: str | None = None) -> bool:
    if evidence_query:
        evidence = find_card(data, evidence_query, kind="Evidence")
        if not evidence_is_concrete(evidence):
            raise SystemExit(f"FAIL: evidence card {evidence.id} is not concrete")
        add_edge(data, task.id, evidence.id, "evidence", color="4")
        task.node["text"] = replace_field(str(task.node.get("text", "")), "Evidence", evidence.title)
        return True
    fields = parse_fields(str(task.node.get("text", "")))
    evidence_field = fields.get("Evidence", "none").strip().lower()
    concrete = [c for c in all_cards(data) if c.kind == "Evidence" and evidence_is_concrete(c)]
    if evidence_field in {c.title.strip().lower() for c in concrete}:
        return True
    evidence_ids = {c.id for c in concrete}
    return any(edge.get("fromNode") == task.id and edge.get("toNode") in evidence_ids for edge in edges(data))


def cmd_transition(args: argparse.Namespace) -> int:
    if args.state not in VALID_STATES:
        raise SystemExit(f"FAIL: invalid state {args.state}")
    data = read_json(resolve_canvas(args.project))
    task = find_card(data, args.task, kind="Task")
    has_evidence = task_has_evidence(data, task, args.evidence)
    if args.state == "Done" and (not has_evidence or not args.gate):
        raise SystemExit("FAIL: Done requires evidence and --gate <human/script confirmation>")
    old = task.state
    task.node["text"] = replace_field(str(task.node.get("text", "")), "State", args.state)
    task.node["color"] = STATE_COLORS[args.state]
    x, y, w, h = next_position(data, "Task", args.state, exclude_id=task.id)
    task.node.update({"x": x, "y": y, "width": w, "height": h})
    if args.gate:
        task.node["text"] = replace_field(str(task.node.get("text", "")), "Gate", args.gate)
    print(f"{task.id} Task:{task.title} {old}->{args.state}")
    return save_after_change(args.project, data, strict=args.state in {"Verify", "Done"})


def iter_markdown_docs(project: Path) -> list[Path]:
    docs: list[Path] = []
    for path in project.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in MARKDOWN_EXTS:
            continue
        rel = path.relative_to(project)
        if any(part in IGNORED_DOC_PARTS for part in rel.parts):
            continue
        docs.append(rel)
    return sorted(docs, key=lambda p: p.as_posix().lower())


def classify_doc(rel: Path) -> str:
    value = rel.as_posix()
    if value == "README.md":
        return "contract"
    if DOC_STATE_RE.search(value):
        return "state"
    if DOC_KNOWLEDGE_RE.search(value):
        return "knowledge"
    return "other"


def canvas_text_index(data: dict[str, Any]) -> str:
    chunks: list[str] = []
    for node in nodes(data):
        if not isinstance(node, dict):
            continue
        for key in ("text", "label", "file", "url"):
            value = node.get(key)
            if isinstance(value, str):
                chunks.append(value)
    for edge in edges(data):
        if isinstance(edge, dict) and isinstance(edge.get("label"), str):
            chunks.append(str(edge["label"]))
    return "\n".join(chunks)


def project_text_index(project: Path, canvas_path: Path) -> str:
    chunks: list[str] = []
    readme = project / "README.md"
    if readme.exists():
        try:
            chunks.append(readme.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            pass
    if canvas_path.exists():
        chunks.append(canvas_text_index(read_json(canvas_path)))
    return "\n".join(chunks)


def doc_is_referenced(rel: Path, index: str) -> bool:
    posix = rel.as_posix()
    stem = rel.stem
    return posix in index or rel.name in index or (len(stem) >= 4 and stem in index)


def audit_documents(project: Path, canvas_path: Path, strict: bool = False, show_all: bool = False) -> int:
    docs = iter_markdown_docs(project)
    if not docs:
        print("WARN: no Markdown project docs found")
        return 1 if strict else 0

    by_kind = Counter(classify_doc(rel) for rel in docs)
    print("Docs: " + ", ".join(f"{kind}={by_kind[kind]}" for kind in sorted(by_kind)))

    index = project_text_index(project, canvas_path)
    rc = 0
    state_docs: list[Path] = []
    stale_docs: list[Path] = []
    unreferenced_key_docs: list[Path] = []

    for rel in docs:
        path = project / rel
        kind = classify_doc(rel)
        text = ""
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            pass
        if kind == "state":
            state_docs.append(rel)
        if STALE_DOC_RE.search(text):
            stale_docs.append(rel)
        if kind in {"knowledge", "other"} and rel.as_posix() != "README.md" and not doc_is_referenced(rel, index):
            # This is intentionally a warning. Some repos have many reference docs.
            unreferenced_key_docs.append(rel)

    if show_all:
        for kind in ("contract", "knowledge", "other", "state"):
            selected = [rel for rel in docs if classify_doc(rel) == kind]
            if selected:
                print(f"\n{kind} docs:")
                for rel in selected[:100]:
                    print(f"  - {rel.as_posix()}")

    if state_docs:
        print("WARN: state/progress docs exist; keep only if they are an explicit canonical runbook/status artifact, otherwise move live state to Project.canvas:")
        for rel in state_docs[:50]:
            print(f"  - {rel.as_posix()}")
    if stale_docs:
        print("WARN: docs contain stale/deprecated markers; update, archive, or point to the canonical replacement:")
        for rel in stale_docs[:50]:
            print(f"  - {rel.as_posix()}")
        if strict:
            rc = 1
    if unreferenced_key_docs:
        print("WARN: knowledge docs not referenced from README.md or Project.canvas; consider linking key docs so agents can discover them:")
        for rel in unreferenced_key_docs[:50]:
            print(f"  - {rel.as_posix()}")

    return rc


def cmd_audit(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    canvas_path = resolve_canvas(project)
    rc = 0
    if not canvas_path.exists():
        print(f"FAIL: missing {canvas_path}", file=sys.stderr)
        rc = 1
    for required in [project / "README.md", canvas_path]:
        if required.exists():
            print(f"OK: {required}")
    doc_rc = audit_documents(project, canvas_path, strict=args.docs_strict, show_all=args.list_docs)
    if doc_rc:
        rc = 1
    if canvas_path.exists():
        errors, warnings = validate_data(read_json(canvas_path), strict=args.strict)
        for msg in warnings:
            print(f"WARN: {msg}")
        for msg in errors:
            print(f"FAIL: {msg}", file=sys.stderr)
        if errors:
            rc = 1
    return rc


def cmd_docs(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    return audit_documents(project, resolve_canvas(project), strict=args.strict, show_all=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate README.md + Project.canvas projects")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create README.md, Project.canvas, and optional .agents protocol")
    p.add_argument("project")
    p.add_argument("--name")
    p.add_argument("--goal")
    p.add_argument("--force", action="store_true")
    p.add_argument("--agent-rules", action="store_true", default=True)
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("validate", help="validate Project.canvas")
    p.add_argument("project")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("status", help="summarize cards and active/verify/blocked tasks")
    p.add_argument("project")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("list", help="list cards")
    p.add_argument("project")
    p.add_argument("--kind", choices=sorted(CARD_KINDS))
    p.add_argument("--state", choices=sorted(VALID_STATES))
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("add-goal")
    p.add_argument("project")
    p.add_argument("--title", required=True)
    p.add_argument("--success", default="<observable success condition>")
    p.add_argument("--constraints", default="<hard constraints>")
    p.set_defaults(func=cmd_add_goal)

    p = sub.add_parser("add-module")
    p.add_argument("project")
    p.add_argument("--title", required=True)
    p.add_argument("--role", default="<what it owns>")
    p.add_argument("--inputs", default="<sources>")
    p.add_argument("--outputs", default="<interfaces>")
    p.set_defaults(func=cmd_add_module)

    p = sub.add_parser("add-task")
    p.add_argument("project")
    p.add_argument("--title", required=True)
    p.add_argument("--state", choices=sorted(VALID_STATES - {"Done"}), default="Proposed")
    p.add_argument("--owner", default="Hermes")
    p.add_argument("--depends", default="none")
    p.add_argument("--depends-card", action="append")
    p.add_argument("--module")
    p.add_argument("--risk", default="none")
    p.add_argument("--risk-card")
    p.set_defaults(func=cmd_add_task)

    p = sub.add_parser("add-evidence")
    p.add_argument("project")
    p.add_argument("--title", required=True)
    p.add_argument("--task")
    p.add_argument("--commit", default="none")
    p.add_argument("--test", default="none")
    p.add_argument("--build", default="none")
    p.add_argument("--manual", default="none")
    p.add_argument("--artifact", default="none")
    p.add_argument("--set-task-verify", action="store_true")
    p.set_defaults(func=cmd_add_evidence)

    p = sub.add_parser("add-risk")
    p.add_argument("project")
    p.add_argument("--title", required=True)
    p.add_argument("--task")
    p.add_argument("--impact", default="<what breaks>")
    p.add_argument("--mitigation", default="<next check>")
    p.add_argument("--status", default="Open")
    p.set_defaults(func=cmd_add_risk)

    p = sub.add_parser("add-decision")
    p.add_argument("project")
    p.add_argument("--title", required=True)
    p.add_argument("--rationale", default="<why>")
    p.add_argument("--impact", default="<what changes>")
    p.add_argument("--evidence", default="none")
    p.add_argument("--evidence-card")
    p.set_defaults(func=cmd_add_decision)

    p = sub.add_parser("link")
    p.add_argument("project")
    p.add_argument("--from", dest="from_card", required=True)
    p.add_argument("--to", dest="to_card", required=True)
    p.add_argument("--label", required=True)
    p.add_argument("--color")
    p.set_defaults(func=cmd_link)

    p = sub.add_parser("transition")
    p.add_argument("project")
    p.add_argument("--task", required=True)
    p.add_argument("--state", choices=sorted(VALID_STATES), required=True)
    p.add_argument("--evidence")
    p.add_argument("--gate")
    p.set_defaults(func=cmd_transition)

    p = sub.add_parser("docs", help="audit and list project knowledge documents")
    p.add_argument("project")
    p.add_argument("--strict", action="store_true", help="fail when stale/deprecated document markers are found")
    p.set_defaults(func=cmd_docs)

    p = sub.add_parser("audit")
    p.add_argument("project")
    p.add_argument("--strict", action="store_true", help="strict Canvas validation")
    p.add_argument("--docs-strict", action="store_true", help="fail when stale/deprecated document markers are found")
    p.add_argument("--list-docs", action="store_true", help="print classified Markdown document inventory")
    p.set_defaults(func=cmd_audit)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
