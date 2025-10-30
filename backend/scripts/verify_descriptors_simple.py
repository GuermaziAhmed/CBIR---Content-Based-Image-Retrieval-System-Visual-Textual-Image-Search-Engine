"""Quick verification of descriptors"""
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://elasticsearch:9200'])

print("=" * 70)
print("DESCRIPTOR VERIFICATION REPORT")
print("=" * 70)

# Get total count
total_result = es.count(index='flickr_images')
total_docs = total_result['count']
print(f"\n📊 Total documents in index: {total_docs:,}")

# Check each descriptor individually
descriptors = {
    'vgg16_features': 'VGG16 (Deep Learning)',
    'color_histogram': 'Color Histogram',
    'lbp_features': 'LBP (Texture)',
    'hog_features': 'HOG (Shape)',
    'edge_histogram': 'Edge Histogram',
    'sift_features': 'SIFT (Keypoints)'
}

print("\n" + "=" * 70)
print("INDIVIDUAL DESCRIPTOR COUNTS")
print("=" * 70)

for field, name in descriptors.items():
    query = {"query": {"exists": {"field": field}}}
    result = es.count(index='flickr_images', body=query)
    count = result['count']
    percentage = (count / total_docs * 100) if total_docs > 0 else 0
    print(f"{name:25s}: {count:10,} docs ({percentage:6.2f}%)")

# Get documents with ALL descriptors
print("\n" + "=" * 70)
print("COMPLETE DOCUMENTS (ALL 6 DESCRIPTORS)")
print("=" * 70)

query_all = {
    "query": {
        "bool": {
            "must": [
                {"exists": {"field": "vgg16_features"}},
                {"exists": {"field": "color_histogram"}},
                {"exists": {"field": "lbp_features"}},
                {"exists": {"field": "hog_features"}},
                {"exists": {"field": "edge_histogram"}},
                {"exists": {"field": "sift_features"}}
            ]
        }
    }
}

result_all = es.count(index='flickr_images', body=query_all)
complete_count = result_all['count']
complete_percentage = (complete_count / total_docs * 100) if total_docs > 0 else 0

print(f"\n✅ Documents with ALL descriptors: {complete_count:,} ({complete_percentage:.2f}%)")

# Calculate missing descriptors
missing_count = total_docs - complete_count
missing_percentage = (missing_count / total_docs * 100) if total_docs > 0 else 0
print(f"❌ Documents MISSING descriptors: {missing_count:,} ({missing_percentage:.2f}%)")

# Get documents with only VGG (need other descriptors)
print("\n" + "=" * 70)
print("DOCUMENTS NEEDING ADDITIONAL DESCRIPTORS")
print("=" * 70)

query_only_vgg = {
    "query": {
        "bool": {
            "must": [
                {"exists": {"field": "vgg16_features"}}
            ],
            "must_not": [
                {"exists": {"field": "color_histogram"}}
            ]
        }
    }
}

result_only_vgg = es.count(index='flickr_images', body=query_only_vgg)
only_vgg_count = result_only_vgg['count']
print(f"\n⚠️  Documents with only VGG (missing CV descriptors): {only_vgg_count:,}")

# Sample a few complete documents
print("\n" + "=" * 70)
print("SAMPLE COMPLETE DOCUMENTS (First 3)")
print("=" * 70)

query_sample = {
    "query": {
        "bool": {
            "must": [
                {"exists": {"field": "vgg16_features"}},
                {"exists": {"field": "color_histogram"}},
                {"exists": {"field": "lbp_features"}},
                {"exists": {"field": "hog_features"}},
                {"exists": {"field": "edge_histogram"}},
                {"exists": {"field": "sift_features"}}
            ]
        }
    },
    "size": 3
}

result_sample = es.search(index='flickr_images', body=query_sample)

for i, hit in enumerate(result_sample['hits']['hits'], 1):
    doc = hit['_source']
    print(f"\n{i}. Document ID: {hit['_id']}")
    print(f"   Title: {doc.get('title', 'N/A')[:60]}")
    for field, name in descriptors.items():
        if field in doc:
            print(f"   ✅ {name:25s}: {len(doc[field]):4d} dims")
        else:
            print(f"   ❌ {name:25s}: MISSING")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total documents:        {total_docs:,}")
print(f"Complete (all 6 desc):  {complete_count:,} ({complete_percentage:.2f}%)")
print(f"Incomplete:             {missing_count:,} ({missing_percentage:.2f}%)")
print(f"Only VGG:               {only_vgg_count:,}")
print("=" * 70 + "\n")

