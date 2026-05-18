from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    """后续接入向量库后，RAG 返回的最小信息单元。"""

    content: str
    source: str | None = None
    score: float | None = None


class RAGService:
    """当前先保留空实现，保证 RAG 边界清晰。"""

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievedChunk]:
        return []

    def build_context_message(self, chunks: list[RetrievedChunk]) -> str | None:
        if not chunks:
            return None

        context = "\n\n".join(chunk.content for chunk in chunks)
        return f"以下是可参考的外部资料，请仅在相关时使用：\n{context}"
