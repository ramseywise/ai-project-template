# Evals

Heuristic eval suite, run independently against every retrieval backend
actually present in this project — see `pipelines/run.py`'s `BACKENDS` list
(`rag_agent`'s embeddings).
the ADK chat agent has no entry of its own since it routes retrieval through MCP and
inherits its coverage. Everything here runs without an LLM call or API key for
the retrieval grade itself — it grades retrieval quality and (best-effort,
when a key is available) coarse answer overlap against a small golden QA set.
It is not a substitute for an LLM-judge eval; it's a fast, free, CI-safe smoke
check that catches retrieval regressions.

## Layout

```
evals/
├── graders/    heuristic grading functions (retrieval hit/rank, answer token overlap)
├── metrics/    pure aggregate metrics (hit_rate, mean_reciprocal_rank)
├── pipelines/  CLI entrypoint (run.py) — the only place that wires graders + metrics together
├── reports/    output/ holds generated JSON + HTML (gitignored, regenerated per run)
└── utils/      shared helpers, currently empty
```

## The golden QA set

`data/corpus/golden_qa.jsonl` has 10 rows, each shaped like:

```json
{"id": "qa_001", "question": "How often should I descale the machine?",
 "expected_answer": "Every 2-3 months, or when the descale light turns on.",
 "source_article": "descaling", "category": "maintenance"}
```

`source_article` is the article `id` (the corpus filename stem, e.g.
`descaling` for `data/corpus/descaling.md`) that a well-behaved retriever
should surface for that question.

## How grading works

For each backend, for each row:

1. The backend's own search function (`core.index.search` for the LangGraph chat agent's BM25
   index, `agents.rag_agent.vectorstore.get_vector_index().similarity_search` for
   `rag_agent`'s embeddings — backend picked by `vector_backend`: duckdb/memory/
   opensearch) returns the top-k `SearchResult`s, wrapped into a common shape so
   the graders below don't care which backend produced them.
2. `evals.graders.citation.grade_retrieval` checks whether `source_article`
   appears among the result ids, and at what (1-indexed) rank.
3. If `ANTHROPIC_API_KEY` is set, the pipeline also invokes that backend's own
   agent graph to generate an answer and grades it with
   `evals.graders.citation.grade_answer_overlap` — a token-overlap ratio
   against `expected_answer`. Without a key this step is skipped and the
   report notes it as `n/a`; the retrieval grading is unaffected either way.
4. `evals.metrics.retrieval.hit_rate` and `.mean_reciprocal_rank` aggregate
   the per-row ranks into two summary numbers.

## Running it

```
make eval-heuristic   # == python -m evals.pipelines.run heuristic
make eval-render      # == python -m evals.pipelines.run render
```

Both commands loop over every backend in `BACKENDS`. `eval-heuristic` requires
each backend's vector DB to exist first — run `make rag-corpus-ingest` (`rag_agent`) if you see a "vector DB not
found" error. It prints a per-backend summary table to stdout and writes
`reports/output/heuristic_results_{backend}.json` for each.

`eval-render` reads each backend's JSON file and writes a minimal static HTML
table to `reports/output/heuristic_report_{backend}.html` — open it in a
browser. It errors clearly if you run it before `eval-heuristic` has produced
that backend's results file.

Everything under `reports/output/` is generated, not committed — see the root
`.gitignore`.

