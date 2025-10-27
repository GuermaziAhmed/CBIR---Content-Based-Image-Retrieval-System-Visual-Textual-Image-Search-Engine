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

from config import settings

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


@app.post("/api/search/text")
async def search_by_text(request: TextSearchRequest):
    """Text-based search using tags and title"""
    from elasticsearch import Elasticsearch
    
    es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    es_index = os.getenv("ELASTICSEARCH_INDEX", "flickr_images")
    
    try:
        es = Elasticsearch([f"http://{es_host}:{es_port}"])
        
        # Build query
        must_clauses = [
            {
                "multi_match": {
                    "query": request.query,
                    "fields": ["title^2", "tags^3"],  # Boost tags more than title
                    "type": "best_fields"
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
        
        # Format results
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
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
                "score": hit["_score"]
            })
        
        return {
            "query": request.query,
            "results": results,
            "total": response["hits"]["total"]["value"],
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
    """Hybrid search combining text and image features"""
    from elasticsearch import Elasticsearch
    
    es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    es_index = os.getenv("ELASTICSEARCH_INDEX", "flickr_images")
    vgg_model = os.getenv("VGG_MODEL", "vgg16").lower()
    
    # Determine the correct field name based on model
    vgg_field = f"{vgg_model}_features"
    
    try:
        # Decode and extract VGG features
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
            
            # Verify it's a valid image
            image.verify()
            
            # Re-open after verify
            image_buffer.seek(0)
            image = Image.open(image_buffer)
            
            # Convert to RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file. Supported formats: JPEG, PNG, WebP. Error: {str(e)}")
        
        features = extract_vgg_features(image)
        
        es = Elasticsearch([f"http://{es_host}:{es_port}"])
        
        # Hybrid query combining kNN and text
        query_body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": request.query,
                                "fields": ["title^2", "tags^3"],
                                "boost": request.text_weight
                            }
                        }
                    ]
                }
            },
            "knn": {
                "field": vgg_field,  # Use model-specific field
                "query_vector": features.tolist(),
                "k": request.top_k,
                "num_candidates": request.top_k * 10,
                "boost": request.image_weight
            },
            "size": request.top_k
        }
        
        response = es.search(index=es_index, body=query_body)
        
        # Format results
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
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
            "query": request.query,
            "results": results,
            "total": len(results),
            "took": response["took"]
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
