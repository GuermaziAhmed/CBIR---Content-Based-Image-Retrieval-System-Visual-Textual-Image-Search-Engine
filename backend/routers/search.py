from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import time
import base64
import io
from PIL import Image
import numpy as np

from models.schemas import SearchRequest, SearchResponse, ImageResult
from database import get_db, ImageModel
from utils.descriptor_extractor import extract_all_descriptors
from utils.faiss_search import FaissSearchEngine
from config import settings

router = APIRouter()
search_engine = FaissSearchEngine()

@router.post("/search", response_model=SearchResponse)
async def search_images(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Search for similar images using text and/or visual queries.
    
    - **query_text**: Optional text keywords
    - **image_data**: Optional base64 encoded image
    - **descriptors**: List of descriptors to use (color, lbp, hog, mpeg7)
    - **top_k**: Number of results to return
    """
    start_time = time.time()
    
    # Validate descriptors
    invalid_descriptors = [d for d in request.descriptors if d not in settings.AVAILABLE_DESCRIPTORS]
    if invalid_descriptors:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid descriptors: {invalid_descriptors}. Available: {settings.AVAILABLE_DESCRIPTORS}"
        )
    
    results = []
    
    try:
        # Image-based search
        if request.use_image and request.image_data:
            image_results = await _search_by_image(
                request.image_data,
                request.descriptors,
                request.top_k,
                db
            )
            results.extend(image_results)
        
        # Text-based search
        if request.query_text:
            text_results = await _search_by_text(
                request.query_text,
                request.top_k,
                db
            )
            
            # Combine results if both image and text
            if results:
                results = _combine_results(results, text_results, request.combine_mode)
            else:
                results = text_results
        
        # If no search criteria provided
        if not results and not request.query_text and not request.use_image:
            raise HTTPException(
                status_code=400,
                detail="Please provide either query_text or image_data"
            )
        
        # Sort by score and limit
        results = sorted(results, key=lambda x: x.score)[:request.top_k]
        
        search_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query_text=request.query_text,
            query_image="provided" if request.use_image else None,
            results=results,
            total_results=len(results),
            search_time_ms=round(search_time, 2),
            descriptors_used=request.descriptors
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


async def _search_by_image(
    image_data: str,
    descriptors: list,
    top_k: int,
    db: Session
) -> list:
    """Search using visual descriptors"""
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data.split(',')[-1])
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image_np = np.array(image)
        
        # Extract descriptors
        features = extract_all_descriptors(image_np, descriptors)
        
        # Search each descriptor index
        all_results = []
        for desc_name, desc_vector in features.items():
            if desc_vector is not None:
                indices, distances = search_engine.search(
                    desc_name,
                    desc_vector,
                    top_k * 2  # Get more to merge later
                )
                
                # Convert to ImageResult
                for idx, dist in zip(indices, distances):
                    image_db = db.query(ImageModel).filter(ImageModel.id == int(idx)).first()
                    if image_db:
                        all_results.append(ImageResult(
                            id=image_db.id,
                            filename=image_db.filename,
                            url=image_db.url,
                            score=float(dist),
                            tags=image_db.tags,
                            caption=image_db.caption,
                            width=image_db.width,
                            height=image_db.height
                        ))
        
        # Merge results from different descriptors
        merged = _merge_descriptor_results(all_results)
        return merged
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing failed: {str(e)}")


async def _search_by_text(query_text: str, top_k: int, db: Session) -> list:
    """Search using text metadata"""
    # Full-text search on tags and captions
    query = db.query(ImageModel).filter(
        (ImageModel.tags.ilike(f"%{query_text}%")) |
        (ImageModel.caption.ilike(f"%{query_text}%")) |
        (ImageModel.filename.ilike(f"%{query_text}%"))
    ).limit(top_k * 2)
    
    results = []
    for image in query.all():
        # Simple scoring based on keyword matches
        score = _calculate_text_score(query_text, image)
        results.append(ImageResult(
            id=image.id,
            filename=image.filename,
            url=image.url,
            score=score,
            tags=image.tags,
            caption=image.caption,
            width=image.width,
            height=image.height
        ))
    
    return results


def _calculate_text_score(query: str, image: ImageModel) -> float:
    """Calculate relevance score for text search"""
    score = 0.0
    query_lower = query.lower()
    
    if image.tags and query_lower in image.tags.lower():
        score += 0.3
    if image.caption and query_lower in image.caption.lower():
        score += 0.5
    if image.filename and query_lower in image.filename.lower():
        score += 0.2
    
    return 1.0 - min(score, 1.0)  # Lower is better


def _merge_descriptor_results(results: list) -> list:
    """Merge results from multiple descriptors"""
    # Group by image ID and average scores
    image_scores = {}
    for result in results:
        if result.id not in image_scores:
            image_scores[result.id] = {
                'result': result,
                'scores': []
            }
        image_scores[result.id]['scores'].append(result.score)
    
    # Average scores
    merged = []
    for img_id, data in image_scores.items():
        avg_score = np.mean(data['scores'])
        result = data['result']
        result.score = float(avg_score)
        merged.append(result)
    
    return merged


def _combine_results(image_results: list, text_results: list, mode: str) -> list:
    """Combine image and text search results"""
    if mode == "text_only":
        return text_results
    elif mode == "image_only":
        return image_results
    
    # Fusion mode: combine and re-rank
    combined = {}
    
    # Add image results
    for result in image_results:
        combined[result.id] = result
        combined[result.id].score *= 0.6  # Weight image similarity
    
    # Add text results
    for result in text_results:
        if result.id in combined:
            # Combine scores
            combined[result.id].score = (combined[result.id].score + result.score * 0.4) / 2
        else:
            combined[result.id] = result
            combined[result.id].score *= 0.4  # Weight text similarity
    
    return list(combined.values())
