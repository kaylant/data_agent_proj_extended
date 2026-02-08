"""FastAPI backend for the Data Analysis Agent"""

import time
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agent import build_graph, df
from src.data_loader import get_schema_summary

# Initialize FastAPI
app = FastAPI(title="Data Analysis Agent API")

# CORS for React frontend - must be before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build agent once at startup
agent = build_graph()
schema_summary = get_schema_summary(df)


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    time_seconds: float


class SchemaResponse(BaseModel):
    rows: int
    columns: int
    schema_text: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/schema", response_model=SchemaResponse)
def get_schema():
    return SchemaResponse(
        rows=len(df),
        columns=len(df.columns),
        schema_text=schema_summary,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    thread_id = request.thread_id or str(uuid.uuid4())

    start_time = time.time()
    result = agent.invoke(
        {"messages": [("user", request.message)]},
        config={"configurable": {"thread_id": thread_id}},
    )
    elapsed = time.time() - start_time
    response = result["messages"][-1].content
    return ChatResponse(
        response=response,
        thread_id=thread_id,
        time_seconds=round(elapsed, 2),
    )


@app.post("/clear/{thread_id}")
def clear_thread(thread_id: str):
    return {"new_thread_id": str(uuid.uuid4())}
