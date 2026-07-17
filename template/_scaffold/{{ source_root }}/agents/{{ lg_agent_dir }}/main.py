from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from langchain_core.runnables import RunnableConfig

from .graph import build_graph
from .schema import ChatRequest, ChatResponse
from .settings import settings

_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _graph
    if settings.vectordb_path != ":memory:" and not Path(settings.vectordb_path).exists():
        print(
            f"Warning: {settings.vectordb_path} does not exist yet — "
            "run `make corpus-ingest` before sending chat requests."
        )
    _graph = build_graph()
    yield


app = FastAPI(title=__package__.split(".")[-1], lifespan=lifespan)

try:
    from integrations.n8n_webhook import router as n8n_webhook_router

    app.include_router(n8n_webhook_router)
except ImportError:
    pass  # include_n8n_webhook=false — integrations/ wasn't scaffolded

try:
    from fastapi.middleware.cors import CORSMiddleware

    from middleware.settings import settings as auth_settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=auth_settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
except ImportError:
    pass  # frontend_backend_topology != split_service — middleware/ wasn't scaffolded


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    assert _graph is not None
    config: RunnableConfig = {"configurable": {"thread_id": request.thread_id}}
    result = await _graph.ainvoke({"message": request.message}, config)
    return ChatResponse(
        message=result["answer"],
        sources=result.get("sources", []),
        blocked=result.get("blocked", False),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal error"})
