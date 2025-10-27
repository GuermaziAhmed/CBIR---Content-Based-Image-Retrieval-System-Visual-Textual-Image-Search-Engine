"""
Configuration for CBIR Elasticsearch Backend
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Elasticsearch
    ELASTICSEARCH_HOST: str = Field(default="elasticsearch", env="ELASTICSEARCH_HOST")
    ELASTICSEARCH_PORT: int = Field(default=9200, env="ELASTICSEARCH_PORT")
    ELASTICSEARCH_INDEX: str = Field(default="flickr_images", env="ELASTICSEARCH_INDEX")
    
    # VGG Model
    VGG_MODEL: str = Field(default="vgg16", env="VGG_MODEL")  # vgg16 or vgg19
    VGG_LAYER: str = Field(default="fc2", env="VGG_LAYER")    # fc2 or block5_pool
    
    # Directories
    IMAGE_DIR: str = Field(default="/data/images", env="IMAGE_DIR")
    MODEL_DIR: str = Field(default="/data/models", env="MODEL_DIR")
    
    # API
    API_TITLE: str = "CBIR API - Elasticsearch"
    API_VERSION: str = "2.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
