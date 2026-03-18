from mcp.server import FastMCP
from pydantic import AnyHttpUrl
import os
from todo_manager import TodoDataManager

settings = {
    "host": "localhost",
    "port": 8000,
    "auth_server_url": AnyHttpUrl("http://localhost:8001"),
    "mcp_scope": "mcp:read",
    "server_url": AnyHttpUrl("http://localhost:8000"),
}

# Create MCP Server
app = FastMCP(
    name="MCP Resource Server for TODO App",
    instructions="Resource server that validates tokens via Authorization Server introspection",
    host= settings["host"],
    port=settings["port"],
    debug=True
)

# Create Tool Permissions
tool_permission = {
   "create_todo": ["User.Write", "Admin.Write"],
   "delete_todo": ["Admin.Write"],
   "list_todo": ["User.Read", "Admin.Read"],
}

# Get secret key
secret = os.environ.get("SECRET")

# Init db
db = TodoDataManager()