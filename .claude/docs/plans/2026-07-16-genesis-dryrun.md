# Genesis dry-run (friction log + render review)
Date: 2026-07-16
Status: EXECUTED

---

# Genesis dry-run friction log

Date: 2026-07-16
Setup: live end-user test of `/scope-poc` → `/project-genesis`, user = ramsey as DSSG
platform engineer, target = a real DSSG initiative. Every entry is a UX defect or
gap observed while running the flow for real — each should end as a template fix.

## Friction entries

### F1 — scope-poc's DSSG context block is stale
The skill's §DSSG block knows two projects (nonprofit-success-ai, project-mgmt-ai).
dssg/roadmap.md + .claude/docs/milestones/sequencing.md (2026-07-16) define five
initiatives — kb-platform-api (first in planning order), customer-portal,
portal-assistant (broken out of the portal plan), project-mgmt-ai, cohort-template —
plus resolved decisions the block doesn't know (LangGraph chosen 2026-07-16; PM-AI is
sole writer of Engagement.stage; comms folds into platform-api). The interview would
have offered a stale project menu and re-asked settled questions.
**Fix direction**: the DSSG context doesn't belong hardcoded in the template's skill at
all — it belongs in the org workspace (e.g. dssg/.claude/ context file) that the skill
*reads at runtime* when detection fires. Hardcoding org state in a template guarantees
staleness and makes the template non-portable for other teams.

