# CBIR - Content-Based Image Retrieval System

**Elasticsearch + VGG Deep Learning | Flickr Dataset | Visual Search Engine**

---

##  Features

### Core Features
- **Visual Search**: Upload an image and find similar images using VGG16/VGG19 deep learning
- **Multi-Descriptor Search**: Combine 6 visual descriptors (VGG, Color, LBP, HOG, Edge Histogram, SIFT) for superior accuracy
- **Individual Match Scores**: See how well each descriptor matches (VGG 82%, Color 91%, LBP 65%, HOG 73%, Edge 78%, SIFT 68%)
- **Text Search**: Fuzzy text search with typo tolerance (e.g., "mooon" finds "moon")
- **Hybrid Search**: Combine visual + text queries with automatic VGG prioritization
- **Smart Filtering**: Automatically excludes broken images and failed downloads

### User Interface
- **Clean Design**: Simplified interface with descriptor-based controls
- **Rich Metadata**: Display tags, views, dates, and similarity scores
- **Descriptor Controls**: Enable/disable individual descriptors (VGG, Color, LBP, HOG, Edge, SIFT)
- **Real-time Results**: Shows query timing and result count
- **Tag Visualization**: Colored badges for better tag readability

### Technical Features
- **90% Disk Savings**: Auto-delete images after feature extraction
- **Scalable**: Handles millions of images with Elasticsearch kNN
- **VGG Auto-Prioritization**: Automatically gives VGG 50% weight when combined with other descriptors
- **Resumable Processing**: Use --offset and --limit for interruptible large-scale ingestion
- **Parallel Processing**: Multi-worker support for 8-20x faster descriptor extraction
- **GPU Acceleration**: TensorFlow auto-detects GPU for 10-50x faster processing
- **Fuzzy Text Search**: 3-strategy matching (exact, fuzzy AUTO with 1-2 typos, phrase with slop)

---

##  Architecture

```
Frontend (Next.js)  Backend (FastAPI)  Elasticsearch + kNN
                                          Logstash (CSV ingestion)
                                          VGG Feature Extractor
```

---

##  Tech Stack

- **Frontend**: Next.js 14, React, TailwindCSS
- **Backend**: FastAPI, Python 3.11
- **Search Engine**: Elasticsearch 8.11 with kNN plugin (cosine similarity)
- **Deep Learning**: VGG16/VGG19 (TensorFlow 2.15, GPU support)
- **Computer Vision**: OpenCV, scikit-image
- **Data Pipeline**: Pandas, tqdm
- **Deployment**: Docker Compose
- **Visual Descriptors**: 
  - **VGG16/19** (4096-dim deep features, L2 normalized)
  - **Color Histogram** (24-dim RGB distribution, L1 normalized for probability)
  - **LBP** (10-dim uniform texture patterns, L2 normalized)
  - **HOG** (81-dim shape gradients, 9 orientations, L2 normalized)
  - **Edge Histogram** (64-dim MPEG-7 style edge distribution, L2 normalized)
  - **SIFT** (128-dim keypoint features, RootSIFT + mean+std pooling)

---

##  Quick Start

### Prerequisites
- Docker Desktop with 8GB+ RAM
- 20GB+ disk space

### Installation (3 Steps)

```powershell
# 1. Start Elasticsearch
docker-compose up -d elasticsearch
Start-Sleep -Seconds 60

# 2. Create index and ingest data (with GPU acceleration if available)
cd scripts
pip install -r requirements.txt
python elasticsearch_mapping.py

# Ingest first 1 million images with resumable processing
python ingest_flickr_data.py `
  --csv ..\data\csv\photo_metadata.csv `
  --limit 1000000 `
  --batch-size 2000 `
  --workers 24

# 3. Add all descriptors (Color, LBP, HOG, Edge, SIFT) with parallel processing
cd ..
docker-compose exec backend python scripts/add_all_descriptors.py `
  --host elasticsearch `
  --workers 16 `
  --batch-size 50

# 4. Start application
docker-compose up -d backend frontend
```

**Access:** http://localhost:3000

**Resume if interrupted:**
```powershell
# Resume ingestion from document 500,000
python ingest_flickr_data.py --offset 500000 --limit 500000

