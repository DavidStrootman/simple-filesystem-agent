from enum import StrEnum

from anthropic.types import ThinkingConfigAdaptiveParam

__all__ = ["default_model", "max_tokens", "thinking_level"]


class _Models(StrEnum):
    CLAUDE_SONNET_5 = "claude-sonnet-5"
    CLAUDE_OPUS_5 = "claude-opus-5"


max_tokens = 2500
default_model = _Models.CLAUDE_SONNET_5

thinking_level = ThinkingConfigAdaptiveParam(type="adaptive", display="summarized")
