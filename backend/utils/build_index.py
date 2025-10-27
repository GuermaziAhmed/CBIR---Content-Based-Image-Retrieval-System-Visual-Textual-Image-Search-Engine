"""
Index building utilities
Processes images and builds Faiss indexes for all descriptors
"""

import os
import numpy as np
import cv2
from pathlib import Path
from tqdm import tqdm
import logging
from typing import List
from datetime import datetime

from config import settings
from database import SessionLocal, ImageModel
from utils.descriptor_extractor import extract_all_descriptors
from utils.faiss_search import FaissSearchEngine

logger = logging.getLogger(__name__)


class IndexBuilder:
    """Build and manage search indexes"""
    
    def __init__(self):
        self.search_engine = FaissSearchEngine()
    
    def build_all_indexes(
        self,
        descriptors: List[str],
        force_rebuild: bool = False
    ):
        """
        Build indexes for all descriptors
        
        Args:
            descriptors: List of descriptor names to build
            force_rebuild: Force rebuild even if index exists
        """
        logger.info(f"Starting index build for descriptors: {descriptors}")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get all images from database
            images = db.query(ImageModel).all()
            
            if not images:
                logger.warning("No images found in database")
                return
            
            logger.info(f"Found {len(images)} images to index")
            
            # Process each descriptor
            for descriptor in descriptors:
                if descriptor not in settings.AVAILABLE_DESCRIPTORS:
                    logger.warning(f"Unknown descriptor: {descriptor}")
                    continue
                
                # Check if index already exists
                index_path = os.path.join(settings.INDEX_DIR, f"{descriptor}.index")
                if os.path.exists(index_path) and not force_rebuild:
                    logger.info(f"Index for {descriptor} already exists, skipping")
                    continue
                
                self._build_descriptor_index(descriptor, images)
            
            logger.info("Index building completed")
            
        except Exception as e:
            logger.error(f"Index building failed: {e}")
            raise
        finally:
            db.close()
    
    def _build_descriptor_index(
        self,
        descriptor_name: str,
        images: List[ImageModel]
    ):
        """Build index for a specific descriptor"""
        logger.info(f"Building {descriptor_name} index...")
        
        vectors = []
        image_ids = []
        
        # Extract descriptors from all images
        for image in tqdm(images, desc=f"Extracting {descriptor_name}"):
            try:
                # Load image
                image_path = os.path.join(settings.IMAGE_DIR, image.filename)
                if not os.path.exists(image_path):
                    logger.warning(f"Image not found: {image_path}")
                    continue
                
                img = cv2.imread(image_path)
                if img is None:
                    logger.warning(f"Failed to load: {image_path}")
                    continue
                
                # Convert BGR to RGB
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Extract descriptor
                features = extract_all_descriptors(img_rgb, [descriptor_name])
                feature_vector = features.get(descriptor_name)
                
                if feature_vector is not None:
                    vectors.append(feature_vector)
                    image_ids.append(image.id)
                    
            except Exception as e:
                logger.error(f"Failed to process {image.filename}: {e}")
                continue
        
        if not vectors:
            logger.warning(f"No vectors extracted for {descriptor_name}")
            return
        
        # Convert to numpy array
        vectors_array = np.vstack(vectors).astype(np.float32)
        ids_array = np.array(image_ids)
        
        logger.info(
            f"Extracted {len(vectors)} vectors of dimension {vectors_array.shape[1]}"
        )
        
        # Clear existing index
        self.search_engine.clear_index(descriptor_name)
        
        # Add to index
        self.search_engine.add_to_index(descriptor_name, vectors_array, ids_array)
        
        # Save index
        self.search_engine.save_index(descriptor_name)
        
        logger.info(f"Successfully built {descriptor_name} index")
    
    def scan_and_index_new_images(self):
        """
        Scan image directory and add new images to database and indexes
        """
        logger.info("Scanning for new images...")
        
        db = SessionLocal()
        
        try:
            # Get existing filenames
            existing = {img.filename for img in db.query(ImageModel.filename).all()}
            
            # Scan image directory
            new_images = []
            image_dir = Path(settings.IMAGE_DIR)
            
            for ext in settings.ALLOWED_EXTENSIONS:
                for img_path in image_dir.rglob(f"*{ext}"):
                    filename = img_path.name
                    
                    if filename not in existing:
                        # Add to database
                        img = cv2.imread(str(img_path))
                        if img is not None:
                            height, width = img.shape[:2]
                            file_size = img_path.stat().st_size
                            
                            new_image = ImageModel(
                                filename=filename,
                                url=f"/images/{filename}",
                                file_size=file_size,
                                width=width,
                                height=height,
                                descriptors_json={}
                            )
                            db.add(new_image)
                            new_images.append(new_image)
            
            if new_images:
                db.commit()
                logger.info(f"Added {len(new_images)} new images to database")
                
                # Build indexes for new images
                self._build_descriptor_index("color", new_images)
                self._build_descriptor_index("lbp", new_images)
                
            else:
                logger.info("No new images found")
                
        except Exception as e:
            logger.error(f"Failed to scan images: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_stats(self):
        """Get index statistics"""
        db = SessionLocal()
        
        try:
            total_images = db.query(ImageModel).count()
            index_stats = self.search_engine.get_index_stats()
            
            # Calculate total index size
            total_size = 0
            for descriptor in settings.AVAILABLE_DESCRIPTORS:
                index_path = os.path.join(settings.INDEX_DIR, f"{descriptor}.index")
                if os.path.exists(index_path):
                    total_size += os.path.getsize(index_path)
            
            return {
                "total_images": total_images,
                "indexed_descriptors": index_stats,
                "index_size_mb": round(total_size / (1024 * 1024), 2),
                "last_build": datetime.now()
            }
            
        finally:
            db.close()


# CLI script for building indexes
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    builder = IndexBuilder()
    
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        builder.scan_and_index_new_images()
    else:
        builder.build_all_indexes(
            descriptors=settings.AVAILABLE_DESCRIPTORS,
            force_rebuild=True
        )
