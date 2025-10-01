import os
import uvicorn
from coveo_mcp_server.server import mcp

if __name__ == "__main__":
    # Check for transport type from environment variable
    use_stdio = os.getenv("USE_STDIO", "false").lower() == "true"
    use_sse = os.getenv("USE_SSE", "false").lower() == "true"
    
    if use_stdio:
        transport = "stdio"
    elif use_sse:
        transport = "sse"
    else:
        # Default to the new streamable-http transport
        transport = "streamable-http"
    
    print(f"✅ Running Coveo MCP Server on {transport} transport...")

    if transport == "streamable-http":
        print("🔗 Connect to the server using the streamable-http protocol.")
        print("📍 Server will be available at http://127.0.0.1:8000")
        mcp.run(transport="streamable-http")
    elif transport == "sse":
        print("🔗 Connect to the server using a web browser or SSE client.")
        print("📍 Server will be available at http://127.0.0.1:8000")
        uvicorn.run(mcp.sse_app, host="127.0.0.1", port=8000)
    else:  # stdio
        print("🔗 Connect to the server using a standard input/output client.")
        mcp.run(transport="stdio")
