You must use Skill('ship:design'). Skip preamble and auth gate.

Planning request:
---

在 uni-rag 项目中实现链接内容提取功能。设计文档在 .ship/tasks/uni-rag-link-extractor-design/plan/spec.md，调研报告在 /Users/mahaoxuan/Desktop/AI产品经理/uni-rag接入优先级评估.md。实施第一批 MVP（P1-P7）：通用网页提取器（Trafilatura）+ API端点 + Web UI + CLI。第二批（P8-P9 YouTube/B站）暂不实施，留待后续。关键技术决策：1) yt-dlp/BBDown 用 subprocess 调用 2) Trafilatura 直接 import 3) 小红书明确跳过 4) faster-whisper 作为可选依赖。
---

## Pre-flight: Constitution Check

1. Check if CONSTITUTION.md exists at the project root:
   `[ -f CONSTITUTION.md ] && echo "EXISTS" || echo "MISSING"`
2. If MISSING: invoke Skill('ship:constitution') FIRST, wait for it to complete, then proceed.
3. If EXISTS: read it. Reference its principles when making scope and design decisions.

## Phase 0: Product Foundation (before code investigation)

### Step A: Discover
- Read README.md, CLAUDE.md, AGENTS.md for existing product context
- Write `.ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/plan/problem.md`:
  - User: <who has the problem>
  - Task: <what they're trying to complete>
  - Obstacle: <what's blocking them>
  - Evidence: <what evidence exists or is needed>
- Quality gate: must name a specific user, task, and obstacle.

### Step B: Shape
- Set appetite: time-boxed effort (e.g., "2-day spike", "1-week cycle")
- Define boundary: what's in scope, what's explicitly out of scope
- List risks and open questions
- Write `.ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/plan/scope.md`:
  - In scope: <list>
  - Out of scope: <at least one item>
  - Risks: <list>
- Quality gate: scope.md must include at least one "out of scope" item.

### Step C: Specify
- Write 3-7 acceptance criteria (behavior-focused, not implementation)
- Define 1-3 golden journeys (primary user paths that must work end-to-end)
- Include these in `.ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/plan/spec.md` (merged with Phase 3 output)
- Quality gate: every criterion must be verifiable by test or manual check.

Then proceed with standard design flow (Phases 1-6 from design SKILL.md).

IMPORTANT: You MUST write spec.md and plan.md to the artifacts directory.
The orchestrator validates these files exist and are non-empty before advancing
to the dev phase. Do NOT respond conversationally — write the artifacts to disk.

If this task involves frontend/UI changes and no DESIGN.md exists at project root,
note in spec.md that one should be created via /ship:visual-design before or
after this pipeline run.

task_id: uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m
Artifacts: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/plan/
Raw input: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/input/requirement.md
Run state: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/control/run_state.yaml
Branch: ship/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m
HEAD: 2d64ee5977db0e15dec389e2d64596cfc9c284d1
Scope mode: full
Mode: /ship:auto staged workflow — no user questions, treat escalations as blocked.

If lightweight YAML planning notes would help this specific task, you may write
them under .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/control/. Choose the schema yourself and keep
Markdown/code as the real deliverables.

Scope mode `refactor` means the task is behavior-preserving (refactor,
simplify, rename, extract, dedupe, etc.). In that mode, skip Phase 6
(Execution Drill) — the "every step is implementable" check adds little
value when the steps are small code movements. Peer investigation and
diff still run. See design SKILL.md "Scope Mode" for details.
Scope mode `full` runs all phases including Phase 0 (Product Foundation).
