# Policy RAG Assistant

A small demo project for an internal policy assistant powered by retrieval-augmented generation (RAG).

The goal is to mimic a realistic workplace tool: a user asks natural-language questions about company policies, the system retrieves relevant passages from internal policy documents, and the LLM answers using that retrieved context instead of relying on general knowledge alone.

## Project Goal

This repository is the starting point for a mini project that demonstrates a practical RAG workflow for internal documentation.

The assistant should:

- accept natural-language questions about company policies
- retrieve relevant chunks from local policy documents
- provide grounded answers based on retrieved content
- make it clear when the answer comes from policy context
- serve as a clean demo project rather than a production system

## Current Document Set

Policy source documents currently live in [`documents/`](/home/zakye/policy-rag-assistant/documents):

- `northstar-ai-acceptable-use-policy.pdf`
- `northstar-employee-handbook.pdf`
- `northstar-information-security-policy.pdf`

These files will be the initial knowledge base for retrieval and answering.

## Expected User Flow

At a high level, the application will work like this:

1. A user asks a question such as "Can I use public AI tools with company data?"
2. The system searches the indexed policy documents for relevant passages.
3. The most relevant chunks are supplied to the LLM as context.
4. The LLM answers using that context and, ideally, cites or references the source material.

## Non-Goals For The First Iteration

To keep the demo focused, the initial version should avoid production concerns such as:

- authentication and access control
- multi-user document management
- advanced observability
- continuous document syncing from external systems
- complex agent behavior

## Repository Status

This repository now has the initial project scaffold in place.

Current setup includes:

- Python project configuration in `pyproject.toml`
- a FastAPI app with both API and browser entrypoints
- environment-based configuration via `.env`
- an initial PDF extraction pipeline in `app/ingest/`
- a chunking step that produces chunk-level metadata for later retrieval
- local Chroma indexing with configurable embedding providers
- retrieval and grounded answer generation services
- a small unit test suite in `tests/`

The app is now a working MVP prototype. It can ingest the local policy PDFs, build a local vector index, retrieve matching chunks, and return grounded answers through both a JSON API and a simple browser UI.

## Initial Project Structure

- `app/` application package
- `app/ingest/` extraction, chunking, and indexing CLI logic
- `app/retrieval/` embedding, retrieval, and answer generation logic
- `app/assistant.py` orchestration service for end-to-end question answering
- `app/web/` FastAPI routes
- `documents/` source policy PDFs
- `data/` local generated artifacts such as the vector store
- `tests/` unit tests for ingestion, retrieval, API behavior, and answer generation

## Quickstart

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

If you are already using the environment and want to leave it later:

```bash
deactivate
```

### 2. Install the project

With the virtual environment activated:

```bash
python -m pip install -e .
```

### 3. Configure environment variables

Copy [`.env.example`](/home/zakye/policy-rag-assistant/.env.example) to `.env` and set your real `OPENAI_API_KEY`.

Example:

```bash
cp .env.example .env
```

The default MVP path does not require live OpenAI calls because embeddings default to a local provider and answers default to an extractive grounded response. You can switch to OpenAI-backed embeddings or answer generation later through environment variables.

## Current App Surface

The current FastAPI app exposes:

- `GET /` for the browser demo UI
- `GET /api/status` for basic app status and paths
- `POST /api/ask` for the grounded question-answer API
- `GET /health` for a simple health check

Run the app locally with:

```bash
uvicorn app.main:app --reload
```

Then test it manually:

- open `http://127.0.0.1:8000/`
- open `http://127.0.0.1:8000/api/status`
- open `http://127.0.0.1:8000/health`

Expected behavior:

- `/` shows a browser-based policy assistant UI
- `/api/status` returns JSON describing the app status and configured paths
- `/health` returns a JSON health response such as `{"status":"ok","environment":"development"}`

## PDF Extraction

The repository now includes an initial extraction step for local policy PDFs.

With the virtual environment activated, run:

```bash
policy-rag-extract
```

This command:

- reads all `*.pdf` files from `documents/`
- extracts text page by page
- normalizes whitespace
- preserves document name and page number metadata
- writes the result to `data/extracted/documents.json`

To inspect the generated extraction output:

```bash
sed -n '1,80p' data/extracted/documents.json
```

You can also override paths:

```bash
policy-rag-extract --documents-dir documents --output data/extracted/documents.json
```

## Chunking

The repository now includes a chunking step built on top of the extracted page text.

With the virtual environment activated, run:

```bash
policy-rag-chunk
```

This command:

- reads the local PDFs from `documents/`
- extracts text page by page
- splits each page into overlapping chunks
- preserves chunk metadata including document name, page number, chunk index, and character offsets
- writes the result to `data/chunks/chunks.json`

You can adjust chunking parameters:

```bash
policy-rag-chunk --chunk-size 900 --chunk-overlap 150
```

## Indexing

The repository now includes a local indexing command that writes chunk embeddings to Chroma.

With the virtual environment activated, run:

```bash
policy-rag-index --reset
```

This command:

- reads the local PDFs from `documents/`
- extracts and chunks the source text
- creates embeddings using the configured embedding provider
- upserts chunk records into the local Chroma store at `data/chroma/`

Notes:

- the default prototype mode uses `EMBEDDING_PROVIDER=local`
- set `EMBEDDING_PROVIDER=openai` to use the configured OpenAI embedding model
- OpenAI mode requires a valid `OPENAI_API_KEY` and network access
- `--reset` clears the current collection before re-indexing

## Manual Testing

The smallest manual test loop right now is:

1. Activate the virtual environment.
2. Start the FastAPI app with `uvicorn app.main:app --reload`.
3. Run `policy-rag-extract`.
4. Run `policy-rag-chunk`.
5. Run `policy-rag-index --reset` once to build the local index.
6. Open `/` in a browser and ask a policy question.
7. Check `/api/status` and `/health`.
8. Optionally hit `POST /api/ask` directly.
9. Inspect the generated JSON artifacts and local vector store to confirm indexing completed.

Example commands:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

In another terminal:

```bash
source .venv/bin/activate
policy-rag-index --reset
curl http://127.0.0.1:8000/api/status
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/api/ask \
  -H 'content-type: application/json' \
  -d '{"question":"Can I put customer data into a public AI tool?"}'
policy-rag-extract
sed -n '1,80p' data/extracted/documents.json
policy-rag-chunk
sed -n '1,120p' data/chunks/chunks.json
```

## Unit Tests

Run the current unit test suite with:

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

The current tests cover:

- app setup and route smoke behavior
- assistant orchestration and API response shaping
- whitespace normalization in extraction
- extraction output serialization
- real PDF extraction across the current `documents/` directory
- chunk generation and chunk metadata capture
- Chroma indexing, metadata persistence, and reset behavior
- retrieval ranking and metadata return
- grounded answer generation with source metadata

## Current Limitations

- the default local answer mode is extractive and less fluent than an LLM-backed answer
- the browser UI is intentionally simple and built for demo use
- there is no conversation memory yet
- there is no authentication or multi-user support yet
- document updates still require manual re-indexing

See [`plan.md`](/home/zakye/policy-rag-assistant/plan.md) for the proposed MVP scope and implementation plan.
