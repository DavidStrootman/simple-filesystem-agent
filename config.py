from enum import StrEnum
from pathlib import Path
from typing import Literal

from anthropic.types import ThinkingConfigAdaptiveParam

__all__ = ["default_model", "max_tokens", "thinking_level"]


class _Models(StrEnum):
    CLAUDE_SONNET_5 = "claude-sonnet-5"
    CLAUDE_OPUS_5 = "claude-opus-5"


max_tokens = 2500
default_model: Literal[_Models.CLAUDE_SONNET_5] = _Models.CLAUDE_SONNET_5

thinking_level = ThinkingConfigAdaptiveParam(type="adaptive", display="summarized")
disable_parallel_tool_use = False

sandbox_home = Path.home()