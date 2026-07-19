# Context System

Automated context reconstruction for AI operating system agents.

## Purpose

Agents need project context before starting work. This system stores and generates that context so agents don't depend solely on conversation memory.

## Structure

```
context/
├── README.md              # This file
├── templates/             # Input templates with placeholders
│   ├── project_state.md   # Current project state
│   ├── architecture.md    # Architecture decisions
│   ├── agents.md          # Agent definitions
│   ├── workflow.md        # Workflow rules
│   └── session_history.md # Session summaries
├── generated/             # Auto-generated context files
│   └── *.md               # Populated context files
└── scripts/
    └── generate_context.py  # Generation script
```

## Usage

### Generate context files

```bash
python context/scripts/generate_context.py
```

This scans the project and produces files in `context/generated/` with real data filled in from the templates.

### Template Placeholders

Templates use `{{variable}}` syntax. The generation script replaces known variables:

| Variable | Source |
|----------|--------|
| `{{timestamp}}` | Current UTC time |
| `{{version}}` | Git commit hash |
| `{{file_tree}}` | Scanned directory tree |
| `{{status}}` | Derived from project state |

### Adding New Templates

1. Create a `.md` file in `context/templates/`
2. Use `{{variable}}` placeholders for dynamic content
3. Add generation logic in `generate_context.py` if automated filling is needed
4. Run the script to populate

### Agent Context Loading

Before any task, agents should:

1. Run `generate_context.py` to refresh generated files
2. Read `generated/INDEX.md` for available context
3. Load relevant context files based on the task

## Design Principles

- **Templates are source of truth** for what context to capture
- **Generated files are disposable** and can be regenerated at any time
- **Minimal dependencies** - only Python stdlib needed
- **Incremental** - templates can be filled manually or via script
