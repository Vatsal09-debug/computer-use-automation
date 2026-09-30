from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright

from app.artifact.schema import Recipe
from app.discovery.canonicalizer import DiscoveryCanonicalizer
from app.discovery.engine import DiscoveryEngine
from app.llm.anthropic_provider import AnthropicProvider
from app.session.manager import SessionManager


class DiscoveryRequest(BaseModel):
    goal: str


class DiscoveryResponse(BaseModel):
    session_id: str
    recipe: Recipe
    history: list[dict[str, Any]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    playwright = await async_playwright().start()
    app.state.session_manager = SessionManager(playwright)

    yield

    session_manager: SessionManager = app.state.session_manager

    for session_id in list(session_manager.sessions):
        await session_manager.close(session_id)

    await playwright.stop()


app = FastAPI(
    title="Computer-Use Automation",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sessions")
async def create_session() -> dict[str, str]:
    session_manager: SessionManager = app.state.session_manager
    session = await session_manager.create()

    return {
        "session_id": session.session_id,
        "status": "created",
    }


@app.delete("/sessions/{session_id}")
async def close_session(session_id: str) -> dict[str, str]:
    session_manager: SessionManager = app.state.session_manager

    try:
        await session_manager.close(session_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "session_id": session_id,
        "status": "closed",
    }


@app.post("/sessions/{session_id}/discover", response_model=DiscoveryResponse)
async def discover(
    session_id: str,
    request: DiscoveryRequest,
) -> DiscoveryResponse:
    session_manager: SessionManager = app.state.session_manager

    try:
        session = session_manager.get(session_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    provider = AnthropicProvider()

    engine = DiscoveryEngine(
        surface=session.surface,
        provider=provider,
    )

    try:
        history = await engine.run(request.goal)

        recipe = DiscoveryCanonicalizer().canonicalize(
            request.goal,
            history,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return DiscoveryResponse(
        session_id=session_id,
        recipe=recipe,
        history=history,
    )
