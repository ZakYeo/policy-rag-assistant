# Policy RAG Assistant

A small demo project for an internal policy assistant powered by retrieval-augmented generation (RAG).

It mimics a realistic workplace tool: a user asks natural-language questions about company policies, the system retrieves relevant passages from internal policy documents, and the answer is generated from that retrieved context instead of relying on general knowledge alone.

## Capabilities And Features

- browser-based UI for asking policy questions
- `POST /api/ask` JSON API for grounded answers
- local PDF ingestion from the `documents/` directory
- page-level extraction and chunk-level metadata capture
- document routing before chunk retrieval
- local Chroma vector indexing
- selectable answer modes: `openai` and `extractive`
- inline source references and surfaced retrieved chunks
- backend-only handling of OpenAI credentials
- isolated RAG integration tests against the current fake PDF corpus
- unit test coverage across ingestion, routing, retrieval, answering, and API behavior

<img width="2559" height="1282" alt="image" src="https://github.com/user-attachments/assets/58c308ba-42a2-4bbb-a65f-69b92963fb0b" />
<img width="1240" height="1148" alt="image" src="https://github.com/user-attachments/assets/3f95d0a2-0fa6-4d95-8f40-545f7a7110de" />


## Current Document Set

Policy source documents currently live in [`documents/`](/home/zakye/policy-rag-assistant/documents):

- `northstar-ai-acceptable-use-policy.pdf`
- `northstar-employee-handbook.pdf`
- `northstar-information-security-policy.pdf`

These are intentionally fake sample PDFs created for the demo. They act as the project’s internal policy corpus for retrieval and answering.

## User Flow

The current application flow is:

1. A user asks a question such as "Can I use public AI tools with company data?"
2. The backend routes the question to the most relevant policy document or documents.
3. Chunk retrieval runs only against those routed documents.
4. The selected answer mode generates a grounded response from the retrieved chunks.
5. The UI shows the answer, routed documents, sources, and retrieved chunk context.

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
- document routing that can choose relevant PDFs before chunk retrieval
- retrieval and grounded answer generation services
- a small unit test suite in `tests/`
- a separate RAG integration test suite in `integration_tests/`

The app is now a working MVP prototype. It can ingest the local policy PDFs, build a local vector index, route each question to the most relevant documents, retrieve matching chunks, and return grounded answers through both a JSON API and a simple browser UI.

## Initial Project Structure

- `app/` application package
- `app/ingest/` extraction, chunking, and indexing CLI logic
- `app/retrieval/` document catalog, routing, embedding, retrieval, and answer generation logic
- `app/assistant.py` orchestration service for end-to-end question answering
- `app/web/` FastAPI routes
- `documents/` source policy PDFs
- `data/` local generated artifacts such as the vector store
- `integration_tests/` end-to-end RAG tests for the current sample corpus
- `scripts/` repo-local test runner commands
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
python3 -m pip install -e .
```

If you want to run the full test toolchain, including the RAGAS-based integration evaluation:

```bash
python3 -m pip install -e ".[dev]"
```

### 3. Configure environment variables

Copy [`.env.example`](/home/zakye/policy-rag-assistant/.env.example) to `.env` and set your real `OPENAI_API_KEY`.

Example:

```bash
cp .env.example .env
```

The default MVP answer mode is now `openai`, while embeddings still default to the local provider. That means the browser UI will try to use OpenAI for answer generation unless you switch it to `extractive`. You can control both behaviors through environment variables.

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
- the UI includes an `Answer mode` toggle with `OpenAI` selected by default
- `/api/status` returns JSON describing the app status and configured paths
- `/health` returns a JSON health response such as `{"status":"ok","environment":"development"}`

### UI Answer Mode Toggle

The browser UI lets you choose between two answer modes:

- `OpenAI`: sends the retrieved chunks to the backend OpenAI chat provider for a more natural response
- `Extractive`: returns a grounded extractive answer built directly from the retrieved chunks without calling OpenAI

Important notes:

- the API key stays on the backend only and is never exposed to the frontend
- the frontend sends only the selected answer mode, never any secret
- if `OpenAI` is selected but the backend is missing `OPENAI_API_KEY`, lacks network access, or hits provider errors, the UI shows the backend error message instead of silently failing

## Document Routing

Before chunk retrieval runs, the backend now performs a document-routing step to decide which policy PDFs are relevant to the user’s question.

Current behavior:

- the router can use OpenAI to choose the most relevant documents from the policy catalog
- if OpenAI routing is unavailable, the backend falls back to a heuristic router
- chunk retrieval then runs only against the routed documents instead of the full corpus

This keeps retrieval narrower and more intentional, especially as the document set grows.

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
- the default answer mode uses `ANSWER_PROVIDER=openai`
- set `EMBEDDING_PROVIDER=openai` to use the configured OpenAI embedding model
- set `ANSWER_PROVIDER=extractive` if you want non-LLM answers by default
- OpenAI answering requires a valid `OPENAI_API_KEY` and network access
- `--reset` clears the current collection before re-indexing

## Manual Testing

The smallest manual test loop right now is:

1. Activate the virtual environment.
2. Start the FastAPI app with `uvicorn app.main:app --reload`.
3. Run `policy-rag-extract`.
4. Run `policy-rag-chunk`.
5. Run `policy-rag-index --reset` once to build the local index.
6. Open `/` in a browser, keep `OpenAI` selected or switch to `Extractive`, and ask a policy question.
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
  -d '{"question":"Can I put customer data into a public AI tool?","answer_provider":"openai"}'
curl -X POST http://127.0.0.1:8000/api/ask \
  -H 'content-type: application/json' \
  -d '{"question":"Can I put customer data into a public AI tool?","answer_provider":"extractive"}'
policy-rag-extract
sed -n '1,80p' data/extracted/documents.json
policy-rag-chunk
sed -n '1,120p' data/chunks/chunks.json
```

