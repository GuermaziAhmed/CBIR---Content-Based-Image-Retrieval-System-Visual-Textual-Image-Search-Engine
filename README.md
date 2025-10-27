# CBIR - Content-Based Image Retrieval System# CBIR - Content-Based Image Retrieval System



**Elasticsearch + VGG Deep Learning | Flickr Dataset | Visual Search Engine****Elasticsearch + VGG Deep Learning | Flickr Dataset | Visual Search Engine**



------



## 🎯 Features## 🎯 Features



- **Visual Search**: Upload an image and find similar images using VGG16/VGG19 deep learning- **Visual Search**: Upload an image and find similar images using VGG16/VGG19 deep learning

- **Text Search**: Search by tags, titles, and descriptions- **Text Search**: Search by tags, titles, and descriptions

- **Geo Search**: Find images by location (latitude/longitude)- **Geo Search**: Find images by location (latitude/longitude)

- **Hybrid Search**: Combine visual + textual + geo queries- **Hybrid Search**: Combine visual + textual + geo queries

- **90% Disk Savings**: Auto-delete images after feature extraction- **90% Disk Savings**: Auto-delete images after feature extraction

- **Scalable**: Handles millions of images with Elasticsearch kNN- **Scalable**: Handles millions of images with Elasticsearch kNN



------



## 🏗️ Architecture## 🏗️ Architecture



``````

Frontend (Next.js) ↔ Backend (FastAPI) ↔ Elasticsearch + kNNFrontend (Next.js) ↔ Backend (FastAPI) ↔ Elasticsearch + kNN

                                         ↔ Logstash (CSV ingestion)                                         ↔ Logstash (CSV ingestion)

                                         ↔ VGG Feature Extractor                                         ↔ VGG Feature Extractor

``````



------



## 📦 Tech Stack## 📦 Tech Stack



- **Frontend**: Next.js 14, React, TailwindCSS- **Frontend**: Next.js 14, React, TailwindCSS

- **Backend**: FastAPI, Python 3.11- **Backend**: FastAPI, Python 3.11

- **Search Engine**: Elasticsearch 8.11 with kNN plugin- **Search Engine**: Elasticsearch 8.11 with kNN plugin

- **Deep Learning**: VGG16/VGG19 (TensorFlow 2.15)- **Deep Learning**: VGG16/VGG19 (TensorFlow 2.15)

- **Data Pipeline**: Logstash 8.11- **Data Pipeline**: Logstash 8.11

- **Deployment**: Docker Compose- **Deployment**: Docker Compose



------



## 🚀 Quick Start## 🚀 Quick Start (3 Steps)



### Prerequisites### Prerequisites

- Docker Desktop with 8GB+ RAM- Docker Desktop with 8GB+ RAM

- 20GB+ disk space- 20GB+ disk space



### Installation (3 Steps)### Installation



```powershell```powershell

# 1. Start Elasticsearch# 1. Start Elasticsearch

docker-compose up -d elasticsearchdocker-compose up -d elasticsearch

Start-Sleep -Seconds 60Start-Sleep -Seconds 60



# 2. Create index and ingest sample data# 2. Create index and ingest sample data

cd scriptscd scripts

pip install -r requirements.txtpip install -r requirements.txt

python elasticsearch_mapping.pypython elasticsearch_mapping.py

python ingest_flickr_data.py --csv ..\data\csv\sample_photo_metadata.csv --limit 10python ingest_flickr_data.py --csv ..\data\csv\sample_photo_metadata.csv --limit 10



# 3. Start application# 3. Start application

cd ..cd ..

docker-compose up -d backend frontenddocker-compose up -d backend frontend

``````



**Access:** http://localhost:3000**Access:** http://localhost:3000



------



## 📁 Project Structure## 📁 Project Structure



``````

CBIR/CBIR/

├── docker-compose.yml              # Main Docker configuration├── docker-compose.yml              # Main Docker configuration

├── README.md                       # This file├── README.md                       # This file

││

├── backend/                        # FastAPI backend├── backend/                        # FastAPI backend

│   ├── main.py                    # API server│   ├── main.py                    # API server

│   ├── Dockerfile                 # Backend container│   ├── Dockerfile                 # Backend container

│   └── requirements.txt           # Python dependencies│   └── requirements.txt           # Python dependencies

││

├── frontend/                       # Next.js frontend├── frontend/                       # Next.js frontend

│   ├── app/page.tsx               # Main search interface│   ├── app/page.tsx               # Main search interface

│   ├── Dockerfile                 # Frontend container│   ├── Dockerfile                 # Frontend container

│   └── package.json               # Node dependencies│   └── package.json               # Node dependencies

││

├── scripts/                        # Data ingestion pipeline├── scripts/                        # Data ingestion pipeline

│   ├── elasticsearch_mapping.py   # Create ES index│   ├── elasticsearch_mapping.py   # Create ES index

│   ├── vgg_extractor.py           # VGG feature extraction│   ├── vgg_extractor.py           # VGG feature extraction

