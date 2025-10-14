"""LangGraph agent implementation."""

from typing import Annotated

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from app.agents.tools import AVAILABLE_TOOLS
from app.config import settings


class AgentState(TypedDict):
    """Agent state definition."""

    messages: Annotated[list[BaseMessage], add_messages]


def get_llm():
    """Get the LLM based on configuration."""
    # Try Anthropic first
    if settings.ANTHROPIC_API_KEY:
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=0,
        )

    # Try Azure OpenAI
    if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
        return AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            deployment_name=settings.AZURE_OPENAI_DEPLOYMENT_NAME or "gpt-4",
            temperature=0,
        )

    # Fall back to OpenAI
    if settings.OPENAI_API_KEY:
        return ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0,
        )

    raise ValueError("No LLM API key configured")


def create_agent():
    """Create a LangGraph agent."""
    # Initialize LLM with tools
    llm = get_llm()
    llm_with_tools = llm.bind_tools(AVAILABLE_TOOLS)

    # Define the function that calls the model
    def call_model(state: AgentState) -> dict:
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # Define a new graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(AVAILABLE_TOOLS))

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    def should_continue(state: AgentState) -> str:
        messages = state["messages"]
        last_message = messages[-1]

        # If there are no tool calls, we finish
        if not last_message.tool_calls:
            return "end"

        # Otherwise continue to tools
        return "continue"

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": "__end__",
        },
    )

    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")

    # Compile the graph
    return workflow.compile()


# Create the agent graph
agent_graph = create_agent()


async def run_agent(message: str) -> str:
    """
    Run the agent with a message.

    Args:
        message: User message

    Returns:
        Agent response
    """
    result = await agent_graph.ainvoke(
        {"messages": [HumanMessage(content=message)]},
    )

    # Extract the final response
    messages = result["messages"]
    return messages[-1].content
