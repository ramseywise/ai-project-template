# `_mcp_ts/` — TypeScript MCP staging tree (template-internal)

This is **not** a directory in generated projects. It is the TypeScript variant of
`template/mcp_servers/{{ mcp_server_slug }}` (the Python/FastMCP variant), staged
here under an underscore-prefixed name so it can never collide with a pre-existing
repo during `copier update`.

**How the swap works** (`copier.yaml` `_tasks`):

- `mcp_server_language == "python"` (default) → `mcp_servers/{{ mcp_server_slug }}`
  is copied straight to its final path; this tree is discarded.
- `mcp_server_language == "typescript"` → the Python tree is `rm -rf`'d and this
  tree is `mv`'d into `mcp_servers/` in its place.

Either way `_mcp_ts/` is deleted at the end of generation. Edit the language
default / choices at the `mcp_server_language` question in `copier.yaml`; edit the
swap at the `_mcp_ts` `mv` task in the same file.