│   ├── ingest_flickr_data.py      # Complete ingestion pipeline│   ├── ingest_flickr_data.py      # Complete ingestion pipeline

│   └── requirements.txt           # Python dependencies│   └── requirements.txt           # Python dependencies

││

├── logstash/                       # Logstash configuration├── logstash/                       # Logstash configuration

│   └── pipeline/│   └── pipeline/

│       └── flickr-csv.conf        # CSV parsing pipeline│       └── flickr-csv.conf        # CSV parsing pipeline

││

└── data/└── data/

    ├── csv/                        # Place your CSV here    ├── csv/                        # Place your CSV here

    │   └── sample_photo_metadata.csv    │   └── sample_photo_metadata.csv

    └── temp/                       # Temporary images (auto-deleted)    └── temp/                       # Temporary images (auto-deleted)

``````



------



## 🗂️ CSV Data Format## 🗂️ CSV Data Format



Your CSV file must have these columns:Your CSV file must have these columns:



```csv```csv

id,userid,title,tags,latitude,longitude,views,date_taken,date_uploaded,accuracy,flickr_secret,flickr_server,flickr_farmid,userid,title,tags,latitude,longitude,views,date_taken,date_uploaded,accuracy,flickr_secret,flickr_server,flickr_farm

5133463568,78697380@N00,"Tunisi 2010","{tunisia,carthage}",36.85,10.33,6,"2010-10-23 11:50:06","2010-10-31 21:42:28",14,002f695b15,1152,25133463568,78697380@N00,"Tunisi 2010","{tunisia,carthage}",36.85,10.33,6,"2010-10-23 11:50:06","2010-10-31 21:42:28",14,002f695b15,1152,2

``````



**Image URL Format:****Image URL Format:**

``````

http://farm{flickr_farm}.staticflickr.com/{flickr_server}/{id}_{flickr_secret}.jpghttp://farm{flickr_farm}.staticflickr.com/{flickr_server}/{id}_{flickr_secret}.jpg



Example:Example:

http://farm2.staticflickr.com/1152/5133463568_002f695b15.jpghttp://farm2.staticflickr.com/1152/5133463568_002f695b15.jpg

``````



------



## 💾 Disk Space Management## 💾 Disk Space Management



### Default Mode: Auto-Delete Images (90% Savings) ✅### Default Mode: Auto-Delete Images (90% Savings) ✅



```powershell```powershell

# Images are automatically deleted after feature extraction# Images are automatically deleted after feature extraction

python ingest_flickr_data.py --csv photo_metadata.csvpython ingest_flickr_data.py --csv photo_metadata.csv



# Storage for 1 million images:# Storage for 1 million images:

# - Elasticsearch: 20 GB (features + metadata)# - Elasticsearch: 20 GB (features + metadata)

# - Local images: 0 GB (deleted)# - Local images: 0 GB (deleted)

# - Total: 20 GB# - Total: 20 GB

``````



### Optional: Keep Downloaded Images### Optional: Keep Downloaded Images



```powershell```powershell

# Use --keep-images flag to preserve images# Use --keep-images flag to preserve images

python ingest_flickr_data.py --csv photo_metadata.csv --keep-imagespython ingest_flickr_data.py --csv photo_metadata.csv --keep-images



# Storage for 1 million images:# Storage for 1 million images:

# - Elasticsearch: 20 GB# - Elasticsearch: 20 GB

# - Local images: 200 GB# - Local images: 200 GB

# - Total: 220 GB# - Total: 220 GB

``````



**💡 Recommendation:** Use default mode (without `--keep-images`) to save 90% disk space!**💡 Recommendation:** Use default mode (without `--keep-images`) to save 90% disk space!



------



## 🔧 Configuration## 🔧 Configuration



### Ingestion Parameters### Ingestion Parameters



```powershell```powershell

python scripts/ingest_flickr_data.py `python scripts/ingest_flickr_data.py `

  --csv data/csv/photo_metadata.csv `    # CSV file path  --csv data/csv/photo_metadata.csv `    # CSV file path

  --es-host localhost `                  # Elasticsearch host  --es-host localhost `                  # Elasticsearch host

  --es-port 9200 `                       # Elasticsearch port  --es-port 9200 `                       # Elasticsearch port

  --model vgg16 `                        # VGG model (vgg16 or vgg19)  --model vgg16 `                        # VGG model (vgg16 or vgg19)

  --layer fc2 `                          # Feature layer (fc2 or block5_pool)  --layer fc2 `                          # Feature layer (fc2 or block5_pool)

  --batch-size 100 `                     # Batch size  --batch-size 100 `                     # Batch size

  --workers 4 `                          # Parallel workers  --workers 4 `                          # Parallel workers

  --limit 1000 `                         # Limit images (optional)  --limit 1000 `                         # Limit images (optional)

  --keep-images                          # Keep images (optional)  --keep-images                          # Keep images (optional)

``````



