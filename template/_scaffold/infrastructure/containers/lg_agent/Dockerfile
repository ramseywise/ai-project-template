# Dockerfile for the example lg_agent service (src/agents/lg_agent).
#
# NOTE on `src`: this repo's convention only Jinja-templates a file when it needs
# a variable (see Makefile.jinja for {{ source_root }}). Dockerfiles aren't
# templated here — we hardcode the default `source_root` value ("src", per
# copier.yaml) instead of renaming this to Dockerfile.jinja. If you change
# `source_root` at generation time, update the COPY/ENV lines below to match.
#
# Build context is the project root (see docker-compose.yml `build.context: ../../..`)
# because the app needs src/, core/, pyproject.toml, and uv.lock together.

FROM python:3.12-slim

# Keep in sync with the `python_version` copier variable (default "3.12").

# uv installs itself via the official static binary — avoids a pip bootstrap step.
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency manifests first so `uv sync` is cached unless deps change.
COPY pyproject.toml uv.lock* ./

# --no-dev: skip the dev/notebooks dependency groups (pytest, ruff, marimo, ...) —
# this is a runtime image, not a dev environment.
# --frozen: fail instead of silently re-resolving if uv.lock is missing/out of date.
RUN uv sync --no-dev --frozen

# Now copy the actual source. `core/` and `src/` are the only two top-level trees
# the running app imports from (see pyproject.toml [tool.uv] package = false
# comment — "agents" and "core" are made importable via PYTHONPATH, not a build).
COPY src/ ./src/
COPY core/ ./core/

# Mirrors the Makefile's `PYTHONPATH={{ source_root }}:. uv run ...` convention:
# "src" makes `agents.lg_agent` importable, "." (== /app) makes `core` importable.
ENV PYTHONPATH=/app/src:/app

ARG LG_PORT=8010
ENV LG_PORT=${LG_PORT}
EXPOSE ${LG_PORT}

# Bare uvicorn invocation, matching `make lg-up` (no `uv run` needed since the
# venv uv created is already on PATH via `uv sync`'s .venv — we activate it by
# calling the venv's uvicorn directly rather than re-invoking `uv run`, which
# would require the pyproject/uv.lock context again at runtime).
CMD ["sh", "-c", ".venv/bin/uvicorn agents.lg_agent.main:app --host 0.0.0.0 --port ${LG_PORT}"]
