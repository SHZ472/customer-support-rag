"""FastAPI entry point for the customer support demo."""

from contextlib import asynccontextmanager
import os
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from prometheus_client import Counter
from psycopg import OperationalError
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, Field, field_validator

from app.database import get_record, seed_database
from app.metrics import instrument_app
from app.routing import answer_question


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def nonempty(cls, value):
        question = value.strip()
        if not question:
            raise ValueError("问题不能为空白。")
        return question


class AskResponse(BaseModel):
    route: Literal["database", "faq", "unknown"]
    sources: list[str]
    answer: str
    trace: list[str]


@asynccontextmanager
async def lifespan(app):
    from app.retrieval import FaqRetriever

    settings = dict(host="postgres", port=5432, dbname="postgres", user="course_admin",
                    connect_timeout=5, row_factory=dict_row)
    with ConnectionPool(kwargs=settings, min_size=4, max_size=4, timeout=3, open=False) as pool:
        pool.wait(timeout=15)
        with pool.connection() as conn:
            seed_database(conn)
        app.state.pool = pool
        app.state.retriever = FaqRetriever(cache_size=int(os.getenv("FAQ_QUERY_CACHE_SIZE", "256")))
        yield


app = FastAPI(title="星河书店智能客服 RAG", lifespan=lifespan)
registry = instrument_app(app)
answer_counts = Counter("agentguide_customer_answers_total", "Customer API responses by answer route",
                        ["answer_route"], registry=registry)


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest, request: Request):
    def lookup(kind, number):
        with request.app.state.pool.connection() as conn:
            return get_record(conn, kind, number)

    try:
        result = answer_question(body.question, lookup, request.app.state.retriever)
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="数据库暂不可用，本次未能确认记录。") from exc
    answer_counts.labels(answer_route=result["route"]).inc()
    return result