### VGG Model Options### VGG Model Options



| Model | Layer | Dimensions | Speed | Use Case || Model | Layer | Dimensions | Speed | Use Case |

|-------|-------|------------|-------|----------||-------|-------|------------|-------|----------|

| VGG16 | fc2 | 4096 | Fast | General purpose || VGG16 | fc2 | 4096 | Fast | General purpose |

| VGG19 | fc2 | 4096 | Slower | Higher accuracy || VGG19 | fc2 | 4096 | Slower | Higher accuracy |

| VGG16 | block5_pool | 512 | Fastest | Large datasets || VGG16 | block5_pool | 512 | Fastest | Large datasets |



------



## 🐳 Docker Commands## 🐳 Docker Commands



### Start Services### Start Services



```powershell```powershell

# Start all services# Start all services

docker-compose up -ddocker-compose up -d



# Start specific services# Start specific services

docker-compose up -d elasticsearchdocker-compose up -d elasticsearch

docker-compose up -d backend frontenddocker-compose up -d backend frontend



# View logs# View logs

docker-compose logs -f backenddocker-compose logs -f backend

docker-compose logs -f elasticsearchdocker-compose logs -f elasticsearch

``````



### Stop Services### Stop Services



```powershell```powershell

# Stop all services# Stop all services

docker-compose downdocker-compose down



# Stop and remove volumes (⚠️ WARNING: deletes all data)# Stop and remove volumes (⚠️ WARNING: deletes all data)

docker-compose down -vdocker-compose down -v

``````



### Check Status### Check Status



```powershell```powershell

# Check running containers# Check running containers

docker-compose psdocker-compose ps



# Check Elasticsearch health# Check Elasticsearch health

curl http://localhost:9200/_cluster/healthcurl http://localhost:9200/_cluster/health



# Check document count# Check document count

curl http://localhost:9200/flickr_images/_countcurl http://localhost:9200/flickr_images/_count

``````



------



## 🔍 API Examples## 🔍 API Examples



### Visual Search (Similar Images)### Visual Search (Similar Images)



```powershell```powershell

# Using curl# Using curl

curl -X POST http://localhost:8000/api/search/visual `curl -X POST http://localhost:8000/api/search/visual `

  -F "image=@query.jpg" `  -F "image=@query.jpg" `

  -F "top_k=10"  -F "top_k=10"

``````



### Text Search (Tags/Titles)### Text Search (Tags/Titles)



```powershell```powershell

curl -X POST http://localhost:8000/api/search/text `curl -X POST http://localhost:8000/api/search/text `

  -H "Content-Type: application/json" `  -H "Content-Type: application/json" `

  -d '{  -d '{

    "query": "paris eiffel tower",    "query": "paris eiffel tower",

    "top_k": 10    "top_k": 10

  }'  }'

``````



### Geo Search (Location)### Geo Search (Location)



```powershell```powershell

curl -X POST http://localhost:8000/api/search/geo `curl -X POST http://localhost:8000/api/search/geo `

  -H "Content-Type: application/json" `  -H "Content-Type: application/json" `

  -d '{  -d '{

    "lat": 48.858370,    "lat": 48.858370,

    "lon": 2.294481,    "lon": 2.294481,

    "radius": "10km",    "radius": "10km",

    "top_k": 20    "top_k": 20

  }'  }'

``````



### Hybrid Search (Combined)### Hybrid Search (Combined)



```powershell```powershell

curl -X POST http://localhost:8000/api/search/hybrid `curl -X POST http://localhost:8000/api/search/hybrid `

  -F "image=@query.jpg" `  -F "image=@query.jpg" `

  -F "query_text=paris" `  -F "query_text=paris" `

  -F "lat=48.85" `  -F "lat=48.85" `

  -F "lon=2.29" `  -F "lon=2.29" `

  -F "radius=50km" `  -F "radius=50km" `

  -F "top_k=10"  -F "top_k=10"

``````



------



## 🛠️ Troubleshooting## 🛠️ Troubleshooting



### ❌ Elasticsearch Won't Start### ❌ Elasticsearch Won't Start



**Problem:** Docker container exits immediately**Problem:** Docker container exits immediately



**Solution:****Solution:**

```powershell```powershell

# Increase Docker memory to 8GB minimum# Increase Docker memory to 8GB minimum

# Docker Desktop → Settings → Resources → Memory → 8GB# Docker Desktop → Settings → Resources → Memory → 8GB



# Clean restart# Clean restart

docker-compose down -vdocker-compose down -v

docker-compose up -d elasticsearchdocker-compose up -d elasticsearch

``````



------



### ❌ Connection Refused### ❌ Connection Refused



**Problem:** `Connection refused to localhost:9200`**Problem:** `Connection refused to localhost:9200`



**Solution:****Solution:**

```powershell```powershell

# Wait for Elasticsearch (can take 60-120 seconds)# Wait for Elasticsearch (can take 60-120 seconds)

Start-Sleep -Seconds 120Start-Sleep -Seconds 120



