from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.agent.prompts import SYSTEM_PROMPT
from app.config import settings

checkpointer = InMemorySaver()

def create_agent_graph(tools):
    model = ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0,
        reasoning_effort="low",
        reasoning_format="hidden",
        max_tokens=800,
        max_retries=2,
    )

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    return agent