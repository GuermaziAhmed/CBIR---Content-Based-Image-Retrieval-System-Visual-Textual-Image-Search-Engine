from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.schemas import IndexBuildRequest, IndexStats
from utils.build_index import IndexBuilder
from config import settings
import os
from datetime import datetime

router = APIRouter()
index_builder = IndexBuilder()

@router.post("/index/build")
async def build_index(
    request: IndexBuildRequest,
    background_tasks: BackgroundTasks
):
    """
    Build or rebuild the search indexes.
    This is a long-running operation that runs in the background.
    """
    descriptors = request.descriptors or settings.AVAILABLE_DESCRIPTORS
    
    # Start index building in background
    background_tasks.add_task(
        index_builder.build_all_indexes,
        descriptors,
        request.force_rebuild
    )
    
    return {
        "status": "started",
        "message": f"Index building started for descriptors: {descriptors}",
        "descriptors": descriptors
    }

@router.get("/index/status", response_model=IndexStats)
async def get_index_status():
    """Get current index statistics"""
    try:
        stats = index_builder.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.delete("/index/{descriptor}")
async def delete_index(descriptor: str):
    """Delete a specific descriptor index"""
    if descriptor not in settings.AVAILABLE_DESCRIPTORS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid descriptor. Available: {settings.AVAILABLE_DESCRIPTORS}"
        )
    
    index_path = os.path.join(settings.INDEX_DIR, f"{descriptor}.index")
    
    if os.path.exists(index_path):
        os.remove(index_path)
        return {"status": "deleted", "descriptor": descriptor}
    else:
        raise HTTPException(status_code=404, detail=f"Index for {descriptor} not found")
