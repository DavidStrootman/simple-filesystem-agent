from dataclasses import dataclass
from enum import StrEnum

from anthropic.types import ThinkingConfigAdaptiveParam


class _Models(StrEnum):
    CLAUDE_SONNET_5 = "claude-sonnet-5"
    CLAUDE_OPUS_5 = "claude-opus-5"


@dataclass
class Config:
    max_tokens = 2500
    default_model: _Models = _Models.CLAUDE_SONNET_5
    thinking_level = ThinkingConfigAdaptiveParam(type="adaptive")  # Defaulted to adaptive for opus 5

    def __post_init__(self):
        if self.default_model == _Models.CLAUDE_OPUS_5:
            # Always default to adaptive thinking for Claude Opus 5 to prevent issues with unsupported thinking modes
            self.thinking_level = ThinkingConfigAdaptiveParam(type="adaptive")
