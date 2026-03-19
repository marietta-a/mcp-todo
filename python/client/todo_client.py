# todo_client.py
# This is a simple MCP CLIENT used for testing the server from the command line.
#
# In MCP architecture:
#   - The SERVER (todo_service.py) hosts the tools and handles requests
#   - The CLIENT (this file) connects to the server and calls those tools
#
# This client uses "stdio" transport — it launches the server as a subprocess
# and communicates with it through stdin/stdout pipes. No network required!
#
# This is useful for quickly testing that your MCP server works correctly
# before hooking it up to a UI or AI agent.

import asyncio
import os

from pydantic import AnyUrl

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.shared.context import RequestContext


# StdioServerParameters tells the client HOW to launch the server.
# Here we're telling it: "run `python -m server.todo_service` as a subprocess"
# The client will automatically start this process and connect to it.
server_params = StdioServerParameters(
    command="python",
    args=["-m", "server.todo_service"]  # Runs the server module
)


async def run():
    """
    Main async function that connects to the server and demonstrates all the tools.

    This function shows the full MCP client lifecycle:
      1. Open a stdio connection to the server
      2. Create a ClientSession (handles the MCP handshake)
      3. Call tools by name with arguments
      4. Read and print the responses
    """

    # `stdio_client` launches the server process and opens read/write streams to it
    async with stdio_client(server_params) as (read, write):

        # `ClientSession` manages the MCP protocol on top of those streams.
        # It handles initialization, message framing, and response parsing.
        async with ClientSession(read, write) as session:

            # Step 1: Perform the MCP handshake.
            # This exchanges version info and capabilities between client and server.
            await session.initialize()

            # Step 2: Ask the server what tools it offers.
            # This calls handle_list_tools() on the server side.
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

            # Step 3: Call the "add" tool to create a new task.
            # Arguments must match the tool's input schema (TodoModel in this case).
            result = await session.call_tool(
                name="add",
                arguments={
                    "id": 1,
                    "description": "Go to the market",
                    "completed": False
                }
            )
            print(f"Result of add tool: {result}")

            # Step 4: Call the "update" tool to modify the task we just created.
            # We pass the same `id` but a new description.
            update_result = await session.call_tool(
                name="update",
                arguments={
                    "id": 1,
                    "description": "Go to church",
                    "completed": False
                }
            )
            print(f"Result of update tool: {update_result}")

            # Step 5: Call the "list" tool to retrieve all tasks.
            # No arguments needed — the server returns everything.
            list_result = await session.call_tool(
                name="list",
                arguments={}
            )
            print(f"Result of list tool: {list_result}")


def main():
    """
    Entry point for running this script directly.
    asyncio.run() starts the event loop and runs our async `run()` function.
    """
    asyncio.run(run())


if __name__ == "__main__":
    main()