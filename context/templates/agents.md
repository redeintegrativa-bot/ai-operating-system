# Agent Definitions

> Definitions, roles, capabilities, and configurations for all agents in the system.

## Metadata

- **Generated**: `{{timestamp}}`
- **Version**: `{{version}}`

---

## 1. Agent Registry

### 1.1 Active Agents

| Agent ID | Name | Role | Status | Model |
|----------|------|------|--------|-------|
| `{{agent_id}}` | `{{name}}` | `{{role}}` | `{{status}}` | `{{model}}` |

### 1.2 Agent Hierarchy

```
{{hierarchy}}
```

### 1.3 Communication Matrix

| From | To | Protocol | Frequency |
|------|----|----------|-----------|
| `{{from}}` | `{{to}}` | `{{protocol}}` | `{{frequency}}` |

---

## 2. Agent Profiles

### 2.1 Orchestrator Agent

- **ID**: `{{id}}`
- **Role**: Central coordination and task delegation
- **Responsibilities**:
  - `{{responsibility}}`
- **Capabilities**:
  - `{{capability}}`
- **Constraints**:
  - `{{constraint}}`
- **Configuration**:

```yaml
{{config}}
```

### 2.2 Builder Agent

- **ID**: `{{id}}`
- **Role**: Code generation and implementation
- **Responsibilities**:
  - `{{responsibility}}`
- **Capabilities**:
  - `{{capability}}`
- **Constraints**:
  - `{{constraint}}`
- **Configuration**:

```yaml
{{config}}
```

### 2.3 Reviewer Agent

- **ID**: `{{id}}`
- **Role**: Code review and quality assurance
- **Responsibilities**:
  - `{{responsibility}}`
- **Capabilities**:
  - `{{capability}}`
- **Constraints**:
  - `{{constraint}}`
- **Configuration**:

```yaml
{{config}}
```

### 2.4 Researcher Agent

- **ID**: `{{id}}`
- **Role**: Information gathering and analysis
- **Responsibilities**:
  - `{{responsibility}}`
- **Capabilities**:
  - `{{capability}}`
- **Constraints**:
  - `{{constraint}}`
- **Configuration**:

```yaml
{{config}}
```

### 2.5 Tester Agent

- **ID**: `{{id}}`
- **Role**: Testing and validation
- **Responsibilities**:
  - `{{responsibility}}`
- **Capabilities**:
  - `{{capability}}`
- **Constraints**:
  - `{{constraint}}`
- **Configuration**:

```yaml
{{config}}
```

### 2.6 Custom Agent: `{{name}}`

- **ID**: `{{id}}`
- **Role**: `{{role}}`
- **Responsibilities**:
  - `{{responsibility}}`
- **Capabilities**:
  - `{{capability}}`
- **Constraints**:
  - `{{constraint}}`
- **Configuration**:

```yaml
{{config}}
```

---

## 3. Agent Tools & Permissions

### 3.1 Tool Registry

| Tool | Description | Required Agent | Permission Level |
|------|-------------|---------------|-----------------|
| `{{tool}}` | `{{description}}` | `{{agent}}` | `{{level}}` |

### 3.2 Permission Matrix

| Agent | Read | Write | Execute | Network | Admin |
|-------|------|-------|---------|---------|-------|
| `{{agent}}` | `{{read}}` | `{{write}}` | `{{execute}}` | `{{network}}` | `{{admin}}` |

### 3.3 Tool Configuration

| Tool | Config File | Key Settings |
|------|-------------|--------------|
| `{{tool}}` | `{{file}}` | `{{settings}}` |

---

## 4. Agent Prompts & System Instructions

### 4.1 System Prompts

| Agent | Prompt Version | Hash |
|-------|---------------|------|
| `{{agent}}` | `{{version}}` | `{{hash}}` |

### 4.2 Prompt Templates

```
{{prompt_template}}
```

### 4.3 Few-Shot Examples

| Agent | Example ID | Input | Expected Output |
|-------|-----------|-------|-----------------|
| `{{agent}}` | `{{id}}` | `{{input}}` | `{{output}}` |

---

## 5. Agent Lifecycle

### 5.1 Initialization Sequence

1. `{{step_1}}`
2. `{{step_2}}`
3. `{{step_3}}`

### 5.2 Execution Flow

```
{{execution_flow}}
```

### 5.3 Cleanup & Shutdown

| Step | Action | Timeout |
|------|--------|---------|
| `{{step}}` | `{{action}}` | `{{timeout}}` |

---

## 6. Agent Performance

### 6.1 Metrics

| Agent | Avg Response Time | Success Rate | Token Usage |
|-------|------------------|--------------|-------------|
| `{{agent}}` | `{{time}}` | `{{rate}}` | `{{tokens}}` |

### 6.2 Known Issues

| Agent | Issue | Severity | Status |
|-------|-------|----------|--------|
| `{{agent}}` | `{{issue}}` | `{{severity}}` | `{{status}}` |

### 6.3 Improvement History

| Date | Agent | Change | Impact |
|------|-------|--------|--------|
| `{{date}}` | `{{agent}}` | `{{change}}` | `{{impact}}` |

---

## 7. Custom Agent Template

```yaml
agent:
  id: "{{id}}"
  name: "{{name}}"
  role: "{{role}}"
  model: "{{model}}"
  responsibilities:
    - "{{responsibility}}"
  capabilities:
    - "{{capability}}"
  constraints:
    - "{{constraint}}"
  tools:
    - "{{tool}}"
  permissions:
    read: {{read}}
    write: {{write}}
    execute: {{execute}}
```
