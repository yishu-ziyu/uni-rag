You must use Skill('ship:review'). Skip preamble and auth gate.

Review the current diff against the spec. Write findings to the path below.

IMPORTANT: You MUST write your findings to .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/review.md even if the
review is clean (write a short "no findings" report). The orchestrator reads
this file to decide the next phase — if it's missing, the pipeline stalls.
Do NOT only output findings to the conversation; the file is the artifact.

Report card Status rules:
- Zero P1/P2 findings → Status: PASS
- Any P1 or P2 findings → Status: FINDINGS (even if everything else is good)
P2s are real issues that the pipeline must fix. Only P3s are advisory.

spec: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/plan/spec.md
input_requirement: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/input/requirement.md
run_state: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/control/run_state.yaml
task_dir: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m
Write review to: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/review.md
Mode: /ship:auto staged workflow — no user questions. Diff-only review if spec unavailable.
