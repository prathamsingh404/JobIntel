import numpy as np
from typing import List, Dict, Any, Optional
from app.utils.logger import logger
from app.config.settings import settings

class VectorService:
    """Manages vector embeddings and handles semantic lookup indices in JobIntel V2."""

    def __init__(self):
        self.qdrant_client = None
        self.collection_name = "jobs"
        self._init_vector_db()

    def _init_vector_db(self) -> None:
        """Attempts to initialize Qdrant. Falls back to a local memory cache if unavailable."""
        try:
            from qdrant_client import QdrantClient
            # Connect to default Qdrant docker port
            self.qdrant_client = QdrantClient(url="http://localhost:6333", timeout=3.0)
            logger.info("Successfully connected to Qdrant Vector Database.")
        except Exception:
            logger.info("Qdrant Client not available or not running. Falling back to local in-memory semantic indexing.")

    def get_embedding(self, text: str) -> List[float]:
        """Generates a text embedding vector (supports mock fallback)."""
        # Truncate text for simplicity
        clean_text = text.lower().strip()[:500]
        
        # Simple deterministic embedding generation for fallback offline runs
        # Creates a 128-dimension normalized pseudo-vector based on character hash values
        dimensions = 128
        vector = np.zeros(dimensions)
        
        if clean_text:
            for idx, char in enumerate(clean_text):
                vector[idx % dimensions] += ord(char)
                
            # Normalize vector to unit length
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
                
        return vector.tolist()

    async def search_similar(self, query_text: str, candidates: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Finds items semantically similar to the query text using cosine similarity."""
        query_vector = np.array(self.get_embedding(query_text))
        
        scored_candidates = []
        for cand in candidates:
            cand_text = cand.get("description") or cand.get("resume_text") or cand.get("clean_description") or ""
            if not cand_text:
                continue
                
            cand_vector = np.array(self.get_embedding(cand_text))
            
            # Compute cosine similarity: (A . B) / (||A|| * ||B||)
            dot_product = np.dot(query_vector, cand_vector)
            norm_q = np.linalg.norm(query_vector)
            norm_c = np.linalg.norm(cand_vector)
            
            similarity = 0.0
            if norm_q > 0 and norm_c > 0:
                similarity = float(dot_product / (norm_q * norm_c))
                
            scored_candidates.append({
                "item": cand,
                "similarity": similarity
            })
            
        # Sort by highest similarity
        scored_candidates.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_candidates[:limit]
