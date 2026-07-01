"""RAG pipeline — retrieval-augmented generation for document Q&A."""

from typing import Dict, List, Tuple

from backend.config import settings
from backend.core.llm_client import chat_completion
from backend.core.vector_store import similarity_search

# ---------------------------------------------------------------------------
# Prompt template (Chinese-optimized)
# ---------------------------------------------------------------------------

RAG_SYSTEM_PROMPT = """你是一个专业的文档智能分析助手。请基于以下上下文回答用户问题。
如果上下文中找不到答案，请明确说明"根据已上传的文档，无法找到相关信息"，不要编造。

要求：
1. 回答要全面、准确，引用原文条款号作为依据
2. 在回答末尾标注信息来源，格式：[来源文档名，第X段]
3. 如果涉及多条信息，逐条分点作答"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def query_documents(query: str, top_k: int | None = None) -> Tuple[str, List[Dict]]:
    """Main RAG entry point.

    Args:
        query: User's natural language question.
        top_k: Number of chunks to retrieve.  Defaults to settings.

    Returns:
        (answer_text, sources) where sources is a list of
        {"document": str, "chunk_preview": str, "chunk_index": int, "distance": float}.
    """
    if top_k is None:
        top_k = settings.TOP_K_RETRIEVAL

    # 1. Retrieve relevant chunks
    hits = similarity_search(query, k=top_k)

    if not hits:
        return (
            "目前没有已上传的文档，或者您的查询与现有文档内容无关。"
            "请先上传文档再提问。",
            [],
        )

    # 2. Build context
    context_parts: list[str] = []
    sources: list[dict] = []
    for i, hit in enumerate(hits):
        meta = hit["metadata"]
        context_parts.append(
            f"[片段{i + 1}] 来源: {meta['source']}  段号: {meta['chunk_index']}\n{hit['document']}"
        )
        sources.append({
            "document": meta["source"],
            "chunk_preview": hit["document"][:120] + ("..." if len(hit["document"]) > 120 else ""),
            "chunk_index": meta["chunk_index"],
            "distance": round(hit["distance"], 4),
        })

    context = "\n\n---\n\n".join(context_parts)

    # 3. Generate answer
    messages = [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {"role": "user", "content": f"上下文：\n\n{context}\n\n用户问题：{query}"},
    ]

    answer = chat_completion(messages)
    return answer, sources
