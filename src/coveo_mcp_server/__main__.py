import os
import uvicorn
from coveo_mcp_server.server import mcp

if __name__ == "__main__":
    transport = "sse" if os.getenv("USE_STDIO", "false").lower() != "true" else "stdio"
    print(f"✅ Running Coveo MCP Server on {transport} transport...")

    if transport == "sse":
        print("🔗 Connect to the server using a web browser or SSE client.")
        uvicorn.run(mcp.sse_app, host="127.0.0.1", port=8000)
    else:
        print("🔗 Connect to the server using a standard input/output client.")
        mcp.run(transport="stdio")
