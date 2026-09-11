# Filesystem Agent

A small, hand-built Claude agent that answers natural-language questions about files
on your machine. You ask a question, the agent decides which filesystem tools to call
(directory listing, search, file size, file content, ...), and it answers from the
results — looping on its own until it has enough information.

Built around a manual tool-use loop (no SDK tool runner) as a learning exercise for
the Anthropic API — see [PLAN.md](PLAN.md) for the build plan and rationale. All
filesystem access is sandboxed to the current user's home directory; the model only
ever sees paths relative to that root, never the real absolute path.

## What it can do

The agent currently has six tools available to it:

| Tool | Description |
|---|---|
| `cwd` | Get the current working directory, relative to the sandbox root |
| `list_dir` | List the contents of a directory |
| `search_files` | Recursively search a directory for files/subdirectories matching a glob pattern |
| `dir_name` | Get the name of a directory from a path |
| `get_file_size` | Get a file's size in bytes |
| `get_file_content` | Read a file's contents (capped at 25,000 characters; reports if the file has more) |

Claude decides which of these to call, in what order, and can chain multiple calls
together to answer one question (e.g. "find all the config files under this directory,
then show me the contents of the largest one").

## Requirements

- Python 3.14+ (pinned via `.python-version`)
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- An [Anthropic API key](https://platform.claude.com/settings/keys)

## Install

```bash
uv sync
```

This creates `.venv` and installs everything from `uv.lock`, including the `ruff`/`ty`
dev tools.

## Configure

Copy the example env file and add your API key:

```bash
cp .env.example .env
```

Then edit `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Model, token limits, and thinking configuration live in [config.py](config.py) — the
default model is `claude-sonnet-5`. The sandbox root (`sandbox_home`) also lives here,
defaulting to the current user's home directory.

## Run

```bash
uv run main.py
```

This starts an interactive prompt — enter a question, get an answer, and keep asking
follow-up questions in the same session (conversation history is kept for the
duration of one run). Type `exit` to quit.

## Logging

Every run writes structured logs to `agent.log` at the project root (rotated at 1MB,
3 backups kept). See [logging_config.py](logging_config.py) — `LOG_TO_CONSOLE` there
toggles whether logs are also mirrored to stdout, off by default.

## Project layout

```
main.py                              entry point — loads .env, starts the agent
config.py                            model, token, thinking, and sandbox configuration
logging_config.py                    logging setup (file + optional console)
src/filesystem_agent/
    filesystem_agent.py              the manual agentic loop
    filesystem_tools.py              tool definitions, dispatch, and sandbox path handling
    claude_api.py                    the Anthropic API call + error handling
```
