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
- a minimal FastAPI app entrypoint in `app/`
- environment-based configuration via `.env`
- an initial PDF extraction pipeline in `app/ingest/`
- a small unit test suite in `tests/`

The app is not yet a full RAG assistant. Retrieval, chunking, embeddings, and answer generation are still to be built. Right now the repository is in a good early state for local setup, manual smoke testing, and extraction testing.

## Initial Project Structure

- `app/` application package
- `app/ingest/` PDF extraction logic and CLI entrypoint
- `app/retrieval/` future retrieval and answer assembly logic
- `app/web/` FastAPI routes
- `documents/` source policy PDFs
- `data/` local generated artifacts such as the vector store
- `tests/` unit tests for the current scaffold and extraction layer

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

The current extraction and test steps do not require live OpenAI calls, but the key belongs in `.env` for the later RAG steps.

## Current App Surface

The current FastAPI scaffold exposes:

- `GET /` for a basic setup status response
- `GET /health` for a simple health check

Run the app locally with:

```bash
uvicorn app.main:app --reload
```

Then test it manually:

- open `http://127.0.0.1:8000/`
- open `http://127.0.0.1:8000/health`

Expected behavior:

- `/` returns a small JSON payload describing the app status and configured document paths
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

## Manual Testing

The smallest manual test loop right now is:

1. Activate the virtual environment.
2. Start the FastAPI app with `uvicorn app.main:app --reload`.
3. Open `/` and `/health` in a browser or with `curl`.
4. Run `policy-rag-extract`.
5. Inspect `data/extracted/documents.json` to confirm document and page metadata were written.

Example commands:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

In another terminal:

```bash
source .venv/bin/activate
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
policy-rag-extract
sed -n '1,80p' data/extracted/documents.json
```

## Unit Tests

Run the current unit test suite with:

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

The current tests cover:

- app setup and route smoke behavior
- whitespace normalization in extraction
- extraction output serialization
- real PDF extraction across the current `documents/` directory

## Current Limitations

- there is no chunking yet
- there is no vector store indexing yet
- there is no retrieval pipeline yet
- there is no LLM answer generation yet
- the web app is currently a scaffold, not the final user experience

See [`plan.md`](/home/zakye/policy-rag-assistant/plan.md) for the proposed MVP scope and implementation plan.
