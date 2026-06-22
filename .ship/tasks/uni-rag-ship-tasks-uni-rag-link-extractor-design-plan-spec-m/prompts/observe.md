You must use Skill('ship:observe'). Skip preamble.

Post-release observation: monitor the application, capture learnings, close the feedback loop.

Task: Observe the recently shipped changes for uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m.

Steps:
1. Read the task context: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/handoff.md (if it exists) for what was shipped
2. Read the project's observability setup: check for monitoring/, .sentry*, logging config in package.json/pyproject.toml
3. Check application logs for errors in the last 24h: look at .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/e2e/*.log and any app logs
4. Check for open issues or error patterns
5. Run a smoke check: curl the health endpoint or homepage
6. Capture learnings:
   - What worked as expected
   - What was unexpected
   - What needs improvement
7. Write .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/observe/report.md with findings
8. If CONSTITUTION.md exists, note whether any principle needs updating based on findings

task_id: uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m
task_dir: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m
branch: ship/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m
Mode: /ship:auto staged workflow — no user questions.
Observation window: 7 days post-release.
