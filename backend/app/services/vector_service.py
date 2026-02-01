"""
Vector Service
ChromaDB-based vector store for semantic search.
"""
from pathlib import Path
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class VectorService:
    """Service for vector storage and semantic search."""
    
    def __init__(
        self, 
        chroma_path: Path, 
        embedding_model: str = "BAAI/bge-base-en-v1.5"
    ):
        self.chroma_path = chroma_path
        self.embedding_model_name = embedding_model
        self.client = None
        self.collection = None
        self.embedder = None
        self.is_initialized = False
    
    def initialize(self) -> None:
        """Initialize ChromaDB and embedding model."""
        if self.is_initialized:
            return
        
        # Create ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="aetios_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Load embedding model
        self.embedder = SentenceTransformer(self.embedding_model_name)
        
        self.is_initialized = True
    
    def _ensure_initialized(self):
        """Ensure service is initialized."""
        if not self.is_initialized:
            self.initialize()
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Add documents with embeddings to the vector store."""
        self._ensure_initialized()
        
        if not documents:
            return
        
        if len(documents) != len(metadatas) or len(documents) != len(ids):
            raise ValueError("documents, metadatas, and ids must have same length")
        
        # Generate embeddings
        embeddings = self.embedder.encode(
            documents,
            show_progress_bar=False,
            convert_to_numpy=True
        ).tolist()
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    def update_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Update existing documents."""
        self._ensure_initialized()
        
        if not documents:
            return
        
        # Generate embeddings
        embeddings = self.embedder.encode(
            documents,
            show_progress_bar=False,
            convert_to_numpy=True
        ).tolist()
        
        # Update in collection
        self.collection.update(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    def query_similar(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List]:
        """Query for similar documents."""
        self._ensure_initialized()
        
        # Generate query embedding
        query_embedding = self.embedder.encode(
            [query_text],
            show_progress_bar=False,
            convert_to_numpy=True
        ).tolist()[0]
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        return {
            'ids': results['ids'][0] if results['ids'] else [],
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else []
        }
    
    def get_documents_by_topic(
        self,
        topic_id: str,
        n_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all documents related to a topic."""
        self._ensure_initialized()
        
        results = self.collection.get(
            where={"topic_id": topic_id},
            limit=n_results
        )
        
        documents = []
        if results['ids']:
            for i in range(len(results['ids'])):
                documents.append({
                    'id': results['ids'][i],
                    'document': results['documents'][i] if results['documents'] else None,
                    'metadata': results['metadatas'][i] if results['metadatas'] else {}
                })
        
        return documents
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID."""
        self._ensure_initialized()
        
        results = self.collection.get(ids=[doc_id])
        
        if not results['ids']:
            return None
        
        return {
            'id': results['ids'][0],
            'document': results['documents'][0] if results['documents'] else None,
            'metadata': results['metadatas'][0] if results['metadatas'] else {}
        }
    
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by IDs."""
        self._ensure_initialized()
        
        if not ids:
            return
        
        self.collection.delete(ids=ids)
    
    def delete_by_topic(self, topic_id: str) -> None:
        """Delete all documents for a topic."""
        self._ensure_initialized()
        
        self.collection.delete(where={"topic_id": topic_id})
    
    def count_documents(self, where: Optional[Dict[str, Any]] = None) -> int:
        """Count documents in collection."""
        self._ensure_initialized()
        
        if where:
            results = self.collection.get(where=where)
            return len(results['ids'])
        else:
            return self.collection.count()
    
    def find_best_topic_match(
        self,
        text: str,
        candidate_topics: List[Dict[str, str]]
    ) -> Optional[str]:
        """
        Find best matching topic for a text.
        
        Args:
            text: Text to match
            candidate_topics: List of dicts with 'id' and 'description'
        
        Returns:
            Best matching topic_id or None
        """
        self._ensure_initialized()
        
        if not candidate_topics:
            return None
        
        # Encode text
        text_embedding = self.embedder.encode(
            [text],
            show_progress_bar=False,
            convert_to_numpy=True
        )[0]
        
        # Encode topic descriptions
        descriptions = [t['description'] for t in candidate_topics]
        topic_embeddings = self.embedder.encode(
            descriptions,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Calculate cosine similarities
        from numpy import dot
        from numpy.linalg import norm
        
        similarities = []
        for topic_emb in topic_embeddings:
            similarity = dot(text_embedding, topic_emb) / (
                norm(text_embedding) * norm(topic_emb)
            )
            similarities.append(similarity)
        
        # Find best match
        best_idx = similarities.index(max(similarities))
        best_similarity = similarities[best_idx]
        
        # Return topic_id if similarity is good enough
        if best_similarity > 0.3:  # Threshold for matching
            return candidate_topics[best_idx]['id']
        
        return None
    
    def reset_collection(self) -> None:
        """Clear all documents from collection."""
        self._ensure_initialized()
        
        self.client.delete_collection("aetios_knowledge")
        self.collection = self.client.create_collection(
            name="aetios_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        self._ensure_initialized()
        
        return {
            'name': self.collection.name,
            'count': self.collection.count(),
            'metadata': self.collection.metadata
        }
    
    async def close(self) -> None:
        """Close connections and cleanup resources."""
        # ChromaDB doesn't require explicit cleanup
        # Just mark as uninitialized
        self.is_initialized = False
        self.client = None
        self.collection = None
        self.embedder = None