# Check if running# Check if running

docker ps | findstr elasticsearchdocker ps | findstr elasticsearch



# Check logs for errors# Check logs for errors

docker-compose logs elasticsearchdocker-compose logs elasticsearch

``````



------



### ❌ Out of Memory During Ingestion### ❌ Out of Memory During Ingestion



**Problem:** Python process killed or crashes**Problem:** Python process killed or crashes



**Solution:****Solution:**

```powershell```powershell

# Reduce batch size and workers# Reduce batch size and workers

python ingest_flickr_data.py `python ingest_flickr_data.py `

  --csv data.csv `  --csv data.csv `

  --batch-size 20 `  --batch-size 20 `

  --workers 2  --workers 2

``````



------



### ❌ Images Not Downloading### ❌ Images Not Downloading



**Problem:** Many 404 errors during download**Problem:** Many 404 errors during download



**Solution:****Solution:**

```powershell```powershell

# Some Flickr images may be deleted (normal, <10% error rate is OK)# Some Flickr images may be deleted (normal, <10% error rate is OK)



# Verify CSV format# Verify CSV format

Get-Content data\csv\photo_metadata.csv -Head 5Get-Content data\csv\photo_metadata.csv -Head 5



# Check flickr_secret, flickr_server, flickr_farm columns exist# Check flickr_secret, flickr_server, flickr_farm columns exist

``````



------



## 📈 Performance## 📈 Performance



### Processing Speed### Processing Speed



| Hardware | Speed | Time for 10K images || Hardware | Speed | Time for 10K images |

|----------|-------|---------------------||----------|-------|---------------------|

| CPU (8 cores) | ~2 images/sec | ~80 minutes || CPU (8 cores) | ~2 images/sec | ~80 minutes |

| GPU (NVIDIA) | ~20 images/sec | ~8 minutes || GPU (NVIDIA) | ~20 images/sec | ~8 minutes |



### Search Performance### Search Performance



- **kNN Search**: < 100ms for top-10 results- **kNN Search**: < 100ms for top-10 results

- **Text Search**: < 50ms  - **Text Search**: < 50ms  

- **Geo Search**: < 75ms- **Geo Search**: < 75ms

- **Hybrid Search**: < 150ms- **Hybrid Search**: < 150ms



### Storage Requirements### Storage Requirements



| Images | Features Only | With Images | Savings || Images | Features Only | With Images | Savings |

|--------|--------------|-------------|---------||--------|--------------|-------------|---------|

| 10K | 200 MB | 2 GB | 90% || 10K | 200 MB | 2 GB | 90% |

| 100K | 2 GB | 20 GB | 90% || 100K | 2 GB | 20 GB | 90% |

| 1M | 20 GB | 220 GB | 90% || 1M | 20 GB | 220 GB | 90% |



### Optimization Tips### Optimization Tips



```powershell```powershell

# Use RAM disk for ultra-fast processing (Windows)# Use RAM disk for ultra-fast processing (Windows)

python ingest_flickr_data.py `python ingest_flickr_data.py `

  --csv data.csv `  --csv data.csv `

  --temp-dir R:\cbir_temp  --temp-dir R:\cbir_temp



# Increase batch size (requires more RAM)# Increase batch size (requires more RAM)

python ingest_flickr_data.py `python ingest_flickr_data.py `

  --csv data.csv `  --csv data.csv `

  --batch-size 500 `  --batch-size 500 `

  --workers 16  --workers 16

``````



------



## 🌐 Service URLs## 🌐 Service URLs



| Service | URL | Description || Service | URL | Description |

|---------|-----|-------------||---------|-----|-------------|

| **Frontend** | http://localhost:3000 | Search interface || **Frontend** | http://localhost:3000 | Search interface |

| **Backend API** | http://localhost:8000 | REST API || **Backend API** | http://localhost:8000 | REST API |

| **API Docs** | http://localhost:8000/docs | Swagger UI || **API Docs** | http://localhost:8000/docs | Swagger UI |

| **Elasticsearch** | http://localhost:9200 | Search engine || **Elasticsearch** | http://localhost:9200 | Search engine |

| **Kibana** (optional) | http://localhost:5601 | Analytics dashboard || **Kibana** (optional) | http://localhost:5601 | Analytics dashboard |



------



## 📋 System Requirements## 📋 System Requirements



### Minimum Requirements### Minimum Requirements

- **OS**: Windows 10+, Linux, or macOS- **OS**: Windows 10+, Linux, or macOS

- **Docker Desktop**: 20+- **Docker Desktop**: 20+

- **RAM**: 8GB- **RAM**: 8GB

- **Disk**: 20GB free- **Disk**: 20GB free

- **CPU**: 4 cores- **CPU**: 4 cores



### Recommended for Production### Recommended for Production

- **RAM**: 16GB+- **RAM**: 16GB+

- **Disk**: 100GB+ SSD- **Disk**: 100GB+ SSD

