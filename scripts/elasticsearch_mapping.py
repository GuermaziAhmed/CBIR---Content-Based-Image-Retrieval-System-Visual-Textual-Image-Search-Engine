"""
Elasticsearch Index Mapping for Flickr Images with VGG Features
"""

FLICKR_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "tag_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            # Image identifiers
            "id": {"type": "keyword"},
            "userid": {"type": "keyword"},
            
            # Text fields
            "title": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "tags": {
                "type": "text",
                "analyzer": "tag_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            
            # Geolocation
            "latitude": {"type": "float"},
            "longitude": {"type": "float"},
            "location": {"type": "geo_point"},  # For geo queries
            "accuracy": {"type": "integer"},
            
            # Metrics
            "views": {"type": "integer"},
            
            # Dates
            "date_taken": {"type": "text"},
            "date_taken_parsed": {"type": "date"},
            "date_uploaded": {"type": "text"},
            "date_uploaded_parsed": {"type": "date"},
            "indexed_at": {"type": "date"},
            
            # Flickr metadata
            "flickr_secret": {"type": "keyword"},
            "flickr_server": {"type": "keyword"},
            "flickr_farm": {"type": "integer"},
            
            # URLs and paths
            "image_url": {"type": "keyword"},
            "local_path": {"type": "keyword"},
            "image_status": {"type": "keyword"},  # pending_download, downloaded, processed, failed
            
            # VGG Features - Dense vector for kNN search
            "vgg16_features": {
                "type": "dense_vector",
                "dims": 4096,  # VGG16 FC2 layer
                "index": True,
                "similarity": "cosine"  # or "l2_norm", "dot_product"
            },
            
            "vgg19_features": {
                "type": "dense_vector",
                "dims": 4096,  # VGG19 FC2 layer
                "index": True,
                "similarity": "cosine"
            },
            
            # Color Histogram - RGB color distribution
            "color_histogram": {
                "type": "dense_vector",
                "dims": 24,  # 8 bins * 3 channels (RGB)
                "index": True,
                "similarity": "cosine"
            },
            
            # LBP Features - Local Binary Pattern texture descriptor
            "lbp_features": {
                "type": "dense_vector",
                "dims": 10,  # Uniform LBP (n_points + 2)
                "index": True,
                "similarity": "cosine"
            },
            
            # HOG Features - Histogram of Oriented Gradients
            "hog_features": {
                "type": "dense_vector",
                "dims": 81,  # Depends on image size and parameters
                "index": True,
                "similarity": "cosine"
            },
            
            # Edge Histogram - Edge orientation distribution
            "edge_histogram": {
                "type": "dense_vector",
                "dims": 64,  # Edge orientations in different directions
                "index": True,
                "similarity": "cosine"
            },
            
            # SIFT Features - Scale-Invariant Feature Transform
            "sift_features": {
                "type": "dense_vector",
                "dims": 64,  # PCA-reduced from 128 to 64 dimensions
                "index": True,
                "similarity": "cosine"
            },
            
            # Alternative: VGG block5_pool (smaller, faster)
            "vgg16_pool5": {
                "type": "dense_vector",
                "dims": 512,  # 512 * 7 * 7 = 25088, but we'll use global average pooling
                "index": True,
                "similarity": "cosine"
            },
            
            # Image properties
            "width": {"type": "integer"},
            "height": {"type": "integer"},
            "file_size": {"type": "long"},
            "format": {"type": "keyword"},
            
            # Metadata
            "source": {"type": "keyword"},
            "processing_time": {"type": "float"},
            "error_message": {"type": "text"}
        }
    }
}


def create_index(es_client, index_name="flickr_images"):
    """
    Create Elasticsearch index with VGG feature mapping
    """
    try:
        if es_client.indices.exists(index=index_name):
            print(f"Index '{index_name}' already exists")
            return False
        
        es_client.indices.create(
            index=index_name,
            body=FLICKR_INDEX_MAPPING
        )
        print(f"✅ Created index: {index_name}")
        return True
    except Exception as e:
        print(f"❌ Error creating index: {e}")
        return False


def delete_index(es_client, index_name="flickr_images"):
    """
    Delete existing index (use with caution!)
    """
    try:
        if es_client.indices.exists(index=index_name):
            es_client.indices.delete(index=index_name)
            print(f"🗑️ Deleted index: {index_name}")
            return True
        print(f"Index '{index_name}' does not exist")
        return False
    except Exception as e:
        print(f"❌ Error deleting index: {e}")
        return False


def get_index_stats(es_client, index_name="flickr_images"):
    """
    Get index statistics
    """
    try:
        stats = es_client.indices.stats(index=index_name)
        count = es_client.count(index=index_name)
        
        return {
            "document_count": count['count'],
            "store_size": stats['_all']['primaries']['store']['size_in_bytes'],
            "index_size_mb": stats['_all']['primaries']['store']['size_in_bytes'] / (1024 * 1024)
        }
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return None


if __name__ == "__main__":
    from elasticsearch import Elasticsearch
    
    # Connect to Elasticsearch
    es = Elasticsearch(["http://localhost:9200"])
    
    # Check connection
    if not es.ping():
        print("❌ Cannot connect to Elasticsearch")
        exit(1)
    
    print("✅ Connected to Elasticsearch")
    print(f"Cluster: {es.info()['cluster_name']}")
    print(f"Version: {es.info()['version']['number']}")
    
    # Create index
    create_index(es)
    
    # Get stats
    stats = get_index_stats(es)
    if stats:
        print(f"\n📊 Index Stats:")
        print(f"  Documents: {stats['document_count']}")
        print(f"  Size: {stats['index_size_mb']:.2f} MB")
