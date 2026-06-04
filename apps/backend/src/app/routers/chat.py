from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from app.session import append_to_history, get_history

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    session_id: str


async def get_agent(request: Request) -> CompiledStateGraph:
    return request.app.state.agent


@router.post("/chat")
async def chat(
    body: ChatRequest, agent: CompiledStateGraph = Depends(get_agent)
) -> StreamingResponse:
    history = get_history(body.session_id)
    messages = history + [{"role": "user", "content": body.question}]
    append_to_history(body.session_id, "user", body.question)

    async def event_stream():
        full_response: list[str] = []
        try:
            async for event in agent.astream_events(
                {"messages": messages}, version="v2"
            ):
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        token = chunk.content
                        full_response.append(token)
                        yield f"data: {token}\n\n"
            append_to_history(body.session_id, "assistant", "".join(full_response))
            yield "data: [DONE]\n\n"
        except Exception:
            yield "data: [ERROR] An error occurred. Please try again.\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