- **CPU**: 8+ cores- **CPU**: 8+ cores

- **GPU**: NVIDIA GPU with CUDA (optional, 10x faster)- **GPU**: NVIDIA GPU with CUDA (optional, 10x faster)



### For Development### For Development

- **Python**: 3.11+- **Python**: 3.11+

- **Node.js**: 18+- **Node.js**: 18+

- **Git**: Latest- **Git**: Latest



------



## 🎯 Use Cases## 🎯 Use Cases



✅ **E-commerce**: Visual product search  ✅ **E-commerce**: Visual product search  

✅ **Media Libraries**: Find similar photos/videos  ✅ **Media Libraries**: Find similar photos/videos  

✅ **Content Moderation**: Duplicate detection  ✅ **Content Moderation**: Duplicate detection  

✅ **Research**: Computer vision experiments  ✅ **Research**: Computer vision experiments  

✅ **Travel Apps**: Geo-tagged image discovery  ✅ **Travel Apps**: Geo-tagged image discovery  

✅ **Social Media**: Image recommendation systems✅ **Social Media**: Image recommendation systems



------



## 📚 Documentation## 📚 Documentation



- **API Documentation**: http://localhost:8000/docs (when running)- **API Documentation**: http://localhost:8000/docs (when running)

- **Elasticsearch kNN**: https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html- **Elasticsearch kNN**: https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html

- **VGG Networks**: https://arxiv.org/abs/1409.1556- **VGG Networks**: https://arxiv.org/abs/1409.1556

- **TensorFlow Keras**: https://www.tensorflow.org/api_docs/python/tf/keras/applications- **TensorFlow Keras**: https://www.tensorflow.org/api_docs/python/tf/keras/applications



------



## ✅ Quick Test## ✅ Quick Test



Test with sample data (5 minutes):Test with sample data (5 minutes):



```powershell```powershell

# 1. Start Elasticsearch# 1. Start Elasticsearch

docker-compose up -d elasticsearchdocker-compose up -d elasticsearch

Start-Sleep -Seconds 60Start-Sleep -Seconds 60



# 2. Create index & ingest 10 images# 2. Create index & ingest 10 images

cd scriptscd scripts

pip install -r requirements.txtpip install -r requirements.txt

python elasticsearch_mapping.pypython elasticsearch_mapping.py

python ingest_flickr_data.py --csv ..\data\csv\sample_photo_metadata.csv --limit 10python ingest_flickr_data.py --csv ..\data\csv\sample_photo_metadata.csv --limit 10



# 3. Start application# 3. Start application

cd ..cd ..

docker-compose up -d backend frontenddocker-compose up -d backend frontend



# 4. Open browser# 4. Open browser

Start-Process http://localhost:3000Start-Process http://localhost:3000

``````



✨ **Done!** Upload an image and try searching.✨ **Done!** Upload an image and try searching.



------



## 🤝 Contributing## 🤝 Contributing



Contributions are welcome!Contributions are welcome!



1. Fork the repository1. Fork the repository

2. Create a feature branch (`git checkout -b feature/amazing-feature`)2. Create a feature branch (`git checkout -b feature/amazing-feature`)

3. Commit your changes (`git commit -m 'Add amazing feature'`)3. Commit your changes (`git commit -m 'Add amazing feature'`)

4. Push to the branch (`git push origin feature/amazing-feature`)4. Push to the branch (`git push origin feature/amazing-feature`)

5. Open a Pull Request5. Open a Pull Request



------



## 📄 License## 📄 License



MIT License - See LICENSE file for detailsMIT License - See LICENSE file for details



------



## 🆘 Need Help?## 🆘 Need Help?



**Common Solutions:****Common Solutions:**

1. ❌ **Elasticsearch won't start** → Increase Docker RAM to 8GB1. ❌ **Elasticsearch won't start** → Increase Docker RAM to 8GB

2. ❌ **Connection refused** → Wait 60-120 seconds after starting2. ❌ **Connection refused** → Wait 60-120 seconds after starting

3. ❌ **Out of memory** → Reduce `--batch-size` to 20-503. ❌ **Out of memory** → Reduce `--batch-size` to 20-50

4. ❌ **Images fail to download** → Check CSV format (< 10% errors OK)4. ❌ **Images fail to download** → Check CSV format (< 10% errors OK)



**Debugging:****Debugging:**

```powershell```powershell

# View all logs# View all logs

docker-compose logs -fdocker-compose logs -f



# Check Elasticsearch specifically# Check Elasticsearch specifically

docker-compose logs elasticsearch | Select-String "error"docker-compose logs elasticsearch | Select-String "error"



# Test connection# Test connection

curl http://localhost:9200curl http://localhost:9200

``````



------



## 👨‍💻 Author## 👨‍💻 Author



**Ahmed Guermazi****Ahmed Guermazi**



------



## 🏷️ Version## 🏷️ Version



**Version**: 2.0.0 (Elasticsearch + VGG)  **Version**: 2.0.0 (Elasticsearch + VGG)  

