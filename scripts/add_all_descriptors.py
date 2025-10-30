"""
Add all visual descriptors to existing Elasticsearch documents
This script extracts Color Histogram, LBP, HOG, and MPEG-7 features
and adds them to documents that already have VGG features.
"""

import sys
import os
from pathlib import Path

# Add backend to path - script runs inside Docker container
sys.path.insert(0, "/app")

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import numpy as np
from PIL import Image
import cv2
import requests
from io import BytesIO
from tqdm import tqdm
import time

from utils.descriptor_extractor import (
    ColorHistogramExtractor,
    LBPExtractor,
    HOGExtractor,
    MPEG7Extractor
)


def download_image(url: str, timeout: int = 10) -> Image.Image:
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        
        # Convert to RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image
    except Exception as e:
        raise Exception(f"Failed to download {url}: {e}")


def extract_all_cv_descriptors(image: Image.Image) -> dict:
    """
    Extract Color, LBP, HOG, and MPEG-7 descriptors
    (VGG is already in the index)
    """
    try:
        # Convert to numpy array
        img_array = np.array(image)
        
        # Ensure RGB format
        if len(img_array.shape) == 2:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        elif img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        
        # Initialize extractors
        color_extractor = ColorHistogramExtractor(bins=8)
        lbp_extractor = LBPExtractor(n_points=8, radius=1)
        hog_extractor = HOGExtractor(orientations=9, pixels_per_cell=(8, 8), cells_per_block=(3, 3))
        mpeg7_extractor = MPEG7Extractor()
        
        # Extract features
        descriptors = {
            'color_histogram': color_extractor.extract(img_array).tolist(),
            'lbp_features': lbp_extractor.extract(img_array).tolist(),
            'hog_features': hog_extractor.extract(img_array).tolist(),
            'mpeg7_features': mpeg7_extractor.extract(img_array).tolist()
        }
        
        return descriptors
        
    except Exception as e:
        print(f"Error extracting descriptors: {e}")
        return None


def process_documents(es: Elasticsearch, index_name: str = "flickr_images", batch_size: int = 10):
    """
    Process all documents in the index and add missing descriptors
    """
    # Get all documents
    print(f"Fetching documents from index: {index_name}")
    
    # Count total documents
    count_result = es.count(index=index_name)
    total_docs = count_result['count']
    print(f"Found {total_docs} documents to process")
    
    # Scroll through all documents
    query = {
        "query": {
            "match_all": {}
        },
        "size": batch_size
    }
    
    # Use scroll API for large result sets
    response = es.search(
        index=index_name,
        body=query,
        scroll='5m'
    )
    
    scroll_id = response['_scroll_id']
    hits = response['hits']['hits']
    
    processed = 0
    errors = 0
    skipped = 0
    
    with tqdm(total=total_docs, desc="Processing images") as pbar:
        while hits:
            updates = []
            
            for hit in hits:
                doc_id = hit['_id']
                source = hit['_source']
                
                # Check if descriptors already exist
                if all(key in source for key in ['color_histogram', 'lbp_features', 'hog_features', 'mpeg7_features']):
                    skipped += 1
                    pbar.update(1)
                    continue
                
                # Construct image URL
                try:
                    url = f"http://farm{source.get('flickr_farm')}.staticflickr.com/{source.get('flickr_server')}/{source.get('id')}_{source.get('flickr_secret')}.jpg"
                    
                    # Download image
                    image = download_image(url, timeout=10)
                    
                    # Extract descriptors
                    descriptors = extract_all_cv_descriptors(image)
                    
                    if descriptors:
                        # Prepare update
                        updates.append({
                            '_op_type': 'update',
                            '_index': index_name,
                            '_id': doc_id,
                            'doc': descriptors
                        })
                        processed += 1
                    else:
                        errors += 1
                        
                except Exception as e:
                    print(f"\nError processing {doc_id}: {e}")
                    errors += 1
                
                pbar.update(1)
            
            # Bulk update
            if updates:
                try:
                    success, failed = bulk(es, updates, raise_on_error=False)
                    if failed:
                        print(f"\nFailed to update {len(failed)} documents")
                except Exception as e:
                    print(f"\nBulk update error: {e}")
            
            # Get next batch
            response = es.scroll(scroll_id=scroll_id, scroll='5m')
            scroll_id = response['_scroll_id']
            hits = response['hits']['hits']
    
    # Clear scroll
    es.clear_scroll(scroll_id=scroll_id)
    
    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"  Processed: {processed}")
    print(f"  Skipped (already have descriptors): {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Total: {total_docs}")
    print(f"{'='*60}")


def verify_descriptors(es: Elasticsearch, index_name: str = "flickr_images", sample_size: int = 5):
    """
    Verify that descriptors were added correctly
    """
    print(f"\nVerifying descriptors (sampling {sample_size} documents)...")
    
    response = es.search(
        index=index_name,
        body={
            "query": {"match_all": {}},
            "size": sample_size
        }
    )
    
    for hit in response['hits']['hits']:
        doc_id = hit['_id']
        source = hit['_source']
        
        print(f"\nDocument: {doc_id}")
        print(f"  Title: {source.get('title', 'N/A')}")
        
        # Check which descriptors exist
        descriptors = ['vgg16_features', 'color_histogram', 'lbp_features', 'hog_features', 'mpeg7_features']
        for desc in descriptors:
            if desc in source:
                feature_len = len(source[desc])
                print(f"  ✅ {desc}: {feature_len} dimensions")
            else:
                print(f"  ❌ {desc}: MISSING")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Add all descriptors to Elasticsearch documents")
    parser.add_argument("--host", default="localhost", help="Elasticsearch host")
    parser.add_argument("--port", default=9200, type=int, help="Elasticsearch port")
    parser.add_argument("--index", default="flickr_images", help="Index name")
    parser.add_argument("--batch-size", default=10, type=int, help="Batch size for processing")
    parser.add_argument("--verify-only", action="store_true", help="Only verify, don't process")
    
    args = parser.parse_args()
    
    # Connect to Elasticsearch
    es = Elasticsearch([f"http://{args.host}:{args.port}"])
    
    # Check connection
    if not es.ping():
        print(f"❌ Cannot connect to Elasticsearch at {args.host}:{args.port}")
        sys.exit(1)
    
    print("✅ Connected to Elasticsearch")
    print(f"   Cluster: {es.info()['cluster_name']}")
    print(f"   Version: {es.info()['version']['number']}")
    
    if args.verify_only:
        verify_descriptors(es, args.index)
    else:
        # Process documents
        process_documents(es, args.index, args.batch_size)
        
        # Verify results
        verify_descriptors(es, args.index)
