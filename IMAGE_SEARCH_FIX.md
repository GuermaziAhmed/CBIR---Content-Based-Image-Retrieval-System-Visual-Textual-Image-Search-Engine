# ✅ Image Search Fixed - VGG Field Name Issue

## Problem
Image search was failing with error:
```
BadRequestError(400, 'search_phase_execution_exception', 
'failed to create query: field [vgg_features] does not exist in the mapping')
```

## Root Cause
**Mismatch between field names:**
- **Ingestion script** saves features as: `vgg16_features` or `vgg19_features`
- **Backend** was looking for: `vgg_features` (generic name)
- **Elasticsearch mapping** has: `vgg16_features`, `vgg19_features`, `vgg16_pool5`

## Solution
Updated the backend to use the correct field name based on the VGG model:

### Changes Made

#### 1. Image Search Endpoint (`/api/search/image`)
**Before:**
```python
knn_query = {
    "field": "vgg_features",  # ❌ Field doesn't exist
    "query_vector": features.tolist(),
    ...
}
```

**After:**
```python
vgg_model = os.getenv("VGG_MODEL", "vgg16").lower()
vgg_field = f"{vgg_model}_features"  # ✅ vgg16_features or vgg19_features

knn_query = {
    "field": vgg_field,  # ✅ Correct field name
    "query_vector": features.tolist(),
    ...
}
```

#### 2. Hybrid Search Endpoint (`/api/search/hybrid`)
Same fix applied - now uses `{model}_features` based on VGG_MODEL env variable.

---

## Field Name Mapping

| VGG_MODEL | Field Name | Dimensions | Description |
|-----------|------------|------------|-------------|
| vgg16 | `vgg16_features` | 4096 | VGG16 FC2 layer |
| vgg19 | `vgg19_features` | 4096 | VGG19 FC2 layer |
| vgg16 (pool5) | `vgg16_pool5` | 512 | VGG16 block5_pool |

---

## Environment Variable

The backend now reads the `VGG_MODEL` environment variable to determine which field to query:

```bash
# In backend/.env or docker-compose.yml
VGG_MODEL=vgg16  # Default
# or
VGG_MODEL=vgg19
```

**Current setting:** `vgg16` (from backend/.env)

---

## Elasticsearch Index Mapping

The index already has the correct fields defined:

```python
# From elasticsearch_mapping.py
"vgg16_features": {
    "type": "dense_vector",
    "dims": 4096,
    "index": True,
    "similarity": "cosine"
},

"vgg19_features": {
    "type": "dense_vector",
    "dims": 4096,
    "index": True,
    "similarity": "cosine"
},

"vgg16_pool5": {
    "type": "dense_vector",
    "dims": 512,
    "index": True,
    "similarity": "cosine"
}
```

---

## Verification

### 1. Check if documents have VGG features
```bash
curl http://localhost:9200/flickr_images/_search?size=1 | jq
```

Look for `vgg16_features` array in the response.

### 2. Check backend logs
```bash
docker-compose logs backend | grep "vgg"
```

### 3. Test image search
1. Go to http://localhost:3000
2. Upload an image
3. Click Search
4. Should see visually similar images (not an error)

---

## How Image Search Works Now

1. **Frontend** uploads image (base64)
   ↓
2. **Backend** receives image
   ↓
3. **Backend** extracts VGG features using TensorFlow
   ↓
4. **Backend** determines field name: `{VGG_MODEL}_features`
   ↓
5. **Elasticsearch** performs kNN search on `vgg16_features`
   ↓
6. **Backend** returns similar images
   ↓
7. **Frontend** displays results

---

## Important Notes

### Data Must Be Ingested with VGG Features
For image search to work, your data must have been ingested using the ingestion script:

```bash
cd scripts
python ingest_flickr_data.py --csv ../data/csv/sample_photo_metadata.csv
```

This script:
- Downloads images from Flickr
- Extracts VGG features
- Saves features to `vgg16_features` field
- Deletes images (unless --keep-images flag)

### Check if Your Data Has Features
```bash
# Count documents with VGG features
curl -X GET "localhost:9200/flickr_images/_count" -H 'Content-Type: application/json' -d'
{
  "query": {
    "exists": {
      "field": "vgg16_features"
    }
  }
}
'
```

**Expected result:** Should match total document count (160 in your case)

---

## Troubleshooting

### Still Getting "Field Does Not Exist" Error?

1. **Check VGG_MODEL setting:**
   ```bash
   docker-compose exec backend printenv | grep VGG
   ```
   Should show: `VGG_MODEL=vgg16`

2. **Check if data has features:**
   ```bash
   curl http://localhost:9200/flickr_images/_search?size=1 | jq '._source.vgg16_features'
   ```
   Should show array of 4096 numbers

3. **Verify field exists in mapping:**
   ```bash
   curl http://localhost:9200/flickr_images/_mapping | jq
   ```
   Should show `vgg16_features` field with type `dense_vector`

### Data Was Ingested Without Features?

If your 160 documents don't have VGG features, you'll need to re-ingest:

```bash
# Delete old index
curl -X DELETE http://localhost:9200/flickr_images

# Recreate index with mapping
cd scripts
python elasticsearch_mapping.py

# Re-ingest data with VGG extraction
python ingest_flickr_data.py --csv ../data/csv/sample_photo_metadata.csv --limit 160
```

---

## Summary

✅ **Fixed:** Backend now uses correct field name (`vgg16_features`)  
✅ **Dynamic:** Field name adapts to VGG_MODEL setting  
✅ **Compatible:** Works with existing Elasticsearch mapping  
✅ **Restart:** Backend restarted and running successfully  

**Image search should now work!** Try uploading an image in the frontend. 🚀

---

## Next Steps

1. Test image upload and search in frontend
2. Verify results are visually similar
3. Try hybrid search (image + text)
4. Check similarity scores

If you still get errors, check if your 160 documents have `vgg16_features` arrays populated.
