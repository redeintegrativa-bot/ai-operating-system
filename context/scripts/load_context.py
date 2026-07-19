#!/usr/bin/env python3
"""
Context Loader for AI Operating System Agents

Loads generated context files and formats them for agent prompt injection.
Supports different context levels and automatic cache refresh.

Usage:
    python load_context.py [options]

    Options:
        --level LEVEL     Context detail level: full, summary, minimal (default: summary)
        --force           Force regeneration of context files
        --quiet           Suppress output (only prints context block)
        --project-root    Override project root path
        --append          Print only the context block for prompt appending
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATED_DIR = SCRIPT_DIR.parent / "generated"
SNAPSHOT_FILE = GENERATED_DIR / "project_snapshot.json"
SUMMARY_FILE = GENERATED_DIR / "context_summary.md"
STALENESS_SECONDS = 300  # 5 minutes


def log(message: str, quiet: bool = False) -> None:
    if not quiet:
        print(message, file=sys.stderr)


def is_context_stale() -> bool:
    """Check if context files are older than 5 minutes."""
    now = datetime.datetime.now(datetime.timezone.utc)
    for fpath in [SNAPSHOT_FILE, SUMMARY_FILE]:
        if not fpath.exists():
            return True
        try:
            mtime = datetime.datetime.fromtimestamp(fpath.stat().st_mtime, tz=datetime.timezone.utc)
            age = (now - mtime).total_seconds()
            if age > STALENESS_SECONDS:
                return True
        except OSError:
            return True
    return False


def run_reconstruct(project_root: Path, quiet: bool = False) -> bool:
    """Run reconstruct_context.py to regenerate context files."""
    reconstruct_script = SCRIPT_DIR / "reconstruct_context.py"
    if not reconstruct_script.exists():
        log("  reconstruct_context.py not found, skipping regeneration", quiet)
        return False

    log("  Stale context detected, regenerating...", quiet)
    try:
        cmd = [sys.executable, str(reconstruct_script), "--project-root", str(project_root)]
        if quiet:
            cmd.append("--quiet")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            log("  Context regenerated successfully", quiet)
            return True
        else:
            log(f"  Warning: reconstruct_context.py failed: {result.stderr[:200]}", quiet)
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
        log(f"  Warning: Failed to run reconstruct_context.py: {e}", quiet)
        return False


def load_snapshot() -> dict[str, Any] | None:
    """Load project_snapshot.json."""
    if not SNAPSHOT_FILE.exists():
        return None
    try:
        return json.loads(SNAPSHOT_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def load_summary() -> str | None:
    """Load context_summary.md."""
    if not SUMMARY_FILE.exists():
        return None
    try:
        return SUMMARY_FILE.read_text()
    except OSError:
        return None


def load_additional_context(project_root: Path) -> dict[str, str]:
    """Load any additional context files from generated/ directory."""
    additional = {}
    if not GENERATED_DIR.exists():
        return additional
    for fpath in sorted(GENERATED_DIR.iterdir()):
        if fpath.is_file() and fpath.name not in ("project_snapshot.json", "context_summary.md", ".gitkeep"):
            try:
                additional[fpath.name] = fpath.read_text()[:3000]
            except OSError:
                pass
    return additional


def estimate_tokens(text: str) -> int:
    """Rough token estimation (words * 1.3)."""
    return int(len(text.split()) * 1.3)


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to approximate token limit."""
    words = text.split()
    approx_words = int(max_tokens / 1.3)
    if len(words) <= approx_words:
        return text
    return " ".join(words[:approx_words]) + "\n... [truncated]"


def format_context_full(snapshot: dict, summary: str, additional: dict[str, str]) -> str:
    """Full context for complex tasks."""
    lines = []

    if snapshot:
        meta = snapshot.get("metadata", {})
        git = snapshot.get("git", {})
        structure = snapshot.get("structure", {})

        lines.append(f"Project: {meta.get('project_name', 'unknown')}")
        lines.append(f"Root: {meta.get('project_root', 'unknown')}")
        lines.append(f"Generated: {meta.get('generated_at', 'unknown')}")
        lines.append(f"Branch: {git.get('branch', 'unknown')}")
        lines.append(f"Commit: {git.get('commit', 'unknown')}")
        lines.append(f"Dirty: {git.get('is_dirty', False)}")
        lines.append(f"Files: {structure.get('total_files', 0)}")
        lines.append(f"Lines: {structure.get('total_lines', 0)}")

        components = structure.get("components", {})
        active = [k for k, v in components.items() if v]
        lines.append(f"Components: {', '.join(active)}")

        if git.get("last_commits"):
            lines.append("\nRecent commits:")
            for c in git["last_commits"][:5]:
                lines.append(f"  {c['hash']} {c['message'][:60]}")

        if git.get("uncommitted_files"):
            lines.append("\nUncommitted:")
            for f in git["uncommitted_files"][:10]:
                lines.append(f"  {f}")

        if snapshot.get("config_files_loaded"):
            lines.append(f"\nConfig files: {', '.join(snapshot['config_files_loaded'][:10])}")

    if summary:
        lines.append(f"\n---\n{summary}")

    for fname, content in additional.items():
        if fname.endswith(('.md', '.txt')):
            lines.append(f"\n--- {fname} ---\n{content[:2000]}")

    return "\n".join(lines)


