"""
app.py — Thin static server for the MCP Agent UI.

This server ONLY serves the frontend and proxies nothing.
All agent logic lives in the mcp-github-agent backend (default: http://localhost:8000).

The frontend HTML reads window.MCP_BACKEND_URL (injected below) to know
where the backend is — so you can point it at staging/prod without rebuilding.

Run with:
  python app.py
Then open http://localhost:8001
"""

import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.environ.get("MCP_BACKEND_URL", "http://localhost:8000")

app = FastAPI(title="MCP Agent UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve index.html with backend URL injected at the top."""
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(html_path) as f:
        html = f.read()

    # Inject backend URL so the frontend knows where the API lives
    injection = f'<script>window.MCP_BACKEND_URL = "{BACKEND_URL}";</script>'
    html = html.replace("<head>", f"<head>\n    {injection}", 1)
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
