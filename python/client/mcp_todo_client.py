# mcp_todo_client.py
# This file provides a thread-safe MCP client wrapper designed for use with Tkinter UIs.
#
# THE PROBLEM IT SOLVES:
# MCP uses Python's `asyncio` (async/await) for all communication.
# Tkinter (the UI framework) runs in the main thread using a synchronous event loop.
# These two worlds don't mix directly — you can't call `await` from a Tkinter button click.
#
# THE SOLUTION:
# We run the asyncio event loop in a separate background thread.
# The UI thread then submits tasks to that background thread using
# `asyncio.run_coroutine_threadsafe()`, and waits for a result.
# This keeps the UI responsive while MCP operations happen in the background.
#
# ARCHITECTURE OVERVIEW:
#
#   [Tkinter UI Thread]  →  call_tool_sync("add", {...})
#                                  ↓
#   [asyncio Thread]     →  _call_tool_async("add", {...})  →  [MCP Server]
#                                  ↓
#   [Tkinter UI Thread]  ←  returns result string

import asyncio
import threading
from queue import Queue
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPTodoClient:
    """
    A thread-safe MCP client wrapper.

    This class manages:
      - Starting/stopping the background asyncio thread
      - Connecting to the MCP server via stdio
      - Exposing sync methods the UI can call safely
    """

    def __init__(self):
        self.loop = None           # The asyncio event loop running in the background thread
        self.thread = None         # The background thread that runs the event loop
        self.session = None        # The active MCP ClientSession (set after connection)
        self.read_stream = None    # Incoming data stream from the server
        self.write_stream = None   # Outgoing data stream to the server
        self.response_queue = Queue()  # (Unused currently, but available for future use)
        self.running = False       # Flag to control when the client should stop

        # Server parameters: tells the client how to launch the MCP server subprocess
        self.server_params = StdioServerParameters(
            command="python",
            args=["-m", "server.todo_server"]  # Command to start the server
        )

    def start(self):
        """
        Starts the MCP client by launching a background daemon thread.

        A daemon thread is automatically killed when the main program exits,
        so we don't need to manually clean it up in most cases.
        """
        self.running = True
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """
        Stops the MCP client by halting the asyncio event loop.

        `call_soon_threadsafe` is used because we're calling this from a different
        thread (the UI thread) — it's the safe way to interact with a running loop.
        """
        self.running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

    def _run_async_loop(self):
        """
        This method runs in the background thread.

        It creates a new asyncio event loop (each thread needs its own),
        sets it as the current loop for that thread, then starts the connection.
        `run_forever()` keeps the loop alive so it can handle future tool calls.
        """
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            # Establish the initial connection to the MCP server
            self.loop.run_until_complete(self._connect())
            # Keep the loop running to process future tool call requests
            self.loop.run_forever()
        finally:
            self.loop.close()

    async def _connect(self):
        """
        Async method that connects to the MCP server and holds the connection open.

        This runs entirely in the background thread's event loop.
        The `async with` blocks set up and tear down the connection automatically.
        The `while self.running` loop keeps the connection alive until stop() is called.
        """
        try:
            # Launch the server subprocess and open stdio streams
            async with stdio_client(self.server_params) as (read, write):
                self.read_stream = read
                self.write_stream = write

                # Start an MCP session over those streams and do the protocol handshake
                async with ClientSession(read, write) as session:
                    self.session = session
                    await session.initialize()  # MCP handshake

                    # Hold the connection open by looping until stop() is called
                    while self.running:
                        await asyncio.sleep(0.1)  # Small sleep to avoid busy-waiting
        except Exception as e:
            print(f"MCP connection error: {e}")

    def call_tool_sync(self, name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """
        Synchronously calls an MCP tool — safe to use from the Tkinter UI thread.

        This method BLOCKS until the tool returns a result (or times out after 5 seconds).
        Under the hood, it schedules the async tool call on the background event loop
        and waits for the result using a Future.

        Returns the tool's response as a string, or an error message if something fails.
        """
        if not self.loop or not self.loop.is_running():
            return "Error: MCP client not running"

        # Schedule the async tool call on the background thread's event loop.
        # `run_coroutine_threadsafe` is the bridge between sync and async worlds.
        future = asyncio.run_coroutine_threadsafe(
            self._call_tool_async(name, arguments),
            self.loop
        )

        try:
            # Block the current (UI) thread until the result arrives, with a 5s timeout
            result = future.result(timeout=5.0)
            return result
        except Exception as e:
            return f"Error: {str(e)}"

    async def _call_tool_async(self, name: str, arguments: Dict[str, Any]) -> str:
        """
        The actual async tool call — runs inside the background event loop thread.

        Calls the named tool on the MCP server with the provided arguments,
        and returns the first text content block from the response.
        """
        if not self.session:
            return "Error: Not connected to MCP server"

        try:
            result = await self.session.call_tool(name, arguments)
            # MCP responses are lists of content blocks; we grab the first text one
            if result.content and len(result.content) > 0:
                return result.content[0].text
            return "No result"
        except Exception as e:
            return f"Error: {str(e)}"

    def list_tools_sync(self) -> List[str]:
        """
        Synchronously retrieves the list of available tool names from the server.

        Like call_tool_sync, this bridges the sync UI thread with the async event loop.
        Useful for debugging or dynamically building UI elements based on available tools.
        """
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
        """
        The actual async tool listing call — runs inside the background event loop thread.

        Returns a list of tool name strings from the server's tool registry.
        """
        if not self.session:
            return ["Error: Not connected to MCP server"]

        try:
            tools = await self.session.list_tools()
            return [t.name for t in tools.tools]
        except Exception as e:
            return [f"Error: {str(e)}"]