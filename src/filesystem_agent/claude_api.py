from anthropic import (
    AnthropicError,
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)
from anthropic.types import (
    MessageParam,
    ToolChoiceAutoParam,
    ToolChoiceNoneParam,
    ToolChoiceParam,
    ToolParam,
)

import config


def create_message(client, message_param: MessageParam, tool_schemas: list[ToolParam] | None = None):
    tool_choice: ToolChoiceParam = ToolChoiceNoneParam(type="none")
    tools: list[ToolParam] = []
    if tool_schemas:
        tool_choice = ToolChoiceAutoParam(type="auto", disable_parallel_tool_use=True)
        tools = tool_schemas
    try:
        return client.messages.create(
            max_tokens=config.max_tokens,
            messages=[message_param],
            model=config.default_model,
            thinking=config.thinking_level,
            tool_choice=tool_choice,
            tools=tools,
        )
    except BadRequestError as e:
        # 400 — malformed request (bad params, bad tool schema). Not retryable; fix the call.
        e.add_note("Malformed request — check model params, messages, and tool schemas.")
        raise
    except AuthenticationError as e:
        # 401 — missing or invalid API key. Not retryable.
        e.add_note("Authentication failed — check ANTHROPIC_API_KEY.")
        raise
    except PermissionDeniedError as e:
        # 403 — key valid but lacks permission for this resource (model, workspace, ...). Not retryable.
        e.add_note("Permission denied — this API key can't access the requested resource.")
        raise
    except NotFoundError as e:
        # 404 — e.g. unknown model string. Not retryable.
        e.add_note("Resource not found — check the model name.")
        raise
    except ConflictError as e:
        # 409 — request conflicts with current state. Rare on Messages; retry may help.
        e.add_note("Conflict — the request clashed with the current resource state.")
        raise
    except UnprocessableEntityError as e:
        # 422 — well-formed request, semantically invalid. Not retryable.
        e.add_note("Unprocessable request — the payload was well-formed but semantically invalid.")
        raise
    except RateLimitError as e:
        # 429 — SDK already retried internally before this fires. Note retry-after if present.
        retry_after = e.response.headers.get("retry-after", "unknown")
        e.add_note(f"Rate limited — retry after {retry_after}s.")
        raise
    except InternalServerError as e:
        # >=500 — Anthropic-side failure. SDK already retried; safe to retry again later.
        e.add_note("Anthropic API server error — safe to retry later.")
        raise
    except APIConnectionError as e:
        # Network/connection failure, including APITimeoutError (its subclass). SDK already retried.
        e.add_note("Network error contacting the Anthropic API — check connectivity and retry.")
        raise
    except AnthropicError as e:
        # Catch-all for any other AnthropicError not named above.
        e.add_note("Unexpected error from the Anthropic API.")
        raise