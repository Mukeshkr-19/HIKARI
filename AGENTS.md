# HIKARI - Agent Context

## Project Overview
Personal AI assistant project with multi-agent architecture and voice capabilities.

## Structure
- **agents/** - Agent implementations (code, voice, files, research, system)
- **core/** - Core modules (router, orchestrator, voice, semantic_memory, etc.)
- **security/** - Authentication (enhanced_auth, auth)
- **skills/** - Skill system for extending capabilities
- **data/** - User data (personality, preferences, memory, knowledge graph)
- **tests/** - Unit tests

## Key Files
- `hikari.py` - Main entry point
- `services/hikari_daemon.py` - Background daemon
- `core/server.py` - API server
- `docs/QUICKSTART.md` - Quick start guide

## Configuration
- `.env` - Environment variables
- `config/providers.yaml` - API provider configuration

## Available Agents
- code - Code generation/analysis
- voice - Voice interaction
- files - File operations
- research - Research/web search
- system - System operations

## Dependencies
- Python 3.12+
- FastAPI
- PostgreSQL (optional)
- Various LLM providers (configurable in providers.yaml)

## Quick Start
```bash
cd HIKARI
python hikari.py
# or
python hikari.py --server
```
