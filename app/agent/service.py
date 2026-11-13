from langchain.mcp import MCPAdapter

from app.agent.graph import create_agent_graph
from app.mcp.server import create_mcp_server
from app.models.user import User


async def run_andino(query: str, user: User, conversation_id: str):
    """Run the agent and return the full graph state (all messages)."""
    mcp_server = create_mcp_server(user)

    async with MCPAdapter(mcp_server) as adapter:
        tools = await adapter.list_tools()
        agent = create_agent_graph(tools)

        thread_id = f"user:{user.id}:conversation:{conversation_id}"

        response = await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": query}
                ]
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            },
        )

        return response


async def ask_andino(query: str, user: User, conversation_id: str):
    """Run the agent and return only the final answer text."""
    response = await run_andino(query, user, conversation_id)

    return response["messages"][-1].text