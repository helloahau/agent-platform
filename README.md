# Agent Platform

A modular, extensible Python platform for creating, configuring, and running AI agents — with tool use, memory, multi-agent orchestration, a REST API, and a Streamlit dashboard.

## Quick Start

```bash
# 1. Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env   # then fill in your keys

# 4. Start the API server
uvicorn api.main:app --reload

# 5. (Optional) Start the Streamlit UI
streamlit run ui/app.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPEN_AI_KEY` | Yes | Azure OpenAI / EPAM AI Proxy API key |
| `AZURE_OPEN_AI_ENDPOINT` | Yes | Azure OpenAI endpoint URL |
| `GITHUB_TOKEN` | For PR/write ops | GitHub Personal Access Token ([create one](https://github.com/settings/tokens)) |
| `LANGCHAIN_API_KEY` | No | LangSmith tracing key |
| `LANGCHAIN_TRACING_V2` | No | Enable LangSmith tracing (`true`/`false`) |

### GitHub Token Setup

To enable the agent to read private repos and write to GitHub (comment on PRs, update PRs, create issues, merge), set `GITHUB_TOKEN` in your `.env`:

```bash
GITHUB_TOKEN=ghp_your_token_here
```

Create a token at https://github.com/settings/tokens with scopes: `repo`, `read:org`.
This works the same whether running locally or remotely — the agent reads the token from `.env` at startup.

## Project Structure

```
config/          Settings loader (.env)
core/
  llm/           LLM provider abstraction (Azure OpenAI, extensible)
  tools/         Built-in tools (calculator, web search, file reader, GitHub)
  memory/        Conversation + persistent (SQLite) memory
  agent/         Core Agent with ReAct loop, YAML config loading
orchestration/   Multi-agent pipeline & router
api/             FastAPI REST API (CRUD agents, chat, tools)
ui/              Streamlit dashboard
agents/          YAML agent definitions
tests/           Test suite
```

## Built-in Tools

| Tool | Description | Auth Required |
|------|-------------|---------------|
| `calculator` | Evaluate math expressions | No |
| `web_search` | Search the web via DuckDuckGo | No |
| `file_reader` | Read local files | No |
| `github` | Full GitHub integration (see below) | Token for write ops |

### GitHub Tool Actions

**Read actions** (work without token on public repos):
- `search_repos` — Find repositories by keyword
- `get_repo` — Get repository details
- `list_files` / `read_file` — Browse and read repo contents
- `list_issues` / `get_issue` — List and read issues
- `list_prs` / `get_pr` / `get_pr_diff` — List PRs, read details, view diffs

**Write actions** (require `GITHUB_TOKEN`):
- `create_issue` — Create a new issue
- `comment_on_issue` / `comment_on_pr` — Post comments
- `update_pr` — Update PR title, body, or state
- `merge_pr` — Merge a pull request

## Creating an Agent (YAML)

Drop a `.yaml` file in `agents/`:

```yaml
name: my-agent
description: A custom agent that can search the web and interact with GitHub.
system_prompt: |
  You are a helpful research assistant.
tools:
  - web_search
  - github
  - calculator
max_iterations: 10
temperature: 0.0
memory_type: conversation
```

## Creating an Agent (API)

```bash
curl -X POST http://localhost:8000/api/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-agent",
    "description": "A custom agent",
    "system_prompt": "You are helpful.",
    "tools": ["calculator", "web_search", "github"]
  }'
```

## Chat with an Agent

```bash
curl -X POST http://localhost:8000/api/chat/my-agent \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 42 * 17?"}'
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/agents/` | List all agents |
| GET | `/api/agents/{name}` | Get agent details |
| POST | `/api/agents/` | Create a new agent |
| DELETE | `/api/agents/{name}` | Delete an agent |
| POST | `/api/chat/{name}` | Chat with an agent |
| POST | `/api/chat/{name}/stream` | Chat with SSE streaming |
| GET | `/api/tools/` | List available tools |

## Running Tests

```bash
PYTHONPATH=. pytest tests/ -v
```

## Architecture

- **LLM Layer**: Abstract provider interface with Azure OpenAI implementation. Add new providers by subclassing `BaseLLMProvider`.
- **Tool System**: Tools are Python classes with typed schemas. Register custom tools via `ToolRegistry.register()`.
- **Memory**: Pluggable memory backends — in-memory conversation history or SQLite-backed persistent memory.
- **Agent Core**: ReAct (Reasoning + Acting) loop that reasons, calls tools, observes results, and iterates.
- **Orchestration**: Chain agents in a sequential pipeline or use a router agent to delegate to specialists.
- **API**: FastAPI with full CRUD, chat, and streaming endpoints.
- **UI**: Streamlit dashboard for visual agent creation, management, and interactive chat.
