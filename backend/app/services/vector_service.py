"""
Vector Service
LanceDB-based vector store for semantic search.
"""
from pathlib import Path
from typing import List, Dict, Optional, Any
import lancedb
import pyarrow as pa
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np


class VectorService:
    """Service for vector storage and semantic search."""
    
    def __init__(
        self, 
        db_path: Path, 
        embedding_model: str = "BAAI/bge-base-en-v1.5"
    ):
        self.db_path = db_path
        self.embedding_model_name = embedding_model
        self.db = None
        self.table = None
        self.embedder = None
        self.is_initialized = False
        self.table_name = "aetios_knowledge"
    
    def initialize(self) -> None:
        """Initialize LanceDB and embedding model."""
        if self.is_initialized:
            return
        
        # Create LanceDB connection
        self.db = lancedb.connect(str(self.db_path))
        
        # Load embedding model
        self.embedder = SentenceTransformer(self.embedding_model_name)
        
        # Check if table exists
        table_names = self.db.table_names()
        if self.table_name in table_names:
            self.table = self.db.open_table(self.table_name)
        else:
            # Table will be created on first add_documents
            self.table = None
        
        self.is_initialized = True
    
    def _ensure_initialized(self):
        """Ensure service is initialized."""
        if not self.is_initialized:
            self.initialize()
    
    def _create_table_if_needed(self, sample_metadata: Dict[str, Any]) -> None:
        """Create table with schema based on sample metadata."""
        if self.table is not None:
            return
        
        # Get embedding dimension
        sample_embedding = self.embedder.encode(["sample"], convert_to_numpy=True)[0]
        embedding_dim = len(sample_embedding)
        
        # Build schema fields dynamically based on metadata
        fields = [
            pa.field("id", pa.string()),
            pa.field("document", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), embedding_dim)),
        ]
        
        # Add metadata fields dynamically
        for key, value in sample_metadata.items():
            if isinstance(value, str):
                fields.append(pa.field(key, pa.string()))
            elif isinstance(value, int):
                fields.append(pa.field(key, pa.int64()))
            elif isinstance(value, float):
                fields.append(pa.field(key, pa.float64()))
            elif isinstance(value, bool):
                fields.append(pa.field(key, pa.bool_()))
        
        schema = pa.schema(fields)
        
        # Create empty table with schema
        empty_data = pa.Table.from_pydict({
            "id": [],
            "document": [],
            "vector": [],
            **{key: [] for key in sample_metadata.keys()}
        }, schema=schema)
        
        self.table = self.db.create_table(self.table_name, empty_data, mode="overwrite")
    
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
        
        # Create table if it doesn't exist
        if self.table is None:
            self._create_table_if_needed(metadatas[0] if metadatas else {})
        
        # Generate embeddings
        embeddings = self.embedder.encode(
            documents,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Prepare data for insertion
        data = {
            "id": ids,
            "document": documents,
            "vector": embeddings.tolist(),
        }
        
        # Add all metadata fields
        if metadatas:
            metadata_keys = set()
            for metadata in metadatas:
                metadata_keys.update(metadata.keys())
            
            for key in metadata_keys:
                data[key] = [metadata.get(key, None) for metadata in metadatas]
        
        # Convert to PyArrow table and add
        pa_table = pa.Table.from_pydict(data)
        self.table.add(pa_table)
    
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
        
        # Delete existing documents with these IDs
        self.delete_documents(ids)
        
        # Add updated documents
        self.add_documents(documents, metadatas, ids)
    
    def query_similar(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List]:
        """Query for similar documents."""
        self._ensure_initialized()
        
        if self.table is None:
            return {
                'ids': [],
                'documents': [],
                'metadatas': [],
                'distances': []
            }
        
        # Generate query embedding
        query_embedding = self.embedder.encode(
            [query_text],
            show_progress_bar=False,
            convert_to_numpy=True
        )[0]
        
        # Build query
        query = self.table.search(query_embedding).limit(n_results)
        
        # Apply filters if provided
        if where:
            filter_str = self._build_filter_string(where)
            if filter_str:
                query = query.where(filter_str)
        
        # Execute query
        results = query.to_pandas()
        
        if results.empty:
            return {
                'ids': [],
                'documents': [],
                'metadatas': [],
                'distances': []
            }
        
        # Extract metadata columns (exclude id, document, vector, _distance)
        metadata_cols = [col for col in results.columns 
                        if col not in ['id', 'document', 'vector', '_distance']]
        
        metadatas = []
        for _, row in results.iterrows():
            metadata = {col: row[col] for col in metadata_cols if pd.notna(row[col])}
            metadatas.append(metadata)
        
        return {
            'ids': results['id'].tolist(),
            'documents': results['document'].tolist(),
            'metadatas': metadatas,
            'distances': results['_distance'].tolist()
        }
    
    def _build_filter_string(self, where: Dict[str, Any]) -> str:
        """Build LanceDB filter string from where dict."""
        conditions = []
        for key, value in where.items():
            if isinstance(value, str):
                conditions.append(f"{key} = '{value}'")
            elif isinstance(value, (int, float)):
                conditions.append(f"{key} = {value}")
            elif isinstance(value, bool):
                conditions.append(f"{key} = {str(value).lower()}")
        return " AND ".join(conditions) if conditions else ""
    
    def get_documents_by_topic(
        self,
        topic_id: str,
        n_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all documents related to a topic."""
        self._ensure_initialized()
        
        if self.table is None:
            return []
        
        # Query with filter
        filter_str = f"topic_id = '{topic_id}'"
        results = self.table.search().where(filter_str).limit(n_results).to_pandas()
        
        if results.empty:
            return []
        
        documents = []
        metadata_cols = [col for col in results.columns 
                        if col not in ['id', 'document', 'vector', '_distance']]
        
        for _, row in results.iterrows():
            metadata = {col: row[col] for col in metadata_cols if pd.notna(row[col])}
            documents.append({
                'id': row['id'],
                'document': row['document'],
                'metadata': metadata
            })
        
        return documents
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID."""
        self._ensure_initialized()
        
        if self.table is None:
            return None
        
        filter_str = f"id = '{doc_id}'"
        results = self.table.search().where(filter_str).limit(1).to_pandas()
        
        if results.empty:
            return None
        
        row = results.iloc[0]
        metadata_cols = [col for col in results.columns 
                        if col not in ['id', 'document', 'vector', '_distance']]
        metadata = {col: row[col] for col in metadata_cols if pd.notna(row[col])}
        
        return {
            'id': row['id'],
            'document': row['document'],
            'metadata': metadata
        }
    
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by IDs."""
        self._ensure_initialized()
        
        if not ids or self.table is None:
            return
        
        # Build delete filter
        ids_str = "', '".join(ids)
        filter_str = f"id IN ('{ids_str}')"
        self.table.delete(filter_str)
    
    def delete_by_topic(self, topic_id: str) -> None:
        """Delete all documents for a topic."""
        self._ensure_initialized()
        
        if self.table is None:
            return
        
        filter_str = f"topic_id = '{topic_id}'"
        self.table.delete(filter_str)
    
    def count_documents(self, where: Optional[Dict[str, Any]] = None) -> int:
        """Count documents in collection."""
        self._ensure_initialized()
        
        if self.table is None:
            return 0
        
        if where:
            filter_str = self._build_filter_string(where)
            if filter_str:
                results = self.table.search().where(filter_str).to_pandas()
                return len(results)
        
        return self.table.count_rows()
    
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
        
        if self.table is None:
            return
        
        # Drop and recreate empty table
        self.db.drop_table(self.table_name)
        self.table = None
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        self._ensure_initialized()
        
        if self.table is None:
            return {
                'name': self.table_name,
                'count': 0,
                'metadata': {}
            }
        
        return {
            'name': self.table_name,
            'count': self.table.count_rows(),
            'metadata': {}
        }
    
    async def close(self) -> None:
        """Close connections and cleanup resources."""
        # LanceDB connections are automatically managed
        # Just mark as uninitialized
        self.is_initialized = False
        self.db = None
        self.table = None
        self.embedder = None
