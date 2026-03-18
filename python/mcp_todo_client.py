# mcp_client.py
import asyncio
import threading
from queue import Queue
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPTodoClient:
    """Async MCP client wrapper for sync Tkinter UI"""
    
    def __init__(self):
        self.loop = None
        self.thread = None
        self.session = None
        self.read_stream = None
        self.write_stream = None
        self.response_queue = Queue()
        self.running = False
        
        # Server parameters
        self.server_params = StdioServerParameters(
            command="python",
            args=["-m", "server.todo_service"]
        )
    
    def start(self):
        """Start the MCP client in a background thread"""
        self.running = True
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the MCP client"""
        self.running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
    
    def _run_async_loop(self):
        """Run the asyncio event loop in a separate thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._connect())
            self.loop.run_forever()
        finally:
            self.loop.close()
    
    async def _connect(self):
        """Establish connection to MCP server"""
        try:
            async with stdio_client(self.server_params) as (read, write):
                self.read_stream = read
                self.write_stream = write
                
                async with ClientSession(read, write) as session:
                    self.session = session
                    await session.initialize()
                    
                    # Keep the connection alive
                    while self.running:
                        await asyncio.sleep(0.1)
        except Exception as e:
            print(f"MCP connection error: {e}")
    
    def call_tool_sync(self, name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Synchronously call an MCP tool (called from UI thread)"""
        if not self.loop or not self.loop.is_running():
            return "Error: MCP client not running"
        
        # Create a future to wait for the result
        future = asyncio.run_coroutine_threadsafe(
            self._call_tool_async(name, arguments),
            self.loop
        )
        
        try:
            # Wait for the result with a timeout
            result = future.result(timeout=5.0)
            return result
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _call_tool_async(self, name: str, arguments: Dict[str, Any]) -> str:
        """Async tool call (runs in event loop thread)"""
        if not self.session:
            return "Error: Not connected to MCP server"
        
        try:
            result = await self.session.call_tool(name, arguments)
            if result.content and len(result.content) > 0:
                return result.content[0].text
            return "No result"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def list_tools_sync(self) -> List[str]:
        """Synchronously list available tools"""
        if not self.loop or not self.loop.is_running():
            return ["Error: MCP client not running"]
        
        future = asyncio.run_coroutine_threadsafe(
            self._list_tools_async(),
            self.loop
        )
        
        try:
            return future.result(timeout=5.0)
        except Exception as e:
            return [f"Error: {str(e)}"]
    
    async def _list_tools_async(self) -> List[str]:
        """Async list tools (runs in event loop thread)"""
        if not self.session:
            return ["Error: Not connected to MCP server"]
        
        try:
            tools = await self.session.list_tools()
            return [t.name for t in tools.tools]
        except Exception as e:
            return [f"Error: {str(e)}"]