# Resume descriptor extraction from document 500,000
docker-compose exec backend python scripts/add_all_descriptors.py `
  --host elasticsearch `
  --offset 500000 `
  --workers 16
```

---

###  Frontend Features

### Search Modes

1. **Text Search** (with Fuzzy Matching)
   - Search by tags: `sunset, beach, ocean`
   - Typo tolerance: `mooon` finds `moon`, `paryis` finds `paris`
   - 3-strategy matching: exact, fuzzy (AUTO 1-2 typos), phrase (slop=2)

2. **Visual Search** (Multi-Descriptor)
   - Upload an image
   - Enable/disable individual descriptors (VGG, Color, LBP, HOG, Edge, SIFT)
   - Automatic VGG prioritization (50% weight when combined)
   - See individual match scores for each descriptor
   - Results show complete similarity breakdown

3. **Hybrid Search**
   - Upload image + enter text
   - Combines visual similarity (50%) + text relevance (50%)
   - VGG gets 50% of visual score, other descriptors share remaining 50%

### Descriptor Controls

Enable/disable any combination of 6 descriptors:
- **VGG** 🧠: Deep semantic similarity
- **Color** 🎨: RGB color distribution matching  
- **LBP** 📊: Texture pattern similarity
- **HOG** ⚡: Shape and edge orientation
- **Edge** 🎬: MPEG-7 edge histogram
- **SIFT** 🔍: Keypoint-based local features

### Result Display

Each image shows:
- Title and tags (colored badges)
- Similarity scores for each enabled descriptor
- Global match percentage (average of all descriptors)
- View count (formatted: 1K, 1M)
- Query timing (e.g., "150 results in 245ms")

---

##  Project Structure

```
CBIR/
 docker-compose.yml              # Main Docker configuration
 README.md                       # This file

 backend/                        # FastAPI backend
    main.py                    # API server
    Dockerfile                 # Backend container
    requirements.txt           # Python dependencies

 frontend/                       # Next.js frontend
    app/page.tsx               # Main search interface
    Dockerfile                 # Frontend container
    package.json               # Node dependencies

 scripts/                        # Data ingestion pipeline
    elasticsearch_mapping.py   # Create ES index
    vgg_extractor.py           # VGG feature extraction
    ingest_flickr_data.py      # Complete ingestion pipeline
    requirements.txt           # Python dependencies

 logstash/                       # Logstash configuration
    pipeline/
        flickr-csv.conf        # CSV parsing pipeline

 data/
     csv/                        # Place your CSV here
        sample_photo_metadata.csv
     temp/                       # Temporary images (auto-deleted)
```

---

##  CSV Data Format

Your CSV file must have these columns:

```csv
id,userid,title,tags,latitude,longitude,views,date_taken,date_uploaded,accuracy,flickr_secret,flickr_server,flickr_farm
5133463568,78697380@N00,"Tunisi 2010","{tunisia,carthage}",36.85,10.33,6,"2010-10-23 11:50:06","2010-10-31 21:42:28",14,002f695b15,1152,2
```

**Image URL Format:**
```
http://farm{flickr_farm}.staticflickr.com/{flickr_server}/{id}_{flickr_secret}.jpg

Example:
http://farm2.staticflickr.com/1152/5133463568_002f695b15.jpg
```

---

##  Disk Space Management

### Default Mode: Auto-Delete Images (90% Savings) 

```powershell
# Images are automatically deleted after feature extraction
python ingest_flickr_data.py --csv photo_metadata.csv

# Storage for 1 million images:
# - Elasticsearch: 20 GB (features + metadata)
# - Local images: 0 GB (deleted)
# - Total: 20 GB
```

### Optional: Keep Downloaded Images

```powershell
# Use --keep-images flag to preserve images
python ingest_flickr_data.py --csv photo_metadata.csv --keep-images

# Storage for 1 million images:
# - Elasticsearch: 20 GB
# - Local images: 200 GB
# - Total: 220 GB
```

** Recommendation:** Use default mode (without `--keep-images`) to save 90% disk space!

---

##  Configuration

### Ingestion Parameters

