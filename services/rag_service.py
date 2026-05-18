from dataclasses import dataclass


@dataclass
class RetrievedChunk:

    content: str
    source: str | None = None
    score: float | None = None


class RAGService:

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievedChunk]:
        return []

    def build_context_message(self, chunks: list[RetrievedChunk]) -> str | None:
        if not chunks:
            return None

        context = "\n\n".join(chunk.content for chunk in chunks)
        return f"以下是可参考的外部资料，请仅在相关时使用：\n{context}"
