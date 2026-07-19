#!/usr/bin/env python3
"""
Context Integration for AI Operating System Orchestrator

Provides hooks for orchestrator to automatically inject project context
into agent prompts and track task execution.

Usage:
    python context_integration.py --pre-task            # Get context for pre-task injection
    python context_integration.py --post-task TASK_ID STATUS  # Log task completion
    python context_integration.py --agent-context AGENT_TYPE   # Get agent-specific context

Programmatic API:
    from context_integration import ContextIntegration
    ci = ContextIntegration()
    context = ci.pre_task_hook()
    ci.post_task_hook("task-001", "success")
    agent_ctx = ci.get_context_for_agent("coder")
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
CONTEXT_DIR = PROJECT_ROOT / "context"
GENERATED_DIR = CONTEXT_DIR / "generated"
SESSION_LOG_FILE = GENERATED_DIR / "session_log.json"

STALENESS_SECONDS = 300  # 5 minutes

EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".tox", ".mypy_cache", ".pytest_cache",
    "egg-info", ".eggs", "context/generated",
}

AGENT_CONTEXT_PROFILES = {
    "coder": {
        "level": "summary",
        "focus": ["src/", "scripts/", "config/"],
        "instructions": "Focus on code implementation. Check existing patterns before writing.",
    },
    "reviewer": {
        "level": "full",
        "focus": ["src/", "tests/", "docs/"],
        "instructions": "Review code quality, security, and adherence to project conventions.",
    },
    "architect": {
        "level": "full",
        "focus": ["src/", "config/", "docs/", "context/"],
        "instructions": "Consider system architecture and component interactions.",
    },
    "debugger": {
        "level": "summary",
        "focus": ["src/", "logs/", "tests/"],
        "instructions": "Investigate issues systematically. Check logs and test outputs.",
    },
    "tester": {
        "level": "summary",
        "focus": ["tests/", "src/", "config/"],
        "instructions": "Write and run tests. Ensure coverage of critical paths.",
    },
    "devops": {
        "level": "minimal",
        "focus": ["docker-compose.yml", "scripts/", "config/"],
        "instructions": "Manage deployment, containers, and infrastructure.",
    },
    "docwriter": {
        "level": "minimal",
        "focus": ["docs/", "README.md", "src/"],
        "instructions": "Document features, APIs, and workflows clearly.",
    },
}


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


def get_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class ContextIntegration:
    """Integration between context system and orchestrator."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or PROJECT_ROOT
        self.context_dir = self.project_root / "context"
        self.generated_dir = self.context_dir / "generated"
        self.session_log_path = self.generated_dir / "session_log.json"
        self._context_cache: str | None = None

    def _is_context_fresh(self) -> bool:
        """Check if context exists and is less than 5 minutes old."""
        snapshot = self.generated_dir / "project_snapshot.json"
        summary = self.generated_dir / "context_summary.md"

        for fpath in [snapshot, summary]:
            if not fpath.exists():
                return False
            try:
                mtime = datetime.datetime.fromtimestamp(
                    fpath.stat().st_mtime, tz=datetime.timezone.utc
                )
                age = (datetime.datetime.now(datetime.timezone.utc) - mtime).total_seconds()
                if age > STALENESS_SECONDS:
                    return False
            except OSError:
                return False
        return True

    def _reconstruct_context(self, quiet: bool = True) -> bool:
        """Run reconstruct_context.py if context is stale or missing."""
        reconstruct_script = SCRIPT_DIR / "reconstruct_context.py"
        if not reconstruct_script.exists():
            log("reconstruct_context.py not found", quiet)
            return False

        try:
            cmd = [sys.executable, str(reconstruct_script),
                   "--project-root", str(self.project_root)]
            if quiet:
                cmd.append("--quiet")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                log("Context reconstructed successfully", quiet)
                return True
            else:
                log(f"Reconstruct failed: {result.stderr[:200]}", quiet)
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
            log(f"Failed to run reconstruct: {e}", quiet)
            return False

    def _load_snapshot(self) -> dict[str, Any]:
        """Load project_snapshot.json."""
        snapshot_path = self.generated_dir / "project_snapshot.json"
        if not snapshot_path.exists():
            return {}
        try:
            return json.loads(snapshot_path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def _load_context_text(self, level: str = "summary") -> str:
        """Load context using load_context.py."""
        load_script = SCRIPT_DIR / "load_context.py"
        if not load_script.exists():
            return self._build_fallback_context()

        try:
            cmd = [sys.executable, str(load_script),
                   "--level", level, "--append", "--quiet"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return self._build_fallback_context()

    def _build_fallback_context(self) -> str:
        """Build minimal context from available data."""
        snapshot = self._load_snapshot()
        if not snapshot:
            return "Project: unknown | No context available"

        meta = snapshot.get("metadata", {})
        git = snapshot.get("git", {})
        structure = snapshot.get("structure", {})

        return (
            f"Project: {meta.get('project_name', 'unknown')}\n"
            f"Branch: {git.get('branch', 'unknown')} @ {git.get('commit', 'unknown')}\n"
            f"Files: {structure.get('total_files', 0)} | Lines: {structure.get('total_lines', 0)}"
        )

    def _build_project_structure_summary(self, snapshot: dict) -> str:
        """Build a concise project structure summary."""
        git = snapshot.get("git", {})
        structure = snapshot.get("structure", {})
        components = structure.get("components", {})

        lines = []

        # Directories
        if components:
            active = [f"{k}/" for k, v in components.items() if v]
            if active:
                lines.append(f"- {', '.join(active[:6])}")

        # Key files
        key_files = []
        for fname in ["README.md", "package.json", "requirements.txt",
                       "docker-compose.yml", "pyproject.toml", "Makefile"]:
            if (self.project_root / fname).exists():
                key_files.append(fname)
        if key_files:
            lines.append(f"- Key: {', '.join(key_files)}")

        # Recent changes
        if git.get("last_commits"):
            lines.append("- Recent changes:")
            for c in git["last_commits"][:3]:
                lines.append(f"  - {c['message'][:50]}")

        return "\n".join(lines) if lines else "- No structure info available"

    def _build_context_block(self, snapshot: dict, level: str = "summary",
                              agent_type: str | None = None) -> str:
        """Build the formatted context injection block."""
        now = get_timestamp()
        meta = snapshot.get("metadata", {})
        git = snapshot.get("git", {})
        structure = snapshot.get("structure", {})

        # Git info
        branch = git.get("branch", "unknown")
        commit = git.get("commit", "unknown")
        last_commit_msg = ""
        if git.get("last_commits"):
            last_commit_msg = f" - {git['last_commits'][0]['message'][:50]}"

        remote = ""
        if git.get("remotes"):
            remote = git["remotes"][0].split("\t")[0] if "\t" in git["remotes"][0] else git["remotes"][0]

        # Structure summary
        structure_summary = self._build_project_structure_summary(snapshot)

        # Agent-specific instructions
        agent_section = ""
        if agent_type and agent_type in AGENT_CONTEXT_PROFILES:
            profile = AGENT_CONTEXT_PROFILES[agent_type]
            agent_section = f"\nAgent Type: {agent_type}\nAgent Guidelines:\n- {profile['instructions']}"
            if profile.get("focus"):
                agent_section += f"\n- Focus areas: {', '.join(profile['focus'])}"

        # Build block
        block = (
            f"---PROJECT CONTEXT (auto-generated)---\n"
            f"Project: {meta.get('project_name', 'unknown')}\n"
            f"Generated: {now}\n"
            f"Branch: {branch}\n"
            f"Last commit: {commit}{last_commit_msg}\n"
        )

        if remote:
            block += f"Remote: {remote}\n"

        block += f"\nProject Structure:\n{structure_summary}\n"

        # Uncommitted changes
        if git.get("uncommitted_files"):
            block += f"\nUncommitted Changes: {len(git['uncommitted_files'])} files\n"

        if agent_section:
            block += agent_section

        block += f"---END PROJECT CONTEXT---"

        return block

    def _load_session_log(self) -> list[dict]:
        """Load session log from JSON file."""
        if not self.session_log_path.exists():
            return []
        try:
            return json.loads(self.session_log_path.read_text())
        except (json.JSONDecodeError, OSError):
            return []

    def _save_session_log(self, entries: list[dict]) -> None:
        """Save session log to JSON file."""
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.session_log_path.write_text(
                json.dumps(entries, indent=2, ensure_ascii=False)
            )
        except OSError as e:
            log(f"Warning: Could not save session log: {e}", quiet=False)

    def pre_task_hook(self, agent_type: str | None = None) -> str:
        """
        Called before each task by orchestrator.
        Ensures context is fresh and returns formatted context block.
        """
        # Check freshness and reconstruct if needed
        if not self._is_context_fresh():
            self._reconstruct_context(quiet=True)
            self._context_cache = None  # Invalidate cache

        # Load or use cached context
        if self._context_cache is None:
            snapshot = self._load_snapshot()
            if not snapshot:
                return self._build_fallback_context()
            self._context_cache = self._build_context_block(snapshot)

        return self._context_cache

    def post_task_hook(self, task_id: str, status: str, agent_type: str | None = None,
                       details: str | None = None) -> bool:
        """
        Called after each task by orchestrator.
        Updates session history with task execution record.
        """
        entry = {
            "task_id": task_id,
            "timestamp": get_timestamp(),
            "status": status,
            "agent_type": agent_type or "unknown",
            "project": self.project_root.name,
            "details": details,
        }

        entries = self._load_session_log()
        entries.append(entry)

        # Keep last 500 entries
        if len(entries) > 500:
            entries = entries[-500:]

        self._save_session_log(entries)
        return True

    def get_context_for_agent(self, agent_type: str) -> str:
        """
        Returns relevant context formatted for a specific agent type.
        """
        # Check freshness
        if not self._is_context_fresh():
            self._reconstruct_context(quiet=True)
            self._context_cache = None

        snapshot = self._load_snapshot()
        if not snapshot:
            return self._build_fallback_context()

        return self._build_context_block(snapshot, agent_type=agent_type)

    def get_session_stats(self) -> dict[str, Any]:
        """Get summary statistics from session log."""
        entries = self._load_session_log()
        if not entries:
            return {"total_tasks": 0, "agents_used": [], "success_rate": 0}

        agents = {}
        successes = 0
        for e in entries:
            agent = e.get("agent_type", "unknown")
            agents[agent] = agents.get(agent, 0) + 1
            if e.get("status") == "success":
                successes += 1

        return {
            "total_tasks": len(entries),
            "agents_used": list(agents.keys()),
            "agent_counts": agents,
            "success_rate": successes / len(entries) if entries else 0,
            "last_task": entries[-1] if entries else None,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Context Integration for Orchestrator"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--pre-task", action="store_true",
        help="Get context for pre-task injection"
    )
    group.add_argument(
        "--post-task", nargs=2, metavar=("TASK_ID", "STATUS"),
        help="Log task completion (TASK_ID STATUS)"
    )
    group.add_argument(
        "--agent-context", metavar="AGENT_TYPE",
        help="Get context for specific agent type"
    )
    group.add_argument(
        "--stats", action="store_true",
        help="Show session statistics"
    )
    parser.add_argument(
        "--project-root", type=str, default=None,
        help="Override project root path"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suppress status output"
    )

    args = parser.parse_args()

    root = Path(args.project_root) if args.project_root else None
    ci = ContextIntegration(project_root=root)

    if args.pre_task:
        context = ci.pre_task_hook()
        print(context)

    elif args.post_task:
        task_id, status = args.post_task
        success = ci.post_task_hook(task_id, status)
        if not args.quiet:
            if success:
                print(f"Task {task_id} logged with status: {status}")
            else:
                print(f"Warning: Failed to log task {task_id}", file=sys.stderr)
                sys.exit(1)

    elif args.agent_context:
        context = ci.get_context_for_agent(args.agent_context)
        print(context)

    elif args.stats:
        stats = ci.get_session_stats()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
