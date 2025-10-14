"""Custom tools for the AI agent."""

from langchain_core.tools import tool


@tool
def get_current_time() -> str:
    """Get the current time in ISO format."""
    from datetime import datetime

    return datetime.now().isoformat()


@tool
def search_files(query: str) -> str:
    """
    Search for files matching the query.

    Args:
        query: Search query

    Returns:
        List of matching files
    """
    # TODO: Implement actual file search logic
    return f"Searching for files matching: {query}"


# List of available tools
AVAILABLE_TOOLS = [get_current_time, search_files]
