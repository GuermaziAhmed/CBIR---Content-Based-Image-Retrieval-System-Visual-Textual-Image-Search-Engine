"""
Demo script to test the CBIR system
Run this after building the indexes
"""

import requests
import base64
from pathlib import Path
import json

API_BASE = "http://localhost:8000"

def test_health():
    """Test API health"""
    print("🔍 Testing API health...")
    response = requests.get(f"{API_BASE}/health")
    print(f"✅ Health check: {response.json()}")
    print()

def test_text_search(query: str):
    """Test text search"""
    print(f"🔍 Searching for: '{query}'")
    response = requests.post(f"{API_BASE}/api/search", json={
        "query_text": query,
        "descriptors": ["color", "lbp"],
        "top_k": 10
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total_results']} results in {data['search_time_ms']}ms")
        for i, result in enumerate(data['results'][:5], 1):
            print(f"   {i}. {result['filename']} (score: {result['score']:.4f})")
    else:
        print(f"❌ Error: {response.json()}")
    print()

def test_image_search(image_path: str):
    """Test image search"""
    print(f"🔍 Searching with image: {image_path}")
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()
    
    response = requests.post(f"{API_BASE}/api/search", json={
        "image_data": f"data:image/jpeg;base64,{image_data}",
        "use_image": True,
        "descriptors": ["color", "lbp", "hog"],
        "top_k": 10
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total_results']} results in {data['search_time_ms']}ms")
        for i, result in enumerate(data['results'][:5], 1):
            print(f"   {i}. {result['filename']} (score: {result['score']:.4f})")
    else:
        print(f"❌ Error: {response.json()}")
    print()

def test_list_images():
    """Test listing images"""
    print("🔍 Listing images...")
    response = requests.get(f"{API_BASE}/api/images", params={"limit": 5})
    
    if response.status_code == 200:
        images = response.json()
        print(f"✅ Total images: {len(images)}")
        for img in images:
            print(f"   - {img['filename']}")
    else:
        print(f"❌ Error: {response.json()}")
    print()

def test_random_images():
    """Test getting random images"""
    print("🔍 Getting random images...")
    response = requests.get(f"{API_BASE}/api/images/random", params={"count": 5})
    
    if response.status_code == 200:
        images = response.json()
        print(f"✅ Random images:")
        for img in images:
            print(f"   - {img['filename']}")
    else:
        print(f"❌ Error: {response.json()}")
    print()

def test_index_stats():
    """Test getting index statistics"""
    print("🔍 Getting index stats...")
    response = requests.get(f"{API_BASE}/api/index/status")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Index Statistics:")
        print(f"   Total images: {stats['total_images']}")
        print(f"   Index size: {stats['index_size_mb']} MB")
        print(f"   Indexed descriptors:")
        for desc, info in stats['indexed_descriptors'].items():
            print(f"      - {desc}: {info['total_vectors']} vectors, dim={info['dimension']}")
    else:
        print(f"❌ Error: {response.json()}")
    print()

def main():
    print("=" * 60)
    print("CBIR System Demo")
    print("=" * 60)
    print()
    
    # Test health
    test_health()
    
    # Test index stats
    test_index_stats()
    
    # Test listing images
    test_list_images()
    
    # Test random images
    test_random_images()
    
    # Test text search
    test_text_search("cat")
    test_text_search("dog")
    
    # Test image search (if you have an image)
    # Uncomment and update path:
    # image_path = "data/images/sample.jpg"
    # if Path(image_path).exists():
    #     test_image_search(image_path)
    
    print("=" * 60)
    print("✅ Demo completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
