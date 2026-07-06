# ricco-ai — MOVED

> ⚠️ **This repository has been migrated.**

The code from this repository is now part of the `ai` monorepo:

**New location**: https://github.com/grootme/ai/tree/main/services/ricco-ai

## What happened

- The `ricco-ai` project (LLM Agents/RAG/MCP service (FastAPI + LangChain + Qdrant)) was migrated to `ai/services/ricco-ai/` using `git filter-repo`, preserving the full git history.
- Large binary files were stripped from the history to reduce repo size.

## Upstream sync

This repo is kept as an **upstream remote** in the `ai` monorepo so changes pushed here can be pulled into the monorepo. A daily GitHub Action runs `sync-upstream.sh` to detect and sync new commits.

See [architecture/processes/sync-upstream.md](https://github.com/grootme/architecture/blob/main/processes/sync-upstream.md) for the full sync procedure.

## This repository

This repository is kept for historical reference and upstream sync. Direct development should happen in the monorepo.

## Related

- [ai monorepo](https://github.com/grootme/ai)
- [GOVERNANCE.md](https://github.com/grootme/ai/blob/main/GOVERNANCE.md)
- [architecture repo](https://github.com/grootme/architecture)
