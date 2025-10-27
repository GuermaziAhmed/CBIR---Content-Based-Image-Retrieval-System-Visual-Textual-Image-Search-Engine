"""
Faiss-based similarity search engine
"""

import faiss
import numpy as np
import os
import pickle
from typing import Tuple, Optional
import logging
from config import settings

logger = logging.getLogger(__name__)


class FaissSearchEngine:
    """Manages Faiss indexes for different descriptors"""
    
    def __init__(self):
        self.indexes = {}
        self.id_mappings = {}
        self._load_indexes()
    
    def _load_indexes(self):
        """Load all available indexes from disk"""
        if not os.path.exists(settings.INDEX_DIR):
            logger.warning(f"Index directory not found: {settings.INDEX_DIR}")
            return
        
        for descriptor in settings.AVAILABLE_DESCRIPTORS:
            index_path = os.path.join(settings.INDEX_DIR, f"{descriptor}.index")
            mapping_path = os.path.join(settings.INDEX_DIR, f"{descriptor}_ids.pkl")
            
            if os.path.exists(index_path) and os.path.exists(mapping_path):
                try:
                    # Load Faiss index
                    self.indexes[descriptor] = faiss.read_index(index_path)
                    
                    # Load ID mapping
                    with open(mapping_path, 'rb') as f:
                        self.id_mappings[descriptor] = pickle.load(f)
                    
                    logger.info(
                        f"Loaded {descriptor} index: "
                        f"{self.indexes[descriptor].ntotal} vectors"
                    )
                except Exception as e:
                    logger.error(f"Failed to load {descriptor} index: {e}")
    
    def search(
        self,
        descriptor_name: str,
        query_vector: np.ndarray,
        top_k: int = 50
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for similar images using a descriptor
        
        Args:
            descriptor_name: Name of the descriptor (color, lbp, hog, mpeg7)
            query_vector: Query feature vector
            top_k: Number of results to return
            
        Returns:
            Tuple of (image_ids, distances)
        """
        if descriptor_name not in self.indexes:
            logger.warning(f"Index for {descriptor_name} not loaded")
            return np.array([]), np.array([])
        
        try:
            # Ensure query is 2D array
            if len(query_vector.shape) == 1:
                query_vector = query_vector.reshape(1, -1)
            
            # Normalize query vector
            faiss.normalize_L2(query_vector)
            
            # Search
            index = self.indexes[descriptor_name]
            distances, indices = index.search(query_vector, top_k)
            
            # Map indices to image IDs
            id_mapping = self.id_mappings[descriptor_name]
            image_ids = np.array([id_mapping[idx] for idx in indices[0]])
            
            return image_ids, distances[0]
            
        except Exception as e:
            logger.error(f"Search failed for {descriptor_name}: {e}")
            return np.array([]), np.array([])
    
    def add_to_index(
        self,
        descriptor_name: str,
        vectors: np.ndarray,
        image_ids: np.ndarray
    ):
        """
        Add vectors to an index
        
        Args:
            descriptor_name: Name of the descriptor
            vectors: Feature vectors to add (N, D)
            image_ids: Corresponding image IDs (N,)
        """
        try:
            # Create index if doesn't exist
            if descriptor_name not in self.indexes:
                dimension = vectors.shape[1]
                # Use Flat index with L2 distance
                self.indexes[descriptor_name] = faiss.IndexFlatL2(dimension)
                self.id_mappings[descriptor_name] = {}
            
            # Normalize vectors
            faiss.normalize_L2(vectors)
            
            # Add to index
            start_idx = self.indexes[descriptor_name].ntotal
            self.indexes[descriptor_name].add(vectors)
            
            # Update ID mapping
            for i, img_id in enumerate(image_ids):
                self.id_mappings[descriptor_name][start_idx + i] = img_id
            
            logger.info(
                f"Added {len(image_ids)} vectors to {descriptor_name} index"
            )
            
        except Exception as e:
            logger.error(f"Failed to add to {descriptor_name} index: {e}")
    
    def save_index(self, descriptor_name: str):
        """Save index and ID mapping to disk"""
        if descriptor_name not in self.indexes:
            logger.warning(f"No index to save for {descriptor_name}")
            return
        
        try:
            os.makedirs(settings.INDEX_DIR, exist_ok=True)
            
            # Save Faiss index
            index_path = os.path.join(settings.INDEX_DIR, f"{descriptor_name}.index")
            faiss.write_index(self.indexes[descriptor_name], index_path)
            
            # Save ID mapping
            mapping_path = os.path.join(settings.INDEX_DIR, f"{descriptor_name}_ids.pkl")
            with open(mapping_path, 'wb') as f:
                pickle.dump(self.id_mappings[descriptor_name], f)
            
            logger.info(f"Saved {descriptor_name} index to {index_path}")
            
        except Exception as e:
            logger.error(f"Failed to save {descriptor_name} index: {e}")
    
    def save_all_indexes(self):
        """Save all loaded indexes"""
        for descriptor in self.indexes.keys():
            self.save_index(descriptor)
    
    def get_index_stats(self) -> dict:
        """Get statistics for all indexes"""
        stats = {}
        for descriptor, index in self.indexes.items():
            stats[descriptor] = {
                'total_vectors': index.ntotal,
                'dimension': index.d,
                'is_trained': index.is_trained
            }
        return stats
    
    def clear_index(self, descriptor_name: str):
        """Clear a specific index"""
        if descriptor_name in self.indexes:
            del self.indexes[descriptor_name]
            del self.id_mappings[descriptor_name]
            logger.info(f"Cleared {descriptor_name} index")


# Global search engine instance
_search_engine = None

def get_search_engine() -> FaissSearchEngine:
    """Get or create global search engine instance"""
    global _search_engine
    if _search_engine is None:
        _search_engine = FaissSearchEngine()
    return _search_engine