## Unit Tests

The regular unit test suite covers the internal building blocks of the app and runs separately from the RAG integration suite.

Run it with:

```bash
source .venv/bin/activate
python3 -m unittest discover -s tests -v
```

The current unit tests cover:

- app setup and route smoke behavior
- assistant orchestration and API response shaping
- whitespace normalization in extraction
- extraction output serialization
- real PDF extraction across the current `documents/` directory
- chunk generation and chunk metadata capture
- Chroma indexing, metadata persistence, and reset behavior
- retrieval ranking and metadata return
- document routing and router fallback behavior
- grounded answer generation with source metadata
- backend error handling for answer-provider failures

## RAG Integration Tests

The integration suite validates the actual MVP RAG pipeline against the current sample PDFs and produces a timestamped JSON report for each run.

Each run:

- extracts the PDFs from `documents/`
- chunks the extracted text
- embeds and indexes the chunks into a temporary local Chroma store
- runs sample policy questions through routing, retrieval, and extractive answering
- checks the returned answers and routed documents against expected outcomes for this corpus
- scores the run with RAGAS metrics and compares the summary values to thresholds

The test workspace is isolated per run and uses a temporary directory, so it does not mutate the main app data under `data/`.

Run the integration suite with the repo-local command:

```bash
./scripts/run_rag_integration_tests.sh
```

If you have installed the project entrypoints into your virtual environment, you can also run:

```bash
policy-rag-integration-tests
```

By default, the command runs:

- the end-to-end integration tests in `integration_tests/`
- deterministic RAGAS retrieval metrics:
- `id_based_context_precision`
- `id_based_context_recall`
- `nonllm_context_precision`
- `nonllm_context_recall`

Each run writes a report to `data/rag-test-reports/` using the format:

```text
rag-test-run-YYYYMMDD-HHMMSS.json
```

If you want to include the OpenAI-backed RAGAS answer-quality metrics as well, enable them explicitly:

```bash
RAGAS_ENABLE_LLM_METRICS=1 ./scripts/run_rag_integration_tests.sh
```

When enabled, the report also includes:

- `faithfulness`
- `answer_relevancy`

This opt-in mode requires a valid backend `OPENAI_API_KEY` and network access. The default integration command keeps those LLM metrics disabled so the suite remains fast and runnable in offline environments.

The current integration cases cover:

- prohibited public-AI use with customer data
- employee core working hours
- lost company laptop incident reporting
- password-sharing guidance
- remote-work allowance rules

<img width="896" height="1240" alt="image" src="https://github.com/user-attachments/assets/87aae80d-3682-437c-9f53-439e32068808" />


## Current Limitations

- OpenAI is the default answer mode, so missing backend API configuration will surface as an explicit UI/API error until you configure it or switch to `extractive`
- the extractive fallback is grounded but less fluent than an LLM-backed answer
- the browser UI is intentionally simple and built for demo use
- there is no conversation memory yet
- there is no authentication or multi-user support yet
- document updates still require manual re-indexing
