# SANYI.md — change contract

project: my-project
version: 1
last-audit: pending — complete /sanyi init

<!-- Seeded by the scaffold from your copier answers. The Jianyi/Bianyi entries
     below are inferred from the scaffolded structure; 不易 Buyi CANNOT be
     inferred from code — business/safety intent isn't in any AST. Complete the
     Buyi interview with `/sanyi init` before the first review run. -->

## 不易 Buyi

<!-- TODO (interview required — /sanyi init). Admission test: something is Buyi
     only if violating it causes a security, legal, financial, or trust failure.
     Every entry needs a deterministic code-layer implementation (a prompt-only
     invariant is BY-4 debt) and must never be bypassable via config/env/flag.

     Question bank:
     - What must the agent never do, say, or promise?
     - Which compliance constraints apply (data classification here: internal)?
     - Which escalation fallbacks must always fire?
     - Which data must never leave the system boundary?
     - Which actions are irreversible, and what guards them?
     - What would a misbehaving agent concretely cost?

     Candidates from your scaffold answers (confirm, don't rubber-stamp):
     - data_sensitivity = internal
     - "make eval-gate must pass before release" — the threshold VALUES are
       Bianyi (targets.yaml); "the gate must run" is the Buyi part once you
       wire it into CI. -->

## 简易 Jianyi

### Agent response schemas

- paths: src/agents/rag_agent/schema.py
- contract: Response/state shapes are inter-component interfaces. New fields
  need justification in the PR; untyped catch-alls (dict/Any/**kwargs) are
  JY-3 unbounded growth, not "one field".
- budget: each new field needs justification; set a numeric ceiling at first
  audit
- current: baseline at first audit (pending first audit)
### Graph control flow

- paths: src/agents/rag_agent/graph.py
- contract: The execution graph is usually the dominant complexity carrier —
  a perfect schema can wrap a hellish graph. New nodes, edges, branches, or
  retry cycles need justification in the PR.
- budget: qualitative until scripted flow metrics; topology changes bump the
  contract version
- current: baseline at first audit (pending first audit)


### Eval suite topology

- paths: evals/
- contract: Top-level layout (graders/, metrics/, pipelines/, reports/,
  utils/) is fixed; new eval code fits in one of these.
- budget: no new top-level directories without a contract version bump
- current: 5 directories (pending first audit)

### MCP tool surface

- paths: mcp_servers/my-project/
- contract: Tool schemas are an external interface consumed by other agents;
  signature changes are JY-3 drift.
- budget: tool additions need justification
- current: baseline at first audit (pending first audit)

## 变易 Bianyi

### Eval targets

- paths: evals/targets.yaml
- contract: Metric thresholds live here and only here — `make eval-gate`
  reads them. A literal threshold in grader/pipeline code is BN-1.

### Agent settings

- paths: src/agents/rag_agent/settings.py
- contract: Model names, retrieval parameters, and tunables live in settings
  (env-overridable); changing a value must not require touching node/graph
  logic.


## Migrations

<!-- Empty at init. Format: - YYYY-MM-DD: <from> → <to> / <entry> — <rationale>. (author: <who>) -->

## Pending

<!-- Disputed assignments park here; enforced as Buyi until resolved. -->

## Debt

<!-- Filled by init's closing audit and by accepted review findings.
     Format: - [CODE] <location> — <one-line description> (recorded YYYY-MM-DD) -->