### F2 — end user conflated the three decision axes
When asked about the PF-2 gate, the user answered "im so confused now whether this
should be vercel agent, langgraph agent or one of the supabase/firebase" — framework,
database, and deployment collapsed into one anxiety. The interviewer's own question
contributed (mixed a governance gate with scaffold posture in one prompt).
**Fix direction**: scope-poc Step 1 should open agent-shaped interviews with a 3-row
disambiguation ("framework = how the AI code is written; database = where data lives;
deployment = where it runs — independent decisions"), and never bundle governance
gates with technical choices in a single question.

### F3 — Step 0 only looks for DESIGN.md; the answers lived in milestones docs
dssg/.claude/docs/milestones/project-mgmt-ai.md M2 literally listed the copier
arguments (vector_backend=postgres, include_meeting_intelligence, primary_chat_agent=
lg_agent). scope-poc's Step 0 checks only for an existing DESIGN.md, so a faithful
run would have re-interviewed the user on decisions their planning docs had already
written down.
**Fix direction**: Step 0 should scan the workspace for roadmap/milestone/plan docs
(.claude/docs/milestones/*, roadmap.md, plans/*) and treat them as pre-answered
sources, same as DESIGN.md.

### F4 — genesis has no existing-repo conflict story
The target repo already had README.md (tracked) and .claude/docs/{DESIGN.md,plans/}
(untracked). Rendering required --overwrite, a manual scratchpad backup of the
untracked files, and a post-render `git checkout -- README.md`. The skill's Step 4
says nothing about any of this; an end user running it verbatim would have clobbered
their README and had no recovery for untracked docs.
**Fix direction**: genesis Step 4 should, for a non-empty output dir: snapshot
untracked collision paths, render, then restore user-owned files (README.md at
minimum) and report exactly what the template overwrote.

### F5 — the raw copier command is operator-hostile
15 -d flags in one command; even the operator (Claude) dropped the positional source
arg on the first attempt and burned a debugging cycle on a misleading grep count.
**Fix direction**: genesis Step 4 should write the answer set to a temp answers file
and pass --data-file, or the Makefile should gain a `render FROM_ANSWERS=...` target —
one mistake-proof invocation instead of a 15-flag shell line.

### F6 — legacy toggle names vs new interview axes need a documented mapping
The milestone doc (written against the old flat interview) pinned include_calendar_
integration / include_meeting_intelligence; the new interview derives those from
external_systems=[calendar,...] and optional_features=[meeting_intelligence,...].
The mapping was done in the operator's head. Both forms work (-d include_*=true still
honored), but nothing documents the equivalence.
**Fix direction**: a short "legacy toggle → new axis" table in genesis SKILL.md (or
copier.yaml comments) so pre-rework planning docs stay actionable.

### F7 — the project's PRIMARY metric has no home in the eval harness
The Sprint-1 go/no-go metric is action_item_accuracy ≥ 0.70 (graded transcript
sample). targets.yaml keys must match HeuristicReport fields (hit_rate, mrr,
answer_overlap) — all retrieval-shaped. The single most important metric of this
real project cannot be expressed in the generated harness; it lives only in
DESIGN.md prose. This is exactly the "metrics for the project for eval harness"
promise the template makes.
**Fix direction**: evals/ needs a custom-grader slot — e.g. graders/custom/*.py
each exposing `name` + `score(golden_row, output) -> float`, auto-registered into
HeuristicReport as dynamic fields so targets.yaml can gate on them. This is the
biggest genuine capability gap the dry-run found.

### F8 — inherited decisions were never owned by the user
The interview treated "LangGraph — resolved 2026-07-16 per roadmap" as settled and
moved on. The user's post-render reaction: "we didn't decide on langgraph did we? but
does it work well? how can we test it?" Docs saying resolved ≠ the human in the room
owning the decision — the interview optimized for not re-asking and lost the moment
where the user ratifies (or reopens) each inherited choice.
**Fix direction**: when Step 0 pre-fills decisions from docs, the interview must
surface them as one-line ratification checkpoints ("your roadmap resolved X on
<date> — confirm, or reopen?") before building on them. Skipping the question is
right; skipping the *consent* is not.

### F9 — capabilities ship without consent (rag_agent)
"is rag needed? we don't know" — correct: DESIGN.md puts retrieval in kb-platform-api,
yet rag_agent (embeddings, sentence-transformers/torch, corpus pipeline) rendered
anyway because the template treats it as unconditional shared infra backing the MCP
tool. This render has include_mcp_server=false, so that rationale doesn't even apply.
"We should always ask first before we build."
**Fix direction**: (a) interview asks "does the MVP itself need retrieval?" explicitly;
(b) template change — gate rag_agent (+ its heavy deps + corpus pipeline) on
include_mcp_server or a needs_retrieval answer instead of always-on. Revisits backlog
item #2's "rag_agent never becomes optional" decision, which was made when the MCP
tool was assumed present.

### F10 — no "add it later" story is ever surfaced
The user's instinct: "scaffold all at once but be able to somehow add things later if
needed." The mechanism exists — re-run copier with changed answers / `copier update`
against the answers file — but neither skill ever tells the user, so the interview
feels like a one-shot, all-or-nothing commitment, which pushes people toward
over-scaffolding.
**Fix direction**: genesis Step 5's report must state the add-later path explicitly
(which file records the answers, and the exact re-render command to flip a toggle on
later).

### F11 — the template has no pipeline shape
The PM-AI MVP is clients + nodes + DB writes (MeetingProcessor), not a chat service —
"it shouldn't be rag agent or lg agent but should start with clients, nodes etc."
Every project_type currently renders chat-shaped FastAPI /chat agents. project_type=
workflow/agent should be able to scaffold a pipeline skeleton (typed models, clients/,
graph nodes/, a CLI/webhook entrypoint, `make run-pipeline`) instead.
**Fix direction**: pending the architecture reviewer's findings — likely a new
scaffold shape, the biggest template evolution item after F7.

## Outcome

Dry-run completed end-to-end (2026-07-16): DESIGN.md written from docs + 6 structured
answers; render into the real existing repo succeeded with all 13 pinned/derived
values landing correctly; README restored; DESIGN.md carried over the stub;
targets.yaml seeded (hit_rate 0.8); uv sync + make lint-check + 38 unit tests green
on the first try. The template's mechanical path works; the friction is all in
discovery (F1, F3), user comprehension (F2), and edges (F4–F7).

---

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
