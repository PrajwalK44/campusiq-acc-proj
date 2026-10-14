import logging
import os
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None

    def __init__(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def encode(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


class VectorStoreService:
    _instance: Optional["VectorStoreService"] = None

    def __init__(self):
        self.mode = settings.CHROMA_MODE
        if self.mode == "server":
            logger.info(f"Connecting to remote ChromaDB server at {settings.CHROMA_SERVER_HOST}:{settings.CHROMA_SERVER_PORT}")
            self.client = chromadb.HttpClient(
                host=settings.CHROMA_SERVER_HOST,
                port=settings.CHROMA_SERVER_PORT
            )
        else:
            logger.info(f"Initializing embedded ChromaDB at {settings.CHROMA_PERSIST_DIRECTORY}")
            os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=ChromaSettings(anonymized_telemetry=False)
            )

        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    @classmethod
    def get_instance(cls) -> "VectorStoreService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[dict]
    ):
        """Add text chunks and embeddings into ChromaDB collection."""
        self.collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def delete_document_chunks(self, document_id: str):
        """Remove all chunks associated with a specific document_id."""
        self.collection.delete(where={"document_id": document_id})

    def query_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        category: Optional[str] = None
    ) -> dict:
        """Query nearest chunks based on cosine distance."""
        where_filter = None
        if category and category != "General":
            where_filter = {"category": category}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        return results
