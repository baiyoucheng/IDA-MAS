"""Dual-API LLM client.

- DeepSeek  API  → chat completions (deepseek-chat)
- SiliconFlow API → embeddings (BAAI/bge-m3, free)

Both are OpenAI-compatible, so we use two `openai.OpenAI` instances.
"""

import logging
from typing import Dict, List

from openai import OpenAI

from backend.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Two OpenAI-compatible clients
# ---------------------------------------------------------------------------
_chat_client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_API_BASE,
)

_embed_client = OpenAI(
    api_key=settings.SILICONFLOW_API_KEY,
    base_url=settings.SILICONFLOW_API_BASE,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def chat_completion(messages: List[Dict[str, str]]) -> str:
    """Send a chat completion request and return the assistant's reply text.

    Args:
        messages: List of {"role": "...", "content": "..."} dicts.

    Returns:
        The assistant's response text.

    Raises:
        RuntimeError: On API failure.
    """
    try:
        resp = _chat_client.chat.completions.create(
            model=settings.CHAT_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        return resp.choices[0].message.content or ""
    except Exception as exc:
        logger.error("Chat completion failed: %s", exc)
        raise RuntimeError(f"LLM 调用失败: {exc}") from exc


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embedding vectors for a batch of texts via SiliconFlow API.

    Args:
        texts: List of text strings to embed.  Each must be non-empty and
               shorter than the model's token limit (8192 for bge-m3).

    Returns:
        List of embedding vectors, each a list of floats (1024-dim for bge-m3).

    Raises:
        RuntimeError: On API failure.
    """
    if not texts:
        return []

    try:
        resp = _embed_client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts,
        )
        # Sort by index to preserve input order
        embeddings = sorted(resp.data, key=lambda d: d.index)
        return [e.embedding for e in embeddings]
    except Exception as exc:
        logger.error("Embedding generation failed: %s", exc)
        raise RuntimeError(f"Embedding 生成失败: {exc}") from exc