def format_context_summary(snapshot: dict, summary: str) -> str:
    """Brief summary for simple tasks."""
    lines = []
    if snapshot:
        meta = snapshot.get("metadata", {})
        git = snapshot.get("git", {})
        structure = snapshot.get("structure", {})

        lines.append(f"Project: {meta.get('project_name', 'unknown')}")
        lines.append(f"Branch: {git.get('branch', 'unknown')} @ {git.get('commit', 'unknown')}")
        lines.append(f"Dirty: {git.get('is_dirty', False)}")
        lines.append(f"Files: {structure.get('total_files', 0)} | Lines: {structure.get('total_lines', 0)}")

        if git.get("last_commits"):
            lines.append(f"Last commit: {git['last_commits'][0]['message'][:60]}")

        if git.get("uncommitted_files"):
            lines.append(f"Uncommitted: {len(git['uncommitted_files'])} files")

    return "\n".join(lines)


def format_context_minimal(snapshot: dict) -> str:
    """Minimal context for quick checks."""
    if snapshot:
        meta = snapshot.get("metadata", {})
        git = snapshot.get("git", {})
        dirty = " (dirty)" if git.get("is_dirty") else ""
        return f"Project: {meta.get('project_name', 'unknown')} | Branch: {git.get('branch', 'unknown')} | Commit: {git.get('commit', 'unknown')}{dirty}"
    return "Project: unknown | No context available"


def build_context_block(context_text: str, level: str) -> str:
    """Wrap context text in the standard injection format."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return (
        f"---PROJECT CONTEXT---\n"
        f"[Auto-generated by load_context.py]\n"
        f"Level: {level}\n"
        f"Generated: {now}\n"
        f"{context_text}\n"
        f"---END PROJECT CONTEXT---"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Load and format project context for agents")
    parser.add_argument("--level", choices=["full", "summary", "minimal"], default="summary",
                        help="Context detail level (default: summary)")
    parser.add_argument("--force", action="store_true",
                        help="Force regeneration of context files")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress status output")
    parser.add_argument("--project-root", type=str, default=None,
                        help="Override project root path")
    parser.add_argument("--append", action="store_true",
                        help="Output only the injectable context block")
    args = parser.parse_args()

    if args.project_root:
        project_root = Path(args.project_root).resolve()
    else:
        project_root = SCRIPT_DIR.parent.parent

    log(f"Loading context for: {project_root.name}", args.quiet)

    # Cache check
    if args.force or is_context_stale():
        if args.force:
            log("Forcing context regeneration...", args.quiet)
        run_reconstruct(project_root, args.quiet)

    # Load context files
    snapshot = load_snapshot()
    summary = load_summary()
    additional = load_additional_context(project_root)

    if not snapshot and not summary:
        log("No context files found. Generating...", args.quiet)
        run_reconstruct(project_root, args.quiet)
        snapshot = load_snapshot()
        summary = load_summary()
        additional = load_additional_context(project_root)

    if not snapshot and not summary:
        log("ERROR: Could not load or generate context", args.quiet)
        # Output minimal fallback
        fallback = "---PROJECT CONTEXT---\nProject: unknown | No context available\n---END PROJECT CONTEXT---"
        print(fallback)
        sys.exit(1)

    # Format context based on level
    if args.level == "full":
        context_text = format_context_full(snapshot or {}, summary or "", additional)
    elif args.level == "summary":
        context_text = format_context_summary(snapshot or {}, summary or "")
    else:
        context_text = format_context_minimal(snapshot or {})

    # Enforce max ~2000 tokens for full level
    if args.level == "full":
        context_text = truncate_to_tokens(context_text, 2000)

    # Build final block
    context_block = build_context_block(context_text, args.level)

    if not args.quiet:
        log(f"Context level: {args.level}", args.quiet)
        log(f"Token estimate: ~{estimate_tokens(context_block)}", args.quiet)

    # Output
    if args.append:
        print(context_block)
    else:
        # Print to stdout for easy capture
        print(context_block)


if __name__ == "__main__":
    main()
