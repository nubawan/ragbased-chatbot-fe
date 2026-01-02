"""
Z.M.ai - LLM Handler Module

Handles integration with Groq API for LLM responses.
"""

import logging
from typing import Optional, List, Dict, Any, Iterator
from dataclasses import dataclass, field
import json

import requests
from groq import Groq

from config import get_groq_config, get_ui_config
from .retriever import RetrievalResult

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from the LLM."""
    content: str
    sources: List[str] = field(default_factory=list)
    model_used: str = ""
    tokens_used: int = 0
    raw_response: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_sources(self) -> bool:
        """Check if response has source citations."""
        return len(self.sources) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "content": self.content,
            "sources": self.sources,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
        }


class GroqHandler:
    """
    Handler for Groq API interactions.
    """

    def __init__(self):
        """Initialize the Groq handler with configuration."""
        self.config = get_groq_config()
        self.ui_config = get_ui_config()

        if not self.config.api_key:
            logger.warning("GROQ_API_KEY not configured")

        self.client = Groq(api_key=self.config.api_key) if self.config.api_key else None

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a response from Groq.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse object

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API call fails
        """
        if not self.client:
            raise ValueError("Groq API key not configured. Please set GROQ_API_KEY.")

        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        logger.debug(f"Sending request to Groq: model={self.config.model_name}, tokens={max_tokens}")

        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.config.timeout,
            )

            # Extract response
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            logger.info(f"Groq response received: {len(content)} chars, {tokens_used} tokens")

            return LLMResponse(
                content=content,
                model_used=self.config.model_name,
                tokens_used=tokens_used,
                raw_response={
                    "model": response.model,
                    "usage": response.usage.model_dump() if response.usage else {},
                },
            )

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise RuntimeError(f"Failed to generate response: {e}")

    def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Iterator[str]:
        """
        Stream a response from Groq.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature

        Yields:
            Chunks of response text as they arrive

        Raises:
            ValueError: If API key is not configured
        """
        if not self.client:
            raise ValueError("Groq API key not configured. Please set GROQ_API_KEY.")

        temperature = temperature or self.config.temperature

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        logger.debug(f"Starting stream: model={self.config.model_name}")

        try:
            stream = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=temperature,
                stream=True,
                timeout=self.config.timeout,
            )

            for chunk in stream:
                if delta := chunk.choices[0].delta.content:
                    yield delta

        except Exception as e:
            logger.error(f"Groq streaming error: {e}")
            raise RuntimeError(f"Failed to stream response: {e}")


class RAGLLMHandler:
    """
    High-level handler that combines RAG retrieval with LLM generation.
    """

    def __init__(self):
        """Initialize the RAG-LLM handler."""
        self.groq = GroqHandler()
        self.default_system_prompt = self._get_system_prompt()

    def answer_question(
        self,
        query: str,
        retrieval_result: RetrievalResult,
        custom_system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Answer a question using retrieved context.

        Args:
            query: User question
            retrieval_result: Result from RAG retrieval
            custom_system_prompt: Optional custom system prompt

        Returns:
            LLMResponse with answer and sources
        """
        # Build prompt with context
        system_prompt = custom_system_prompt or self.default_system_prompt

        if retrieval_result.has_context:
            context = retrieval_result.context_text
            prompt = self._build_rag_prompt(query, context)
        else:
            # No context found
            prompt = f"""Based on the available policy documents, I cannot find information to answer this question.

Question: {query}

Please respond that you don't have enough information about this topic in the policy documents."""

        # Generate response
        response = self.groq.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
        )

        # Add sources
        response.sources = retrieval_result.get_sources_with_pages()

        return response

    def stream_answer(
        self,
        query: str,
        retrieval_result: RetrievalResult,
        custom_system_prompt: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Stream an answer to a question.

        Args:
            query: User question
            retrieval_result: Result from RAG retrieval
            custom_system_prompt: Optional custom system prompt

        Yields:
            Response chunks as they arrive
        """
        system_prompt = custom_system_prompt or self.default_system_prompt

        if retrieval_result.has_context:
            context = retrieval_result.context_text
            prompt = self._build_rag_prompt(query, context)
        else:
            prompt = f"""Based on the available policy documents, I cannot find information to answer this question.

Question: {query}

Please respond that you don't have enough information about this topic in the policy documents."""

        yield from self.groq.stream_response(
            prompt=prompt,
            system_prompt=system_prompt,
        )

    def _build_rag_prompt(self, query: str, context: str) -> str:
        """Build RAG prompt with context and query."""
        return f"""CONTEXT FROM ACADEMIC POLICY DOCUMENTS:
{context}

QUESTION:
{query}

Provide a helpful answer based ONLY on the context above. If the answer isn't in the context, say that you don't have enough information."""

    def _get_system_prompt(self) -> str:
        """Get the default system prompt for Z.M.ai."""
        return """You are Z.M.ai, a helpful academic policy assistant for university students.

YOUR ROLE:
- Help students understand academic policies clearly
- Provide accurate information based ONLY on the provided context
- Be friendly, clear, and concise

IMPORTANT RULES:
1. NEVER make up information that isn't in the context
2. If you don't know something based on the context, say so clearly
3. Keep answers relevant to academic policies
4. Use bullet points or numbered lists for clarity
5. Be concise but thorough

RESPONSE STYLE:
- Start with a direct answer
- Use markdown formatting for readability
- Include relevant details from the context
- End with a helpful follow-up if appropriate"""

    def answer_without_context(self, query: str) -> LLMResponse:
        """
        Answer a question without RAG context (general conversation).

        Args:
            query: User query

        Returns:
            LLMResponse
        """
        system_prompt = """You are Z.M.ai, an academic policy assistant. You don't have access to specific documents right now, but you can provide general guidance about university policies.

Be helpful but clarify that for specific questions, the user should refer to the official policy documents."""

        response = self.groq.generate_response(
            prompt=query,
            system_prompt=system_prompt,
        )

        return response


def format_response_with_sources(response: LLMResponse) -> str:
    """
    Format an LLM response with sources for display.

    Args:
        response: LLMResponse object

    Returns:
        Formatted markdown string
    """
    output = response.content

    if response.has_sources:
        output += "\n\n---\n\n**Sources:**\n"
        for source in response.sources:
            output += f"- {source}\n"

    return output
