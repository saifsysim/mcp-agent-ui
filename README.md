# mcp-agent-ui

A web dashboard for running AI agents powered by [Claude](https://anthropic.com) and the [Model Context Protocol (MCP)](https://modelcontextprotocol.io).

Features:
- 💬 **Live Chat** — ask Claude questions about any GitHub repo; watch every MCP tool call in real-time
- 🗄️ **Repo Tracker** — local SQLite database tracking repo health (PRs, commits, contributors, etc.)
- ⚡ **Streaming UI** — Server-Sent Events for real-time agent responses

## Architecture

```
mcp-agent-ui/
  app.py              ← FastAPI backend with SSE streaming
  agent.py            ← Claude agentic loop
  cli.py              ← Terminal interface
  db.py               ← SQLite repo tracker database
  tracker.py          ← GitHub stats fetcher
  static/index.html   ← Dashboard UI
  servers/
    github/server.py  ← Bundled GitHub MCP server
```

The bundled `servers/github/server.py` is also available as a standalone server at [mcp-servers](https://github.com/saifsysim/mcp-servers).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY
```

## Running

```bash
python app.py
# Open http://localhost:8000
```

## Repo Tracker

The local SQLite database (`repos.db`) tracks:

| Metric | Description |
|---|---|
| Stars / Forks | Repository popularity |
| Open PRs | Current pull request count |
| Commits (30d) | Activity over last 30 days |
| Days since last commit | Freshness indicator |
| Days since last merge | PR merge activity |
| Top contributor | Most active committer |
| Repo created date | Project age |
| Health status | 🟢 Active / 🔵 Recent / 🟡 Quiet / 🔴 Stale |

## CLI Usage

```bash
python cli.py --repo pallets/flask --ask "How much test coverage does this repo have?"
```
