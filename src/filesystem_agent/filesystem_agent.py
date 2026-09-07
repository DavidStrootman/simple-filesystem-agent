import logging
import os

from anthropic import Anthropic
from anthropic.types import (
    Message,
    MessageParam,
    StopReason,
    TextBlock,
    ThinkingBlock,
    ToolResultBlockParam,
    ToolUseBlock,
)

from src.filesystem_agent import claude_api
from src.filesystem_agent.filesystem_tools import dispatch, tool_schemas

logger = logging.getLogger(__name__)


def _log_agent_message(message: str, level=logging.DEBUG):
    logger.log(level=level, msg="AGENT| " + message)


def _log_user_message(message: str, level=logging.DEBUG):
    logger.log(level=level, msg="USER | " + message)


class FilesystemAgent:
    def __init__(self):
        self.client = Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )

    def ask(self, question: str):
        print(f"Question: {question}")
        _log_user_message(f"Question: {question}", level=logging.INFO)
        message_user = MessageParam(content=question, role="user")
        return self._looped_messaging(message_user)

    def _looped_messaging(self, initial_message: MessageParam):
        message_list: list[MessageParam] = [initial_message]
        done = False
        while not done:
            message_resp: Message = claude_api.create_message(
                self.client, message_list, tool_schemas
            )

            new_messages, done = self.handle_stop_reason(message_resp)
            message_list.extend(new_messages)

    def handle_stop_reason(
        self, message_resp: Message
    ) -> tuple[list[MessageParam], bool]:
        end_of_turn = False
        stop_reason: StopReason | None = message_resp.stop_reason

        message_params: list[MessageParam] = [
            MessageParam(role="assistant", content=message_resp.content)
        ]
        match stop_reason:
            case "end_turn":
                # End of response
                message_params = self.handle_content_blocks(
                    message_resp, message_params
                )
                end_of_turn = True
            case "max_tokens":
                message_params = self.handle_content_blocks(
                    message_resp, message_params
                )
                end_of_turn = True
            case "stop_sequence":
                # TODO: Implement stop sequence handling (and passing?)
                raise RuntimeError(
                    "Stop sequence received but stop sequences are not implemented."
                )
            case "tool_use":
                message_params = self.handle_content_blocks(
                    message_resp, message_params
                )
            case "pause_turn":
                # Pause turn indicates the server has exceeded its limits for a single request. Send the complete received message back in without modification.
                message_params = self.handle_content_blocks(
                    message_resp, message_params
                )
            case "refusal":
                # Server or model refused the request. Retry with changes made based on the stop_details.
                # TODO
                raise RuntimeError("Server or model refused the request.")
            case "model_context_window_exceeded":
                # Context window was exceeded which has likely truncated the output. This state should have been prevented.
                # TODO
                message_params = self.handle_content_blocks(
                    message_resp, message_params
                )
                end_of_turn = True

        return message_params, end_of_turn

    def handle_content_blocks(
        self,
        message_resp: Message,
        message_params: list[MessageParam],
    ) -> list[MessageParam]:
        """Loop over all tool usage, in case parallel tool use is enabled. Only return after all blocks are run."""
        tool_result_params: list[ToolResultBlockParam] = []
        for block in message_resp.content:
            match block:
                case ToolUseBlock() as tool_use_block:
                    tool_result_params.append(
                        self.handle_tool_use_block(tool_use_block)
                    )
                case TextBlock() as block:
                    self.handle_text_block(block)
                case ThinkingBlock() as block:
                    self.handle_thinking_block(block)
                case _:
                    raise NotImplementedError(
                        f"Unexpected content type {type(block)}. Implement before continuing"
                    )
        message_params.append(MessageParam(role="user", content=tool_result_params))
        return message_params

    def handle_tool_use_block(
        self, tool_use_block: ToolUseBlock
    ) -> ToolResultBlockParam:
        _log_agent_message(f"Request tool use: {tool_use_block.name}")
        tool_result, is_error = dispatch(tool_use_block.name, **tool_use_block.input)
        return ToolResultBlockParam(
            tool_use_id=tool_use_block.id,
            type="tool_result",
            content=tool_result,
            is_error=is_error,
        )

    def handle_text_block(self, block: TextBlock):
        print(block.text, end="")
        _log_agent_message(f"Message: {block.text}", level=logging.INFO)

    def handle_thinking_block(self, block: ThinkingBlock):
        _log_agent_message(f"Thought: {block.thinking}")
