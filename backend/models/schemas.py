from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Request Models
class SearchRequest(BaseModel):
    query_text: Optional[str] = Field(None, description="Text query (keywords)")
    image_data: Optional[str] = Field(None, description="Base64 encoded image")
    use_image: bool = Field(False, description="Whether to use image for search")
    descriptors: List[str] = Field(["color", "lbp"], description="List of descriptors to use")
    top_k: int = Field(50, ge=1, le=200, description="Number of results to return")
    combine_mode: str = Field("fusion", description="How to combine text+image: 'fusion', 'text_only', 'image_only'")

class IndexBuildRequest(BaseModel):
    force_rebuild: bool = Field(False, description="Force rebuild even if index exists")
    descriptors: Optional[List[str]] = Field(None, description="Specific descriptors to rebuild")

# Response Models
class ImageResult(BaseModel):
    id: int
    filename: str
    url: str
    score: float
    tags: Optional[str] = None
    caption: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

class SearchResponse(BaseModel):
    query_text: Optional[str] = None
    query_image: Optional[str] = None
    results: List[ImageResult]
    total_results: int
    search_time_ms: float
    descriptors_used: List[str]

class ImageMetadata(BaseModel):
    id: int
    filename: str
    url: str
    tags: Optional[str] = None
    caption: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    descriptors_available: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class IndexStats(BaseModel):
    total_images: int
    indexed_descriptors: dict
    index_size_mb: float
    last_build: Optional[datetime] = None

class HealthResponse(BaseModel):
    status: str
    database: str
    image_dir: bool
    descriptor_dir: bool
    index_dir: bool
