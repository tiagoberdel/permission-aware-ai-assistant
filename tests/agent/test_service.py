import asyncio

from app.agent import service


class FakeMessage:
    text = "final answer"


def test_ask_andino_forwards_arguments_and_returns_last_message_text(monkeypatch):
    calls = []

    async def fake_run_andino(query, user, thread_id):
        calls.append((query, user, thread_id))
        return {"messages": [object(), FakeMessage()]}

    monkeypatch.setattr(service, "run_andino", fake_run_andino)

    answer = asyncio.run(
        service.ask_andino(query="hola", user="user-object", thread_id="conv-1")
    )

    assert answer == "final answer"
    assert calls == [("hola", "user-object", "conv-1")]