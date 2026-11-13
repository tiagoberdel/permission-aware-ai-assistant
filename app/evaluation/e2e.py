import argparse
import asyncio
import json
import time
import uuid
from dataclasses import asdict, dataclass

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.agent.service import run_andino
from app.db import SessionLocal
from app.models import User, UserRole


def _tool_content_to_texts(content) -> list[str]:
    if isinstance(content, str):
        return [content]

    texts = []

    for block in content:
        if isinstance(block, str):
            texts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            texts.append(block["text"])

    return texts


def extract_retrieved_documents(messages) -> list[dict]:
    documents: list[dict] = []

    for message in messages:
        if getattr(message, "type", None) != "tool":
            continue

        if getattr(message, "status", "success") == "error":
            continue

        for text in _tool_content_to_texts(message.content):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Tool message content is not valid JSON: {text[:200]!r}"
                ) from exc

            if isinstance(parsed, list):
                documents.extend(parsed)
            elif isinstance(parsed, dict):
                documents.append(parsed)

    return documents


def get_retrieved_document_ids(messages) -> list[str]:
    ids: list[str] = []

    for document in extract_retrieved_documents(messages):
        document_id = document["document_id"]

        if document_id not in ids:
            ids.append(document_id)

    return ids

@dataclass
class AgentRun:
    answer: str
    retrieved_document_ids: list[str]
    tool_calls: int
    latency_s: float
    input_tokens: int | None
    output_tokens: int | None
    finish_reason: str | None


def summarize_run(messages, latency_s: float) -> AgentRun:
    ai_messages = [m for m in messages if getattr(m, "type", None) == "ai"]

    tool_calls = sum(len(getattr(m, "tool_calls", None) or []) for m in ai_messages)

    input_tokens = None
    output_tokens = None

    for message in ai_messages:
        usage = getattr(message, "usage_metadata", None)

        if not usage:
            continue

        input_tokens = (input_tokens or 0) + usage.get("input_tokens", 0)
        output_tokens = (output_tokens or 0) + usage.get("output_tokens", 0)

    last = messages[-1]
    metadata = getattr(last, "response_metadata", None) or {}

    return AgentRun(
        answer=last.text,
        retrieved_document_ids=get_retrieved_document_ids(messages),
        tool_calls=tool_calls,
        latency_s=round(latency_s, 3),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        finish_reason=metadata.get("finish_reason"),
    )


async def run_case(email: str, query: str) -> AgentRun:
    """Ask the agent as a seeded user, exactly as the API would."""
    with SessionLocal() as db:
        user = db.scalar(
            select(User)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(User.email == email, User.is_active == True)
        )

        if user is None:
            raise ValueError(f"Active user not found: {email}")

        started = time.perf_counter()
        response = await run_andino(query, user, str(uuid.uuid4()))
        latency_s = time.perf_counter() - started

    return summarize_run(response["messages"], latency_s)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run one question through the agent.")
    parser.add_argument("--as", dest="email", required=True)
    parser.add_argument("--query", required=True)
    args = parser.parse_args()

    run = asyncio.run(run_case(args.email, args.query))
    print(json.dumps(asdict(run), ensure_ascii=False, indent=2))