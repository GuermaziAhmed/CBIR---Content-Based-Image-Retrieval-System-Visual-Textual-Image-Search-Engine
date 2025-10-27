from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path

from routers import search, images, index
from database import engine, Base
from config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CBIR API",
    description="Content-Based Image Retrieval System - Visual & Textual Search",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(images.router, prefix="/api", tags=["Images"])
app.include_router(index.router, prefix="/api", tags=["Index"])

# Mount static files for images
if os.path.exists(settings.IMAGE_DIR):
    app.mount("/images", StaticFiles(directory=settings.IMAGE_DIR), name="images")

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "CBIR API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "image_dir": os.path.exists(settings.IMAGE_DIR),
        "descriptor_dir": os.path.exists(settings.DESCRIPTOR_DIR),
        "index_dir": os.path.exists(settings.INDEX_DIR)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
