from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://cbir_user:cbir_password@db:5432/cbir_db"
    
    # Directories
    IMAGE_DIR: str = "/data/images"
    DESCRIPTOR_DIR: str = "/data/descriptors"
    INDEX_DIR: str = "/data/indexes"
    
    # Search Settings
    DEFAULT_TOP_K: int = 50
    MAX_TOP_K: int = 200
    
    # Descriptor Settings
    AVAILABLE_DESCRIPTORS: list = ["color", "lbp", "hog", "mpeg7"]
    DEFAULT_DESCRIPTORS: list = ["color", "lbp"]
    
    # Image Processing
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".bmp"}
    THUMBNAIL_SIZE: tuple = (256, 256)
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Ensure directories exist
Path(settings.IMAGE_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.DESCRIPTOR_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.INDEX_DIR).mkdir(parents=True, exist_ok=True)
