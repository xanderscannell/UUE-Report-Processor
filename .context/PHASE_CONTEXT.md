# Context Loading by Phase

<!-- This file tells Claude (and you) which context files are most relevant
     for each phase of the project. Saves time by avoiding loading everything. -->

## Phase 1: [PHASE_NAME]

**Always read**:
- `CURRENT_STATUS.md`
- `CONVENTIONS.md`

**Read if relevant**:
- `ARCHITECTURE.md` (sections: [relevant sections])
- `CONTEXT/[relevant_file].md`

**Can skip**:
- [Files not relevant to this phase]

---

## Phase 2: [PHASE_NAME]

**Always read**:
- `CURRENT_STATUS.md`
- `CONVENTIONS.md`
- `ARCHITECTURE.md`

**Read if relevant**:
- `CONTEXT/[relevant_file].md`
- `DECISIONS.md` (ADRs: [relevant numbers])

---

<!-- Add more phases as your MASTER_PLAN grows.
     The goal is efficient context loading - Claude doesn't need to read
     every file every time. Point it to what matters for the current work. -->
