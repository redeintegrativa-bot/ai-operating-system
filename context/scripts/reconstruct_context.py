#!/usr/bin/env python3
"""
Context Reconstruction Script for AI Operating System

Scans project structure, analyzes git state, reads key configuration files,
and generates context files for agent prompt injection.

Usage:
    python reconstruct_context.py [--quiet] [--project-root PATH] [--output-dir PATH]
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".tox", ".mypy_cache", ".pytest_cache",
    "egg-info", ".eggs", "context/generated",
}

CONFIG_FILES = [
    "package.json", "requirements.txt", "pyproject.toml",
    "setup.py", "setup.cfg", "Cargo.toml", "go.mod",
    "docker-compose.yml", "Makefile", ".env.example",
]

DOC_FILES = [
    "README.md", "CONTRIBUTING.md", "LICENSE", ".gitignore",
]


def log(message: str, quiet: bool = False) -> None:
    if not quiet:
        print(message, file=sys.stderr)


def run_git(args: list[str], root: Path, timeout: int = 10) -> str | None:
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True, cwd=root, timeout=timeout,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
        return None


def scan_project_structure(root: Path) -> dict[str, Any]:
    dirs = []
    files = []
    lines_by_ext: Counter[str] = Counter()
    files_by_ext: Counter[str] = Counter()

    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        parts = rel.parts
        if any(p in EXCLUDE_DIRS for p in parts):
            continue
        if any(p.startswith(".") and p not in (".gitkeep", ".env.example", ".gitignore") for p in parts[:-1]):
            continue

        if path.is_dir():
            dirs.append(str(rel))
        elif path.is_file():
            files.append(str(rel))
            ext = path.suffix or "(no ext)"
            files_by_ext[ext] += 1
            try:
                if path.stat().st_size < 1_000_000:
                    lines = path.read_text(errors="replace").count("\n") + 1
                    lines_by_ext[ext] += lines
            except (OSError, PermissionError):
                pass

    components = {
        "agents": any((root / d).exists() for d in ["agents", "src/agents", "lib/agents"]),
        "scripts": (root / "scripts").exists(),
        "configs": (root / "config").exists(),
        "docs": (root / "docs").exists(),
        "tests": (root / "tests").exists(),
        "src": (root / "src").exists(),
        "context": (root / "context").exists(),
    }

    return {
        "directories": dirs,
        "files": files,
        "total_files": len(files),
        "total_dirs": len(dirs),
        "files_by_extension": dict(sorted(files_by_ext.items(), key=lambda x: -x[1])),
        "lines_by_extension": dict(sorted(lines_by_ext.items(), key=lambda x: -x[1])),
        "total_lines": sum(lines_by_ext.values()),
        "components": components,
    }


def analyze_git_state(root: Path) -> dict[str, Any]:
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], root) or "unknown"
    commit = run_git(["rev-parse", "--short", "HEAD"], root) or "unknown"
    is_dirty = run_git(["status", "--porcelain"], root) or ""
    remotes = run_git(["remote", "-v"], root) or ""

    raw_commits = run_git(
        ["log", "--oneline", "--decorate", "-10", "--format=%h|%s|%ai|%an"], root
    ) or ""
    commits = []
    for line in raw_commits.splitlines():
        if "|" in line:
            parts = line.split("|", 3)
            commits.append({
                "hash": parts[0] if len(parts) > 0 else "",
                "message": parts[1] if len(parts) > 1 else "",
                "date": parts[2] if len(parts) > 2 else "",
                "author": parts[3] if len(parts) > 3 else "",
            })

    remote_lines = remotes.splitlines() if remotes else []
    remote_list = []
    for line in remote_lines:
        if line.strip():
            remote_list.append(line.strip())

    return {
        "branch": branch,
        "commit": commit,
        "is_dirty": bool(is_dirty.strip()),
        "uncommitted_files": [l.strip().split()[-1] for l in is_dirty.splitlines() if l.strip()],
        "remotes": remote_list,
        "last_commits": commits,
    }


def read_config_files(root: Path) -> dict[str, Any]:
    configs = {}

    for fname in CONFIG_FILES:
        fpath = root / fname
        if fpath.exists():
            try:
                content = fpath.read_text(errors="replace")
                if fname.endswith(".json"):
                    configs[fname] = {"type": "json", "data": json.loads(content)}
                else:
                    configs[fname] = {"type": "text", "data": content[:5000]}
            except (json.JSONDecodeError, OSError) as e:
                configs[fname] = {"type": "error", "error": str(e)}

    config_dir = root / "config"
    if config_dir.is_dir():
        for f in sorted(config_dir.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                try:
                    content = f.read_text(errors="replace")
                    configs[f"config/{f.name}"] = {"type": "text", "data": content[:3000]}
                except OSError:
                    configs[f"config/{f.name}"] = {"type": "error", "error": "unreadable"}

    for fname in DOC_FILES:
        fpath = root / fname
        if fpath.exists():
            try:
                configs[fname] = {"type": "markdown", "data": fpath.read_text(errors="replace")[:5000]}
            except OSError:
                configs[fname] = {"type": "error", "error": "unreadable"}

    return configs


def generate_project_snapshot(
    structure: dict, git_state: dict, configs: dict, root: Path
) -> dict[str, Any]:
    return {
        "metadata": {
            "project_name": root.name,
            "project_root": str(root),
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        "structure": {
            "total_files": structure["total_files"],
            "total_dirs": structure["total_dirs"],
            "total_lines": structure["total_lines"],
            "files_by_extension": structure["files_by_extension"],
            "lines_by_extension": structure["lines_by_extension"],
            "components": structure["components"],
        },
        "git": git_state,
        "config_files_loaded": list(configs.keys()),
    }


def generate_context_summary(
    structure: dict, git_state: dict, configs: dict, root: Path
) -> str:
    lines = [
        "# Project Context Summary",
        "",
        f"**Generated**: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"**Project**: {root.name}",
        "",
        "## Git State",
        "",
        f"- Branch: `{git_state['branch']}`",
        f"- Commit: `{git_state['commit']}`",
        f"- Dirty: {git_state['is_dirty']}",
    ]

    if git_state["last_commits"]:
        lines.extend(["", "### Last Commits", ""])
        for c in git_state["last_commits"][:10]:
            lines.append(f"- `{c['hash']}` {c['message']} ({c['date'][:10]}, {c['author']})")

    if git_state["uncommitted_files"]:
        lines.extend(["", "### Uncommitted Changes", ""])
        for f in git_state["uncommitted_files"][:20]:
            lines.append(f"- `{f}`")

    lines.extend([
        "",
        "## Project Structure",
        "",
        f"- Total files: **{structure['total_files']}**",
        f"- Total directories: **{structure['total_dirs']}**",
        f"- Total lines of code: **{structure['total_lines']}**",
        "",
        "### Files by Type",
        "",
        "| Extension | Count | Lines |",
        "|-----------|-------|-------|",
    ])

    all_exts = set(structure["files_by_extension"]) | set(structure["lines_by_extension"])
    for ext in sorted(all_exts, key=lambda e: -structure["files_by_extension"].get(e, 0)):
        count = structure["files_by_extension"].get(ext, 0)
        loc = structure["lines_by_extension"].get(ext, 0)
        lines.append(f"| `{ext}` | {count} | {loc} |")

    lines.extend(["", "### Key Components", ""])
    for comp, exists in structure["components"].items():
        status = "present" if exists else "absent"
        lines.append(f"- {comp}: **{status}**")

    if configs:
        lines.extend(["", "## Configuration Files", ""])
        for fname in configs:
            lines.append(f"- `{fname}`")

    lines.extend([
        "",
        "## Remotes",
        "",
    ])
    if git_state["remotes"]:
        for r in git_state["remotes"]:
            lines.append(f"- {r}")
    else:
        lines.append("- (none)")

    return "\n".join(lines)


def build_context_string(
    structure: dict, git_state: dict, configs: dict, root: Path
) -> str:
    parts = [
        f"PROJECT: {root.name}",
        f"BRANCH: {git_state['branch']}",
        f"COMMIT: {git_state['commit']}",
        f"DIRTY: {git_state['is_dirty']}",
        f"FILES: {structure['total_files']}",
        f"LINES: {structure['total_lines']}",
        f"COMPONENTS: {', '.join(k for k, v in structure['components'].items() if v)}",
        "",
        "FILE TYPES:",
    ]
    for ext, count in list(structure["files_by_extension"].items())[:10]:
        parts.append(f"  {ext}: {count}")

    if git_state["last_commits"]:
        parts.extend(["", "RECENT COMMITS:"])
        for c in git_state["last_commits"][:5]:
            parts.append(f"  {c['hash']} {c['message'][:60]}")

    if git_state["uncommitted_files"]:
        parts.extend(["", "UNCOMMITTED:"])
        for f in git_state["uncommitted_files"][:10]:
            parts.append(f"  {f}")

    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconstruct project context")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")
    parser.add_argument("--project-root", type=str, default=None, help="Project root path")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    parser.add_argument("--print-context", action="store_true", help="Print context string to stdout")
    args = parser.parse_args()

    if args.project_root:
        root = Path(args.project_root).resolve()
    else:
        root = Path(__file__).resolve().parent.parent.parent

    output_dir = Path(args.output_dir) if args.output_dir else root / "context" / "generated"

    log(f"Project root: {root}", args.quiet)
    log(f"Output dir: {output_dir}", args.quiet)
    log("", args.quiet)

    log("Scanning project structure...", args.quiet)
    structure = scan_project_structure(root)
    log(f"  Found {structure['total_files']} files, {structure['total_dirs']} dirs, {structure['total_lines']} lines", args.quiet)

    log("Analyzing git state...", args.quiet)
    git_state = analyze_git_state(root)
    log(f"  Branch: {git_state['branch']}, Commit: {git_state['commit']}, Dirty: {git_state['is_dirty']}", args.quiet)

    log("Reading configuration files...", args.quiet)
    configs = read_config_files(root)
    log(f"  Loaded {len(configs)} config files", args.quiet)

    log("Generating outputs...", args.quiet)
    output_dir.mkdir(parents=True, exist_ok=True)

    snapshot = generate_project_snapshot(structure, git_state, configs, root)
    snapshot_path = output_dir / "project_snapshot.json"
    snapshot_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False))
    log(f"  -> {snapshot_path}", args.quiet)

    summary = generate_context_summary(structure, git_state, configs, root)
    summary_path = output_dir / "context_summary.md"
    summary_path.write_text(summary)
    log(f"  -> {summary_path}", args.quiet)

    context_str = build_context_string(structure, git_state, configs, root)

    log("", args.quiet)
    log("Done.", args.quiet)

    if args.print_context:
        print(context_str)


if __name__ == "__main__":
    main()
