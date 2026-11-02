# Development guide

[Back to the README](../README.md)

## Setup

- Follow the [local quickstart](../README.md#run-locally).
- Use Python 3.12 and Node.js 22.19+ within the Node 22 line for the pinned environment.
- Keep `.env`, `.venv`, `node_modules` and generated data out of Git.
- Dependency date checks cover pinned direct and transitive packages before installation. See [validation notes](../validation/README.md#package-release-policy).

## Configuration

Settings come from environment variables or a root `.env` file. Start with [`.env.example`](../.env.example).

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | Empty | Required for OpenAI routing, answers or embeddings |
| `OPENAI_CHAT_MODEL` | `gpt-4.1-mini` | Routing and answer model |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Model when using OpenAI embeddings |
| `ROUTER_PROVIDER` | `openai` | `openai` or `heuristic` |
| `ANSWER_PROVIDER` | `openai` | API default: `openai` or `extractive` |
| `EMBEDDING_PROVIDER` | `local` | `local` or `openai` |
| `DOCUMENTS_DIR` | `documents/` | Seed PDFs imported on first use |
| `VECTOR_STORE_DIR` | `data/chroma/` | Legacy index location; its parent also holds managed policy data |
| `RETRIEVAL_TOP_K` | `4` | Default number of retrieved chunks |

- The UI's **Answer style** explicitly selects the answer provider; it starts on OpenAI independently of `ANSWER_PROVIDER`.
- Selecting direct extracts does not change routing. Use `ROUTER_PROVIDER=heuristic` to avoid OpenAI routing calls.
- OpenAI failures appear in the UI. The app does not silently replace a failed OpenAI answer with an extractive answer.
- If OpenAI routing cannot be configured, the router can fall back to heuristics. A failed routing request is not an automatic retry through another provider.
- Changing the embedding provider or model requires a compatible, freshly rebuilt index. Do not query vectors created with a different embedding model.

## Run without OpenAI

With the virtual environment active, start the app with local providers:

```bash
ROUTER_PROVIDER=heuristic EMBEDDING_PROVIDER=local ANSWER_PROVIDER=extractive \
  uvicorn app.main:app --reload
```

- Open [localhost:8000](http://localhost:8000).
- Select **Direct policy extracts (Extractive)** before submitting a question.
- For API requests, set `answer_provider` to `extractive` as in the example below.
- This mode uses no OpenAI calls. It still needs the dependencies and built frontend installed.

## Frontend development

Run the backend on port 8000, then in another terminal:

```bash
cd frontend
npm run dev
```

- Vite proxies API requests to the backend.
- `npm run build` writes assets to `app/web/static/` for FastAPI to serve.
- Rebuild when reviewing frontend changes through the backend URL.
- Models own API and browser I/O; ViewModels own application state; Views render data and callbacks.
- The composition root wires those layers together. `npm run lint` enforces the MVVM boundaries.

## API

With the app running, explore [interactive API documentation](http://localhost:8000/docs).

| Route | Purpose |
| --- | --- |
| `GET /` | Question page |
| `GET /policies` | Policy-management page |
| `GET /health` | Health check |
| `GET /api/status` | Basic status and configured paths |
| `POST /api/ask` | Answer and evidence as JSON |
| `POST /api/ask/stream` | Incremental OpenAI answer over server-sent events |
| `/api/policies` | List, read, upload, rename and delete policies; inspect chunks; preview/apply settings |
| `GET /api/operations/{id}` | Persisted processing status |

Example JSON request:

```bash
curl http://localhost:8000/api/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"What are our core working hours?","answer_provider":"extractive"}'
```

- Optional `top_k` accepts 1–10.
- Streaming uses the same request shape. It emits `delta` events with `{ "text": "..." }`.
- A terminal `result` contains the complete answer and evidence; a terminal `error` contains `{ "message": "..." }`.
- EOF without a terminal result is an interrupted answer. Evidence is published only after completion.
- Uploads use a raw body with a URL-encoded `X-Filename` header. Browser mutations must come from the app's origin.
- Rename, delete and apply requests check the policy version to reject stale edits.

## CLI ingestion

The UI imports the bundled sample PDFs automatically; CLI commands are optional.
Run these from the repository root with the virtual environment active:

```bash
policy-rag-extract
policy-rag-chunk --chunk-size 900 --chunk-overlap 150
policy-rag-index
```

- Extraction writes `data/extracted/documents.json`.
- Chunking writes `data/chunks/chunks.json` with page numbers, offsets and identifiers.
- Indexing updates both the legacy Chroma index and the managed policy catalogue.
- `--documents-dir` selects a different PDF directory.
- `policy-rag-index --reset` clears the legacy collection; it does not delete UI-uploaded policies.

## Checks

Backend, from the repository root:

```bash
.venv/bin/ruff check app tests integration_tests scripts/check_python_release_dates.py
.venv/bin/python -m unittest discover -s tests -v
./scripts/run_rag_integration_tests.sh
```

Frontend:

```bash
cd frontend
npm run lint
npm test
npm run build
npm exec -- playwright install chromium
npm run test:e2e
```

- Browser tests start a temporary app on port 8010 and use isolated policy storage.
- The regular tests use local/fake provider boundaries and do not require paid OpenAI calls.
- Integration tests check routing, retrieval and extractive answers against the fictional PDFs.
- RAGAS retrieval metrics run by default; reports go to `data/rag-test-reports/`.
- Optional answer-quality metrics make real OpenAI calls: `RAGAS_ENABLE_LLM_METRICS=1 ./scripts/run_rag_integration_tests.sh`.
- For a separate live streaming check, run the configured app on port 8001, then `npm exec -- playwright test --config playwright.live.config.ts` from `frontend/`. This makes a paid request.
- See [demo media instructions](media/README.md#reproduce) for opt-in screenshot/video capture.
