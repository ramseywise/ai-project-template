# configs/

Non-secret, per-environment application configuration — model names, retrieval
tuning, feature flags. Secrets (API keys) live in `.env` (root), never here.

Load these via `pydantic-settings` in `src/agents/*/settings.py`,
selecting the file by an `ENVIRONMENT` env var (`dev` | `prod`) rather than hardcoding
values inline. The Terraform environments under `infrastructure/terraform/environments/`
mirror this same `dev`/`prod` split.
