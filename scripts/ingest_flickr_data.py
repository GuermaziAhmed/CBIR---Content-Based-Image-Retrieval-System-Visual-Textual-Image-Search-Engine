"""
Complete Data Ingestion Pipeline for Flickr Images
1. Parse CSV metadata
2. Download images from Flickr (temporarily)
3. Extract VGG features
4. Delete images (optional, saves 90% disk space)
5. Index features to Elasticsearch
"""

import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import os
import time
from pathlib import Path
from tqdm import tqdm
from elasticsearch import Elasticsearch, helpers
from vgg_extractor import VGGFeatureExtractor
import numpy as np
from typing import Dict, List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlickrImageIngestion:
    """
    Handles downloading and indexing of Flickr images
    """
    
    def __init__(
        self,
        es_host: str = "localhost",
        es_port: int = 9200,
        index_name: str = "flickr_images",
        image_dir: str = "./data/images",
        model_name: str = "vgg16",
        layer_name: str = "fc2",
        batch_size: int = 100,
        max_workers: int = 4,
        keep_images: bool = False,
        temp_dir: Optional[str] = None
    ):
        """
        Initialize ingestion pipeline
        
        Args:
            keep_images: If False, deletes images after feature extraction (saves 90% disk space)
            temp_dir: Temporary directory for images (if keep_images=False)
        """
        self.es = Elasticsearch([f"http://{es_host}:{es_port}"])
        self.index_name = index_name
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.keep_images = keep_images
        
        # Setup directories
        if keep_images:
            self.image_dir = Path(image_dir)
            self.image_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Images will be stored in: {self.image_dir}")
        else:
            # Use temporary directory
            self.image_dir = Path(temp_dir) if temp_dir else Path("./data/temp/images")
            self.image_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Using temporary directory: {self.image_dir}")
            logger.info("🗑️  Images will be DELETED after feature extraction (saves disk space)")
        
        # Initialize VGG extractor
        logger.info(f"Initializing {model_name} feature extractor...")
        self.extractor = VGGFeatureExtractor(
            model_name=model_name,
            layer_name=layer_name
        )
        
        # Check Elasticsearch connection
        if not self.es.ping():
            raise ConnectionError("Cannot connect to Elasticsearch")
        logger.info(f"✅ Connected to Elasticsearch at {es_host}:{es_port}")
    
    def construct_flickr_url(self, row: pd.Series) -> str:
        """
        Construct Flickr image URL from CSV row
        """
        return (
            f"http://farm{int(row['flickr_farm'])}.staticflickr.com/"
            f"{row['flickr_server']}/{row['id']}_{row['flickr_secret']}.jpg"
        )
    
    def download_image(
        self,
        url: str,
        image_id: str,
        timeout: int = 10,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Download image from Flickr URL
        
        Returns:
            Local file path if successful, None otherwise
        """
        local_path = os.path.join(self.image_dir, f"{image_id}.jpg")
        
        # Skip if already downloaded
        if os.path.exists(local_path):
            return local_path
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=timeout, stream=True)
                response.raise_for_status()
                
                # Validate image
                img = Image.open(BytesIO(response.content))
                img.verify()  # Verify it's a valid image
                
                # Re-open and save (verify() closes the file)
                img = Image.open(BytesIO(response.content))
                img.save(local_path, "JPEG")
                
                return local_path
            
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    logger.warning(f"Failed to download {url}: {e}")
                    return None
        
        return None
    
    def process_row(self, row: pd.Series) -> Optional[Dict]:
        """
        Process a single CSV row:
        1. Download image
        2. Extract features
        3. Delete image if keep_images=False
        4. Prepare document for Elasticsearch
        """
        image_id = str(row['id'])
        
        try:
            # Construct URL
            image_url = self.construct_flickr_url(row)
            
            # Download image
            start_time = time.time()
            local_path = self.download_image(image_url, image_id)
            
            if not local_path:
                return {
                    '_index': self.index_name,
                    '_id': image_id,
                    '_source': {
                        'id': image_id,
                        'image_url': image_url,
                        'image_status': 'download_failed',
                        'error_message': 'Failed to download image',
                        **row.to_dict()
                    }
                }
            
            # Extract VGG features
            try:
                features = self.extractor.extract_features(local_path)
                feature_key = f"{self.extractor.model_name}_features"
                
                # Get image properties
                img = Image.open(local_path)
                width, height = img.size
                file_size = os.path.getsize(local_path)
                img_format = img.format
                img.close()
                
                processing_time = time.time() - start_time
                
                # Delete image if not keeping (SAVE 90% DISK SPACE)
                if not self.keep_images:
                    try:
                        os.remove(local_path)
                        logger.debug(f"🗑️  Deleted temporary image: {image_id}")
                    except Exception as e:
                        logger.warning(f"Could not delete {local_path}: {e}")
                
                # Prepare document
                doc = {
                    '_index': self.index_name,
                    '_id': image_id,
                    '_source': {
                        'id': image_id,
                        'image_url': image_url,
                        'local_path': local_path if self.keep_images else None,
                        'image_status': 'processed',
                        feature_key: features.tolist(),
                        'width': width,
                        'height': height,
                        'file_size': file_size,
                        'format': img_format,
                        'processing_time': processing_time,
                        **row.to_dict()
                    }
                }
                
                return doc
            
            except Exception as e:
                logger.warning(f"Feature extraction failed for {image_id}: {e}")
                # Always delete image on error
                if os.path.exists(local_path):
                    try:
                        os.remove(local_path)
                    except:
                        pass
                return {
                    '_index': self.index_name,
                    '_id': image_id,
                    '_source': {
                        'id': image_id,
                        'image_url': image_url,
                        'local_path': None,
                        'image_status': 'feature_extraction_failed',
                        'error_message': str(e),
                        **row.to_dict()
                    }
                }
        
        except Exception as e:
            logger.error(f"Error processing row {image_id}: {e}")
            return None
    
    def ingest_csv(
        self,
        csv_path: str,
        limit: Optional[int] = None,
        skip_existing: bool = True
    ):
        """
        Ingest CSV file with Flickr metadata
        """
        logger.info(f"📂 Reading CSV: {csv_path}")
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        if limit:
            df = df.head(limit)
        
        logger.info(f"📊 Total rows: {len(df)}")
        logger.info(f"💾 Keep images after extraction: {self.keep_images}")
        if not self.keep_images:
            logger.info(f"💡 Disk space saving mode: Images will be deleted after feature extraction")
        
        # Process in batches
        total_processed = 0
        total_success = 0
        total_failed = 0
        
        for i in range(0, len(df), self.batch_size):
            batch_df = df.iloc[i:i + self.batch_size]
            logger.info(f"\n🔄 Processing batch {i // self.batch_size + 1} ({i+1}-{min(i+self.batch_size, len(df))}/{len(df)})")
            
            # Process batch with threading
            documents = []
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self.process_row, row): idx
                    for idx, row in batch_df.iterrows()
                }
                
                for future in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
                    doc = future.result()
                    if doc:
                        documents.append(doc)
            
            # Bulk index to Elasticsearch
            if documents:
                try:
                    success, failed = helpers.bulk(
                        self.es,
                        documents,
                        raise_on_error=False,
                        raise_on_exception=False
                    )
                    total_success += success
                    total_failed += len(failed)
                    logger.info(f"✅ Indexed {success} documents, {len(failed)} failed")
                except Exception as e:
                    logger.error(f"❌ Bulk indexing error: {e}")
                    total_failed += len(documents)
            
            total_processed += len(batch_df)
            
            # Progress report
            logger.info(f"📊 Progress: {total_processed}/{len(df)} processed")
        
        # Cleanup temp directory if not keeping images
        if not self.keep_images:
            try:
                # Remove empty temp directory
                if self.image_dir.exists() and not any(self.image_dir.iterdir()):
                    self.image_dir.rmdir()
                    logger.info(f"🗑️  Removed empty temp directory: {self.image_dir}")
                elif self.image_dir.exists():
                    remaining = len(list(self.image_dir.iterdir()))
                    logger.warning(f"⚠️  Temp directory not empty ({remaining} files remain): {self.image_dir}")
            except Exception as e:
                logger.warning(f"Could not remove temp directory: {e}")
        
        # Final report
        logger.info("\n" + "="*60)
        logger.info("✅ INGESTION COMPLETE")
        logger.info("="*60)
        logger.info(f"Total processed: {total_processed}")
        logger.info(f"Successfully indexed: {total_success}")
        logger.info(f"Failed: {total_failed}")
        logger.info(f"Success rate: {total_success/total_processed*100:.2f}%")
        if not self.keep_images:
            logger.info(f"💾 Disk space saved: ~{total_success * 0.2:.1f} MB (images deleted)")
        logger.info("="*60 + "\n")


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest Flickr images to Elasticsearch")
    parser.add_argument("--csv", type=str, required=True, help="Path to CSV file")
    parser.add_argument("--es-host", type=str, default="localhost", help="Elasticsearch host")
    parser.add_argument("--es-port", type=int, default=9200, help="Elasticsearch port")
    parser.add_argument("--index", type=str, default="flickr_images", help="Index name")
    parser.add_argument("--image-dir", type=str, default="./data/images", help="Image directory (if --keep-images)")
    parser.add_argument("--model", type=str, default="vgg16", choices=["vgg16", "vgg19"], help="VGG model")
    parser.add_argument("--layer", type=str, default="fc2", help="Feature layer")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker threads")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows")
    parser.add_argument("--keep-images", action="store_true", 
                        help="Keep downloaded images (default: delete after extraction to save 90%% disk space)")
    parser.add_argument("--temp-dir", type=str, default=None,
                        help="Temporary directory for images (default: ./data/temp/images)")
    
    args = parser.parse_args()
    
    # Print configuration
    print("\n" + "="*60)
    print("FLICKR IMAGE INGESTION PIPELINE")
    print("="*60)
    print(f"CSV File: {args.csv}")
    print(f"Elasticsearch: {args.es_host}:{args.es_port}")
    print(f"Index: {args.index}")
    print(f"VGG Model: {args.model} (layer: {args.layer})")
    print(f"Batch Size: {args.batch_size}")
    print(f"Workers: {args.workers}")
    print(f"Keep Images: {'YES (high disk usage)' if args.keep_images else 'NO (saves 90% disk space) ✅'}")
    if args.limit:
        print(f"Limit: {args.limit} images")
    print("="*60 + "\n")
    
    # Create ingestion pipeline
    pipeline = FlickrImageIngestion(
        es_host=args.es_host,
        es_port=args.es_port,
        index_name=args.index,
        image_dir=args.image_dir,
        model_name=args.model,
        layer_name=args.layer,
        batch_size=args.batch_size,
        max_workers=args.workers,
        keep_images=args.keep_images,
        temp_dir=args.temp_dir
    )
    
    # Run ingestion
    pipeline.ingest_csv(args.csv, limit=args.limit)
