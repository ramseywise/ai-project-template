# Render review — project-mgmt-ai scaffold (2026-07-16)

Four-angle review of the freshly-rendered repo (correctness, MVP-shape fit,
testability/evals, infra/deps/conventions), run as part of the genesis dry-run.
Findings consolidated into a prioritized template backlog. Repo-only fixes are
marked; everything else lands in the template first, then re-renders.

## The headline

The template's single scaffold shape is a **chat/RAG product** (FastAPI /chat,
guardrail→retrieve→generate graph, corpus ingestion, coffee-machine example data).
project-mgmt-ai is a **pipeline** (transcript → extract → score → persist). Result:
everything the MVP needs is missing, and most of what rendered is dead weight for it.
The user's live critique — "it shouldn't be rag agent or lg agent, it should start
with clients, nodes etc." — is exactly what the shape reviewer concluded independently.

## Backlog (priority order)

### B1 — pipeline scaffold shape (biggest; = friction F11)
`project_type=workflow` (and arguably `agent`) should render: an ingest→transform→
persist LangGraph skeleton with a records-shaped State (not message/answer); a CLI +
webhook entrypoint (`make process-<thing>`), no /chat; typed extraction models with an
enum discriminator + 0–100 certainty field; and when `database` ∈ agent_tools, a
first-migration stub (domain tables + tenant FK + RLS placeholders) — "in the first
migration" should be a scaffolded file, not homework. Plan-sized; needs its own
/plan-review pass.

### B2 — gate rag_agent (+ heavy deps) on actual need (= friction F9)
rag_agent ships unconditionally as "shared infra for the MCP tool" — rationale
collapses when include_mcp_server=false. It drags sentence-transformers/torch (~2GB),
psycopg/pgvector, corpus pipeline, Makefile surface, and is the eval runner's default
backend (so deleting it in a rendered repo breaks eval-heuristic). Gate it on
include_mcp_server or a needs_retrieval interview answer; decouple the eval runner's
default backend so removal doesn't break CI. Revisits backlog #2's decision.

### B3 — ship src/utils/logging.py and purge print()/stdlib logging from src/
The owner's logging rule assumes src/utils/logging.py exists; the template never
scaffolds it, so rendered code structurally CANNOT comply: print() in
lg_agent/rag_agent clients/llm.py (every LLM turn), main.py lifespans, akira nodes;
`import logging` in embeddings.py, clients/mcp.py, akira/subagents/base.py. The
scaffold fails its own advertised no-print hook. One move: ship the structlog util +
convert call sites.

### B4 — deployment_target must actually deploy something
`deployment_target=cloud` rendered an AWS ECS Fargate/ALB/ECR Terraform stack (the
answer is consumed nowhere) while DESIGN.md says Railway — no railway.toml outside
split_service. Also: terraform tfvars hardcode `data_sensitivity = "internal"` (the
copier help promises a real tag; it exists with the WRONG value — tfvars aren't
templated); docker-compose boots only lg_agent with no postgres service despite
vector_backend=postgres.

### B5 — restricted-data hardening (rendered code, data_sensitivity=restricted)
- meeting_intelligence.py json.loads + model_validate on untrusted LLM output with no
  error boundary — tracebacks can echo transcript text into logs.
- evals run.py writes golden questions/answers verbatim to stdout, JSON results, and
  HTML reports — with a restricted corpus that's raw field values in observability.
- PostgresVectorIndex.__init__ runs CREATE EXTENSION (needs superuser — fails on
  least-privilege Supabase roles even when the extension exists) and connects eagerly
  with an unvalidated possibly-empty DSN.
- lg_agent/checkpointer.py postgres branch: unguarded from_conn_string('').__enter__()
  at graph-compile → app fails to boot with a raw psycopg error + leaked half-entered
  context manager.

### B6 — integrations render with no caller (silent dead code)
main.py's try/except-ImportError mounts integrations.n8n_webhook — not scaffolded here
— so the except swallows everything and the comment misexplains why. Result:
meeting_intelligence + google_calendar rendered with zero HTTP surface or caller; app
is healthy while the project's headline feature is unreachable. The n8n router was the
only mount path for integrations — that coupling is the template bug.

### B7 — custom-grader slot in the eval harness (= friction F7) ✓ DONE 2026-07-16
targets.yaml keys must match HeuristicReport fields (all retrieval metrics), so the
project's PRIMARY metric (action_item_accuracy ≥ 0.70, the Sprint-2 go/no-go) is
structurally inexpressible — a team adding it to targets.yaml gets "n/a — skipped" and
a green gate on an unmeasured metric. Implemented: evals/graders/custom/ registry
(@register("name") def score(golden_row, generated) -> float|None), scores averaged
into HeuristicReport.custom_scores, _check_targets falls back to custom_scores, so
any registered metric is gateable with zero runner changes.

## Repo-only fixes for project-mgmt-ai (apply there, not template)
- Replace data/corpus golden_qa coffee-machine fixtures with golden transcripts
  (data/golden_transcripts/<name>.txt + <name>.expected.json) — M3/M4 work.
- Write the action_item_accuracy custom grader once B7 re-renders (or hand-copy).
- Decide rag_agent deletion (after B2 lands the eval decoupling).
- Integration-tier test for extract_action_items against the live model
  (@pytest.mark.integration) — mocked-only today.
- .env.example: verify POSTGRES_DSN/SUPABASE vars present (review agent was
  permission-blocked from reading it).
