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
