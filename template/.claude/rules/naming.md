# Naming & layering — role-based directory convention

Directory names encode a **role** (what the code does), not a topic. The same topic word
(`corpus`, `agent`, `eval`) may legitimately appear in more than one layer — but each
occurrence must be doing a *different job*, and code must live in the layer whose job it
does. Two occurrences doing the *same* job, or code filed in the wrong layer, is the smell
this rule catches.

## The layers

| Layer | Owns | Never contains |
|-------|------|----------------|
| `data/` | **artifacts** — raw docs, fixtures, golden sets (`.md`, `.jsonl`, samples) | executable pipeline code |
| `core/` (`core/pipelines/`) | **ingestion + preprocessing** — crawl/fetch external data, clean, normalize, chunk. Produces a *processed corpus artifact*. | model/embedding code, retrieval, serving |
| `source/` (rendered `src/`) | **serving** — agent loops, integrations, middleware, **and RAG index-build/retrieval** (embed → vector index → query). Consumes the processed corpus. | raw-data ETL (crawl/clean belongs in `core/`) |

The seam: **`core` produces a processed corpus; `source` consumes it to build and query a
retrieval index.** Embedding and vector-index construction are *serving* infrastructure
(coupled to the vector store / retrieval framework), so they live in `source/`, not `core/`.

## Rules

1. **`data/` holds artifacts, never code.** A `.py` under any `data/` dir is misfiled.
2. **`core/` is ETL only.** Crawl, fetch, clean, chunk. If a module imports an embedding
   model or a vector store, it belongs in `source/`, not `core/`.
3. **RAG index/retrieval lives in `source/`** (`source/rag/` or `source/agents/*_agent/`),
   never in `core/`. `index.py` (embed + build index) is the canonical piece that must NOT
   sit under `core/`.
4. **Same name in two layers is allowed only if the jobs differ.** `data/corpus/`
   (artifacts) and `core/pipelines/corpus/` (ETL that reads them) is fine — different roles.
   Two modules named `corpus` both doing ETL is a duplicate; consolidate.
5. **No language suffix in rendered trees.** `backend-py` / `backend-ts` are template
   *staging* names only; they render to plain `backend/` unless a project genuinely runs
   two backends. (See the template redesign plan for the staging↔rendered split.)

## Smells this rule names (for the review check)

- `naming-collision` — same dir/module name in two role-layers where both do the same job.
- `layer-violation` — code filed in the wrong layer: RAG index/embedding code under
  `core/`; ETL (crawl/clean) under `source/`; executable code under `data/`.

These are **advisory** (`[Non-blocking]` by default; `[Nit]` for a bare name overlap that is
role-justified but confusing). A deliberate, documented placement in a repo's own `CLAUDE.md`
overrides this rule — flag only genuine drift.
