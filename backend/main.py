"""
FastAPI Backend for CBIR with Elasticsearch
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import os
from pathlib import Path
import base64
import io
import numpy as np
from PIL import Image
import cv2

from config import settings
from utils.descriptor_extractor import (
    ColorHistogramExtractor,
    LBPExtractor,
    HOGExtractor,
    EdgeHistogramExtractor,
    SIFTExtractor
)

app = FastAPI(
    title="CBIR API - Elasticsearch",
    description="Content-Based Image Retrieval System with VGG + Elasticsearch",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for images (if they exist)
IMAGE_DIR = os.getenv("IMAGE_DIR", "/data/images")
if os.path.exists(IMAGE_DIR):
    app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "CBIR API with Elasticsearch is running",
        "version": "2.0.0",
        "search_engine": "Elasticsearch 8.11",
        "feature_extractor": "VGG16/VGG19",
        "docs": "/docs",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from elasticsearch import Elasticsearch
    
    es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    
    try:
        es = Elasticsearch([f"http://{es_host}:{es_port}"])
        es_health = es.cluster.health()
        es_connected = es_health["status"] in ["green", "yellow"]
    except Exception as e:
        es_connected = False
        es_health = {"error": str(e)}
    
    return {
        "status": "healthy" if es_connected else "degraded",
        "elasticsearch": {
            "connected": es_connected,
            "host": f"{es_host}:{es_port}",
            "cluster_status": es_health.get("status", "unknown")
        },
        "image_dir": os.path.exists(IMAGE_DIR),
        "vgg_model": os.getenv("VGG_MODEL", "vgg16"),
        "vgg_layer": os.getenv("VGG_LAYER", "fc2")
    }

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    from elasticsearch import Elasticsearch
    
    es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    es_index = os.getenv("ELASTICSEARCH_INDEX", "flickr_images")
    
    try:
        es = Elasticsearch([f"http://{es_host}:{es_port}"])
        count = es.count(index=es_index)
        cluster_health = es.cluster.health()
        
        return {
            "total_documents": count["count"],
            "index_name": es_index,
            "cluster_health": cluster_health["status"],
            "status": "ok"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error",
            "total_documents": 0
        }


# Pydantic Models for Request/Response
class TextSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 50
    tags: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    min_views: Optional[int] = None


class ImageSearchRequest(BaseModel):
    image_data: str  # base64 encoded image
    top_k: Optional[int] = 50
    tags: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class HybridSearchRequest(BaseModel):
    query: str
    image_data: str
    text_weight: Optional[float] = 0.5
    image_weight: Optional[float] = 0.5
    top_k: Optional[int] = 50


class MultiDescriptorSearchRequest(BaseModel):
    """Request for multi-descriptor image search"""
    image_data: str  # base64 encoded image
    top_k: Optional[int] = 50
    tags: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    # Weights for each descriptor (should sum to ~1.0)
    vgg_weight: Optional[float] = 0.25
    color_weight: Optional[float] = 0.25
    lbp_weight: Optional[float] = 0.15
    hog_weight: Optional[float] = 0.15
    edge_histogram_weight: Optional[float] = 0.1
    sift_weight: Optional[float] = 0.1


@app.post("/api/search/multi-descriptor")
async def search_by_multi_descriptor(request: MultiDescriptorSearchRequest):
    """
    Advanced image search using multiple visual descriptors
    Returns results with individual descriptor similarity scores
    """
    import time
    from elasticsearch import Elasticsearch
    
    start_time = time.time()
    
    es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    es_index = os.getenv("ELASTICSEARCH_INDEX", "flickr_images")
    vgg_model = os.getenv("VGG_MODEL", "vgg16").lower()
    vgg_field = f"{vgg_model}_features"
    
    try:
        # Decode and validate image
        if "," in request.image_data:
            image_data = request.image_data.split(",")[1]
        else:
            image_data = request.image_data
        
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {str(e)}")
        
        # Open and validate image
        try:
            image_buffer = io.BytesIO(image_bytes)
            image = Image.open(image_buffer)
            image.verify()
            image_buffer.seek(0)
            image = Image.open(image_buffer)
            if image.mode != 'RGB':
                image = image.convert('RGB')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
        
        # Extract ALL descriptors from query image
        print("Extracting all descriptors from query image...")
        descriptors = extract_all_descriptors(image)
        print(f"Extracted descriptors: {list(descriptors.keys())}")
        
        es = Elasticsearch([f"http://{es_host}:{es_port}"])
        
        # Adjust weights to prioritize VGG when it's selected
        # If VGG has non-zero weight, give it higher importance (50% of total weight)
        weights = {
            'vgg': request.vgg_weight,
            'color': request.color_weight,
            'lbp': request.lbp_weight,
            'hog': request.hog_weight,
            'edge_histogram': request.edge_histogram_weight,
            'sift': request.sift_weight
        }
        
        # Count active descriptors (non-zero weights)
        active_descriptors = [k for k, v in weights.items() if v > 0]
        
        # If VGG is active among other descriptors, rebalance weights
        if 'vgg' in active_descriptors and len(active_descriptors) > 1:
            # Give VGG 50% of total weight, distribute rest among others
            vgg_weight = 0.70
            remaining_weight = 0.30
            other_descriptors = [d for d in active_descriptors if d != 'vgg']
            other_weight_each = remaining_weight / len(other_descriptors)
            
            weights['vgg'] = vgg_weight
            for desc in other_descriptors:
                weights[desc] = other_weight_each
            
            print(f"Auto-adjusted weights (VGG prioritized): {weights}")
        
        # Perform individual kNN searches for each descriptor
        # We'll search with each descriptor separately to get individual scores
        all_results = {}
        descriptor_configs = [
            ('vgg', vgg_field, descriptors['vgg_features'], weights['vgg']),
            ('color', 'color_histogram', descriptors['color_histogram'], weights['color']),
            ('lbp', 'lbp_features', descriptors['lbp_features'], weights['lbp']),
            ('hog', 'hog_features', descriptors['hog_features'], weights['hog']),
            ('edge_histogram', 'edge_histogram', descriptors['edge_histogram'], weights['edge_histogram']),
            ('sift', 'sift_features', descriptors['sift_features'], weights['sift'])
        ]
        
        # Get results for each descriptor
        for desc_name, field_name, features, weight in descriptor_configs:
            if weight <= 0:
                continue  # Skip if weight is 0
                
            knn_query = {
                "field": field_name,
                "query_vector": features.tolist(),
                "k": request.top_k * 2,  # Get more candidates
                "num_candidates": request.top_k * 10
            }
            
            query_body = {
                "knn": knn_query,
                "size": request.top_k * 2
            }
            
            try:
                response = es.search(index=es_index, body=query_body)
                
                # Store scores for each image
                for hit in response["hits"]["hits"]:
                    image_id = hit["_source"]["id"]
                    score = hit["_score"]
                    
                    if image_id not in all_results:
                        all_results[image_id] = {
                            "source": hit["_source"],
                            "descriptor_scores": {},
                            "weighted_scores": {}
                        }
                    
                    all_results[image_id]["descriptor_scores"][desc_name] = score
                    all_results[image_id]["weighted_scores"][desc_name] = score * weight
                    
            except Exception as e:
                print(f"Warning: {desc_name} search failed: {e}")
                continue
        
        # Calculate combined scores and get top candidates
        combined_results = []
        for image_id, data in all_results.items():
            # Calculate weighted sum
            total_score = sum(data["weighted_scores"].values())
            
            # Calculate percentages for each descriptor that found this image
            descriptor_percentages = {}
            raw_scores = data["descriptor_scores"]
            
            for desc_name in raw_scores:
                # Convert Elasticsearch cosine similarity score to percentage
                # Elasticsearch 8.x uses: score = (1 + cosine_similarity) / 2
                # where cosine_similarity ranges from -1 to 1
                # So ES score ranges from 0 to 1
                # To get cosine: cosine_similarity = (score * 2) - 1
                # 
                # For identical vectors: cosine = 1.0 → ES score = 1.0 → 100%
                # For orthogonal vectors: cosine = 0.0 → ES score = 0.5 → 0%
                # For opposite vectors: cosine = -1.0 → ES score = 0.0 → -100% (clip to 0)
                
                es_score = raw_scores[desc_name]
                # Convert ES score back to cosine similarity
                cosine_similarity = (es_score * 2.0) - 1.0
                # Convert to percentage (0-100)
                percentage = max(0.0, cosine_similarity * 100.0)
                # Cap to 100
                percentage = min(100.0, percentage)
                descriptor_percentages[desc_name] = round(percentage, 1)
            
            data["descriptor_percentages"] = descriptor_percentages
            data["total_score"] = total_score
            
            # Build result object
            source = data["source"]
            
            # Validate required Flickr metadata for image URL
            if not all([source.get('flickr_farm'), source.get('flickr_server'), 
                       source.get('id'), source.get('flickr_secret')]):
                # Skip this result - missing required image metadata
                continue
            
            # Skip failed downloads
            if source.get('image_status') == 'download_failed':
                continue
            
            url = f"http://farm{source.get('flickr_farm')}.staticflickr.com/{source.get('flickr_server')}/{source.get('id')}_{source.get('flickr_secret')}.jpg"
            
            combined_results.append({
                "image_id": image_id,  # Keep track of the all_results key
                "id": source.get("id"),
                "userid": source.get("userid"),
                "title": source.get("title", "Untitled"),
                "tags": source.get("tags", ""),
                "latitude": source.get("latitude"),
                "longitude": source.get("longitude"),
                "views": source.get("views", 0),
                "date_taken": source.get("date_taken"),
                "date_uploaded": source.get("date_uploaded"),
                "accuracy": source.get("accuracy", 0),
                "flickr_secret": source.get("flickr_secret"),
                "flickr_server": source.get("flickr_server"),
                "flickr_farm": source.get("flickr_farm"),
                "url": url,
                "score": total_score,
                "descriptor_scores": descriptor_percentages,  # Individual match percentages
                "global_match": round(sum(descriptor_percentages.values()) / len(descriptor_percentages), 1) if descriptor_percentages else 0
            })
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Get top K candidates
        top_candidates = combined_results[:request.top_k]
        
        # Second pass: Calculate similarity for ALL enabled descriptors on top results
        # This ensures every result shows scores for all descriptors, not just the ones that found it
        print(f"Computing complete descriptor scores for top {len(top_candidates)} results...")
        
        for candidate in top_candidates:
            image_id = candidate["image_id"]
            data = all_results[image_id]
            source = data["source"]
            
            # Check which descriptors are available in this document
            complete_scores = {}
            
            for desc_name, field_name, query_features, weight in descriptor_configs:
                if weight <= 0:
                    continue  # Skip disabled descriptors
                
                # Check if document has this descriptor
                if field_name not in source:
                    continue  # Document doesn't have this descriptor
                
                # If we already have the score from the first pass, use it
                if desc_name in data["descriptor_percentages"]:
                    complete_scores[desc_name] = data["descriptor_percentages"][desc_name]
                else:
                    # Calculate similarity manually (cosine similarity)
                    try:
                        doc_features = np.array(source[field_name])
                        query_vec = np.array(query_features)
                        
                        # Compute cosine similarity
                        dot_product = np.dot(query_vec, doc_features)
                        query_norm = np.linalg.norm(query_vec)
                        doc_norm = np.linalg.norm(doc_features)
                        
                        if query_norm > 0 and doc_norm > 0:
                            cosine_sim = dot_product / (query_norm * doc_norm)
                            # Convert to percentage
                            percentage = max(0.0, cosine_sim * 100.0)
                            percentage = min(100.0, percentage)
                            complete_scores[desc_name] = round(percentage, 1)
                        else:
                            complete_scores[desc_name] = 0.0
                    except Exception as e:
                        print(f"Warning: Failed to compute {desc_name} similarity for {image_id}: {e}")
                        complete_scores[desc_name] = 0.0
            
            # Update candidate with complete scores
            candidate["descriptor_scores"] = complete_scores
            candidate["global_match"] = round(sum(complete_scores.values()) / len(complete_scores), 1) if complete_scores else 0
            # Remove the temporary image_id field
            del candidate["image_id"]
        
        # Return top K with complete scores
        final_results = top_candidates
        
        # Calculate time taken in milliseconds
        time_taken_ms = int((time.time() - start_time) * 1000)
        
        return {
            "results": final_results,
            "total": len(final_results),
            "descriptor_weights": {
                "vgg": request.vgg_weight,
                "color": request.color_weight,
                "lbp": request.lbp_weight,
                "hog": request.hog_weight,
                "edge_histogram": request.edge_histogram_weight,
                "sift": request.sift_weight
            },
            "search_type": "multi-descriptor",
            "took": time_taken_ms
        }
        
    except Exception as e:
        import traceback
        error_detail = f"Multi-descriptor search failed: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR in multi-descriptor search: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Multi-descriptor search failed: {str(e)}")


@app.post("/api/search/text")
async def search_by_text(request: TextSearchRequest):
    """Text-based search using tags and title with normalized scoring"""
    from elasticsearch import Elasticsearch
    
    es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    es_index = os.getenv("ELASTICSEARCH_INDEX", "flickr_images")
    
    try:
        es = Elasticsearch([f"http://{es_host}:{es_port}"])
        
        # Build query with fuzzy matching for spelling tolerance
        # Use bool query with should clauses to combine exact and fuzzy matches
        must_clauses = [
            {
                "bool": {
                    "should": [
                        # Exact match (highest priority)
                        {
                            "multi_match": {
                                "query": request.query,
                                "fields": ["title^3", "tags^4"],
                                "type": "best_fields",
                                "boost": 2.0  # Boost exact matches
                            }
                        },
                        # Fuzzy match (tolerates typos)
                        {
                            "multi_match": {
                                "query": request.query,
                                "fields": ["title^2", "tags^3"],
                                "type": "best_fields",
                                "fuzziness": "AUTO",  # AUTO: 1 edit for 3-5 chars, 2 edits for >5 chars
                                "prefix_length": 2,  # First 2 chars must match exactly
                                "max_expansions": 50  # Limit fuzzy term expansions
                            }
                        },
                        # Phrase match with slop (word order variation)
                        {
                            "multi_match": {
                                "query": request.query,
                                "fields": ["title", "tags^2"],
                                "type": "phrase",
                                "slop": 2  # Allow 2 positions between words
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            }
        ]
        
        # Add filters
        filter_clauses = []
        if request.tags:
            for tag in request.tags:
                filter_clauses.append({"match": {"tags": tag}})
        
        if request.date_from or request.date_to:
            date_range = {}
            if request.date_from:
                date_range["gte"] = request.date_from
            if request.date_to:
                date_range["lte"] = request.date_to
            filter_clauses.append({"range": {"date_taken": date_range}})
        
        if request.min_views:
            filter_clauses.append({"range": {"views": {"gte": request.min_views}}})
        
        # Construct query body
        query_body = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses
                }
            } if filter_clauses else {
                "bool": {
                    "must": must_clauses
                }
            },
            "size": request.top_k
        }
        
        response = es.search(index=es_index, body=query_body)
        
        # Get max score for normalization
        max_score = response["hits"]["max_score"] if response["hits"]["hits"] else 1.0
        
        # Format results
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            # Validate required Flickr metadata
            if not all([source.get('flickr_farm'), source.get('flickr_server'), 
                       source.get('id'), source.get('flickr_secret')]):
                continue  # Skip results with missing image metadata
            
            # Skip failed downloads
            if source.get('image_status') == 'download_failed':
                continue
            
            # Normalize BM25 score to 0-100%
            # BM25 scores are unbounded, so we normalize relative to max score
            normalized_score = (hit["_score"] / max_score) * 100.0
            
            # Construct Flickr URL
            url = f"http://farm{source.get('flickr_farm')}.staticflickr.com/{source.get('flickr_server')}/{source.get('id')}_{source.get('flickr_secret')}.jpg"
            
            results.append({
                "id": source.get("id"),
                "userid": source.get("userid"),
                "title": source.get("title", "Untitled"),
                "tags": source.get("tags", ""),
                "latitude": source.get("latitude"),
                "longitude": source.get("longitude"),
                "views": source.get("views", 0),
                "date_taken": source.get("date_taken"),
                "date_uploaded": source.get("date_uploaded"),
                "accuracy": source.get("accuracy", 0),
                "flickr_secret": source.get("flickr_secret"),
                "flickr_server": source.get("flickr_server"),
                "flickr_farm": source.get("flickr_farm"),
                "url": url,
                "score": hit["_score"],
                "text_match": round(normalized_score, 1),  # Add normalized percentage
                "global_match": round(normalized_score, 1)  # For consistency with other search types
            })
        
        return {
            "query": request.query,
            "results": results,
            "total": response["hits"]["total"]["value"],
            "search_type": "text",
            "took": response["took"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/api/search/image")
async def search_by_image(request: ImageSearchRequest):
    """Image-based search using VGG features (kNN)"""
    from elasticsearch import Elasticsearch
    
    es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    es_index = os.getenv("ELASTICSEARCH_INDEX", "flickr_images")
    vgg_model = os.getenv("VGG_MODEL", "vgg16").lower()
    
    # Determine the correct field name based on model
    vgg_field = f"{vgg_model}_features"
    
    try:
        # Decode base64 image
        if "," in request.image_data:
            image_data = request.image_data.split(",")[1]
        else:
            image_data = request.image_data
        
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {str(e)}")
        
        # Open and validate image
        try:
            image_buffer = io.BytesIO(image_bytes)
            image = Image.open(image_buffer)
            
            # Verify it's a valid image by loading it
            image.verify()
            
            # Re-open after verify (verify closes the file)
            image_buffer.seek(0)
            image = Image.open(image_buffer)
            
            # Convert to RGB (handles RGBA, grayscale, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file. Supported formats: JPEG, PNG, WebP. Error: {str(e)}")
        
        # Extract VGG features
        features = extract_vgg_features(image)
        
        es = Elasticsearch([f"http://{es_host}:{es_port}"])
        
        # Build kNN query
        knn_query = {
            "field": vgg_field,  # Use model-specific field
            "query_vector": features.tolist(),
            "k": request.top_k,
            "num_candidates": request.top_k * 10
        }
        
        # Add filters if provided
        filter_clauses = []
        if request.tags:
            for tag in request.tags:
                filter_clauses.append({"match": {"tags": tag}})
        
        if request.date_from or request.date_to:
            date_range = {}
            if request.date_from:
                date_range["gte"] = request.date_from
            if request.date_to:
                date_range["lte"] = request.date_to
            filter_clauses.append({"range": {"date_taken": date_range}})
        
        query_body = {
            "knn": knn_query,
            "size": request.top_k
        }
        
        if filter_clauses:
            query_body["query"] = {
                "bool": {
                    "filter": filter_clauses
                }
            }
        
        response = es.search(index=es_index, body=query_body)
        
        # Format results
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            # Validate required Flickr metadata
            if not all([source.get('flickr_farm'), source.get('flickr_server'), 
                       source.get('id'), source.get('flickr_secret')]):
                continue  # Skip results with missing image metadata
            
            # Skip failed downloads
            if source.get('image_status') == 'download_failed':
                continue
            
            url = f"http://farm{source.get('flickr_farm')}.staticflickr.com/{source.get('flickr_server')}/{source.get('id')}_{source.get('flickr_secret')}.jpg"
            
            results.append({
                "id": source.get("id"),
                "userid": source.get("userid"),
                "title": source.get("title", "Untitled"),
                "tags": source.get("tags", ""),
                "latitude": source.get("latitude"),
                "longitude": source.get("longitude"),
                "views": source.get("views", 0),
                "date_taken": source.get("date_taken"),
                "date_uploaded": source.get("date_uploaded"),
                "accuracy": source.get("accuracy", 0),
                "flickr_secret": source.get("flickr_secret"),
                "flickr_server": source.get("flickr_server"),
                "flickr_farm": source.get("flickr_farm"),
                "url": url,
                "score": hit["_score"]
            })
        
        return {
            "results": results,
            "total": len(results),
            "took": response["took"]
        }
        
    except Exception as e:
        import traceback
        error_detail = f"Image search failed: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR in image search: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")


@app.post("/api/search/hybrid")
async def search_hybrid(request: HybridSearchRequest):
    """
    Hybrid search combining text and multi-descriptor image features
    Combines BM25 text matching with cosine similarity for multiple visual descriptors
    """
    import time
    from elasticsearch import Elasticsearch
    
    start_time = time.time()
    
    es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    es_index = os.getenv("ELASTICSEARCH_INDEX", "flickr_images")
    vgg_model = os.getenv("VGG_MODEL", "vgg16").lower()
    vgg_field = f"{vgg_model}_features"
    
    try:
        # Decode and extract ALL descriptors from image
        if "," in request.image_data:
            image_data = request.image_data.split(",")[1]
        else:
            image_data = request.image_data
        
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {str(e)}")
        
        # Open and validate image
        try:
            image_buffer = io.BytesIO(image_bytes)
            image = Image.open(image_buffer)
            image.verify()
            image_buffer.seek(0)
            image = Image.open(image_buffer)
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
        
        # Extract ALL descriptors (not just VGG)
        img_array = np.array(image)
        
        # Extract VGG features
        vgg_features = extract_vgg_features(image)
        
        # Extract CV descriptors (color, LBP, HOG, edge, SIFT)
        from utils.descriptor_extractor import (
            ColorHistogramExtractor, LBPExtractor, HOGExtractor,
            EdgeHistogramExtractor, SIFTExtractor
        )
        
        try:
            color_hist = ColorHistogramExtractor().extract(img_array)
            lbp_features = LBPExtractor().extract(img_array)
            hog_features = HOGExtractor().extract(img_array)
            edge_hist = EdgeHistogramExtractor().extract(img_array)
            sift_features = SIFTExtractor().extract(img_array)
        except Exception as e:
            print(f"Warning: CV descriptor extraction failed: {e}")
            color_hist = lbp_features = hog_features = edge_hist = sift_features = None
        
        es = Elasticsearch([f"http://{es_host}:{es_port}"])
        
        # Perform text search
        text_query = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": request.query,
                                "fields": ["title^2", "tags^3"],
                                "type": "best_fields"
                            }
                        }
                    ]
                }
            },
            "size": request.top_k * 3
        }
        
        text_results = {}
        if request.text_weight > 0:
            text_response = es.search(index=es_index, body=text_query)
            max_text_score = text_response["hits"]["max_score"] if text_response["hits"]["hits"] else 1.0
            
            for hit in text_response["hits"]["hits"]:
                image_id = hit["_source"]["id"]
                # Normalize BM25 score to 0-100%
                text_score = (hit["_score"] / max_text_score) * 100.0
                text_results[image_id] = {
                    "text_score": text_score,
                    "source": hit["_source"]
                }
        
        # Perform multi-descriptor image search
        all_results = {}
        descriptor_configs = [
            ('vgg', vgg_field, vgg_features, 1.0),
            ('color', 'color_histogram', color_hist, 1.0),
            ('lbp', 'lbp_features', lbp_features, 1.0),
            ('hog', 'hog_features', hog_features, 1.0),
            ('edge_histogram', 'edge_histogram', edge_hist, 1.0),
            ('sift', 'sift_features', sift_features, 1.0)
        ]
        
        for desc_name, field_name, features, _ in descriptor_configs:
            if features is None or len(features) == 0:
                continue
                
            knn_query = {
                "field": field_name,
                "query_vector": features.tolist(),
                "k": request.top_k * 3,
                "num_candidates": request.top_k * 10
            }
            
            query_body = {
                "knn": knn_query,
                "size": request.top_k * 3
            }
            
            try:
                response = es.search(index=es_index, body=query_body)
                
                for hit in response["hits"]["hits"]:
                    image_id = hit["_source"]["id"]
                    es_score = hit["_score"]
                    
                    # Convert ES score to cosine percentage
                    cosine_similarity = (es_score * 2.0) - 1.0
                    percentage = max(0.0, min(100.0, cosine_similarity * 100.0))
                    
                    if image_id not in all_results:
                        all_results[image_id] = {
                            "source": hit["_source"],
                            "descriptor_scores": {},
                            "text_score": text_results.get(image_id, {}).get("text_score", 0.0)
                        }
                    
                    all_results[image_id]["descriptor_scores"][desc_name] = percentage
                    
            except Exception as e:
                print(f"Warning: {desc_name} search failed: {e}")
                continue
        
        # Merge text and image results
        for image_id in text_results:
            if image_id not in all_results:
                all_results[image_id] = {
                    "source": text_results[image_id]["source"],
                    "descriptor_scores": {},
                    "text_score": text_results[image_id]["text_score"]
                }
        
        # Calculate combined scores
        combined_results = []
        for image_id, data in all_results.items():
            # Calculate weighted visual similarity - prioritize VGG if present
            desc_scores = data["descriptor_scores"]
            
            if desc_scores:
                # If VGG is present among other descriptors, give it 50% weight
                if 'vgg' in desc_scores and len(desc_scores) > 1:
                    vgg_score = desc_scores['vgg']
                    other_scores = [v for k, v in desc_scores.items() if k != 'vgg']
                    avg_other_scores = sum(other_scores) / len(other_scores) if other_scores else 0.0
                    visual_score = (vgg_score * 0.5) + (avg_other_scores * 0.5)
                else:
                    # If only VGG or no VGG, use simple average
                    visual_score = sum(desc_scores.values()) / len(desc_scores)
            else:
                visual_score = 0.0
            
            # Combine text and visual scores
            text_score = data["text_score"]
            combined_score = (visual_score * request.image_weight) + (text_score * request.text_weight)
            
            source = data["source"]
            
            # Validate required Flickr metadata
            if not all([source.get('flickr_farm'), source.get('flickr_server'), 
                       source.get('id'), source.get('flickr_secret')]):
                continue  # Skip results with missing image metadata
            
            # Skip failed downloads
            if source.get('image_status') == 'download_failed':
                continue
            
            url = f"http://farm{source.get('flickr_farm')}.staticflickr.com/{source.get('flickr_server')}/{source.get('id')}_{source.get('flickr_secret')}.jpg"
            
            # Round descriptor percentages
            descriptor_percentages = {k: round(v, 1) for k, v in desc_scores.items()}
            
            combined_results.append({
                "id": source.get("id"),
                "userid": source.get("userid"),
                "title": source.get("title", "Untitled"),
                "tags": source.get("tags", ""),
                "latitude": source.get("latitude"),
                "longitude": source.get("longitude"),
                "views": source.get("views", 0),
                "date_taken": source.get("date_taken"),
                "date_uploaded": source.get("date_uploaded"),
                "accuracy": source.get("accuracy", 0),
                "flickr_secret": source.get("flickr_secret"),
                "flickr_server": source.get("flickr_server"),
                "flickr_farm": source.get("flickr_farm"),
                "url": url,
                "score": combined_score,
                "text_match": round(text_score, 1),
                "visual_match": round(visual_score, 1),
                "descriptor_scores": descriptor_percentages,
                "global_match": round((visual_score + text_score) / 2, 1)
            })
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Calculate time taken in milliseconds
        time_taken_ms = int((time.time() - start_time) * 1000)
        
        return {
            "query": request.query,
            "results": combined_results[:request.top_k],
            "total": len(combined_results),
            "search_type": "hybrid",
            "weights": {
                "text": request.text_weight,
                "image": request.image_weight
            },
            "took": time_taken_ms
        }
        
    except Exception as e:
        import traceback
        error_detail = f"Hybrid search failed: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR in hybrid search: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")


def extract_vgg_features(image: Image.Image) -> np.ndarray:
    """Extract VGG features from an image"""
    try:
        import tensorflow as tf
        from tensorflow.keras.applications import VGG16, VGG19
        from tensorflow.keras.applications.vgg16 import preprocess_input as preprocess_vgg16
        from tensorflow.keras.applications.vgg19 import preprocess_input as preprocess_vgg19
        from tensorflow.keras.models import Model
        
        # Get model settings
        model_name = os.getenv("VGG_MODEL", "vgg16").lower()
        layer_name = os.getenv("VGG_LAYER", "fc2")
        
        # Resize and preprocess image
        image = image.resize((224, 224))
        img_array = np.array(image)
        img_array = np.expand_dims(img_array, axis=0)
        
        # Load model and extract features
        if model_name == "vgg16":
            base_model = VGG16(weights='imagenet', include_top=True)
            img_array = preprocess_vgg16(img_array)
        else:
            base_model = VGG19(weights='imagenet', include_top=True)
            img_array = preprocess_vgg19(img_array)
        
        # Extract from specified layer
        model = Model(inputs=base_model.input, outputs=base_model.get_layer(layer_name).output)
        features = model.predict(img_array, verbose=0)
        
        # Normalize features
        features = features.flatten()
        features = features / np.linalg.norm(features)
        
        return features
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature extraction failed: {str(e)}")


def extract_all_descriptors(image: Image.Image) -> dict:
    """
    Extract all visual descriptors from an image
    
    Returns:
        Dictionary with all descriptor vectors:
        - vgg_features: VGG16/19 deep features (4096-dim)
        - color_histogram: RGB color distribution (24-dim)
        - lbp_features: Local Binary Pattern texture (10-dim)
        - hog_features: Histogram of Oriented Gradients (81-dim)
        - edge_histogram: Edge orientation histogram (64-dim)
        - sift_features: SIFT aggregated features (128-dim)
    """
    try:
        # Convert PIL Image to numpy array for CV descriptors
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
        
        # Extract all features
        descriptors = {
            'vgg_features': extract_vgg_features(image),
            'color_histogram': color_extractor.extract(img_array),
            'lbp_features': lbp_extractor.extract(img_array),
            'hog_features': hog_extractor.extract(img_array),
            'edge_histogram': edge_extractor.extract(img_array),
            'sift_features': sift_extractor.extract(img_array)
        }
        
        return descriptors
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Descriptor extraction failed: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    from elasticsearch import Elasticsearch
    
    es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    es_index = os.getenv("ELASTICSEARCH_INDEX", "flickr_images")
    
    try:
        es = Elasticsearch([f"http://{es_host}:{es_port}"])
        count = es.count(index=es_index)
        cluster_health = es.cluster.health()
        
        return {
            "total_documents": count["count"],
            "index_name": es_index,
            "cluster_health": cluster_health["status"],
            "status": "ok"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error",
            "total_documents": 0
        }

# Simple search endpoint for testing
@app.get("/api/search/test")
async def test_search(query: str = "paris", top_k: int = 5):
    """Test text search endpoint"""
    from elasticsearch import Elasticsearch
    
    es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    es_index = os.getenv("ELASTICSEARCH_INDEX", "flickr_images")
    
    try:
        es = Elasticsearch([f"http://{es_host}:{es_port}"])
        
        # Simple text search
        response = es.search(
            index=es_index,
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "tags", "description"]
                    }
                },
                "size": top_k
            }
        )
        
        results = []
        for hit in response["hits"]["hits"]:
            results.append({
                "id": hit["_id"],
                "score": hit["_score"],
                "title": hit["_source"].get("title", ""),
                "tags": hit["_source"].get("tags", [])
            })
        
        return {
            "query": query,
            "total": response["hits"]["total"]["value"],
            "results": results
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