**Last Updated**: October 2025**Last Updated**: October 2025



------



**Built with ❤️ for visual search and content discovery****Built with ❤️ for visual search and content discovery**


│

├── backend/                        # FastAPI backend**Option 1: Use Docker for Database Only (Recommended)**

│   ├── main.py                    # API server```powershell

│   ├── Dockerfile                 # Backend container# Start only the PostgreSQL container

│   └── requirements.txt           # Python dependenciesdocker-compose up -d db

│

├── frontend/                       # Next.js frontend# Wait for database to initialize (check logs)

│   ├── app/page.tsx               # Main search interfacedocker-compose logs -f db

│   ├── Dockerfile                 # Frontend container

│   └── package.json               # Node dependencies# Database will be available at:

│# Host: localhost

├── scripts/                        # Data ingestion# Port: 5432

│   ├── elasticsearch_mapping.py   # Create ES index# User: cbir_user

│   ├── vgg_extractor.py           # VGG feature extraction# Password: cbir_password

│   ├── ingest_flickr_data.py      # Complete pipeline# Database: cbir_db

│   └── requirements.txt           # Python dependencies```

│

├── logstash/                       # Logstash config**Option 2: Install PostgreSQL Locally**

│   └── pipeline/

│       └── flickr-csv.conf        # CSV ingestion1. **Download and Install PostgreSQL**

│   - Download from: https://www.postgresql.org/download/windows/

└── data/   - Install PostgreSQL 15 or later

    ├── csv/                        # Place your CSV here   - Remember the password you set for the `postgres` user

    │   └── sample_photo_metadata.csv

    └── temp/                       # Temporary images (auto-deleted)2. **Create Database and User**

``````powershell

# Open PowerShell and connect to PostgreSQL

---psql -U postgres



## 🗂️ CSV Data Format# In the PostgreSQL shell, run:

CREATE DATABASE cbir_db;

Your CSV file must have these columns:CREATE USER cbir_user WITH PASSWORD 'cbir_password';

GRANT ALL PRIVILEGES ON DATABASE cbir_db TO cbir_user;

```csv\q

id,userid,title,tags,latitude,longitude,views,date_taken,date_uploaded,accuracy,flickr_secret,flickr_server,flickr_farm```

5133463568,78697380@N00,"Tunisi 2010","{tunisia,carthage}",36.85,10.33,6,"2010-10-23 11:50:06","2010-10-31 21:42:28",14,002f695b15,1152,2

```3. **Initialize Database Schema**

```powershell

**Image URL Construction:**# Run the initialization script

```psql -U cbir_user -d cbir_db -f backend\init.sql

http://farm{flickr_farm}.staticflickr.com/{flickr_server}/{id}_{flickr_secret}.jpg

Example: http://farm2.staticflickr.com/1152/5133463568_002f695b15.jpg# Or connect and run manually:

```psql -U cbir_user -d cbir_db



---# Then paste the contents of backend/init.sql

```

## 💾 Disk Space Management

4. **Update Connection String** (if using different credentials)

### Default: Feature-Only Mode (90% Savings) ✅   

   Edit `backend/.env`:

```bash   ```env

# Images are automatically deleted after feature extraction   DATABASE_URL=postgresql://cbir_user:cbir_password@localhost:5432/cbir_db

python ingest_flickr_data.py --csv photo_metadata.csv   ```



# For 1M images:5. **Verify Connection**

# - Elasticsearch: 20 GB (features + metadata)```powershell

# - Local images: 0 GB (deleted after extraction)# Test the connection

# - Total: 20 GBpsql -U cbir_user -d cbir_db -c "SELECT version();"

``````



### Optional: Keep Images#### Backend Setup

```powershell

```bashcd backend

# Keep downloaded images (high disk usage)

python ingest_flickr_data.py --csv photo_metadata.csv --keep-images# Create virtual environment

python -m venv venv

# For 1M images:

# - Elasticsearch: 20 GB# Activate virtual environment

# - Local images: 200 GB.\venv\Scripts\activate  # Windows PowerShell

# - Total: 220 GB# OR

```venv\Scripts\activate.bat  # Windows CMD



**Recommendation:** Use default mode (no `--keep-images`) to save 90% disk space!# Upgrade pip

python -m pip install --upgrade pip

---

# Install dependencies

## 🔧 Configurationpip install -r requirements.txt



### Ingestion Parameters# Create necessary directories

New-Item -ItemType Directory -Force -Path ..\data\images

```bashNew-Item -ItemType Directory -Force -Path ..\data\descriptors

python scripts/ingest_flickr_data.py \New-Item -ItemType Directory -Force -Path ..\data\indexes

  --csv data/csv/photo_metadata.csv \    # CSV file path

  --es-host localhost \                  # Elasticsearch host# Verify database connection

  --es-port 9200 \                       # Elasticsearch portpython -c "from database import engine; print('Database connection:', engine.url)"

  --model vgg16 \                        # VGG model (vgg16 or vgg19)

  --layer fc2 \                          # Feature layer# Run the application

  --batch-size 100 \                     # Batch sizeuvicorn main:app --reload --port 8000

  --workers 4 \                          # Parallel workers

  --limit 1000 \                         # Limit images (optional)# Application will be available at http://localhost:8000

  --keep-images                          # Keep images (optional)```

