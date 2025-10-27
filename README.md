# CBIR - Content-Based Image Retrieval System# 🧠 Visual & Textual Image Search Engine



**Elasticsearch + VGG Deep Learning | Flickr Dataset | Visual Search Engine**A full-stack content-based image retrieval (CBIR) system combining visual descriptors and textual metadata.



---## 🎯 Features



## 🚀 Quick Start (3 Steps)- **Visual Search**: Upload an image and find similar images using MPEG-7 + custom descriptors

- **Text Search**: Search by keywords (tags, filenames, captions)

```powershell- **Hybrid Search**: Combine visual + textual queries

# 1. Start Elasticsearch- **Multiple Descriptors**: Color Histogram, LBP, HOG, MPEG-7

docker-compose up -d elasticsearch- **Fast Retrieval**: <1s for top-100 results using Faiss indexing

Start-Sleep -Seconds 60- **Scalable**: Supports up to 1M images



# 2. Create index and ingest sample data## 🏗️ Architecture

cd scripts

pip install -r requirements.txt```

python elasticsearch_mapping.pyFrontend (Next.js) ↔ Backend (FastAPI) ↔ PostgreSQL + Faiss Index

python ingest_flickr_data.py --csv ..\data\csv\sample_photo_metadata.csv --limit 10                                         ↔ Local Image Storage

```

# 3. Start application

cd ..## 📦 Tech Stack

docker-compose up -d backend frontend

```- **Frontend**: Next.js 14, React, TailwindCSS

- **Backend**: FastAPI, Python 3.11

**Access:** http://localhost:3000- **Database**: PostgreSQL

- **Indexing**: Faiss (Facebook AI Similarity Search)

---- **Image Processing**: OpenCV, scikit-image

- **Deployment**: Docker Compose

## 📊 System Overview

## 🚀 Quick Start

### What This Does

- **Visual Search**: Upload an image → Find visually similar images### Prerequisites

- **Text Search**: Search by tags, titles, locations  

- **Geo Search**: Find images near a location- Docker & Docker Compose

- **Hybrid Search**: Combine visual + text + location- Node.js 18+ (for local development)

- Python 3.11+ (for local development)

### Technology Stack

- **Search Engine**: Elasticsearch 8.11 with kNN### Installation

- **Deep Learning**: VGG16/VGG19 for feature extraction

- **Dataset**: Flickr images from CSV metadata1. **Clone the repository**

- **Backend**: FastAPI (Python)```bash

- **Frontend**: Next.js (React)cd c:\projects\CBIR

- **Data Pipeline**: Logstash for CSV ingestion```



### Key Features2. **Start all services**

- ✅ **90% Disk Space Savings** - Images auto-deleted after feature extraction```bash

- ✅ **VGG Features** - 4096-dim deep learning embeddingsdocker-compose up --build

- ✅ **Geo-search** - Search by latitude/longitude```

- ✅ **Scalable** - Handles millions of images

- ✅ **Dockerized** - One-command deployment3. **Access the application**

- Frontend: http://localhost:3000

---- Backend API: http://localhost:8000

- API Docs: http://localhost:8000/docs

## 📁 Project Structure

### Local Development

```

CBIR/#### PostgreSQL Database Setup

├── docker-compose.yml              # Main Docker configuration

├── README.md                       # This fileBefore running the backend locally, you need a PostgreSQL database. You have two options:

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
