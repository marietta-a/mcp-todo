## Project Structure

```
MCP-TODO/
├── shared/
│   └── todo_model.py        # Shared data model (used by both client & server)
│
├── client/
│   ├── constants.py         # UI color palette
│   ├── mcp_todo_client.py   # Thread-safe MCP client wrapper
│   ├── todo_client.py       # CLI test client
│   └── todo_ui.py           # Tkinter desktop UI
│
├── server/
│   ├── config.py            # Shared database instance (singleton)
│   ├── todo_manager.py      # In-memory CRUD database
│   ├── todo_service.py      # MCP server entry point
│   └── tools/
│       ├── __init__.py      # Tool registry
│       ├── add.py
│       ├── delete.py
│       ├── list_all.py
│       ├── schema.py
│       └── update.py
│
├── utils/
│   └── todo_utils.py        # JSON parsing helpers
│
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## Getting Started

### 1. Fork and Clone the repository

```bash
git clone https://github.com/your-username/mcp-todo.git
cd mcp-todo
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

---

## Running the App

### Start the desktop UI

```bash
python -m client.todo_ui
```

### Test the server via the CLI client

```bash
python -m client.todo_client
```

### Start the MCP server directly

```bash
python -m server.todo_service
```

---

## How It Works

```
 [Tkinter UI]
      │  calls
      ▼
 [MCPTodoClient]          ← bridges sync UI with async MCP
      │  calls (async)
      ▼
 [MCP Server]             ← todo_service.py
      │  routes to
      ▼
 [Tool Handler]           ← add / delete / update / list
      │  reads/writes
      ▼
 [TodoDataManager]        ← in-memory task list
```

1. The UI calls `mcp_client.call_tool_sync("add", {...})`
2. The MCP client forwards the request to the server over stdio
3. The server routes it to the correct tool handler
4. The handler validates input (via Pydantic) and runs the operation
5. The result is serialized to JSON and returned to the UI

---

## Key Concepts Covered

| Concept | Where to look |
|---|---|
| Defining an MCP tool | `server/tools/add.py` |
| Registering tools with the server | `server/tools/__init__.py` |
| Running an MCP server | `server/todo_service.py` |
| Connecting as an MCP client | `client/todo_client.py` |
| Bridging async MCP with a sync UI | `client/mcp_todo_client.py` |
| Pydantic data validation | `shared/todo_model.py`, `server/tools/schema.py` |

---

## Requirements

- Python 3.10+
- `mcp >= 1.0.0`
- `pydantic >= 2.0.0`