```powershell
python scripts/ingest_flickr_data.py `
  --csv data/csv/photo_metadata.csv `    # CSV file path
  --es-host localhost `                  # Elasticsearch host
  --es-port 9200 `                       # Elasticsearch port
  --model vgg16 `                        # VGG model (vgg16 or vgg19)
  --layer fc2 `                          # Feature layer (fc2 or block5_pool)
  --batch-size 2000 `                    # Batch size (GPU: 2000-4000, CPU: 1000-1500)
  --workers 24 `                         # Parallel workers (GPU: 24-32, CPU: 16)
  --limit 1000000 `                      # Limit images (optional)
  --offset 0 `                           # Skip first N images (for resuming)
  --keep-images                          # Keep images (optional, uses 10x more disk)
```

### Descriptor Extraction Parameters

```powershell
docker-compose exec backend python scripts/add_all_descriptors.py `
  --host elasticsearch `                 # Elasticsearch host
  --port 9200 `                          # Elasticsearch port
  --index flickr_images `                # Index name
  --batch-size 50 `                      # Documents per scroll batch
  --workers 16 `                         # Parallel workers (8-24 recommended)
  --offset 0 `                           # Skip first N documents (for resuming)
  --limit 1000000 `                      # Max documents to process (optional)
  --force                                # Reprocess all (default: skip existing)
```

### VGG Model Options

| Model | Layer | Dimensions | Speed | Use Case |
|-------|-------|------------|-------|----------|
| VGG16 | fc2 | 4096 | Fast | General purpose (recommended) |
| VGG19 | fc2 | 4096 | Slower | Higher accuracy |
| VGG16 | block5_pool | 512 | Fastest | Large datasets (less accurate) |

---

##  Docker Commands

### Start Services

```powershell
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d elasticsearch
docker-compose up -d backend frontend

# View logs
docker-compose logs -f backend
docker-compose logs -f elasticsearch
```

### Stop Services

```powershell
# Stop all services
docker-compose down

# Stop and remove volumes ( WARNING: deletes all data)
docker-compose down -v
```

### Check Status

```powershell
# Check running containers
docker-compose ps

# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Check document count
curl http://localhost:9200/flickr_images/_count
```

---

##  API Examples

### Visual Search (Similar Images)

```powershell
# Using curl
curl -X POST http://localhost:8000/api/search/visual `
  -F "image=@query.jpg" `
  -F "top_k=10"
```

### Text Search (Tags/Titles)

```powershell
curl -X POST http://localhost:8000/api/search/text `
  -H "Content-Type: application/json" `
  -d '{
    "query": "paris eiffel tower",
    "top_k": 10
  }'
```

### Geo Search (Location)

```powershell
curl -X POST http://localhost:8000/api/search/geo `
  -H "Content-Type: application/json" `
  -d '{
    "lat": 48.858370,
    "lon": 2.294481,
    "radius": "10km",
    "top_k": 20
  }'
```

### Hybrid Search (Combined)

```powershell
curl -X POST http://localhost:8000/api/search/hybrid `
  -F "image=@query.jpg" `
  -F "query_text=paris" `
  -F "lat=48.85" `
  -F "lon=2.29" `
  -F "radius=50km" `
  -F "top_k=10"
```

---

##  Troubleshooting

###  Elasticsearch Won't Start

**Problem:** Docker container exits immediately

**Solution:**
```powershell
# Increase Docker memory to 8GB minimum
# Docker Desktop  Settings  Resources  Memory  8GB

# Clean restart
docker-compose down -v
docker-compose up -d elasticsearch
```

---

###  Connection Refused

**Problem:** `Connection refused to localhost:9200`

**Solution:**
```powershell
# Wait for Elasticsearch (can take 60-120 seconds)
Start-Sleep -Seconds 120

# Check if running
docker ps | findstr elasticsearch

# Check logs for errors
docker-compose logs elasticsearch
```

---

###  Out of Memory During Ingestion

**Problem:** Python process killed or crashes

**Solution:**
```powershell
# Reduce batch size and workers
python ingest_flickr_data.py `
  --csv data.csv `
  --batch-size 20 `
  --workers 2
```

---

###  Images Not Downloading

**Problem:** Many 404 errors during download

**Solution:**
```powershell
# Some Flickr images may be deleted (normal, <10% error rate is OK)

