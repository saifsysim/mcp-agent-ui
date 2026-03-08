# mcp-agent-ui

> Decoupled web dashboard for MCP agents — UI auto-discovers agents from the backend API

---

## What This Is

This is the **frontend-only** repo. It serves the web UI and reads its agent list from the [`mcp-github-agent`](https://github.com/saifsysim/mcp-github-agent) backend. No agent logic lives here — adding agents to the backend automatically shows them in the UI.

---

## Setup

### Step 1 — You need the backend running first

This repo has no agent logic of its own. Clone and start the backend:

```bash
git clone https://github.com/saifsysim/mcp-github-agent.git
cd mcp-github-agent
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY and GITHUB_TOKEN to .env (see backend README for details)
python app.py
# → Backend running on http://localhost:8000
```

### Step 2 — Clone & install the UI

```bash
git clone https://github.com/saifsysim/mcp-agent-ui.git
cd mcp-agent-ui
pip install -r requirements.txt
```

### Step 3 — Configure

```bash
cp .env.example .env
```

`.env` contents:
```env
# URL of the mcp-github-agent backend
MCP_BACKEND_URL=http://localhost:8000

# Port this UI server listens on
PORT=8001
```

> If your backend runs on a different host/port, update `MCP_BACKEND_URL` here.

---

## Running

```bash
python app.py
```

Open **[http://localhost:8001](http://localhost:8001)**

The UI will call `GET /api/agents` on the backend and render a card for every registered agent automatically.

---

## How It Connects to the Backend

```
Browser → http://localhost:8001 → This repo (serves index.html)
Browser → http://localhost:8000/api/agents   → Backend (agent cards)
Browser → http://localhost:8000/api/chat     → Backend (SSE stream)
Browser → http://localhost:8000/api/repos    → Backend (repo tracker)
```

The backend URL is injected into the HTML at serve-time via `window.MCP_BACKEND_URL` — so you can point this UI at a staging or production backend without rebuilding anything.

---

## Project Structure

```
mcp-agent-ui/
├── app.py              # Thin static server — injects MCP_BACKEND_URL into HTML
├── static/
│   └── index.html      # Full dashboard UI (agent cards + chat + repo tracker)
├── servers/
│   └── github/
│       └── server.py   # Bundled GitHub MCP server (for reference)
├── requirements.txt    # fastapi, uvicorn, python-dotenv only
└── .env.example
```
