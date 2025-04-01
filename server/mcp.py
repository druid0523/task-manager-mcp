from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict
from mcp.server.fastmcp import FastMCP
from models import connection_manager

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, any]]:
    """Manage the application lifecycle with ModelManager."""
    try:
        yield {"connection_manager": connection_manager}
    finally:
        # Cleanup on shutdown
        connection_manager.close_all()

# # Create an MCP server with lifespan
mcp = FastMCP("Task Manager", lifespan=app_lifespan)
