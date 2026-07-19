#!/usr/bin/env python3
"""
Context Generator for AI Operating System

Scans the project directory and generates context files from templates.
Templates use {{variable}} placeholders that get filled with real data.
"""

import os
import json
import subprocess
import datetime
import hashlib
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = PROJECT_ROOT / "context" / "templates"
GENERATED_DIR = PROJECT_ROOT / "context" / "generated"


def get_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def get_git_info() -> dict:
    info = {"commit": "unknown", "branch": "unknown", "dirty": False}
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=5
        )
        if result.returncode == 0:
            info["commit"] = result.stdout.strip()
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=5
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip()
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=5
        )
        if result.returncode == 0:
            info["dirty"] = bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return info


def get_file_tree(root: Path, max_depth: int = 4, exclude: list[str] = None) -> str:
    if exclude is None:
        exclude = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".tox"}

    lines = []

    def walk(directory: Path, prefix: str = "", depth: int = 0):
        if depth >= max_depth:
            return
        try:
            entries = sorted(directory.iterdir(), key=lambda e: (e.is_file(), e.name))
        except PermissionError:
            return

        entries = [e for e in entries if e.name not in exclude and not e.name.startswith(".")]
        for i, entry in enumerate(entries):
            connector = "---" if i == len(entries) - 1 else "|-- "
            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                walk(entry, prefix + ("    " if i == len(entries) - 1 else "|   "), depth + 1)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    walk(root)
    return "\n".join(lines) if lines else "(empty project)"


def count_files(root: Path, exclude: list[str] = None) -> dict:
    if exclude is None:
        exclude = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

    stats = {"total": 0, "by_extension": {}}

    for path in root.rglob("*"):
        if path.is_file():
            parts = path.parts
            if any(ex in parts for ex in exclude):
                continue
            if path.name.startswith(".") and path.name != ".gitkeep":
                continue
            stats["total"] += 1
            ext = path.suffix or "(no ext)"
            stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1

    return stats


def detect_project_type(root: Path) -> str:
    indicators = {
        "package.json": "Node.js",
        "Cargo.toml": "Rust",
        "go.mod": "Go",
        "pyproject.toml": "Python",
        "setup.py": "Python",
        "setup.cfg": "Python",
        "pom.xml": "Java/Maven",
        "build.gradle": "Java/Gradle",
        "Gemfile": "Ruby",
        "composer.json": "PHP",
        "CMakeLists.txt": "C/C++",
        "Makefile": "C/C++",
    }
    for filename, ptype in indicators.items():
        if (root / filename).exists():
            return ptype
    return "Unknown"


def load_dependencies(root: Path) -> dict:
    deps = {"runtime": {}, "dev": {}}

    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json) as f:
                data = json.load(f)
            deps["runtime"] = data.get("dependencies", {})
            deps["dev"] = data.get("devDependencies", {})
        except (json.JSONDecodeError, KeyError):
            pass

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            deps["runtime"]["pyproject.toml"] = "present"
        except Exception:
            pass

    go_mod = root / "go.mod"
    if go_mod.exists():
        deps["runtime"]["go.mod"] = "present"

    return deps


def generate_project_state() -> str:
    git_info = get_git_info()
    file_tree = get_file_tree(PROJECT_ROOT)
    file_stats = count_files(PROJECT_ROOT)
    project_type = detect_project_type(PROJECT_ROOT)
    deps = load_dependencies(PROJECT_ROOT)

    lines = [
        "# Project State (Auto-Generated)",
        "",
        "## Metadata",
        "",
        f"- **Generated**: {get_timestamp()}",
        f"- **Commit**: {git_info['commit']}",
        f"- **Branch**: {git_info['branch']}",
        f"- **Dirty**: {git_info['dirty']}",
        f"- **Project Type**: {project_type}",
        "",
        "## File Structure",
        "",
        "```",
        file_tree,
        "```",
        "",
        "## File Statistics",
        "",
        f"- **Total files**: {file_stats['total']}",
        "",
        "### By Extension",
        "",
        "| Extension | Count |",
        "|-----------|-------|",
    ]

    for ext, count in sorted(file_stats["by_extension"].items(), key=lambda x: -x[1]):
        lines.append(f"| `{ext}` | {count} |")

    lines.extend([
        "",
        "## Dependencies",
        "",
        "### Runtime",
        "",
    ])

    if deps["runtime"]:
        lines.append("| Package | Version/Info |")
        lines.append("|---------|-------------|")
        for pkg, ver in deps["runtime"].items():
            lines.append(f"| `{pkg}` | `{ver}` |")
    else:
        lines.append("No runtime dependencies detected.")

    lines.extend([
        "",
        "### Dev",
        "",
    ])

    if deps["dev"]:
        lines.append("| Package | Version/Info |")
        lines.append("|---------|-------------|")
        for pkg, ver in deps["dev"].items():
            lines.append(f"| `{pkg}` | `{ver}` |")
    else:
        lines.append("No dev dependencies detected.")

    lines.extend([
        "",
        "## Key Directories",
        "",
        "| Directory | Exists |",
        "|-----------|--------|",
    ])

    for d in ["src", "lib", "tests", "docs", "scripts", "config", ".github", "context"]:
        exists = (PROJECT_ROOT / d).exists()
        lines.append(f"| `{d}/` | {'Yes' if exists else 'No'} |")

    return "\n".join(lines)


def generate_from_template(template_name: str, overrides: dict[str, str] = None) -> str:
    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        return f"ERROR: Template {template_name} not found"

    content = template_path.read_text()

    if overrides:
        for key, value in overrides.items():
            content = content.replace(f"{{{{{key}}}}}", value)

    return content


def main():
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Template dir: {TEMPLATE_DIR}")
    print(f"Output dir:   {GENERATED_DIR}")
    print()

    # Generate project_state.md with real data
    print("Generating project_state.md ...")
    state_content = generate_project_state()
    (GENERATED_DIR / "project_state.md").write_text(state_content)
    print(f"  -> {len(state_content)} bytes written")

    # Copy other templates with basic metadata filled
    for template in ["architecture.md", "agents.md", "workflow.md", "session_history.md"]:
        print(f"Generating {template} ...")
        git_info = get_git_info()
        content = generate_from_template(template, {
            "timestamp": get_timestamp(),
            "version": f"git:{git_info['commit']}",
        })
        (GENERATED_DIR / template).write_text(content)
        print(f"  -> {len(content)} bytes written")

    # Generate summary index
    print("Generating INDEX.md ...")
    index_lines = [
        "# Generated Context Index",
        "",
        f"- **Generated**: {get_timestamp()}",
        f"- **Commit**: {get_git_info()['commit']}",
        f"- **Branch**: {get_git_info()['branch']}",
        "",
        "## Files",
        "",
    ]
    for f in sorted(GENERATED_DIR.glob("*.md")):
        size = f.stat().st_size
        index_lines.append(f"- `{f.name}` ({size} bytes)")

    (GENERATED_DIR / "INDEX.md").write_text("\n".join(index_lines))
    print(f"  -> INDEX.md written")

    print()
    print("Done. Context files generated in:", GENERATED_DIR)


if __name__ == "__main__":
    main()