# Verify CSV format
Get-Content data\csv\photo_metadata.csv -Head 5

# Check flickr_secret, flickr_server, flickr_farm columns exist
```

---

##  Performance

### Processing Speed (VGG Extraction)

| Hardware | Speed | Time for 10K images | Time for 1M images |
|----------|-------|---------------------|---------------------|
| CPU (8 cores) | ~30-50 images/sec | ~3-5 hours | ~6-9 days |
| GPU (NVIDIA) | ~200-1500 images/sec | ~7-30 minutes | ~11-80 hours |

**GPU Optimization:**
- Batch size: 2000-4000 (GPU), 1000-1500 (CPU)
- Workers: 24-32 (GPU), 16 (CPU)
- Expected speedup: 10-50x over CPU

### Descriptor Extraction Speed (5 CV descriptors)

| Configuration | Speed | Time for 100K images |
|--------------|-------|---------------------|
| 1 worker (sequential) | ~5-10 images/min | ~170-330 hours |
| 8 workers (default) | ~40-80 images/min | ~20-40 hours |
| 16 workers (high) | ~80-150 images/min | ~11-20 hours |
| 24 workers (max) | ~120-200 images/min | ~8-14 hours |

### Search Performance

- **Multi-Descriptor kNN**: < 300ms for top-50 results (6 descriptors)
- **Text Search (Fuzzy)**: < 100ms  
- **Hybrid Search**: < 400ms
- **Single Descriptor**: < 100ms

### Storage Requirements

| Images | Features Only | With Images | Savings |
|--------|--------------|-------------|---------|
| 10K | 200 MB | 2 GB | 90% |
| 100K | 2 GB | 20 GB | 90% |
| 1M | 20 GB | 220 GB | 90% |

**Feature sizes per image:**
- VGG16: 16 KB (4096 × 4 bytes)
- Color: 96 bytes (24 × 4 bytes)
- LBP: 40 bytes (10 × 4 bytes)
- HOG: 324 bytes (81 × 4 bytes)
- Edge: 256 bytes (64 × 4 bytes)
- SIFT: 512 bytes (128 × 4 bytes)
- Metadata: ~2 KB
- **Total**: ~19 KB per image

### Optimization Tips

```powershell
# Use RAM disk for ultra-fast processing (Windows)
python ingest_flickr_data.py `
  --csv data.csv `
  --temp-dir R:\cbir_temp

# Increase batch size (requires more RAM)
python ingest_flickr_data.py `
  --csv data.csv `
  --batch-size 500 `
  --workers 16
```

---

##  Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Search interface |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Elasticsearch** | http://localhost:9200 | Search engine |
| **Kibana** (optional) | http://localhost:5601 | Analytics dashboard |

---

##  System Requirements

### Minimum Requirements
- **OS**: Windows 10+, Linux, or macOS
- **Docker Desktop**: 20+
- **RAM**: 8GB
- **Disk**: 20GB free
- **CPU**: 4 cores

### Recommended for Production
- **RAM**: 16GB+
- **Disk**: 100GB+ SSD
- **CPU**: 8+ cores
- **GPU**: NVIDIA GPU with CUDA (optional, 10x faster)

### For Development
- **Python**: 3.11+
- **Node.js**: 18+
- **Git**: Latest

---

##  Use Cases

 **E-commerce**: Visual product search  
 **Media Libraries**: Find similar photos/videos  
 **Content Moderation**: Duplicate detection  
 **Research**: Computer vision experiments  
 **Travel Apps**: Geo-tagged image discovery  
 **Social Media**: Image recommendation systems

---

##  Documentation

- **API Documentation**: http://localhost:8000/docs (when running)
- **Elasticsearch kNN**: https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html
- **VGG Networks**: https://arxiv.org/abs/1409.1556
- **TensorFlow Keras**: https://www.tensorflow.org/api_docs/python/tf/keras/applications

---

##  Quick Test

Test with real data (1M images):

