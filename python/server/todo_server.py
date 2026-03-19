# todo_service.py
# This is the MCP SERVER — the heart of the backend.
#
# The Model Context Protocol (MCP) is a standard way for AI models and clients
# to communicate with tools and services. Think of this server as a plugin host:
# it advertises a list of tools (add, update, delete, list) and handles
# incoming requests to call those tools.
#
# How MCP works (simplified):
#   1. A client connects to this server via stdio (standard input/output streams)
#   2. The client asks: "What tools do you have?" → handle_list_tools() responds
#   3. The client calls a tool by name with arguments → handle_tool_call() runs it
#   4. The result is sent back to the client as a text response

import json
from typing import Any

from .tools import tools             # Dictionary of all registered tool definitions
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from shared.todo_model import TodoModel


# Create the MCP server instance with a human-readable name.
# This name is sent to clients during the handshake so they know what server they're talking to.
server = Server("Todo Server")


def convert_to_json(model_cls: type) -> dict:
    """
    Converts a Pydantic model class into the JSON Schema format that MCP expects.

    MCP requires each tool's input to be described using JSON Schema —
    a standard format that describes what fields are required and what types they should be.

    For example, TodoModel becomes:
    {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "description": {"type": "string"},
            "completed": {"type": "boolean"}
        },
        "required": ["id", "description"]
    }

    This lets the client (and any AI using the tools) know exactly what to send.
    """
    schema = model_cls.schema()           # Get Pydantic's built-in JSON schema
    properties = {}
    required = schema.get("required", []) # List of field names that must be present

    for prop, details in schema.get("properties", {}).items():
        # Extract each property's type (defaulting to "string" if not specified)
        properties[prop] = {"type": details.get("type", "string")}

    return {
        "type": "object",
        "properties": properties,
        "required": required
    }


# This decorator registers the function below as the handler for "list tools" requests.
# When a client connects and asks "what tools are available?", MCP calls this function.
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    Returns a list of all available tools to the client.

    Each Tool object contains:
      - name        : the tool's identifier (e.g. "add", "delete")
      - description : a human-readable explanation of what the tool does
      - inputSchema : the JSON Schema describing what arguments the tool expects

    Clients use this information to know how to call each tool correctly.
    """
    tool_list = []
    print("handling tool listings ...")

    for tool in tools.values():
        tool_list.append(
            Tool(
                name=tool["name"],
                description=tool["description"],
                # Convert the Pydantic model into a JSON Schema the client can understand
                inputSchema=convert_to_json(tool["input_schema"])
            )
        )
    return tool_list


# This decorator registers the function below as the handler for "call tool" requests.
# When a client says "run the 'add' tool with these arguments", MCP calls this function.
@server.call_tool()
async def handle_tool_call(
    name: str,          # The name of the tool to run (e.g. "add", "list")
    arguments: dict[str, Any]  # The input data sent by the client
) -> list[TextContent]:
    """
    Executes the requested tool and returns the result as a text response.

    MCP tool responses must be a list of content blocks.
    We use TextContent, which wraps our result as a JSON string.
    This lets the client parse and use the returned data.
    """
    # Check if the tool name is recognized
    if name not in tools:
        raise ValueError(f"Unknown tool: {name}")

    tool = tools[name]

    try:
        # Call the tool's handler function with the provided arguments
        result = await tool["handler"](arguments)

        # Serialize the result to a JSON string so it can be sent over the wire.
        # MCP responses must be plain text — we use JSON as the format.
        if isinstance(result, TodoModel):
            # A single task → use Pydantic's built-in JSON serializer
            json_str = result.model_dump_json()
        elif isinstance(result, list) and all(isinstance(item, TodoModel) for item in result):
            # A list of tasks → convert each to a dict, then serialize the whole list
            json_str = json.dumps([todo.model_dump() for todo in result])
        else:
            # Any other return value → convert to string as a fallback
            json_str = str(result)

        # Wrap the JSON string in a TextContent block (required by MCP)
        return [TextContent(type="text", text=json_str)]

    except Exception as e:
        raise ValueError(f"Error calling tool {name}: {str(e)}")


async def run():
    """
    Starts the MCP server using stdio transport.

    stdio (standard input/output) is the communication channel used here.
    The server reads requests from stdin and writes responses to stdout.
    This is the simplest MCP transport — no network sockets needed.

    The `async with stdio_server()` context manager sets up the read/write streams,
    then `server.run()` starts the main event loop that listens for client requests.
    """
    async with stdio_server() as (
        read_stream,
        write_stream
    ):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="Todo Server",
                server_version="0.1.0",
                # Declare this server's capabilities to the client during handshake
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            ),
        )


if __name__ == "__main__":
    import asyncio
    print("Starting server...")
    asyncio.run(run())  # Run the async server using Python's asyncio event loop