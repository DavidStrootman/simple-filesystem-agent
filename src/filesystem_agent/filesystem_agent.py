import logging
import os
from typing import Literal

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


def _log(
    actor: Literal["AGENT", "USER", "SYSTEM"], message: str, level: int = logging.DEBUG
) -> None:
    # actor is its own LogRecord field, formatted as a column by
    # logging_config.py's "actor" format entry.
    logger.log(level, message, extra={"actor": actor})


def _log_agent_message(message: str, level: int = logging.DEBUG) -> None:
    _log("AGENT", message, level)


def _log_user_message(message: str, level: int = logging.DEBUG) -> None:
    _log("USER", message, level)


def _log_system_message(message: str, level: int = logging.DEBUG) -> None:
    _log("SYSTEM", message, level)


class FilesystemAgent:
    def __init__(self):
        self.client = Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )

    def ask(self):
        message_history: list[MessageParam] = []
        _log_system_message("Filesystem agent started. Starting conversation.")
        while True:
            question = input("Enter your question or type 'exit' to quit: ")
            if question.lower() == "exit":
                _log_system_message("Exiting conversation.")
                break
            print(f"Question: {question}")
            message_history.append(MessageParam(content=question, role="user"))
            message_history: list[MessageParam] = self._message_loop(message_history)
            _log_system_message("Response completed. Waiting for next question.")

    def _message_loop(self, message_history: list[MessageParam]) -> list[MessageParam]:
        # Every caller passes through here before the first API call, so this
        # is the one place a pending user question always gets logged.
        if message_history and message_history[-1]["role"] == "user":
            pending = message_history[-1]["content"]
            if isinstance(pending, str):
                _log_user_message(f"Question: {pending}", level=logging.INFO)

        done = False
        while not done:
            message_resp: Message = claude_api.create_message(
                self.client,
                prev_built_message=message_history,
                tool_schemas=tool_schemas,
            )

            new_messages, done = self.handle_stop_reason(message_resp)
            message_history.extend(new_messages)
        return message_history

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
                _log_agent_message("Stop reason: End of response")
                end_of_turn = True
            case "max_tokens":
                message_params = self.handle_content_blocks(
                    message_resp, message_params
                )
                _log_agent_message("Stop reason: Max tokens reached")
                end_of_turn = True
            case "stop_sequence":
                # TODO: Implement stop sequence handling (and passing?)
                _log_agent_message("Stop reason: Stop sequence received")
                raise RuntimeError(
                    "Stop sequence received but stop sequences are not implemented."
                )
            case "tool_use":
                _log_agent_message("Stop reason: Tool use received")
                message_params = self.handle_content_blocks(
                    message_resp, message_params
                )
            case "pause_turn":
                _log_agent_message("Stop reason: Pause turn received")
                # Pause turn indicates the server has exceeded its limits for a single request. Send the complete received message back in without modification.
                message_params = self.handle_content_blocks(
                    message_resp, message_params
                )
            case "refusal":
                _log_agent_message("Stop reason: Refusal received")
                # Server or model refused the request. Retry with changes made based on the stop_details.
                # TODO
                raise RuntimeError("Server or model refused the request.")
            case "model_context_window_exceeded":
                _log_agent_message("Stop reason: Model context window exceeded")
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
        """Process every content block in the response, collecting all tool
        results into a single combined tool_result turn — required even
        when only one tool was called, and essential when parallel tool use
        returns several at once."""
        tool_result_params: list[ToolResultBlockParam] = []
        multiple_tool_use = (
            len([block for block in message_resp.content if block.type == "tool_use"])
            > 1
        )
        if multiple_tool_use:
            _log_agent_message("Requested multiple tool usage.")
        for block in message_resp.content:
            match block:
                case ToolUseBlock() as tool_use_block:
                    tool_result_params.append(
                        BlockHandler.handle_tool_use_block(tool_use_block)
                    )
                case TextBlock() as block:
                    BlockHandler.handle_text_block(block)
                case ThinkingBlock() as block:
                    BlockHandler.handle_thinking_block(block)
                case _:
                    raise NotImplementedError(
                        f"Unexpected content type {type(block)}. Implement before continuing"
                    )
        if tool_result_params:
            message_params.append(MessageParam(role="user", content=tool_result_params))
        return message_params


class BlockHandler:
    @staticmethod
    def handle_tool_use_block(tool_use_block: ToolUseBlock) -> ToolResultBlockParam:
        _log_agent_message(f"Request tool use: {tool_use_block.name}")
        tool_result, is_error = dispatch(tool_use_block.name, **tool_use_block.input)
        return ToolResultBlockParam(
            tool_use_id=tool_use_block.id,
            type="tool_result",
            content=tool_result,
            is_error=is_error,
        )

    @staticmethod
    def handle_text_block(block: TextBlock):
        print(block.text)
        _log_agent_message(f"Message: {block.text}", level=logging.INFO)

    @staticmethod
    def handle_thinking_block(block: ThinkingBlock):
        _log_agent_message(f"Thought: {block.thinking}", level=logging.INFO)
