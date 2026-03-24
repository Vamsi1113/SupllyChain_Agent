"""
Vector Memory Store — Long-term memory with ChromaDB.
Stores past incidents, supplier performance records, and decisions.
Provides similarity search for decision support.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

_chroma_client = None
_collection = None
_embeddings = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        try:
            from utils.llm import get_embeddings as get_embeds
            _embeddings = get_embeds()
        except Exception as e:
            logger.warning(f"OpenAI embeddings unavailable: {e}. Using sentence-transformers fallback.")
            from langchain_community.embeddings import SentenceTransformerEmbeddings
            _embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def _get_collection():
    global _chroma_client, _collection
    if _collection is not None:
        return _collection

    from config import get_settings
    settings = get_settings()

    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _chroma_client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB collection '{settings.chroma_collection_name}' ready at {settings.chroma_persist_dir}")
    except Exception as e:
        logger.error(f"ChromaDB initialization failed: {e}")
        raise RuntimeError(f"Vector store unavailable: {e}")

    return _collection


class VectorMemoryStore:
    """
    Long-term memory store backed by ChromaDB.
    Supports storing and querying incidents, supplier records, and decisions.
    """

    def __init__(self):
        self._ready = False

    def initialize(self) -> None:
        try:
            _get_collection()
            _get_embeddings()
            self._ready = True
            logger.info("VectorMemoryStore initialized successfully")
        except Exception as e:
            logger.error(f"VectorMemoryStore init failed: {e}")
            self._ready = False

    @property
    def is_ready(self) -> bool:
        return self._ready

    def _embed_text(self, text: str) -> list[float]:
        embeddings = _get_embeddings()
        return embeddings.embed_query(text)

    def store_incident(
        self,
        run_id: str,
        part_id: str,
        disruption_type: str,
        severity: str,
        summary: str,
        resolution: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Store a supply chain incident for future similarity lookup."""
        if not self._ready:
            return

        try:
            text = (
                f"Part {part_id} disruption: {disruption_type}. "
                f"Severity: {severity}. Summary: {summary}"
            )
            doc_id = f"incident:{run_id}"
            meta = {
                "type": "incident",
                "run_id": run_id,
                "part_id": part_id,
                "disruption_type": disruption_type,
                "severity": severity,
                "resolution": resolution or "",
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {}),
            }
            embedding = self._embed_text(text)
            collection = _get_collection()
            collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[meta],
            )
        except Exception as e:
            logger.error(f"Failed to store incident: {e}")

    def store_decision(
        self,
        run_id: str,
        part_id: str,
        supplier_id: str,
        supplier_name: str,
        score: float,
        reason: str,
        outcome: str = "pending",
    ) -> None:
        """Store a procurement decision for future performance tracking."""
        if not self._ready:
            return

        try:
            text = (
                f"Decision for {part_id}: selected {supplier_name} ({supplier_id}). "
                f"Score: {score:.2f}. Reason: {reason}. Outcome: {outcome}."
            )
            doc_id = f"decision:{run_id}"
            meta = {
                "type": "decision",
                "run_id": run_id,
                "part_id": part_id,
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "score": score,
                "outcome": outcome,
                "timestamp": datetime.utcnow().isoformat(),
            }
            embedding = self._embed_text(text)
            collection = _get_collection()
            collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[meta],
            )
        except Exception as e:
            logger.error(f"Failed to store decision: {e}")

    def store_supplier_performance(
        self,
        supplier_id: str,
        part_id: str,
        reliability_rating: float,
        on_time_delivery: bool,
        quality_score: float,
        notes: str = "",
    ) -> None:
        """Store supplier performance data for historical analysis."""
        if not self._ready:
            return

        try:
            text = (
                f"Supplier {supplier_id} performance for {part_id}: "
                f"reliability={reliability_rating:.2f}, on_time={on_time_delivery}, "
                f"quality={quality_score:.2f}. Notes: {notes}"
            )
            doc_id = f"perf:{supplier_id}:{part_id}:{uuid.uuid4().hex[:8]}"
            meta = {
                "type": "supplier_performance",
                "supplier_id": supplier_id,
                "part_id": part_id,
                "reliability_rating": reliability_rating,
                "on_time_delivery": on_time_delivery,
                "quality_score": quality_score,
                "timestamp": datetime.utcnow().isoformat(),
            }
            embedding = self._embed_text(text)
            collection = _get_collection()
            collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[meta],
            )
        except Exception as e:
            logger.error(f"Failed to store supplier performance: {e}")

    def query_similar_incidents(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Find past incidents similar to the current query."""
        if not self._ready:
            return []

        try:
            embedding = self._embed_text(query)
            collection = _get_collection()
            results = collection.query(
                query_embeddings=[embedding],
                n_results=min(k, collection.count() or 1),
                where={"type": "incident"},
            )

            if not results or not results.get("ids") or not results["ids"][0]:
                return []

            similar: list[dict[str, Any]] = []
            for i, doc_id in enumerate(results["ids"][0]):
                similar.append({
                    "id": doc_id,
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                })
            return similar
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    def query_supplier_history(self, supplier_id: str, k: int = 5) -> list[dict[str, Any]]:
        """Retrieve historical performance records for a supplier."""
        if not self._ready:
            return []

        try:
            embedding = self._embed_text(f"Supplier {supplier_id} performance history")
            collection = _get_collection()
            results = collection.query(
                query_embeddings=[embedding],
                n_results=min(k, collection.count() or 1),
                where={"supplier_id": supplier_id},
            )

            if not results or not results.get("ids") or not results["ids"][0]:
                return []

            return [
                {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                }
                for i in range(len(results["ids"][0]))
            ]
        except Exception as e:
            logger.error(f"Supplier history query failed: {e}")
            return []


# Singleton instance
vector_store = VectorMemoryStore()
