# System Architecture

## High-Level Overview

[System diagram or prose description of how the major components fit together]

```
[Component A] ──► [Component B] ──► [Component C]
       │                                    │
       ▼                                    ▼
[Component D]                        [Component E]
```

## Components

### [COMPONENT_NAME]

**Purpose**: [What it does]
**Tech stack**: [Languages, frameworks, libraries]
**Key files**:
- `path/to/main/file`
- `path/to/config`

**Interfaces**:
- Input: [What it receives]
- Output: [What it produces]

**Notes**: [Design constraints, performance characteristics, etc.]

---

### [COMPONENT_NAME]

**Purpose**: [What it does]
**Tech stack**: [Languages, frameworks, libraries]
**Key files**:
- `path/to/main/file`

---

<!-- Repeat for each component -->

## Data Flow

[Describe how data moves through the system, from input to output]

1. [Step 1: data enters here]
2. [Step 2: processed by X]
3. [Step 3: stored in Y]
4. [Step 4: served via Z]

## External Dependencies

| Dependency | Purpose | Version |
|-----------|---------|---------|
| [Library/Service] | [Why we use it] | [Version] |

## Key Design Patterns

- **[Pattern name]**: Used in [where], because [why]
- **[Pattern name]**: Used in [where], because [why]

## Technology Decisions

See [DECISIONS.md](DECISIONS.md) for rationale behind technology choices.