```powershell
# 1. Start Elasticsearch
docker-compose up -d elasticsearch
Start-Sleep -Seconds 60

# 2. Create index & ingest 1M images (with GPU: ~1-2 hours, CPU: ~6-9 hours)
cd scripts
pip install -r requirements.txt
python elasticsearch_mapping.py

python ingest_flickr_data.py `
  --csv ..\data\csv\photo_metadata.csv `
  --limit 1000000 `
  --batch-size 2000 `
  --workers 24

# 3. Add all descriptors (with 16 workers: ~11-20 hours)
cd ..
docker-compose exec backend python scripts/add_all_descriptors.py `
  --host elasticsearch `
  --workers 16 `
  --batch-size 50 `
  --limit 1000000

# 4. Verify descriptors
docker-compose exec backend python scripts/verify_descriptors_simple.py

# 5. Start application
docker-compose up -d backend frontend

# 6. Open browser
Start-Process http://localhost:3000
```

 **Done!** Upload an image and see all 6 descriptor scores.

### If Processing Gets Interrupted

```powershell
# Resume VGG ingestion from 500K
python ingest_flickr_data.py --offset 500000 --limit 500000

# Resume descriptor extraction from 500K
docker-compose exec backend python scripts/add_all_descriptors.py `
  --host elasticsearch `
  --offset 500000 `
  --workers 16
```

---

##  Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

##  License

MIT License - See LICENSE file for details

---

##  Need Help?

**Common Solutions:**
1. 🐘 **Elasticsearch won't start** → Increase Docker RAM to 8GB
2. 🔌 **Connection refused** → Wait 60-120 seconds after starting
3. 💾 **Out of memory** → Reduce `--batch-size` to 1000 and `--workers` to 16
4. 📷 **Images fail to download** → Check CSV format (< 10% errors OK, failed downloads are automatically filtered)
5. 📊 **Only VGG scores showing** → Run `add_all_descriptors.py` to extract other descriptors
6. ⏸️ **Processing interrupted** → Use `--offset` to resume from where you left off
7. 🐍 **Module not found** → `docker-compose build backend` to rebuild with all dependencies

**Verify Your Setup:**
```powershell
# Check how many documents have all 6 descriptors
docker-compose exec backend python scripts/verify_descriptors_simple.py

# Expected output:
# ✅ Documents with ALL descriptors: 920,503 (66.67%)
# ❌ Documents MISSING descriptors: 46,252 (33.33%)
```

**Debugging:**
```powershell
# View all logs
docker-compose logs -f

# Check Elasticsearch specifically
docker-compose logs elasticsearch | Select-String "error"

# Check backend errors
docker-compose logs backend | Select-String "ERROR"

# Test connections
curl http://localhost:9200           # Elasticsearch
curl http://localhost:8000/health    # Backend
curl http://localhost:3000           # Frontend

# Count documents
curl http://localhost:9200/flickr_images/_count

# Check index mapping
curl http://localhost:9200/flickr_images/_mapping
```

**Performance Tuning:**
```powershell
# GPU users: Maximize throughput
python ingest_flickr_data.py --batch-size 4000 --workers 32

# Limited RAM: Reduce memory usage
python ingest_flickr_data.py --batch-size 1000 --workers 16
docker-compose exec backend python scripts/add_all_descriptors.py --workers 8 --batch-size 20

# Resume from specific point
python ingest_flickr_data.py --offset 500000 --limit 500000
```

---

##  Author

**Ahmed Guermazi**

---

##  Version

**Version**: 3.0.0 (Multi-Descriptor + Fuzzy Search + Resumable Processing)  
**Last Updated**: October 2025

**Major Changes in v3.0:**
- ✅ Added 6-descriptor support (VGG, Color, LBP, HOG, Edge Histogram, SIFT)
- ✅ Fuzzy text search with typo tolerance (AUTO fuzziness)
- ✅ Automatic VGG prioritization (50% weight when combined)
- ✅ Resumable processing with --offset and --limit
- ✅ Multi-worker parallel descriptor extraction (8-20x faster)
- ✅ GPU acceleration for VGG extraction
- ✅ Smart filtering (broken images, failed downloads)
- ✅ Complete descriptor score calculation for all results
- ✅ Simplified UI (removed map view, cleaned controls)
- ✅ Fixed Elasticsearch score conversion (cosine formula)
- ✅ RootSIFT normalization + mean+std pooling

---

**Built with  for visual search and content discovery**
