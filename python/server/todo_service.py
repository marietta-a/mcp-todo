from typing import Any

from mcp.types import Tool, TextContent
from .tools import tools
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from config import app


server = Server("Todo Server")


def convert_to_json(model_cls: type) -> dict:
    schema = model_cls.schema()
    properties = {}
    required = schema.get("required", [])
    for prop, details in schema.get("properties", {}).items():
        properties[prop] = {"type": details.get("type", "string")}
    return {
        "type": "object",
        "properties": properties,
        "required": required
    }

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    tool_list = []
    print("handling tool listings ...")
    index = 0
    for tool in tools.values():
        index += 1
        tool_list.append(
            Tool(
                name=tool["name"], 
                description=tool["description"],
                inputSchema=convert_to_json(tool["input_schema"])
            )
        #   Tool(
        #       name=tool["name"],
        #       description=tool["description"],
        #       inputSchema= convert_to_json(tool["input_schema"]),
        #   )
        )
    return tool_list

@server.call_tool()
async def handle_tool_call(
    name: str,
    arguments: dict[str, Any]
) -> list[TextContent | None]:
    if name not in tools:
        raise ValueError(f"Unknown tool: {name}")
    
    tool = tools[name]

    result = "default"
    try:
        # Invoke the tool
        result = await tool["handler"](arguments)
    except Exception as e:
        raise ValueError(f"Error calling tool {name}: {str(e)}")
    
    return [
        TextContent(type="text",text=str(result))
    ]

async def run():
    """Run the server with lifecycle management"""
    async with stdio_server() as (
        read_stream,
        write_stream
    ): await server.run(
        read_stream,
        write_stream,
        InitializationOptions(
            server_name= "Todo Server",
            server_version="0.1.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )
        ),
    )
        

if __name__ == "__main__":
    import asyncio
    print("Starting server...")
    asyncio.run(run())