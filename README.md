# CBIR - Content-Based Image Retrieval System

**Elasticsearch + VGG Deep Learning | Flickr Dataset | Visual Search Engine**

---

##  Features

- **Visual Search**: Upload an image and find similar images using VGG16/VGG19 deep learning
- **Text Search**: Search by tags, titles, and descriptions
- **Geo Search**: Find images by location (latitude/longitude)
- **Hybrid Search**: Combine visual + textual + geo queries
- **90% Disk Savings**: Auto-delete images after feature extraction
- **Scalable**: Handles millions of images with Elasticsearch kNN

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
- **Search Engine**: Elasticsearch 8.11 with kNN plugin
- **Deep Learning**: VGG16/VGG19 (TensorFlow 2.15)
- **Data Pipeline**: Logstash 8.11
- **Deployment**: Docker Compose

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

# 2. Create index and ingest sample data
cd scripts
pip install -r requirements.txt
python elasticsearch_mapping.py
python ingest_flickr_data.py --csv ..\data\csv\sample_photo_metadata.csv --limit 10

# 3. Start application
cd ..
docker-compose up -d backend frontend
```

**Access:** http://localhost:3000

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
  --batch-size 100 `                     # Batch size
  --workers 4 `                          # Parallel workers
  --limit 1000 `                         # Limit images (optional)
  --keep-images                          # Keep images (optional)
```

### VGG Model Options

| Model | Layer | Dimensions | Speed | Use Case |
|-------|-------|------------|-------|----------|
| VGG16 | fc2 | 4096 | Fast | General purpose |
| VGG19 | fc2 | 4096 | Slower | Higher accuracy |
| VGG16 | block5_pool | 512 | Fastest | Large datasets |

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

### Processing Speed

| Hardware | Speed | Time for 10K images |
|----------|-------|---------------------|
| CPU (8 cores) | ~2 images/sec | ~80 minutes |
| GPU (NVIDIA) | ~20 images/sec | ~8 minutes |

### Search Performance

- **kNN Search**: < 100ms for top-10 results
- **Text Search**: < 50ms  
- **Geo Search**: < 75ms
- **Hybrid Search**: < 150ms

### Storage Requirements

| Images | Features Only | With Images | Savings |
|--------|--------------|-------------|---------|
| 10K | 200 MB | 2 GB | 90% |
| 100K | 2 GB | 20 GB | 90% |
| 1M | 20 GB | 220 GB | 90% |

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

Test with sample data (5 minutes):

```powershell
# 1. Start Elasticsearch
docker-compose up -d elasticsearch
Start-Sleep -Seconds 60

# 2. Create index & ingest 10 images
cd scripts
pip install -r requirements.txt
python elasticsearch_mapping.py
python ingest_flickr_data.py --csv ..\data\csv\sample_photo_metadata.csv --limit 10

# 3. Start application
cd ..
docker-compose up -d backend frontend

# 4. Open browser
Start-Process http://localhost:3000
```

 **Done!** Upload an image and try searching.

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
1.  **Elasticsearch won't start**  Increase Docker RAM to 8GB
2.  **Connection refused**  Wait 60-120 seconds after starting
3.  **Out of memory**  Reduce `--batch-size` to 20-50
4.  **Images fail to download**  Check CSV format (< 10% errors OK)

**Debugging:**
```powershell
# View all logs
docker-compose logs -f

# Check Elasticsearch specifically
docker-compose logs elasticsearch | Select-String "error"

# Test connection
curl http://localhost:9200
```

---

##  Author

**Ahmed Guermazi**

---

##  Version

**Version**: 2.0.0 (Elasticsearch + VGG)  
**Last Updated**: October 2025

---

**Built with  for visual search and content discovery**
