import logging
import os

from anthropic import Anthropic
from anthropic.types import (
    ContentBlock,
    Message,
    MessageParam,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
)

from src.filesystem_agent import claude_api
from src.filesystem_agent.filesystem_tools import tool_schemas

logger = logging.getLogger(__name__)


class FilesystemAgent:
    def __init__(self):
        self.client = Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )

    def ask(self, question: str):
        print(f"Question: {question}")
        logger.info("USER | Message: %s", question)
        message_user = MessageParam(content=question, role="user")
        message_resp: Message = claude_api.create_message(
            self.client, message_user, tool_schemas
        )

        resp_content: list[ContentBlock] = message_resp.content
        for content in resp_content:
            match content:
                case TextBlock(text=text):
                    agent_message = f"Agent response: {text}"
                    print(agent_message)
                    logger.info("AGENT| Message: %s", text)
                case ThinkingBlock(thinking=thinking):
                    logger.debug("AGENT| Thinking: %s", thinking)
                case ToolUseBlock(name=name):
                    # TODO: Handle tool use block
                    logger.debug("AGENT| Tool use: %s", name)
                case _:
                    raise RuntimeError(
                        f"Could not parse unexpected content type {type(content)}."
                    )