```

**Troubleshooting Backend Setup**

### VGG Model Selection

If you get database connection errors:

```bash```powershell

# VGG16 (faster, 4096-dim)# Check if PostgreSQL is running

--model vgg16 --layer fc2docker ps | findstr cbir_db

# OR (for local PostgreSQL)

# VGG19 (more accurate, 4096-dim)Get-Service -Name postgresql*

--model vgg19 --layer fc2

# Test connection manually

# VGG16 Pool5 (faster search, 512-dim)psql -U cbir_user -d cbir_db -h localhost -p 5432

--model vgg16 --layer block5_pool

```# Check DATABASE_URL in backend/.env

cat backend\.env

---```



## 🐳 Docker Commands#### Frontend Setup

```powershell

### Start Servicescd frontend



```powershell# Install dependencies

# Start all servicesnpm install

docker-compose up -d

# Create .env.local if it doesn't exist

# Start specific servicesif (!(Test-Path .env.local)) {

docker-compose up -d elasticsearch    @"

docker-compose up -d backend frontendNEXT_PUBLIC_API_URL=http://localhost:8000

"@ | Out-File -FilePath .env.local -Encoding utf8

# View logs}

docker-compose logs -f backend

```# Run development server

npm run dev

### Stop Services

# Application will be available at http://localhost:3000

```powershell```

# Stop all

docker-compose down**Troubleshooting Frontend Setup**



# Stop and remove volumes (WARNING: deletes data)If you get API connection errors:

docker-compose down -v```powershell

```# Verify backend is running

curl http://localhost:8000/health

### Check Status

# Check .env.local

```powershellcat .env.local

# Check running containers

docker-compose ps# Clear Next.js cache if needed

Remove-Item -Recurse -Force .next

# Check Elasticsearch healthnpm run dev

curl http://localhost:9200/_cluster/health```



# Check document count## 📁 Project Structure

curl http://localhost:9200/flickr_images/_count

``````

CBIR/

---├── frontend/              # Next.js application

│   ├── app/              # App router pages

## 🔍 API Examples│   ├── components/       # React components

│   ├── lib/              # Utilities & API client

### Visual Search│   └── public/           # Static assets

├── backend/              # FastAPI application

```bash│   ├── routers/          # API endpoints

curl -X POST http://localhost:8000/api/search/visual \│   ├── utils/            # Descriptor extraction & indexing

  -F "image=@query.jpg" \│   ├── models/           # Pydantic models

  -F "top_k=10"│   └── main.py           # Application entry point

```├── data/

│   ├── images/           # Image storage

### Text Search│   ├── descriptors/      # Precomputed features

│   └── indexes/          # Faiss indexes

```bash├── docker-compose.yml

curl -X POST http://localhost:8000/api/search/text \└── README.md

  -H "Content-Type: application/json" \```

  -d '{

    "query": "paris eiffel tower",## 🔧 API Endpoints

    "top_k": 10

  }'### Search

``````http

POST /api/search

### Geo SearchContent-Type: application/json



```bash{

curl -X POST http://localhost:8000/api/search/geo \  "query_text": "cat",

  -H "Content-Type: application/json" \  "use_image": true,

  -d '{  "image_data": "base64_encoded_image",

    "lat": 48.858370,  "descriptors": ["color", "lbp"],

    "lon": 2.294481,  "top_k": 50

    "radius": "10km",}

    "top_k": 20```

  }'

```### Get Image

```http

### Hybrid SearchGET /api/image/{id}

```

```bash

curl -X POST http://localhost:8000/api/search/hybrid \### Build Index (Admin)

  -F "image=@query.jpg" \```http

  -F "query_text=paris" \POST /api/index/build

  -F "lat=48.85" \```

  -F "lon=2.29" \

  -F "radius=50km" \## 🎨 Usage Example

  -F "top_k=10"

```1. **Visual Search**

   - Click "Upload Image" button

---   - Select image from your computer

   - Choose descriptors (Color, LBP, HOG)

## 🛠️ Troubleshooting   - Click "Search"



### Elasticsearch Won't Start2. **Text Search**

   - Enter keywords: "cat red"

```powershell   - Click "Search"

# Increase Docker memory to 8GB minimum

# Docker Desktop → Settings → Resources → Memory3. **Hybrid Search**

   - Upload image + enter keywords

# Clean restart   - System combines both similarity scores

docker-compose down -v

docker-compose up -d elasticsearch## 📊 Descriptors

```

| Descriptor      | Dimension | Description                |

### Connection Refused|----------------|-----------|----------------------------|

| Color Histogram | 64        | RGB color distribution     |

