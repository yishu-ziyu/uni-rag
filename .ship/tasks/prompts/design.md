You must use Skill('ship:design'). Skip preamble and auth gate.

Planning request:
---

---

## Pre-flight: Constitution Check

1. Check if CONSTITUTION.md exists at the project root:
   `[ -f CONSTITUTION.md ] && echo "EXISTS" || echo "MISSING"`
2. If MISSING: invoke Skill('ship:constitution') FIRST, wait for it to complete, then proceed.
3. If EXISTS: read it. Reference its principles when making scope and design decisions.

## Phase 0: Product Foundation (before code investigation)

### Step A: Discover
- Read README.md, CLAUDE.md, AGENTS.md for existing product context
- Write `.ship/tasks//plan/problem.md`:
  - User: <who has the problem>
  - Task: <what they're trying to complete>
  - Obstacle: <what's blocking them>
  - Evidence: <what evidence exists or is needed>
- Quality gate: must name a specific user, task, and obstacle.

### Step B: Shape
- Set appetite: time-boxed effort (e.g., "2-day spike", "1-week cycle")
- Define boundary: what's in scope, what's explicitly out of scope
- List risks and open questions
- Write `.ship/tasks//plan/scope.md`:
  - In scope: <list>
  - Out of scope: <at least one item>
  - Risks: <list>
- Quality gate: scope.md must include at least one "out of scope" item.

### Step C: Specify
- Write 3-7 acceptance criteria (behavior-focused, not implementation)
- Define 1-3 golden journeys (primary user paths that must work end-to-end)
- Include these in `.ship/tasks//plan/spec.md` (merged with Phase 3 output)
- Quality gate: every criterion must be verifiable by test or manual check.

Then proceed with standard design flow (Phases 1-6 from design SKILL.md).

IMPORTANT: You MUST write spec.md and plan.md to the artifacts directory.
The orchestrator validates these files exist and are non-empty before advancing
to the dev phase. Do NOT respond conversationally — write the artifacts to disk.

If this task involves frontend/UI changes and no DESIGN.md exists at project root,
note in spec.md that one should be created via /ship:visual-design before or
after this pipeline run.

task_id: 
Artifacts: .ship/tasks//plan/
Raw input: .ship/tasks//input/requirement.md
Run state: .ship/tasks//control/run_state.yaml
Branch: 
HEAD: c6fcecac6c12d3453ffaf425040ac1c5d904c6d4
Scope mode: full
Mode: /ship:auto staged workflow — no user questions, treat escalations as blocked.

If lightweight YAML planning notes would help this specific task, you may write
them under .ship/tasks//control/. Choose the schema yourself and keep
Markdown/code as the real deliverables.

Scope mode `refactor` means the task is behavior-preserving (refactor,
simplify, rename, extract, dedupe, etc.). In that mode, skip Phase 6
(Execution Drill) — the "every step is implementable" check adds little
value when the steps are small code movements. Peer investigation and
diff still run. See design SKILL.md "Scope Mode" for details.
Scope mode `full` runs all phases including Phase 0 (Product Foundation).
