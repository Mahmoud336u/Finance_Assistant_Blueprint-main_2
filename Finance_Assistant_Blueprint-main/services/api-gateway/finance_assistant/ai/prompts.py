"""Meridian AI — Prompt Assembly.

Assembles the full prompt for the LLM by combining:
1. System prompt (persona + guardrails)
2. Retrieved RAG context chunks
3. User financial context
4. Conversation history
5. Current user query

Uses Jinja2-style templates stored in the prompts/ directory.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path

from ..logging import get_logger
from .retriever import RetrievedChunk

logger = get_logger(__name__)

# Path to prompt template files
PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass
class AssembledPrompt:
    """A fully assembled prompt ready for LLM invocation."""

    system_prompt: str
    messages: list[dict[str, str]]
    rag_chunks_used: int
    user_context_used: int

    @property
    def total_context_chunks(self) -> int:
        return self.rag_chunks_used + self.user_context_used


def load_template(template_name: str) -> str:
    """Load a prompt template from the prompts/ directory.

    Args:
        template_name: Name of the template file (without extension).

    Returns:
        Template content as a string.

    Raises:
        FileNotFoundError: If template doesn't exist.
    """
    template_path = PROMPTS_DIR / f"{template_name}.txt"
    if not template_path.exists():
        msg = f"Prompt template not found: {template_path}"
        raise FileNotFoundError(msg)
    return template_path.read_text(encoding="utf-8")


def _format_rag_context(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved RAG chunks into a context block for the prompt."""
    if not chunks:
        return ""

    context_parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.content_type or "knowledge"
        score = f"{chunk.similarity_score:.2f}" if chunk.similarity_score else "N/A"
        context_parts.append(
            f"[Source {i} ({source}, relevance: {score})]:\n{chunk.content}"
        )

    return "\n\n".join(context_parts)


def _format_conversation_history(
    history: list[dict[str, str]],
    max_turns: int = 10,
) -> list[dict[str, str]]:
    """Format conversation history, keeping only the last N turns.

    Args:
        history: Full conversation history.
        max_turns: Maximum number of turns to include.

    Returns:
        Trimmed history as message dicts.
    """
    if len(history) > max_turns * 2:
        return history[-(max_turns * 2) :]
    return history


async def assemble_chat_prompt(
    query: str,
    *,
    rag_chunks: list[RetrievedChunk] | None = None,
    user_context: list[RetrievedChunk] | None = None,
    conversation_history: list[dict[str, str]] | None = None,
    user_name: str | None = None,
) -> AssembledPrompt:
    """Assemble the full prompt for a RAG-powered chat interaction.

    Combines system prompt, RAG context, user context, conversation
    history, and the current query into a structured prompt.

    Args:
        query: The user's current question.
        rag_chunks: Retrieved knowledge base chunks.
        user_context: User-specific financial context chunks.
        conversation_history: Previous messages in this conversation.
        user_name: User's name for personalization.

    Returns:
        AssembledPrompt ready for LLM invocation.
    """
    rag_chunks = rag_chunks or []
    user_context = user_context or []
    conversation_history = conversation_history or []

    # Load and fill system prompt template
    try:
        system_template = load_template("system_financial_advisor")
    except FileNotFoundError:
        system_template = _default_system_prompt()

    # Build context section
    rag_context_text = _format_rag_context(rag_chunks)
    user_context_text = _format_rag_context(user_context)

    context_block = ""
    if rag_context_text:
        context_block += f"## Relevant Financial Knowledge\n\n{rag_context_text}\n\n"
    if user_context_text:
        context_block += f"## User's Financial Context\n\n{user_context_text}\n\n"

    # Compose the full system prompt
    system_prompt = system_template
    if user_name:
        system_prompt = system_prompt.replace("{{USER_NAME}}", user_name)
    else:
        system_prompt = system_prompt.replace("{{USER_NAME}}", "the user")

    # Build message list
    messages = _format_conversation_history(conversation_history)

    # Add context-enhanced user query
    if context_block:
        enhanced_query = (
            f"Based on the following context, answer my question.\n\n"
            f"{context_block}"
            f"## My Question\n\n{query}"
        )
    else:
        enhanced_query = query

    messages.append({"role": "user", "content": enhanced_query})

    await logger.adebug(
        "Prompt assembled",
        rag_chunks=len(rag_chunks),
        user_context=len(user_context),
        history_turns=len(conversation_history) // 2,
    )

    return AssembledPrompt(
        system_prompt=system_prompt,
        messages=messages,
        rag_chunks_used=len(rag_chunks),
        user_context_used=len(user_context),
    )


def _default_system_prompt() -> str:
    """Fallback system prompt if template file is missing."""
    return (
        "You are Meridian, an AI-powered financial assistant. "
        "You help users understand their spending, manage budgets, "
        "and make informed financial decisions.\n\n"
        "Guidelines:\n"
        "- Be precise with financial numbers and calculations.\n"
        "- Always cite your sources when using retrieved context.\n"
        "- Never provide specific investment advice or stock recommendations.\n"
        "- If you're unsure about something, say so clearly.\n"
        "- Protect user privacy — never reveal account numbers or full names.\n"
        "- Format currency values consistently (e.g., $1,234.56).\n"
    )
