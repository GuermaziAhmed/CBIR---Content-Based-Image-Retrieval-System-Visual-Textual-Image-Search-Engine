"""
Add all visual descriptors to existing Elasticsearch documents
This script extracts Color Histogram, LBP, HOG, Edge Histogram, and SIFT features
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading

from utils.descriptor_extractor import (
    ColorHistogramExtractor,
    LBPExtractor,
    HOGExtractor,
    EdgeHistogramExtractor,
    SIFTExtractor
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
    Extract Color, LBP, HOG, Edge Histogram, and SIFT descriptors
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
        edge_extractor = EdgeHistogramExtractor(bins=64)
        sift_extractor = SIFTExtractor(n_features=100, descriptor_size=128)
        
        # Extract features
        descriptors = {
            'color_histogram': color_extractor.extract(img_array).tolist(),
            'lbp_features': lbp_extractor.extract(img_array).tolist(),
            'hog_features': hog_extractor.extract(img_array).tolist(),
            'edge_histogram': edge_extractor.extract(img_array).tolist(),
            'sift_features': sift_extractor.extract(img_array).tolist()
        }
        
        return descriptors
        
    except Exception as e:
        print(f"Error extracting descriptors: {e}")
        return None


def process_single_document(doc_data: dict) -> dict:
    """
    Process a single document - download image and extract descriptors
    This function is designed to run in parallel workers
    
    Args:
        doc_data: Dictionary with 'id', 'url', and 'source' keys
    
    Returns:
        Dictionary with results: {'id': ..., 'descriptors': ..., 'error': ...}
    """
    doc_id = doc_data['id']
    url = doc_data['url']
    
    try:
        # Download image
        image = download_image(url, timeout=10)
        
        # Extract descriptors
        descriptors = extract_all_cv_descriptors(image)
        
        if descriptors:
            # Filter out zero vectors
            valid_descriptors = {}
            for key, vector in descriptors.items():
                if isinstance(vector, list) and len(vector) > 0:
                    if all(v == 0.0 for v in vector):
                        # Skip zero vectors
                        continue
                    else:
                        valid_descriptors[key] = vector
                else:
                    valid_descriptors[key] = vector
            
            if valid_descriptors:
                return {
                    'id': doc_id,
                    'descriptors': valid_descriptors,
                    'error': None
                }
            else:
                return {
                    'id': doc_id,
                    'descriptors': None,
                    'error': 'All descriptors are zero vectors'
                }
        else:
            return {
                'id': doc_id,
                'descriptors': None,
                'error': 'Failed to extract descriptors'
            }
            
    except Exception as e:
        return {
            'id': doc_id,
            'descriptors': None,
            'error': str(e)
        }


def process_documents(es: Elasticsearch, index_name: str = "flickr_images", batch_size: int = 10, force: bool = False, offset: int = 0, limit: int = None, workers: int = 4):
    """
    Process all documents in the index and add missing descriptors
    
    Args:
        es: Elasticsearch client
        index_name: Name of the index
        batch_size: Number of documents to fetch per batch
        force: If True, reprocess documents even if they already have descriptors
        offset: Skip first N documents
        limit: Maximum number of documents to process
        workers: Number of parallel workers for processing
    """
    # Get all documents
    print(f"Fetching documents from index: {index_name}")
    print(f"👷 Workers: {workers}")
    
    # Count total documents
    count_result = es.count(index=index_name)
    total_docs = count_result['count']
    
    # Apply offset and limit
    if offset > 0:
        print(f"⏭️  Skipping first {offset:,} documents")
    
    if limit:
        docs_to_process = min(limit, total_docs - offset)
        print(f"🎯 Processing {docs_to_process:,} documents (from {offset:,} to {offset + docs_to_process:,})")
    else:
        docs_to_process = total_docs - offset
        print(f"📊 Processing {docs_to_process:,} documents (from {offset:,} to {total_docs:,})")
    
    print(f"📊 Total documents in index: {total_docs:,}")
    
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
    documents_seen = 0  # Track total documents seen (for offset)
    documents_processed_count = 0  # Track documents actually processed (for progress bar)
    
    # Adjust progress bar total based on offset and limit
    progress_total = docs_to_process
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=workers) as executor:
        with tqdm(total=progress_total, desc="Processing images", initial=0) as pbar:
            # First, skip offset documents if needed
            if offset > 0:
                skip_pbar = tqdm(total=offset, desc="Skipping to offset", unit="docs")
                while hits and documents_seen < offset:
                    for hit in hits:
                        if documents_seen >= offset:
                            break
                        documents_seen += 1
                        skip_pbar.update(1)
                    
                    if documents_seen < offset:
                        # Get next batch to continue skipping
                        response = es.scroll(scroll_id=scroll_id, scroll='5m')
                        scroll_id = response['_scroll_id']
                        hits = response['hits']['hits']
                skip_pbar.close()
                print(f"✅ Skipped {offset:,} documents, starting processing...")
            
            # Now process documents
            while hits:
                # Prepare batch of documents to process
                batch_docs = []
                
                for hit in hits:
                    # Check if we've reached the limit
                    if limit and (documents_seen - offset) >= limit:
                        # Stop processing
                        hits = []  # This will break the outer while loop
                        break
                    
                    doc_id = hit['_id']
                    source = hit['_source']
                    documents_seen += 1  # Increment for each document we see
                    
                    # Check if descriptors already exist (unless force=True)
                    if not force and all(key in source for key in ['color_histogram', 'lbp_features', 'hog_features', 'edge_histogram', 'sift_features']):
                        skipped += 1
                        documents_processed_count += 1
                        pbar.update(1)
                        continue
                    
                    # Construct image URL and prepare for parallel processing
                    url = f"http://farm{source.get('flickr_farm')}.staticflickr.com/{source.get('flickr_server')}/{source.get('id')}_{source.get('flickr_secret')}.jpg"
                    
                    batch_docs.append({
                        'id': doc_id,
                        'url': url,
                        'source': source
                    })
                
                # Process batch in parallel
                if batch_docs:
                    # Submit all tasks to thread pool
                    future_to_doc = {executor.submit(process_single_document, doc): doc for doc in batch_docs}
                    
                    # Collect results as they complete
                    updates = []
                    for future in as_completed(future_to_doc):
                        result = future.result()
                        
                        if result['error']:
                            errors += 1
                            if result['error'] != 'All descriptors are zero vectors':
                                print(f"\n❌ Error processing {result['id']}: {result['error']}")
                        elif result['descriptors']:
                            # Prepare update
                            updates.append({
                                '_op_type': 'update',
                                '_index': index_name,
                                '_id': result['id'],
                                'doc': result['descriptors']
                            })
                            processed += 1
                        else:
                            errors += 1
                        
                        documents_processed_count += 1
                        pbar.update(1)
                    
                    # Bulk update Elasticsearch
                    if updates:
                        try:
                            print(f"\n📤 Updating {len(updates)} documents...")
                            success, failed = bulk(es, updates, raise_on_error=False, stats_only=False)
                            print(f"✅ Successfully updated: {success}")
                            if failed:
                                print(f"❌ Failed to update {len(failed)} documents")
                                # Print first few errors for debugging
                                for item in failed[:5]:
                                    print(f"   Error: {item}")
                        except Exception as e:
                            print(f"\n❌ Bulk update error: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"\n⚠️ No documents to update in this batch")
                
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
        descriptors = ['vgg16_features', 'color_histogram', 'lbp_features', 'hog_features', 'edge_histogram', 'sift_features']
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
    parser.add_argument("--workers", default=8, type=int, help="Number of parallel workers")
    parser.add_argument("--offset", default=0, type=int, help="Skip first N documents (for resuming)")
    parser.add_argument("--limit", default=None, type=int, help="Maximum number of documents to process")
    parser.add_argument("--verify-only", action="store_true", help="Only verify, don't process")
    parser.add_argument("--force", action="store_true", help="Force reprocess all documents even if descriptors exist")
    
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
        process_documents(es, args.index, args.batch_size, args.force, args.offset, args.limit, args.workers)
        
        # Verify results
        verify_descriptors(es, args.index)