```powershell| LBP            | 59        | Texture patterns           |

# Wait for Elasticsearch to be ready (can take 60+ seconds)| HOG            | 81        | Edge orientations          |

Start-Sleep -Seconds 120| MPEG-7         | varies    | Standard visual descriptors|



# Check if running## 🔨 Build Index

docker ps | findstr elasticsearch

To index your own images:

# Check logs

docker-compose logs elasticsearch1. Place images in `data/images/`

```2. Run indexer:

```bash

### Out of Memory During Ingestiondocker-compose exec backend python utils/build_index.py

```

```powershell

# Reduce batch size and workers## 🧪 Testing

python ingest_flickr_data.py \

  --csv data.csv \```bash

  --batch-size 20 \# Backend tests

  --workers 2cd backend

```pytest



### Images Not Downloading# Frontend tests

cd frontend

```powershellnpm test

# Some Flickr images may be deleted (normal)```

# Check error rate in logs - should be < 10%

## 📈 Performance

# Verify CSV format

Get-Content data\csv\photo_metadata.csv -Head 5- **Search Time**: <1s for 100K images

```- **Index Build**: ~10 min for 100K images

- **Memory**: ~2GB for 1M images (Color + LBP)

---

## 🐳 Docker Services

## 📈 Performance

- `frontend`: Next.js app (port 3000)

### Processing Speed- `backend`: FastAPI server (port 8000)

- `db`: PostgreSQL database (port 5432)

| Hardware | Speed | Time for 10K images |- `pgadmin`: Database admin UI (port 5050)

|----------|-------|---------------------|

| CPU only | ~2 images/sec | ~80 minutes |## 🛠️ Configuration

| GPU (NVIDIA) | ~20 images/sec | ~8 minutes |

Edit `docker-compose.yml` to configure:

### Search Speed- Database credentials

- Volume paths

- **kNN Search**: < 100ms for top-10 results- Port mappings

- **Dataset Size**: Scales to millions of images- Environment variables

- **Index Size**: ~20 KB per image (features only)

## 📝 License

### Optimization Tips

MIT License - feel free to use for your projects!

```bash

# Use RAM disk for ultra-fast processing## 🤝 Contributing

python ingest_flickr_data.py \

  --csv data.csv \Contributions welcome! Please read CONTRIBUTING.md first.

  --temp-dir /tmp/cbir

## 📧 Contact

# Increase batch size for more speed (requires more RAM)

python ingest_flickr_data.py \Ahmed Guermazi - PRD Author

  --csv data.csv \

  --batch-size 500 \---

  --workers 16

```**Version**: 1.0

**Last Updated**: October 2025

---

## 🌐 URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Search interface |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Elasticsearch | http://localhost:9200 | Search engine |
| Kibana | http://localhost:5601 | Analytics (optional) |

---

## 📋 Requirements

### System Requirements
- **Docker Desktop**: 20+
- **RAM**: 8GB minimum
- **Disk**: 20GB+ (feature-only mode)
- **OS**: Windows, Linux, or macOS

### For Development
- **Python**: 3.11+
- **Node.js**: 18+
- **Git**: Latest version

---

## 🎯 Use Cases

- **Image Search Engines**: Build visual search for e-commerce, media libraries
- **Content Discovery**: Find similar images in large datasets
- **Duplicate Detection**: Identify duplicate or near-duplicate images
- **Image Clustering**: Group visually similar images
- **Geo-tagged Search**: Location-based image discovery
- **Research**: Computer vision, deep learning experiments

---

## 📚 Additional Documentation

- **API Documentation**: http://localhost:8000/docs (when running)
- **Elasticsearch Guide**: https://www.elastic.co/guide/
- **VGG Paper**: https://arxiv.org/abs/1409.1556
- **TensorFlow Keras**: https://www.tensorflow.org/api_docs/python/tf/keras/applications

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file

---

## 🆘 Support

**Common Issues:**
1. **Elasticsearch won't start** → Increase Docker memory to 8GB
2. **Connection refused** → Wait 60+ seconds for Elasticsearch startup
3. **Out of memory** → Reduce `--batch-size` and `--workers`
4. **Images not downloading** → Check CSV format and Flickr URLs

**Getting Help:**
- Check logs: `docker-compose logs -f elasticsearch`
- Verify CSV format matches example above
- Ensure Docker has enough resources

---

## ✅ Quick Test

Test the system with sample data:

```powershell
# 1. Start Elasticsearch
docker-compose up -d elasticsearch
Start-Sleep -Seconds 60

# 2. Setup and ingest 5 sample images
cd scripts
pip install -r requirements.txt
python elasticsearch_mapping.py
python ingest_flickr_data.py --csv ..\data\csv\sample_photo_metadata.csv

# 3. Start app
cd ..
docker-compose up -d backend frontend

# 4. Open browser
Start-Process http://localhost:3000
```

Done! Upload an image and try searching. 🎉

---

**Built with ❤️ for visual search and content discovery**
