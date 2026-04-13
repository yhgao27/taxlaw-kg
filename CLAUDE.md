# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TaxLaw KG (税务法规知识库) - A LightRAG-based intelligent knowledge base system for Chinese tax law with knowledge graph extraction, vector search, and Q&A capabilities.

**Stack**: Vue 3 + Element Plus (frontend) | FastAPI + Redis + Neo4j + Milvus (backend) | Alibaba Qwen (LLM via DashScope API)

## Development Commands

### Backend
```bash
cd taxlaw-kg/backend
.venv/bin/activate
uvicorn app.main:app --reload --port 8000  # Dev server
```

### Frontend
```bash
cd taxlaw-kg/frontend
npm install
npm run dev  # Vite dev server on port 3000
```

## Architecture

### Data Storage (Redis-based, no SQLAlchemy)
All data stored in Redis using custom `BaseModel` classes defined in `app/database.py`:
- `User` - user accounts (prefix: `user`)
- `Document` - uploaded documents (prefix: `document`)
- `EntityType` - entity schema definitions (prefix: `entity_type`)
- `RelationType` - relation schema definitions (prefix: `relation_type`)

### Graph Storage (Neo4j)
Knowledge graph stored in Neo4j with direct Cypher queries in `app/api/v1/graph.py`. Node labels are entity types (e.g., `纳税人`, `税目`, `税率`). Relationships are relation types in UPPER_SNAKE_CASE.

### Vector Storage (Milvus)
Used by LightRAG for document chunk embeddings. Initialized via `lightrag_service.py`.

### Service Layer (`app/services/lightrag_service.py`)
- `LightRAGService` - wraps LightRAG for document insertion and entity extraction
- Direct Neo4j queries bypass LightRAG for Q&A (avoids Milvus embedding issues)
- Q&A approach: keyword extraction → Neo4j substring search → LLM context building → DashScope Generation API

## API Structure

All routes under `/api/v1/`:
- `auth.py` - login/register
- `documents.py` - document upload/CRUD
- `schema.py` - entity/relation type management
- `graph.py` - Neo4j graph nodes/edges CRUD (requires auth)
- `query.py` - Q&A endpoint

## Key Implementation Notes

### Neo4j Driver Quirks
- `node.labels` returns a `frozenset` - must convert to `list` before indexing: `labels = list(node.labels)`
- `session.run().single()` returns `None` when no records - always check for null

### File Upload (Vue + el-upload)
- With `auto-upload=false`, raw file is at `uploadFile.raw`, not `uploadFile.file`
- Multi-file: set `limit` prop and use `multiple` attribute on `el-upload` component

### DashScope API
- Embeddings: `TextEmbedding.call()` from `dashscope` package
- LLM: `Generation.call()` from `dashscope` package
- API key configured in `.env` as `DASHSCOPE_API_KEY`

## Environment Variables

Required in `taxlaw-kg/backend/.env`:
```
REDIS_URL=redis://localhost:6379
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
MILVUS_URI=http://localhost:19530
DASHSCOPE_API_KEY=your_api_key
LLM_MODEL_NAME=qwen-turbo
EMBEDDING_MODEL=text-embedding-v3
```

## Important File Paths

| Path | Purpose |
|------|---------|
| `taxlaw-kg/backend/app/main.py` | FastAPI entry point |
| `taxlaw-kg/backend/app/config.py` | Settings via pydantic |
| `taxlaw-kg/backend/app/database.py` | Redis models (BaseModel, User, Document, etc.) |
| `taxlaw-kg/backend/app/services/lightrag_service.py` | LightRAG + Neo4j Q&A logic |
| `taxlaw-kg/backend/app/api/v1/graph.py` | Neo4j graph CRUD endpoints |
| `taxlaw-kg/frontend/src/pages/Documents.vue` | Document upload UI |
| `taxlaw-kg/frontend/src/pages/Query.vue` | Q&A interface |
| `taxlaw-kg/frontend/src/pages/Graph.vue` | Knowledge graph visualization |
