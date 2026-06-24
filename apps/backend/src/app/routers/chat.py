from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from app.auth import require_group_member
from app.session import append_to_history, get_history

router = APIRouter(dependencies=[Depends(require_group_member)])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    question: str
    session_id: str


async def get_agent(request: Request) -> CompiledStateGraph:
    return request.app.state.agent


def _log(record: dict) -> None:
    logger.info(json.dumps(record, default=str))


@router.post("/chat")
async def chat(
    body: ChatRequest, agent: CompiledStateGraph = Depends(get_agent)
) -> StreamingResponse:
    history = get_history(body.session_id)
    messages = history + [{"role": "user", "content": body.question}]
    append_to_history(body.session_id, "user", body.question)

    _log({"event": "chat.question", "session_id": body.session_id, "question": body.question})

    async def event_stream():
        full_response: list[str] = []
        try:
            async for event in agent.astream_events(
                {"messages": messages}, version="v2"
            ):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        token = chunk.content
                        full_response.append(token)
                        yield f"data: {json.dumps(token)}\n\n"

                elif kind == "on_tool_start":
                    _log({
                        "event": "tool.call",
                        "session_id": body.session_id,
                        "tool": event.get("name"),
                        "inputs": event["data"].get("input"),
                    })

                elif kind == "on_chat_model_end":
                    output = event["data"].get("output")
                    usage = getattr(output, "usage_metadata", None)
                    if usage:
                        _log({
                            "event": "token.usage",
                            "session_id": body.session_id,
                            "input_tokens": usage.get("input_tokens"),
                            "output_tokens": usage.get("output_tokens"),
                            "total_tokens": usage.get("total_tokens"),
                        })

            yield "data: [DONE]\n\n"
        except Exception:
            logger.exception("Agent streaming error for session %s", body.session_id)
            yield "data: [ERROR] An error occurred. Please try again.\n\n"
        finally:
            if full_response:
                answer = "".join(full_response)
                _log({"event": "chat.answer", "session_id": body.session_id, "answer": answer})
                append_to_history(body.session_id, "assistant", answer)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
