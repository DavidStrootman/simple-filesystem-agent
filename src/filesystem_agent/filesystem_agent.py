import os

from anthropic import Anthropic
from anthropic.types import ContentBlock, Message, MessageParam, TextBlock

from src.filesystem_agent import claude_api
from src.filesystem_agent.filesystem_tools import tool_schemas


class FilesystemAgent:
    def __init__(self):
        self.client = Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )

    def ask(self, question: str):
        print(f"User message: {question}")
        message_user = MessageParam(content=question, role="user")
        message_resp: Message = claude_api.create_message(
            self.client, message_user, tool_schemas
        )

        resp_content: list[ContentBlock] = message_resp.content
        for content in resp_content:
            match content:
                case TextBlock(text=text):
                    agent_message = f"Agent message: {text}"
                    print(agent_message)
                case _:
                    raise RuntimeError(
                        f"Could not parse unexpected content type {type(content)}."
                    )
