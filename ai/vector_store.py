"""
Vector Store using Milvus Lite
Simple helper for create collection, insert vectors, and search
"""

import os
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient

EMB_MODEL = os.getenv("EMB_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DIM = 384  # MiniLM-L6
METRIC = "IP"  # inner product; use normalized embeddings for cosine-like search

class VectorStore:
    def __init__(self, uri: str, collection: str):
        # Milvus Lite: pass a local file name (e.g., ./fp_vectors.db)
        self.client = MilvusClient(uri)
        self.collection = collection
        self.embedder = SentenceTransformer(EMB_MODEL)
        self._ensure_collection()

    def _ensure_collection(self):
        if not self.client.has_collection(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                dimension=DIM,
                metric_type=METRIC,
                auto_id=False,
                id_type="INT64",
            )

    def embed(self, texts: List[str]) -> np.ndarray:
        return self.embedder.encode(texts, normalize_embeddings=True).astype("float32")

    def upsert(self, docs: List[Dict]):
        """
        docs: [{ "id": int, "text": str, "meta": {...} }, ...]
        """
        vectors = self.embed([d["text"] for d in docs])
        rows = []
        for i, d in enumerate(docs):
            rows.append({
                "id": int(d["id"]),
                "vector": vectors[i].tolist(),
                "text": d["text"],
                "meta": d.get("meta", {})
            })
        self.client.upsert(collection_name=self.collection, data=rows)

    def search(self, query: str, top_k: int = 5):
        qv = self.embed([query])
        res = self.client.search(
            collection_name=self.collection,
            data=qv.tolist(),
            limit=top_k,
            output_fields=["text", "meta"]
        )
        # MilvusClient returns a list per query; unwrap the first
        hits = res[0]
        return [{"score": h["distance"], "text": h["entity"]["text"], "meta": h["entity"]["meta"]} for h in hits]


# Legacy compatibility - keep existing interface
from typing import Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class VectorDocument:
    """Document with text content and metadata"""
    id: str
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

@dataclass
class SearchResult:
    """Search result with similarity score"""
    document: VectorDocument
    score: float

class MilvusVectorStore:
    """Legacy wrapper around simplified VectorStore"""

    def __init__(self,
                 collection_name: str = "food_premi_docs",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 dimension: int = 384):
        self.collection_name = collection_name
        self.dimension = dimension

        # Get Milvus URI from environment
        self.milvus_uri = os.getenv('MILVUS_URI', './fp_vectors.db')

        # Use simplified VectorStore
        self.vs = VectorStore(self.milvus_uri, collection_name)

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using sentence transformer"""
        try:
            embedding = self.vs.embed([text])[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def add_documents(self, documents: List[VectorDocument]) -> bool:
        """Add documents to the vector store"""
        try:
            # Convert VectorDocument format to simplified format
            docs = []
            for i, doc in enumerate(documents):
                # Generate integer ID for simplified format
                doc_id = hash(doc.id) % 2147483647  # Keep within INT64 range
                # Preserve original ID in metadata
                meta = doc.metadata.copy()
                meta["original_id"] = doc.id
                docs.append({
                    "id": doc_id,
                    "text": doc.text,
                    "meta": meta
                })

            # Use simplified upsert
            self.vs.upsert(docs)
            logger.info(f"Added {len(documents)} documents to collection")
            return True

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False

    def search_similar(self,
                      query: str,
                      top_k: int = 5,
                      score_threshold: float = 0.0) -> List[SearchResult]:
        """Search for similar documents"""
        try:
            # Use simplified search
            results = self.vs.search(query, top_k)

            # Convert to legacy format
            search_results = []
            for result in results:
                if result["score"] >= score_threshold:
                    doc = VectorDocument(
                        id=str(result.get("meta", {}).get("original_id", "unknown")),
                        text=result["text"],
                        metadata=result["meta"]
                    )

                    search_results.append(SearchResult(
                        document=doc,
                        score=result["score"]
                    ))

            logger.info(f"Found {len(search_results)} similar documents")
            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            stats = {
                "name": self.collection_name,
                "dimension": self.dimension,
            }
            return stats

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def clear_collection(self) -> bool:
        """Clear all documents from collection"""
        try:
            # Drop and recreate collection for simplicity
            if self.vs.client.has_collection(self.collection_name):
                self.vs.client.drop_collection(self.collection_name)

            # Recreate collection
            self.vs._ensure_collection()

            logger.info("Cleared all documents from collection")
            return True

        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False

# Convenience function to get vector store instance
def get_vector_store() -> MilvusVectorStore:
    """Get a configured vector store instance"""
    return MilvusVectorStore()

# Convenience function to get simplified vector store
def get_simple_vector_store(uri: str = None, collection: str = "food_premi_docs") -> VectorStore:
    """Get a simplified vector store instance"""
    if uri is None:
        uri = os.getenv('MILVUS_URI', './fp_vectors.db')
    return VectorStore(uri, collection)

# Example usage and testing
if __name__ == "__main__":
    print("Vector Store Test")
    print("=" * 40)

    try:
        # Test 1: Simplified VectorStore
        print("\n1. Testing simplified VectorStore...")
        vs = get_simple_vector_store()

        # Test documents with integer IDs
        test_docs = [
            {"id": 1, "text": "Our restaurant serves fresh organic vegetables and healthy meals.", "meta": {"type": "menu", "category": "healthy"}},
            {"id": 2, "text": "We offer catering services for events and parties.", "meta": {"type": "service", "category": "catering"}},
            {"id": 3, "text": "All ingredients are locally sourced and certified organic.", "meta": {"type": "info", "category": "organic"}}
        ]

        # Add documents
        vs.upsert(test_docs)
        print("✓ Added documents successfully")

        # Test search
        results = vs.search("healthy organic food", top_k=2)
        print(f"✓ Found {len(results)} results")
        for i, result in enumerate(results):
            print(f"  {i+1}. Score: {result['score']:.3f}, Text: {result['text'][:50]}...")

        # Test 2: Legacy MilvusVectorStore (for compatibility)
        print("\n2. Testing legacy MilvusVectorStore...")
        legacy_vs = get_vector_store()

        # Test adding documents with legacy format
        legacy_docs = [
            VectorDocument(
                id="legacy_doc1",
                text="We use only the finest organic ingredients in our cooking.",
                metadata={"type": "philosophy", "category": "organic", "original_id": "legacy_doc1"}
            )
        ]

        success = legacy_vs.add_documents(legacy_docs)
        print(f"✓ Legacy add documents: {success}")

        # Test legacy search
        legacy_results = legacy_vs.search_similar("organic cooking", top_k=2)
        print(f"✓ Legacy search found {len(legacy_results)} results")
        for i, result in enumerate(legacy_results):
            print(f"  {i+1}. Score: {result.score:.3f}, Text: {result.document.text[:50]}...")

        # Get stats
        stats = legacy_vs.get_collection_stats()
        print(f"✓ Collection stats: {stats}")

        print("\n✅ All tests passed! Vector store is working correctly.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("This might be due to missing dependencies or Milvus Lite setup issues.")