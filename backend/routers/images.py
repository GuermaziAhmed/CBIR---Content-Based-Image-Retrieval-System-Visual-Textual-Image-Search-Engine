from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from models.schemas import ImageMetadata
from database import get_db, ImageModel

router = APIRouter()

@router.get("/images", response_model=List[ImageMetadata])
async def list_images(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of all images with metadata"""
    images = db.query(ImageModel).offset(skip).limit(limit).all()
    return images

@router.get("/image/{image_id}", response_model=ImageMetadata)
async def get_image(image_id: int, db: Session = Depends(get_db)):
    """Get specific image metadata by ID"""
    image = db.query(ImageModel).filter(ImageModel.id == image_id).first()
    
    if not image:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
    
    return image

@router.get("/images/search/tags")
async def search_by_tags(
    tags: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Search images by tags"""
    images = db.query(ImageModel).filter(
        ImageModel.tags.ilike(f"%{tags}%")
    ).limit(limit).all()
    
    return images

@router.get("/images/random")
async def get_random_images(count: int = 10, db: Session = Depends(get_db)):
    """Get random images for exploration"""
    from sqlalchemy import func
    images = db.query(ImageModel).order_by(func.random()).limit(count).all()
    return images
