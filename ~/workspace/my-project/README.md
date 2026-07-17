# My Project

TODO: describe this project

Scaffolded by `ai-project-template` — working example agent(s) over the same
tiny FAQ corpus:
`src/agents/rag_agent` (embedding-based semantic retrieval,
standalone service — the shared retrieval backend the MCP tool calls).
 Plus `/akira`, a proactive quality-scan skill
(vendored `akira-scan` agent — see `.claude/skills/akira/SKILL.md`).
Plus the project shell (evals, infra, tests, CI) to build real agents on top
of. See `CLAUDE.md` for AI-assistant conventions and `.agents/skills/README.md`
for the ADK/LangGraph framework reference library.

## Quick start

```bash
./project_init.sh                          # uv sync, .env from example, git init if needed
make rag-corpus-ingest                      # build rag_agent's embedding index from data/corpus/
make rag-up && make rag-wait && make rag-chat   # start + smoke test rag_agent
```



## Layout

```
my-project/
├── src/agents/rag_agent/  Working example: embedding-based retrieval, standalone service
├── core/                                Corpus ingestion + preprocessing (feeds every backend's index)
├── data/corpus/                         Example FAQ corpus (swap this out for your own)
├── evals/                     Eval suite (graders metrics pipelines reports utils)
├── nbks/                                Marimo notebooks — inspection, not production code
├── tests/                               unit / smoke / integration
├── infrastructure/                      docker-compose + Dockerfiles, Terraform skeleton
├── configs/                             Per-environment config (non-secret)
├── .claude/                             Claude Code skills + hooks
├── .claude/docs/companion/              Living "how we work" doc — see /grow-companion, /dream
└── .agents/skills/                      ADK/LangGraph framework reference library
```

## Building your own agent

The example agent is a starting point, not the point. Once you understand it:

```
/new-agent <name> --framework langgraph   # or --framework adk
```

reads `.agents/skills/framework-selection` (if you haven't already decided) and
scaffolds a new agent next to the existing one(s) under `src/agents/`.
See `.claude/skills/new-agent/SKILL.md`.

## Replacing the example corpus

`data/corpus/*.md` is a placeholder "Acme Coffee Machine" FAQ set so the example
agent has something real to retrieve over. Delete it, drop your own markdown files
in `data/corpus/`, and re-run `make corpus-ingest`. `core/ingestion.py` expects each
file to start with a single `# Title` line; everything else is body text.

## Everyday commands

See the `Makefile` for the full list (`rag-corpus-ingest`/`rag-up`/`rag-down`/`rag-chat`,
`eval-heuristic`/`eval-render`, `nbks-corpus`, `test`/`test-smoke`/`test-integration`,
`lint`/`typecheck`, `docker-up`/`docker-down`).

## Deploying

See `infrastructure/README.md` for the local Docker Compose flow and the Terraform
skeleton under `infrastructure/terraform/` (defaults to `eu-central-1`).

## Integrations

**n8n calling this project** (outbound from n8n's perspective): every agent's
`POST /chat` (and `rag_agent`'s `POST /api/v1/retrieval`) is plain JSON over
HTTP — callable directly from n8n's HTTP Request node. None of the FastAPI apps require auth out of the box — add an
API-key check before exposing one outside a private network.
