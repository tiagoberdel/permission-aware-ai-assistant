import asyncio
import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.evaluation import e2e
from app.evaluation.e2e import AgentRun, run_case, summarize_run


def search_call(call_id="c1"):
    return {"name": "search_internal_documents", "args": {"query": "x"}, "id": call_id}


def tool_message(document_ids, call_id="c1"):
    documents = [
        {"document_id": i, "title": i, "content": "...", "language": "es"}
        for i in document_ids
    ]
    return ToolMessage(
        content=[{"type": "text", "text": json.dumps(documents)}],
        tool_call_id=call_id,
    )


def usage(inp, out):
    return {"input_tokens": inp, "output_tokens": out, "total_tokens": inp + out}


def test_summarize_run_with_one_search():
    messages = [
        HumanMessage(content="hola"),
        AIMessage(content="", tool_calls=[search_call()], usage_metadata=usage(500, 40)),
        tool_message(["G12", "G01"]),
        AIMessage(
            content="Fue fundada en 2018.",
            usage_metadata=usage(700, 30),
            response_metadata={"finish_reason": "stop"},
        ),
    ]

    run = summarize_run(messages, latency_s=1.23456)

    assert run == AgentRun(
        answer="Fue fundada en 2018.",
        retrieved_document_ids=["G12", "G01"],
        tool_calls=1,
        latency_s=1.235,
        input_tokens=1200,
        output_tokens=70,
        finish_reason="stop",
    )


def test_summarize_run_without_search_or_usage():
    messages = [HumanMessage(content="hola"), AIMessage(content="No tengo esa información.")]

    run = summarize_run(messages, latency_s=0.5)

    assert run.retrieved_document_ids == []
    assert run.tool_calls == 0
    assert run.input_tokens is None
    assert run.output_tokens is None
    assert run.finish_reason is None


def test_summarize_run_counts_every_search():
    messages = [
        AIMessage(content="", tool_calls=[search_call("c1")]),
        tool_message(["G12"], "c1"),
        AIMessage(content="", tool_calls=[search_call("c2")]),
        tool_message(["F01"], "c2"),
        AIMessage(content="listo"),
    ]

    run = summarize_run(messages, latency_s=2)

    assert run.tool_calls == 2
    assert run.retrieved_document_ids == ["G12", "F01"]


def test_summarize_run_reports_truncated_answers():
    messages = [
        AIMessage(content="", response_metadata={"finish_reason": "length"}),
    ]

    assert summarize_run(messages, latency_s=1).finish_reason == "length"


@pytest.mark.integration
def test_run_case_loads_the_user_and_returns_an_agent_run(monkeypatch):
    seen = {}

    async def fake_run_andino(query, user, conversation_id):
        seen["email"] = user.email
        seen["roles"] = sorted(ur.role.name for ur in user.roles)
        seen["query"] = query
        return {"messages": [HumanMessage(content=query), AIMessage(content="ok")]}

    monkeypatch.setattr(e2e, "run_andino", fake_run_andino)

    run = asyncio.run(run_case("laura@andino.com", "hola"))

    assert run.answer == "ok"
    assert seen["email"] == "laura@andino.com"
    assert seen["roles"] == ["employee", "hr"]
    assert seen["query"] == "hola"


@pytest.mark.integration
def test_run_case_rejects_unknown_users():
    with pytest.raises(ValueError):
        asyncio.run(run_case("nadie@andino.com", "hola"))