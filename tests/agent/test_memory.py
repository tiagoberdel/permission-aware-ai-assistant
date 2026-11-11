import asyncio

from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.checkpoint.memory import InMemorySaver

def test_conversation_memory_and_thread_isolation():
    async def run_test():
        checkpointer = InMemorySaver()

        model = FakeListChatModel(
            responses = [
                "Hola Diego",
                "Tu nombre es Diego",
                "Hola Valentina",
                "Nueva conversacion",
            ]
        )

        agent = create_agent(
            model=model,
            tools=[],
            checkpointer=checkpointer,
        )

        diego_config = {
            "configurable": {"thread_id": "diego-1"}
        }

        valentina_config = {
            "configurable": {"thread_id": "valentina-1"}
        }

        diego_new_config = {
            "configurable": {"thread_id": "diego-2"}
        }

        await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Me llamo Diego"}]},
            config=diego_config
        )

        await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Como me llamo?"}]},
            config=diego_config
        )

        diego_state = await agent.aget_state(diego_config)
        diego_messages = diego_state.values["messages"]

        assert len(diego_messages) == 4
        assert diego_messages[0].content == "Me llamo Diego"
        assert diego_messages[2].content == "Como me llamo?"

        await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Me llamo Valentina"}]},
            config=valentina_config
        )

        valentina_state = await agent.aget_state(valentina_config)
        valentina_messages = valentina_state.values["messages"]

        assert len(valentina_messages) == 2
        assert valentina_messages[0].content == "Me llamo Valentina"

        assert all(
            "Valentina" not in str(message.content)
            for message in diego_messages
        )

        await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Empecemos de nuevo"}]},
            config=diego_new_config
        )

        diego_new_state = await agent.aget_state(diego_new_config)
        diego_new_messages = diego_new_state.values["messages"]

        assert len(diego_new_messages) == 2
        assert diego_new_messages[0].content == "Empecemos de nuevo"
        assert all(
            "Me llamo Diego" not in str(message.content)
            for message in diego_new_messages
        )

    asyncio.run(run_test())