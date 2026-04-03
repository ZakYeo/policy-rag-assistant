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
- placeholder package structure for ingestion, retrieval, and web modules

The next implementation step is document ingestion, followed by chunking, embedding, retrieval, and a basic question-answering interface.

## Initial Project Structure

- `app/` application package
- `app/ingest/` future PDF ingestion and indexing logic
- `app/retrieval/` future retrieval and answer assembly logic
- `app/web/` FastAPI routes
- `documents/` source policy PDFs
- `data/` local generated artifacts such as the vector store

## Local Setup

1. Create a virtual environment.
2. Install dependencies from [`pyproject.toml`](/home/zakye/policy-rag-assistant/pyproject.toml).
3. Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY`.
4. Run the FastAPI app with `uvicorn app.main:app --reload`.

The current scaffold exposes:

- `GET /` for a basic setup status response
- `GET /health` for a simple health check

See [`plan.md`](/home/zakye/policy-rag-assistant/plan.md) for the proposed MVP scope and implementation plan.
