from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from app.assistant import AssistantService, build_default_assistant_service
from app.config import get_settings
from app.retrieval.answerer import AnswerProviderError
from app.web.schemas import AskRequest, AskResponse


router = APIRouter()


def get_assistant_service() -> AssistantService:
    return build_default_assistant_service()


@router.get("/", response_class=HTMLResponse, tags=["web"])
def root() -> HTMLResponse:
    return HTMLResponse(_render_home_page())


@router.get("/api/status", tags=["system"])
def status() -> dict[str, object]:
    settings = get_settings()
    return {
        "name": "Policy RAG Assistant",
        "status": "ready",
        "documents_dir": str(settings.documents_dir),
        "vector_store_dir": str(settings.vector_store_dir),
    }


@router.post("/api/ask", response_model=AskResponse, tags=["assistant"])
def ask_question(
    request: AskRequest,
    assistant: AssistantService = Depends(get_assistant_service),
) -> AskResponse:
    try:
        response = assistant.answer_question(
            request.question,
            top_k=request.top_k,
            answer_provider=request.answer_provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AnswerProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AskResponse(
        answer=response.answer,
        answer_provider=response.answer_provider,
        routed_documents=response.routed_documents,
        routing_provider=response.routing_provider,
        routing_rationale=response.routing_rationale,
        sources=response.sources,
        retrieved_chunks=response.retrieved_chunks,
    )


def _render_home_page() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Policy RAG Assistant</title>
  <style>
    :root {
      --bg: #f4efe6;
      --bg-strong: #e8dcc7;
      --panel: rgba(255, 252, 247, 0.88);
      --ink: #1c1b18;
      --muted: #60584f;
      --accent: #8a4b2a;
      --accent-strong: #6e3418;
      --line: rgba(28, 27, 24, 0.12);
      --shadow: 0 20px 60px rgba(76, 53, 31, 0.14);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(180, 104, 44, 0.2), transparent 30%),
        radial-gradient(circle at right, rgba(102, 129, 94, 0.16), transparent 28%),
        linear-gradient(160deg, var(--bg) 0%, #f9f5ee 52%, var(--bg-strong) 100%);
    }

    .shell {
      width: min(1100px, calc(100% - 32px));
      margin: 32px auto;
      display: grid;
      gap: 18px;
    }

    .hero,
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
    }

    .hero {
      padding: 28px;
      display: grid;
      gap: 14px;
    }

    .eyebrow {
      display: inline-flex;
      width: fit-content;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(138, 75, 42, 0.08);
      color: var(--accent-strong);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    h1 {
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", serif;
      font-size: clamp(2rem, 5vw, 4rem);
      line-height: 0.95;
      max-width: 10ch;
    }

    .hero p,
    .panel p,
    .meta,
    .source-item,
    .chunk-item {
      color: var(--muted);
      line-height: 1.5;
    }

    .workspace {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
    }

    .panel {
      padding: 22px;
    }

    .panel h2 {
      margin: 0 0 12px;
      font-size: 1rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    textarea {
      width: 100%;
      min-height: 160px;
      resize: vertical;
      border-radius: 18px;
      border: 1px solid rgba(28, 27, 24, 0.15);
      padding: 16px;
      font: inherit;
      color: var(--ink);
      background: rgba(255, 255, 255, 0.72);
    }

    textarea:focus {
      outline: 2px solid rgba(138, 75, 42, 0.2);
      border-color: rgba(138, 75, 42, 0.35);
    }

    button {
      margin-top: 14px;
      border: 0;
      border-radius: 999px;
      background: linear-gradient(135deg, var(--accent), var(--accent-strong));
      color: white;
      padding: 12px 18px;
      font: inherit;
      font-weight: 600;
      cursor: pointer;
    }

    button:disabled {
      opacity: 0.55;
      cursor: wait;
    }

    .answer {
      white-space: pre-wrap;
      color: var(--ink);
      font-size: 1rem;
      line-height: 1.6;
      min-height: 140px;
    }

    .meta {
      margin-top: 12px;
      font-size: 0.95rem;
    }

    .stack {
      display: grid;
      gap: 12px;
    }

    .source-item,
    .chunk-item {
      padding: 14px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.65);
      border: 1px solid rgba(28, 27, 24, 0.08);
    }

    .source-item strong,
    .chunk-item strong {
      display: block;
      color: var(--ink);
      margin-bottom: 6px;
    }

    .empty {
      color: var(--muted);
      font-style: italic;
    }

    @media (max-width: 900px) {
      .workspace {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">Internal Policy Demo</span>
      <h1>Ask the policy corpus, not the model.</h1>
      <p>
        This MVP retrieves matching policy chunks from the local Northstar documents first,
        then answers from that grounded context.
      </p>
    </section>

    <section class="workspace">
      <div class="panel">
        <h2>Question</h2>
        <p>Try questions about AI use, security handling, attendance, remote work, or confidentiality.</p>
        <textarea id="question">Can I put customer data into a public AI tool?</textarea>
        <div style="margin-top: 14px;">
          <label for="answer-provider" style="display:block; margin-bottom: 8px; color: var(--muted);">Answer mode</label>
          <select id="answer-provider" style="width: 100%; border-radius: 14px; border: 1px solid rgba(28, 27, 24, 0.15); padding: 12px; font: inherit; background: rgba(255,255,255,0.72);">
            <option value="openai" selected>OpenAI</option>
            <option value="extractive">Extractive</option>
          </select>
        </div>
        <button id="ask-button">Ask Policy Assistant</button>
      </div>

      <div class="panel">
        <h2>Answer</h2>
        <div id="answer" class="answer">Your grounded answer will appear here.</div>
        <div id="meta" class="meta"></div>
      </div>
    </section>

    <section class="workspace">
      <div class="panel">
        <h2>Sources</h2>
        <div id="sources" class="stack"><div class="empty">No sources yet.</div></div>
      </div>

      <div class="panel">
        <h2>Routed Documents</h2>
        <div id="routing" class="stack"><div class="empty">No routing decision yet.</div></div>
      </div>

      <div class="panel">
        <h2>Retrieved Chunks</h2>
        <div id="chunks" class="stack"><div class="empty">No retrieved chunks yet.</div></div>
      </div>
    </section>
  </main>

  <script>
    const button = document.getElementById("ask-button");
    const questionInput = document.getElementById("question");
    const answerProviderInput = document.getElementById("answer-provider");
    const answerEl = document.getElementById("answer");
    const metaEl = document.getElementById("meta");
    const sourcesEl = document.getElementById("sources");
    const routingEl = document.getElementById("routing");
    const chunksEl = document.getElementById("chunks");

    function renderSources(sources) {
      if (!sources.length) {
        sourcesEl.innerHTML = '<div class="empty">No sources returned.</div>';
        return;
      }
      sourcesEl.innerHTML = sources.map((source) => `
        <div class="source-item">
          <strong>${source.document_name}</strong>
          <div>Page ${source.page_number}</div>
          <div>${source.chunk_id}</div>
        </div>
      `).join("");
    }

    function renderChunks(chunks) {
      if (!chunks.length) {
        chunksEl.innerHTML = '<div class="empty">No chunks returned.</div>';
        return;
      }
      chunksEl.innerHTML = chunks.map((chunk) => `
        <div class="chunk-item">
          <strong>${chunk.document_name} · page ${chunk.page_number}</strong>
          <div>${chunk.text}</div>
        </div>
      `).join("");
    }

    function renderRouting(payload) {
      if (!payload.routed_documents.length) {
        routingEl.innerHTML = '<div class="empty">No routed documents returned.</div>';
        return;
      }
      const header = `
        <div class="source-item">
          <strong>${payload.routing_provider}</strong>
          <div>${payload.routing_rationale || "No routing rationale returned."}</div>
        </div>
      `;
      const items = payload.routed_documents.map((document) => `
        <div class="source-item">
          <strong>${document.title}</strong>
          <div>${document.document_name}</div>
        </div>
      `).join("");
      routingEl.innerHTML = header + items;
    }

    async function askQuestion() {
      const question = questionInput.value.trim();
      const answerProvider = answerProviderInput.value;
      if (!question) {
        answerEl.textContent = "Enter a question first.";
        return;
      }

      button.disabled = true;
      answerEl.textContent = "Searching policies and composing a grounded answer...";
      metaEl.textContent = "";

      try {
        const response = await fetch("/api/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, answer_provider: answerProvider }),
        });
        const payload = await response.json();

        if (!response.ok) {
          answerEl.textContent = payload.detail || "Request failed.";
          renderSources([]);
          renderRouting({ routed_documents: [], routing_provider: "", routing_rationale: "" });
          renderChunks([]);
          return;
        }

        answerEl.textContent = payload.answer;
        metaEl.textContent = `Provider: ${payload.answer_provider} · Sources: ${payload.sources.length} · Chunks: ${payload.retrieved_chunks.length}`;
        renderSources(payload.sources);
        renderRouting(payload);
        renderChunks(payload.retrieved_chunks);
      } catch (error) {
        answerEl.textContent = "The request failed before the assistant could answer.";
        metaEl.textContent = String(error);
        renderSources([]);
        renderRouting({ routed_documents: [], routing_provider: "", routing_rationale: "" });
        renderChunks([]);
      } finally {
        button.disabled = false;
      }
    }

    button.addEventListener("click", askQuestion);
  </script>
</body>
</html>
"""
