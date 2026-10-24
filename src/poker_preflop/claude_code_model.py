"""A Pydantic AI model backed by the local Claude Code CLI, so runs use your Claude Code login/subscription.

Single-turn only: no function tools. Pair it with `PromptedOutput` so structured output is requested
in the prompt and validated (and retried) by Pydantic AI.
"""

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage


def _render_prompt(messages: list[ModelMessage]) -> str:
    """Flatten the conversation into one prompt (multiple turns only happen on output-validation retries)."""
    chunks: list[str] = []
    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    chunks.append(part.content if isinstance(part.content, str) else str(part.content))
                elif isinstance(part, RetryPromptPart):
                    chunks.append(f'Your previous answer was invalid:\n{part.model_response()}')
        else:
            text = ''.join(p.content for p in message.parts if isinstance(p, TextPart))
            chunks.append(f'Your previous answer:\n{text}')
    return '\n\n'.join(chunks)


def claude_code_model(model: str = 'sonnet') -> FunctionModel:
    """`model` is any value `claude --model` accepts, e.g. "sonnet", "opus", "haiku" or a full model ID."""

    async def call(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        options = ClaudeAgentOptions(
            model=model,
            system_prompt=info.instructions or '',
            tools=[],  # no built-in tools: plain text in, text out
            max_turns=1,
            setting_sources=[],  # don't load your CLAUDE.md / project settings into the eval
        )
        text_parts: list[str] = []
        usage = RequestUsage()
        async for msg in query(prompt=_render_prompt(messages), options=options):
            if isinstance(msg, AssistantMessage):
                text_parts.extend(b.text for b in msg.content if isinstance(b, TextBlock))
            elif isinstance(msg, ResultMessage) and msg.usage:
                usage = RequestUsage(
                    input_tokens=msg.usage.get('input_tokens', 0),
                    output_tokens=msg.usage.get('output_tokens', 0),
                    cache_read_tokens=msg.usage.get('cache_read_input_tokens', 0),
                    cache_write_tokens=msg.usage.get('cache_creation_input_tokens', 0),
                )
        return ModelResponse(parts=[TextPart(''.join(text_parts))], usage=usage, model_name=f'claude-code:{model}')

    return FunctionModel(call, model_name=f'claude-code:{model}')
