from contextlib import asynccontextmanager
from typing import Any

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.ai import AIServiceError, answer_legal_question
from app.config import PROJECT_ROOT
from app.database import (
    delete_consultations,
    get_consultations,
    initialize_database,
    save_consultation,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Tra cứu pháp luật Việt Nam",
    description="Trợ lý AI giúp tra cứu và giải thích pháp luật Việt Nam.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def disable_browser_cache(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


static_directory = PROJECT_ROOT / "static"
app.mount("/static", StaticFiles(directory=static_directory), name="static")


class ConsultationRequest(BaseModel):
    question: str = Field(min_length=5, max_length=2000)


class ConsultationResponse(BaseModel):
    id: int
    question: str
    answer: str
    created_at: str


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(static_directory / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/consultations", response_model=ConsultationResponse)
async def create_consultation(
    request: ConsultationRequest,
) -> dict[str, Any]:
    question = request.question.strip()
    if len(question) < 5:
        raise HTTPException(
            status_code=422, detail="Câu hỏi cần có ít nhất 5 ký tự."
        )

    try:
        answer = await answer_legal_question(question)
    except AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    consultation_id, created_at = save_consultation(question, answer)
    return {
        "id": consultation_id,
        "question": question,
        "answer": answer,
        "created_at": created_at,
    }


@app.get("/api/consultations", response_model=list[ConsultationResponse])
async def consultation_history() -> list[dict[str, Any]]:
    return get_consultations()


@app.delete("/api/consultations", status_code=204)
async def clear_consultation_history() -> None:
    delete_consultations()
