"""Storage modules for vector and memory stores."""

import os
import json
from typing import List, Dict, Any, Optional
import qdrant_client
from qdrant_client.http import models
from fastembed import TextEmbedding
from sentence_transformers import CrossEncoder

from ..config import get_settings


class VectorStore:
    """Handles vector storage and retrieval using Qdrant."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = qdrant_client.QdrantClient(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key
        )
        self.embedding_model = TextEmbedding(model_name=self.settings.embedding_model)
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.collection_name = "archon_documents"
    
    def create_collection(self):
        """Create the Qdrant collection if it doesn't exist."""
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=384,  # Dimension for sentence-transformers/all-MiniLM-L6-v2
                    distance=models.Distance.COSINE
                )
            )
            print(f"Created collection: {self.collection_name}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"Collection {self.collection_name} already exists")
            else:
                print(f"Error creating collection: {e}")
    
    def add_documents(self, chunks: List[Dict[str, Any]]):
        """
        Add documents to the vector store.
        
        Args:
            chunks: List of enriched chunks to add
        """
        self.create_collection()
        
        points = []
        for i, chunk in enumerate(chunks):
            # Create embedding text
            embedding_text = self._create_embedding_text(chunk)
            
            # Generate embedding
            embedding = list(self.embedding_model.embed(embedding_text))[0]
            
            # Create point
            point = models.PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                    "enriched_metadata": chunk["enriched_metadata"],
                    "source_file": chunk["source_file"]
                }
            )
            points.append(point)
        
        # Upload points in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            print(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
        
        print(f"Successfully added {len(chunks)} documents to vector store")
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of similar documents with scores
        """
        # Generate query embedding
        query_embedding = list(self.embedding_model.embed(query))[0]
        
        # Search in Qdrant
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        
        # Rerank results using cross-encoder
        results = []
        for result in search_results:
            doc_text = result.payload["content"]
            cross_score = self.cross_encoder.predict([(query, doc_text)])[0]
            
            results.append({
                "content": result.payload["content"],
                "metadata": result.payload["metadata"],
                "enriched_metadata": result.payload["enriched_metadata"],
                "source_file": result.payload["source_file"],
                "vector_score": result.score,
                "cross_score": float(cross_score),
                "final_score": (result.score + float(cross_score)) / 2
            })
        
        # Sort by final score
        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results
    
    def _create_embedding_text(self, chunk: Dict) -> str:
        """Create embedding text for a chunk."""
        content = chunk["content"]
        enriched_metadata = chunk["enriched_metadata"]
        
        # Combine content with metadata
        embedding_parts = [
            content,
            f"Summary: {enriched_metadata['summary']}",
            f"Keywords: {', '.join(enriched_metadata['keywords'])}",
            f"Questions: {' | '.join(enriched_metadata['hypothetical_questions'])}"
        ]
        
        if enriched_metadata.get('table_summary'):
            embedding_parts.append(f"Table Summary: {enriched_metadata['table_summary']}")
        
        return " | ".join(embedding_parts)


class MemoryStore:
    """Handles persistent memory storage for the agent."""
    
    def __init__(self, file_path: Optional[str] = None):
        self.settings = get_settings()
        self.file_path = file_path or self.settings.memory_store_path
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading memory: {e}")
                return {"insights": [], "preferences": {}, "conversations": []}
        return {"insights": [], "preferences": {}, "conversations": []}
    
    def save_memory(self):
        """Save memory to file."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
    
    def add_insight(self, insight: str, category: str = "general"):
        """Add a new insight to memory."""
        self.memory["insights"].append({
            "text": insight,
            "category": category,
            "timestamp": self._get_timestamp()
        })
        self.save_memory()
    
    def add_preference(self, key: str, value: Any):
        """Add a user preference."""
        self.memory["preferences"][key] = value
        self.save_memory()
    
    def add_conversation(self, conversation: Dict[str, Any]):
        """Add a conversation to memory."""
        self.memory["conversations"].append({
            **conversation,
            "timestamp": self._get_timestamp()
        })
        self.save_memory()
    
    def get_insights(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get insights, optionally filtered by category."""
        if category:
            return [i for i in self.memory["insights"] if i["category"] == category]
        return self.memory["insights"]
    
    def get_preferences(self) -> Dict[str, Any]:
        """Get user preferences."""
        return self.memory["preferences"]
    
    def get_recent_conversations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversations."""
        return self.memory["conversations"][-limit:]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
