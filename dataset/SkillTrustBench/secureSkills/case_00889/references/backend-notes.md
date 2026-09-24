# Backend Notes

## Current preferred backend

### `job-search-mcp-jobspy`

Role in project:
- primary discovery backend candidate for Step 1

Why:
- multi-board job discovery
- structured job-search filters
- strong fit for search/collect layer

Caution:
- depends on JobSpy MCP runtime and setup
- should be wrapped behind project-owned inputs/outputs

## Project rule

The backend may change later.

The project-owned wrapper contract should remain stable even if the discovery backend is replaced, supplemented, or upgraded.
