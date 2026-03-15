from asyncio import run

from mcp.server.fastmcp.server import FastMCP
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl

from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.applications import Starlette
from starlette.routing import Mount

# CREATE WEB SEVER AND MCP INSTANCE

settings = {
    "host": "localhost",
    "port": 8000,
    "auth_server_url": AnyHttpUrl("http://localhost:8001"),
    "mcp_scope": "mcp.read",
    "server_url": AnyHttpUrl("http://localhost:8000")
}


app = FastMCP(
 name="MCP File Server",
 instructions="MCP File Server is a simple file server that allows users to upload and download files. It validates tokens via Authentication Server Introspection",
 host=settings["host"],
 port=settings["port"],
 debug=True
)

# creating starlette web app
starlette_app = app.streamable_http_app()

# serving app via uvicorn
async def fun(starlette_app):
    import uvicorn
    config = uvicorn.Config(
        starlette_app, 
        host=app.settings.host, 
        port=app.settings.port, 
        log_level=app.settings.log_level.lower()
    )
    server = uvicorn.Server(config)
    await server.serve()

run(starlette_app)


# IMPLEMENT A MIDDLEWARE FOR THE SERVER

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):

        has_header = request.headers.get("Authorization")
        if not has_header:
            print("-> Missing Authorization header")
            return Response(
                status_code= 401,
                content="UnAuthorized"
            )
        if not valid_token(has_header):
            print("-> Invalid token")
            return Response(
                status_code=403,
                content="Forbidden"
            )
        
        print("Valid token, proceeding ...")
        print(f"-> Received {request.method} {request.url}")
        response = await call_next(request)
        response.headers['Custome'] = 'Example'
        return response

#DON'T USE FOR PRODUCTION - IMPROVE IT!!!
def valid_token(token: str) -> bool:
    # remove the "Bearer " prefix
    if(token.startswith("Bearer ")):
        token = token[7:]
        return token == "secret-token"
    return False