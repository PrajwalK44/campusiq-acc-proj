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

        # Step 2: Retrieve candidate chunks (with category filter if specified)
        results = self.vector_store.query_similar(
            query_embedding=query_embedding,
            top_k=settings.RAG_TOP_K,
            category=category if category != "General" else None
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        def extract_valid_chunks(docs, metas, dists, chunk_ids):
            valid = []
            best_sim = -1.0
            for doc_text, meta, dist, chunk_id in zip(docs, metas, dists, chunk_ids):
                similarity = 1.0 - float(dist)
                if similarity > best_sim:
                    best_sim = similarity

                if similarity >= settings.RAG_SIMILARITY_THRESHOLD:
                    valid.append({
                        "chunk_id": chunk_id,
                        "text": doc_text,
                        "title": meta.get("title", "Unknown Document"),
                        "page_number": meta.get("page_number"),
                        "document_id": meta.get("document_id"),
                        "similarity": similarity
                    })
            return valid, best_sim

        valid_chunks, best_similarity = extract_valid_chunks(documents, metadatas, distances, ids)

        # If category filter yielded no valid chunks, fallback to global search across all documents
        if (not valid_chunks or best_similarity < settings.RAG_SIMILARITY_THRESHOLD) and category and category != "General":
            logger.info(f"Category '{category}' filter yielded insufficient matches (best: {best_similarity:.4f}). Falling back to global search.")
            global_results = self.vector_store.query_similar(
                query_embedding=query_embedding,
                top_k=settings.RAG_TOP_K,
                category=None
            )
            g_docs = global_results.get("documents", [[]])[0]
            g_metas = global_results.get("metadatas", [[]])[0]
            g_dists = global_results.get("distances", [[]])[0]
            g_ids = global_results.get("ids", [[]])[0]
            g_valid, g_best = extract_valid_chunks(g_docs, g_metas, g_dists, g_ids)
            if g_valid and g_best >= settings.RAG_SIMILARITY_THRESHOLD:
                valid_chunks = g_valid
                best_similarity = g_best

        logger.info(f"Query: '{question}' | Category: '{category}' | Best similarity: {best_similarity:.4f} | Threshold: {settings.RAG_SIMILARITY_THRESHOLD} | Chunks: {len(valid_chunks)}")

        if not valid_chunks or best_similarity < settings.RAG_SIMILARITY_THRESHOLD:
            abstention_msg = (
                "I couldn't verify this information from the currently indexed college documents. "
                "Please contact the relevant department or create a support ticket."
            )
            return abstention_msg, "ABSTAINED", []

        # Grounded answer synthesis
        answer_text = self.llm_service.generate_grounded_answer(question, valid_chunks)
        return answer_text, "ANSWERED", valid_chunks
