"""
GitHub MCP Server
-----------------
Exposes GitHub repository data as MCP tools that Claude can call.

Usage:
  Set GITHUB_TOKEN in your environment (or .env file).
  The server is started by agent.py automatically — you don't run this directly.
"""

import os
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

app = Server("github-mcp-server")

# Global GitHub client and repo — set at startup via environment vars
_github: Github = None
_repo = None


def get_repo():
    global _github, _repo
    if _repo is None:
        token = os.environ.get("GITHUB_TOKEN", "")
        repo_name = os.environ.get("GITHUB_REPO", "")
        if not repo_name:
            raise ValueError("GITHUB_REPO environment variable not set.")
        _github = Github(token) if token else Github()
        _repo = _github.get_repo(repo_name)
    return _repo


# ---------------------------------------------------------------------------
# Tool Definitions
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_repo_info",
            description=(
                "Get general information about the repository: "
                "description, stars, forks, license, default branch, topics."
            ),
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_languages",
            description="Return the programming languages used in the repo and their byte counts.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_contributors",
            description="Return the top contributors ordered by commit count.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max number of contributors to return (default 10)"
                    }
                }
            }
        ),
        types.Tool(
            name="list_files",
            description=(
                "List files in the repository. Optionally filter by file extension "
                "or a path prefix."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "extension": {
                        "type": "string",
                        "description": "File extension filter e.g. '.py', '.js'"
                    },
                    "path_prefix": {
                        "type": "string",
                        "description": "Only include files under this path e.g. 'src/'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max files to return (default 200)"
                    }
                }
            }
        ),
        types.Tool(
            name="read_file",
            description="Read the full contents of a file in the repository.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file relative to repo root e.g. 'src/main.py'"
                    }
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="search_code",
            description=(
                "Search for a pattern/keyword across all files in the repo. "
                "Returns matching file paths and the lines that match."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text or keyword to search for"
                    },
                    "extension": {
                        "type": "string",
                        "description": "Limit search to files with this extension e.g. '.py'"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_commit_history",
            description="Get recent commits with author, date, and message.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of commits to return (default 20)"
                    },
                    "path": {
                        "type": "string",
                        "description": "Optional: only commits that touched this file path"
                    }
                }
            }
        ),
        types.Tool(
            name="list_issues",
            description="List open issues in the repository.",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "Filter by label e.g. 'bug'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max issues to return (default 20)"
                    }
                }
            }
        ),
        types.Tool(
            name="list_pull_requests",
            description="List open pull requests in the repository.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max PRs to return (default 20)"
                    }
                }
            }
        ),
        types.Tool(
            name="analyze_tests",
            description=(
                "Analyze test coverage by finding test files and comparing them "
                "to source files. Returns: test file list, source file list, "
                "estimated coverage percentage, and untested modules."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": "Language to analyze e.g. 'python', 'javascript'. Defaults to auto-detect."
                    }
                }
            }
        ),
    ]


