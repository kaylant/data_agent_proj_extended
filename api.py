"""FastAPI backend for the Data Analysis Agent"""

import os
import time
import uuid
import json
import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import jwt
from jwt import PyJWKClient

from src.agent import build_graph, df
from src.data_loader import get_schema_summary

load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Data Analysis Agent API")

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "dev-3bbpbpfdjsjhyshp.us.auth0.com")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://data-agent-api")
ALGORITHMS = ["RS256"]

# JWT key client
jwks_client = PyJWKClient(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")

security = HTTPBearer()


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Auth0 JWT token"""
    token = credentials.credentials

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    """Health check - no auth required"""
    return {"status": "ok"}


@app.get("/schema", response_model=SchemaResponse)
def get_schema(token_payload: dict = Depends(verify_token)):
    return SchemaResponse(
        rows=len(df),
        columns=len(df.columns),
        schema_text=schema_summary,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, token_payload: dict = Depends(verify_token)):
    """Non-streaming chat endpoint"""
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


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, token_payload: dict = Depends(verify_token)):
    """Streaming chat endpoint using Server-Sent Events"""
    thread_id = request.thread_id or str(uuid.uuid4())

    async def generate():
        start_time = time.time()

        # Send thread_id first
        yield f"data: {json.dumps({'type': 'thread_id', 'thread_id': thread_id})}\n\n"

        try:
            # Invoke agent
            result = agent.invoke(
                {"messages": [("user", request.message)]},
                config={"configurable": {"thread_id": thread_id}},
            )

            # Get the final response
            response = result["messages"][-1].content

            # Stream it in chunks with delay for typing effect
            chunk_size = 10
            for i in range(0, len(response), chunk_size):
                chunk = response[i : i + chunk_size]
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)  # 20ms delay between chunks

            elapsed = time.time() - start_time
            yield f"data: {json.dumps({'type': 'done', 'time_seconds': round(elapsed, 2)})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/clear/{thread_id}")
def clear_thread(thread_id: str, token_payload: dict = Depends(verify_token)):
    return {"new_thread_id": str(uuid.uuid4())}
