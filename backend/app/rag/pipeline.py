import logging
from typing import List, Dict, Any, Tuple
from uuid import UUID

from backend.app.core.config import settings
from backend.app.rag.vector_store import EmbeddingService, VectorStoreService
from backend.app.rag.llm import LLMService

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self):
        self.embedding_service = EmbeddingService.get_instance()
        self.vector_store = VectorStoreService.get_instance()
        self.llm_service = LLMService()

    def answer_student_query(
        self,
        question: str,
        category: str = "General"
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        """
        Executes end-to-end RAG query flow:
        1. Generates query vector embedding.
        2. Retrieves top-K chunks from ChromaDB.
        3. Computes similarity scores from cosine distance.
        4. Compares against RAG_SIMILARITY_THRESHOLD.
        5. Returns abstention if evidence insufficient, or invokes LLM for grounded answer.
        Returns: (answer_text, answer_status, sources_list)
        """
        # Step 1: Query embedding
        query_embedding = self.embedding_service.encode([question])[0]

        # Step 2: Retrieve candidate chunks
        results = self.vector_store.query_similar(
            query_embedding=query_embedding,
            top_k=settings.RAG_TOP_K,
            category=category if category != "General" else None
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        if not documents:
            abstention_msg = (
                "I couldn't verify this information from the currently indexed college documents. "
                "Please contact the relevant department or create a support ticket."
            )
            return abstention_msg, "ABSTAINED", []

        # Cosine distance in ChromaDB is in [0, 2], where 0 is identical
        # Cosine similarity = 1 - (distance / 2) or 1 - distance depending on metric
        # For HNSW cosine space: similarity = 1.0 - distance
        valid_chunks = []
        best_similarity = -1.0

        for doc_text, meta, dist, chunk_id in zip(documents, metadatas, distances, ids):
            similarity = 1.0 - float(dist)
            if similarity > best_similarity:
                best_similarity = similarity

            if similarity >= settings.RAG_SIMILARITY_THRESHOLD:
                valid_chunks.append({
                    "chunk_id": chunk_id,
                    "text": doc_text,
                    "title": meta.get("title", "Unknown Document"),
                    "page_number": meta.get("page_number"),
                    "document_id": meta.get("document_id"),
                    "similarity": similarity
                })

        logger.info(f"Query: '{question}' | Best similarity: {best_similarity:.4f} | Threshold: {settings.RAG_SIMILARITY_THRESHOLD}")

        if not valid_chunks or best_similarity < settings.RAG_SIMILARITY_THRESHOLD:
            abstention_msg = (
                "I couldn't verify this information from the currently indexed college documents. "
                "Please contact the relevant department or create a support ticket."
            )
            return abstention_msg, "ABSTAINED", []

        # Grounded answer synthesis
        answer_text = self.llm_service.generate_grounded_answer(question, valid_chunks)
        return answer_text, "ANSWERED", valid_chunks
