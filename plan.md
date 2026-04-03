# Initial Plan

## Objective

Build a small MVP for a policy-focused RAG assistant that can answer questions grounded in local PDF policy documents stored in `documents/`.

The first version should be easy to understand, easy to run locally, and small enough to finish quickly.

## Recommended MVP Scope

The MVP should do only the essentials:

- load policy PDFs from the local `documents/` directory
- extract text from each PDF
- split text into chunks
- generate embeddings for those chunks
- store embeddings in a simple local vector store
- accept a user question
- retrieve the top relevant chunks
- send the question plus retrieved context to an LLM
- return a concise answer with source references

## Simple Stack

Use a straightforward Python-based stack for the MVP:

- Python 3.11+
- FastAPI for a minimal backend API
- simple HTML page or lightweight frontend served by FastAPI for the demo UI
- LangChain or plain Python orchestration for chunking and retrieval
- Chroma as a local vector store
- PyMuPDF or `pypdf` for PDF text extraction
- OpenAI embeddings + chat model for retrieval and answer generation

This stack is intentionally simple:

- Python is quick for prototyping RAG workflows
- FastAPI keeps the app easy to run and demo
- Chroma works locally and avoids external infrastructure
- local PDFs match the demo’s initial document source

## Suggested MVP Architecture

Keep the initial structure small:

- `documents/` for source PDFs
- `app/` for backend code
- `app/ingest/` for PDF loading, chunking, and indexing
- `app/retrieval/` for search and prompt assembly
- `app/web/` for the minimal UI or API routes
- `data/` for local vector store files and derived artifacts

## Initial Milestones

### 1. Project Setup

- define dependencies
- create the basic app structure
- add environment variable handling for API keys and config

### 2. Ingestion Pipeline

- read PDFs from `documents/`
- extract text reliably
- chunk the text with metadata such as file name and page number
- create embeddings and store them locally

### 3. Retrieval + Answering

- accept a user question
- retrieve top matching chunks
- build a prompt that instructs the model to answer only from provided context
- return the answer plus source snippets or citations

### 4. Demo Interface

- provide a very simple UI with one input box and one answer area
- show retrieved sources alongside the answer

### 5. MVP Validation

- test a small set of realistic policy questions
- verify the system refuses or qualifies answers when context is weak
- check that retrieved passages are actually relevant

## First Implementation Steps

Start in this order:

1. Set up the Python project and dependency management.
2. Implement PDF extraction for the files already in `documents/`.
3. Add chunking and metadata capture.
4. Build a local indexing command that writes to a Chroma store.
5. Implement retrieval for a single user query.
6. Add answer generation with strict grounding instructions.
7. Expose the flow through a minimal FastAPI endpoint and simple web page.

## Early Product Decisions

For the MVP, make the following simplifying choices:

- local-only document source
- manual re-indexing when documents change
- single-user local demo
- no authentication
- no conversation memory beyond a single question/answer flow
- citations based on document name and page metadata where possible

## Risks To Watch Early

- PDF extraction quality may vary across documents
- poor chunking can reduce retrieval quality
- answers may still hallucinate if prompting is weak
- citation quality depends on preserving useful metadata during ingestion

## After The MVP

Once the basic version works, the next improvements can include:

- better citations and highlighted source snippets
- evaluation set for common policy questions
- document update workflow
- support for follow-up questions
- stronger guardrails for uncertain or missing answers