# ---------------------------------------------------------------------------
# Tool Handlers
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        repo = get_repo()

        # ── get_repo_info ──────────────────────────────────────────────────
        if name == "get_repo_info":
            info = (
                f"Name: {repo.full_name}\n"
                f"Description: {repo.description}\n"
                f"Stars: {repo.stargazers_count}\n"
                f"Forks: {repo.forks_count}\n"
                f"Open Issues: {repo.open_issues_count}\n"
                f"Default Branch: {repo.default_branch}\n"
                f"License: {repo.license.name if repo.license else 'None'}\n"
                f"Topics: {', '.join(repo.get_topics()) or 'None'}\n"
                f"Language: {repo.language}\n"
                f"Created: {repo.created_at}\n"
                f"Last Push: {repo.pushed_at}\n"
            )
            return [types.TextContent(type="text", text=info)]

        # ── get_languages ──────────────────────────────────────────────────
        elif name == "get_languages":
            langs = repo.get_languages()
            total = sum(langs.values()) or 1
            lines = [f"{lang}: {bytes_:,} bytes ({bytes_/total*100:.1f}%)"
                     for lang, bytes_ in sorted(langs.items(), key=lambda x: -x[1])]
            return [types.TextContent(type="text", text="\n".join(lines))]

        # ── get_contributors ───────────────────────────────────────────────
        elif name == "get_contributors":
            limit = arguments.get("limit", 10)
            contributors = list(repo.get_contributors())[:limit]
            lines = [f"{c.login}: {c.contributions} commits" for c in contributors]
            return [types.TextContent(type="text", text="\n".join(lines))]

        # ── list_files ─────────────────────────────────────────────────────
        elif name == "list_files":
            ext = arguments.get("extension", "").lower()
            prefix = arguments.get("path_prefix", "").lower()
            limit = arguments.get("limit", 200)
            contents = repo.get_git_tree(repo.default_branch, recursive=True)
            files = [
                item.path for item in contents.tree
                if item.type == "blob"
                and (not ext or item.path.lower().endswith(ext))
                and (not prefix or item.path.lower().startswith(prefix))
            ][:limit]
            result = f"Found {len(files)} files:\n" + "\n".join(files)
            return [types.TextContent(type="text", text=result)]

        # ── read_file ──────────────────────────────────────────────────────
        elif name == "read_file":
            path = arguments["path"]
            file_content = repo.get_contents(path)
            if isinstance(file_content, list):
                return [types.TextContent(type="text", text="That path is a directory, not a file.")]
            decoded = file_content.decoded_content.decode("utf-8", errors="replace")
            # Truncate very large files
            if len(decoded) > 30_000:
                decoded = decoded[:30_000] + "\n\n[... file truncated at 30,000 chars ...]"
            return [types.TextContent(type="text", text=decoded)]

        # ── search_code ────────────────────────────────────────────────────
        elif name == "search_code":
            query = arguments["query"]
            ext = arguments.get("extension", "").lower()
            contents = repo.get_git_tree(repo.default_branch, recursive=True)
            matches = []
            for item in contents.tree:
                if item.type != "blob":
                    continue
                if ext and not item.path.lower().endswith(ext):
                    continue
                try:
                    file_obj = repo.get_contents(item.path)
                    text = file_obj.decoded_content.decode("utf-8", errors="replace")
                    for i, line in enumerate(text.splitlines(), 1):
                        if query.lower() in line.lower():
                            matches.append(f"{item.path}:{i}: {line.strip()}")
                            if len(matches) >= 100:
                                break
                except Exception:
                    continue
                if len(matches) >= 100:
                    break
            if not matches:
                return [types.TextContent(type="text", text=f"No matches found for '{query}'")]
            result = f"Found {len(matches)} match(es) for '{query}':\n\n" + "\n".join(matches)
            return [types.TextContent(type="text", text=result)]

        # ── get_commit_history ─────────────────────────────────────────────
        elif name == "get_commit_history":
            limit = arguments.get("limit", 20)
            path = arguments.get("path")
            kwargs = {"path": path} if path else {}
            commits = list(repo.get_commits(**kwargs))[:limit]
            lines = [
                f"{c.sha[:7]} | {c.commit.author.name} | {c.commit.author.date.strftime('%Y-%m-%d')} | {c.commit.message.splitlines()[0]}"
                for c in commits
            ]
            return [types.TextContent(type="text", text="\n".join(lines))]

        # ── list_issues ────────────────────────────────────────────────────
        elif name == "list_issues":
            limit = arguments.get("limit", 20)
            label = arguments.get("label")
            kwargs = {"labels": [label]} if label else {}
            issues = list(repo.get_issues(state="open", **kwargs))[:limit]
            lines = [
                f"#{i.number} [{', '.join(l.name for l in i.labels) or 'no labels'}] {i.title}"
                for i in issues
            ]
            result = f"Open issues ({len(lines)}):\n" + "\n".join(lines)
            return [types.TextContent(type="text", text=result)]

        # ── list_pull_requests ─────────────────────────────────────────────
        elif name == "list_pull_requests":
            limit = arguments.get("limit", 20)
            prs = list(repo.get_pulls(state="open"))[:limit]
            lines = [
                f"#{pr.number} [{pr.head.ref} → {pr.base.ref}] {pr.title} (by {pr.user.login})"
                for pr in prs
            ]
            result = f"Open pull requests ({len(lines)}):\n" + "\n".join(lines)
            return [types.TextContent(type="text", text=result)]

        # ── analyze_tests ──────────────────────────────────────────────────
        elif name == "analyze_tests":
            lang = arguments.get("language", "").lower()
            contents = repo.get_git_tree(repo.default_branch, recursive=True)
            all_files = [item.path for item in contents.tree if item.type == "blob"]

            # Detect language from repo if not specified
            if not lang:
                repo_lang = (repo.language or "").lower()
                lang = repo_lang

            # Define test vs source patterns per language
            test_patterns = ["test", "spec", "__tests__"]
            if lang in ("python", "py"):
                src_ext, test_ext = ".py", ".py"
            elif lang in ("javascript", "js", "typescript", "ts"):
                src_ext = (".js", ".ts", ".jsx", ".tsx")
                test_ext = (".test.js", ".spec.js", ".test.ts", ".spec.ts")
            else:
                src_ext, test_ext = None, None

            def is_test(path):
                p = path.lower()
                return any(pat in p for pat in test_patterns)

            def is_source(path):
                p = path.lower()
                if is_test(p):
                    return False
                if src_ext:
                    exts = src_ext if isinstance(src_ext, tuple) else (src_ext,)
                    return any(p.endswith(e) for e in exts)
                return True

            test_files = [f for f in all_files if is_test(f)]
            source_files = [f for f in all_files if is_source(f)]

            if source_files:
                coverage_estimate = min(100, round(len(test_files) / len(source_files) * 100))
            else:
                coverage_estimate = 0

            result = (
                f"Test Analysis for {repo.full_name}\n"
                f"{'='*50}\n"
                f"Source files: {len(source_files)}\n"
                f"Test files:   {len(test_files)}\n"
                f"Estimated test coverage: ~{coverage_estimate}%\n\n"
                f"Test files found:\n" + "\n".join(f"  {f}" for f in test_files[:50]) +
                ("\n  ... (truncated)" if len(test_files) > 50 else "") +
                f"\n\nSource files (sample of up to 30):\n" +
                "\n".join(f"  {f}" for f in source_files[:30])
            )
            return [types.TextContent(type="text", text=result)]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except GithubException as e:
        return [types.TextContent(type="text", text=f"GitHub API error: {e.status} — {e.data.get('message', str(e))}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
