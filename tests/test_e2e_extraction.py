import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.evaluation.e2e import (
    extract_retrieved_documents,
    get_retrieved_document_ids,
)


def doc(document_id, language="es"):
    return {
        "document_id": document_id,
        "title": f"Title {document_id}",
        "content": "...",
        "language": language,
    }


def tool_message(documents, call_id="c1"):
    return ToolMessage(
        content=[{"type": "text", "text": json.dumps(documents)}],
        tool_call_id=call_id,
    )


def test_extracts_documents_from_a_single_tool_message():
    messages = [
        HumanMessage(content="hola"),
        AIMessage(content="", tool_calls=[{"name": "search_internal_documents", "args": {"query": "x"}, "id": "c1"}]),
        tool_message([doc("G12"), doc("G01")]),
        AIMessage(content="respuesta"),
    ]

    assert [d["document_id"] for d in extract_retrieved_documents(messages)] == ["G12", "G01"]


def test_collects_documents_from_several_tool_calls():
    messages = [tool_message([doc("G12")], "c1"), tool_message([doc("F01")], "c2")]

    assert get_retrieved_document_ids(messages) == ["G12", "F01"]


def test_returns_nothing_when_the_model_never_searched():
    messages = [HumanMessage(content="hola"), AIMessage(content="no tengo info")]

    assert extract_retrieved_documents(messages) == []


def test_accepts_plain_string_content():
    message = ToolMessage(content=json.dumps([doc("G12")]), tool_call_id="c1")

    assert get_retrieved_document_ids([message]) == ["G12"]


def test_empty_result_list_gives_no_documents():
    assert extract_retrieved_documents([tool_message([])]) == []


def test_skips_tool_calls_that_ended_in_error():
    message = ToolMessage(content="Error calling tool", tool_call_id="c1", status="error")

    assert extract_retrieved_documents([message]) == []


def test_invalid_json_raises_instead_of_hiding_documents():
    message = ToolMessage(content=[{"type": "text", "text": "not json"}], tool_call_id="c1")

    with pytest.raises(ValueError):
        extract_retrieved_documents([message])


def test_document_ids_are_unique_and_keep_first_appearance_order():
    messages = [tool_message([doc("G12", "es"), doc("F01"), doc("G12", "en")])]

    assert get_retrieved_document_ids(messages) == ["G12", "F01"]