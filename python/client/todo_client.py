import asyncio 
import os

from pydantic import AnyUrl

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.shared.context import RequestContext

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",
    args=["-m", "server.todo_service"]
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

            result = await session.call_tool(
                name="add", 
                arguments={
                    "id": 1, 
                    "description": "Go to the market", 
                    "completed": False
                }
            )
            print(f"Result of add tool: {result}")

            update_result = await session.call_tool(
                name="update", 
                arguments={
                    "id": 1, 
                    "description": "Go to church", 
                    "completed": False
                }
            )
            print(f"Result of update tool: {update_result}")

            list_result = await session.call_tool(
                name="list",
                arguments={}
            )
            print(f"Result of list tool: {list_result}")


def main():
    """Entry point for the client script"""
    asyncio.run(run())

if __name__ == "__main__":
    main()
