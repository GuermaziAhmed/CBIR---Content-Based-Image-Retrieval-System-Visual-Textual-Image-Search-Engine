# 🚀 CBIR Project Setup Guide - Step by Step

Complete guide to get your Content-Based Image Retrieval system running from scratch.

---

## ✅ Prerequisites Check

### 1. Install Required Software

**Docker Desktop** (Required)
```powershell
# Check if Docker is installed
docker --version

# If not installed, download from:
# https://www.docker.com/products/docker-desktop
# Minimum: Docker Desktop 20.10+
```

**Python 3.11+** (For local scripts)
```powershell
# Check Python version
python --version

# If not installed, download from:
# https://www.python.org/downloads/
```

**Git** (For version control)
```powershell
# Check Git version
git --version

# If not installed, download from:
# https://git-scm.com/downloads
```

---

## 📋 Step 1: Start Docker Desktop

### Windows:

1. **Open Docker Desktop**
   - Press `Windows Key`
   - Type "Docker Desktop"
   - Click to launch

2. **Wait for Docker to Start**
   - Look for Docker whale icon in system tray (bottom-right)
   - Wait until it shows "Docker Desktop is running"
   - This can take 30-60 seconds

3. **Verify Docker is Running**
   ```powershell
   # Should show version info (not errors)
   docker version
   
   # Should show "Docker is running"
   docker info
   ```

**❌ If Docker won't start:**
- Check if Windows Subsystem for Linux (WSL 2) is installed
- Enable virtualization in BIOS
- Restart your computer
- See: https://docs.docker.com/desktop/troubleshoot/overview/

---

## 📋 Step 2: Prepare Project Structure

### Navigate to Project Directory

```powershell
# Go to your project folder
cd C:\projects\CBIR

# Verify you're in the right place
Get-ChildItem | Select-Object Name
# You should see: backend, frontend, scripts, docker-compose.yml, README.md
```

### Create Required Directories

```powershell
# Create data directories
New-Item -ItemType Directory -Force -Path data\csv
New-Item -ItemType Directory -Force -Path data\images
New-Item -ItemType Directory -Force -Path data\temp
New-Item -ItemType Directory -Force -Path data\models

# Create logstash config directory
New-Item -ItemType Directory -Force -Path logstash\pipeline
New-Item -ItemType Directory -Force -Path logstash\config

Write-Host "✅ Directories created successfully!"
```

---

## 📋 Step 3: Prepare Your CSV Data

### Option A: Use Sample Data (For Testing)

Create a sample CSV file for testing:

```powershell
# Create sample CSV
@"
id,userid,title,tags,latitude,longitude,views,date_taken,date_uploaded,accuracy,flickr_secret,flickr_server,flickr_farm
5133463568,78697380@N00,"Tunisi 2010","{tunisia,carthage}",36.85,10.33,6,"2010-10-23 11:50:06","2010-10-31 21:42:28",14,002f695b15,1152,2
8733984273,92847362@N01,"Paris Eiffel","{paris,france,eiffel}",48.858370,2.294481,125,"2012-06-15 14:20:00","2012-06-20 10:30:00",16,a1b2c3d4e5,2341,3
3928473821,73829103@N02,"NYC Statue","{newyork,statue,liberty}",40.689247,-74.044502,89,"2011-08-10 09:15:00","2011-08-12 18:45:00",15,f6g7h8i9j0,4521,5
"@ | Out-File -FilePath data\csv\sample_photo_metadata.csv -Encoding UTF8

Write-Host "✅ Sample CSV created: data\csv\sample_photo_metadata.csv"
```

### Option B: Use Your Own Data

Place your Flickr metadata CSV in: `data\csv\photo_metadata.csv`

**Required CSV columns:**
- id, userid, title, tags, latitude, longitude, views
- date_taken, date_uploaded, accuracy
- flickr_secret, flickr_server, flickr_farm

---

## 📋 Step 4: Start Elasticsearch (Core Service)

### Start Elasticsearch Container

```powershell
# Start only Elasticsearch first
docker-compose up -d elasticsearch

# You should see:
# [+] Running 2/2
#  ✔ Network cbir_network           Created
#  ✔ Container cbir_elasticsearch   Started
```

### Wait for Elasticsearch to Initialize

```powershell
# Wait 60 seconds for Elasticsearch to start
Write-Host "⏳ Waiting for Elasticsearch to initialize (60 seconds)..."
Start-Sleep -Seconds 60

# Check if Elasticsearch is running
docker-compose ps

# Should show:
# NAME                  STATUS
# cbir_elasticsearch    Up (healthy)
```

### Verify Elasticsearch is Ready

```powershell
# Test connection (should return cluster info)
curl http://localhost:9200

# Check cluster health (should show "green" or "yellow")
curl http://localhost:9200/_cluster/health

# Expected output:
# {"cluster_name":"cbir-cluster","status":"green",...}
```

**❌ If Elasticsearch fails to start:**
```powershell
# Check logs for errors
docker-compose logs elasticsearch

# Common issues:
# 1. Not enough memory: Docker Desktop → Settings → Resources → Memory → 8GB
# 2. Port already in use: Stop other services using port 9200
# 3. WSL 2 issues: wsl --update
```

---

## 📋 Step 5: Create Elasticsearch Index

### Install Python Dependencies

```powershell
# Go to scripts directory
cd scripts

# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\activate

# Install required packages
pip install --upgrade pip
pip install -r requirements.txt

# You should see installations of:
# - elasticsearch
# - tensorflow
# - pandas
# - requests
# - Pillow
```

### Create the Elasticsearch Index

```powershell
# Create index with VGG feature mappings
python elasticsearch_mapping.py

# Expected output:
# ✅ Index 'flickr_images' created successfully with VGG mappings
# or
# ℹ️ Index already exists

# Verify index was created
curl http://localhost:9200/flickr_images
```

---

## 📋 Step 6: Ingest Sample Data

### Run Data Ingestion Script

```powershell
# Still in scripts directory
# Ingest 10 sample images (for testing)
python ingest_flickr_data.py `
  --csv ..\data\csv\sample_photo_metadata.csv `
  --limit 10 `
  --batch-size 5

# Process overview:
# 1. 📥 Reading CSV...
# 2. 🌐 Downloading images from Flickr...
# 3. 🧠 Extracting VGG features...
# 4. 🗑️ Auto-deleting images (saves 90% disk space)
# 5. 📤 Indexing to Elasticsearch...
# 
# ✅ Completed: 10/10 images processed
```

**⏱️ Processing Time:**
- 10 images: ~2-5 minutes (CPU)
- 100 images: ~20-40 minutes (CPU)
- 1000 images: ~3-6 hours (CPU)

### Verify Data was Indexed

```powershell
# Check document count
curl http://localhost:9200/flickr_images/_count

# Should return:
# {"count":10,...}

# Search for a document
curl http://localhost:9200/flickr_images/_search?size=1

# Go back to project root
cd ..
```

---

## 📋 Step 7: Start Backend API

### Start Backend Service

```powershell
# From project root directory
docker-compose up -d backend

# Wait for backend to build and start (first time: 2-5 minutes)
Write-Host "⏳ Building backend container (first time only)..."
Start-Sleep -Seconds 30

# Check status
docker-compose ps backend

# Should show:
# NAME            STATUS
# cbir_backend    Up
```

### Verify Backend is Running

```powershell
# Test health endpoint
curl http://localhost:8000/health

# Expected: {"status": "healthy"}

# View API documentation
Start-Process http://localhost:8000/docs

# You should see Swagger UI with all endpoints
```

**❌ If backend fails:**
```powershell
# Check logs
docker-compose logs backend

# Common issues:
# 1. Port 8000 in use: Stop other services
# 2. Elasticsearch not ready: Wait longer or restart
# 3. Missing files: Check backend/Dockerfile exists
```

---

## 📋 Step 8: Start Frontend

### Start Frontend Service

```powershell
# Start Next.js frontend
docker-compose up -d frontend

# Wait for frontend to build (first time: 3-7 minutes)
Write-Host "⏳ Building frontend container (first time only)..."
Start-Sleep -Seconds 60

# Check status
docker-compose ps frontend

# Should show:
# NAME              STATUS
# cbir_frontend     Up
```

### Access the Application

```powershell
# Open in browser
Start-Process http://localhost:3000

# You should see:
# - CBIR Image Search Interface
# - Upload button
# - Search options
```

---

## 📋 Step 9: Test the System

### Upload and Search

1. **Open Application**
   - Go to http://localhost:3000

2. **Upload an Image**
   - Click "Upload Image" button
   - Select any image from your computer
   - Click "Search Similar"

3. **View Results**
   - See visually similar images
   - Click images to view details
   - Filter by tags, location, date

### Test API Endpoints

```powershell
# Text search
curl -X POST http://localhost:8000/api/search/text `
  -H "Content-Type: application/json" `
  -d '{"query": "paris", "top_k": 5}'

# Geo search (if you have geo-tagged images)
curl -X POST http://localhost:8000/api/search/geo `
  -H "Content-Type: application/json" `
  -d '{"lat": 48.858370, "lon": 2.294481, "radius": "10km", "top_k": 5}'
```

---

## 📋 Step 10: Monitor and Manage

### View Container Status

```powershell
# See all running containers
docker-compose ps

# Should show:
# NAME                  STATUS
# cbir_elasticsearch    Up (healthy)
# cbir_backend          Up
# cbir_frontend         Up
```

### View Logs

```powershell
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f elasticsearch

# Press Ctrl+C to stop viewing logs
```

### Check Resource Usage

```powershell
# See container resource usage
docker stats

# Press Ctrl+C to stop
```

---

## 🛑 Stopping the System

### Stop All Services

```powershell
# Stop all containers (keeps data)
docker-compose down

# Stop and remove all data (⚠️ WARNING: deletes everything)
docker-compose down -v
```

### Stop Individual Services

```powershell
# Stop only frontend
docker-compose stop frontend

# Stop only backend
docker-compose stop backend

# Restart a service
docker-compose restart backend
```

---

## 🔄 Restarting the System

### Quick Restart (After First Setup)

```powershell
# 1. Start Docker Desktop (if not running)
# 2. Start all services
docker-compose up -d

# 3. Wait for Elasticsearch (30 seconds)
Start-Sleep -Seconds 30

# 4. Check status
docker-compose ps

# 5. Access application
Start-Process http://localhost:3000
```

---

## 📊 Processing Large Datasets

### For Production Use (1000+ images)

```powershell
# 1. Ensure Elasticsearch is running
docker-compose ps elasticsearch

# 2. Go to scripts directory
cd scripts

# 3. Run ingestion with optimized settings
python ingest_flickr_data.py `
  --csv ..\data\csv\photo_metadata.csv `
  --batch-size 100 `
  --workers 4 `
  --model vgg16 `
  --layer fc2

# 4. Monitor progress (in another terminal)
docker-compose logs -f elasticsearch
```

**⚡ Performance Tips:**
```powershell
# For faster processing (requires 16GB+ RAM)
python ingest_flickr_data.py `
  --csv ..\data\csv\photo_metadata.csv `
  --batch-size 500 `
  --workers 8

# For memory-constrained systems
python ingest_flickr_data.py `
  --csv ..\data\csv\photo_metadata.csv `
  --batch-size 20 `
  --workers 2
```

---

## 🐛 Troubleshooting

### Issue: Docker Desktop Won't Start
```powershell
# 1. Check WSL 2
wsl --status
wsl --update

# 2. Restart Docker Desktop
taskkill /IM "Docker Desktop.exe" /F
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# 3. Restart computer if needed
```

### Issue: Elasticsearch Out of Memory
```powershell
# Increase Docker memory
# Docker Desktop → Settings → Resources → Memory → 8GB minimum

# Or reduce Elasticsearch heap size in docker-compose.yml
# Change: "ES_JAVA_OPTS=-Xms2g -Xmx2g"
# To:     "ES_JAVA_OPTS=-Xms1g -Xmx1g"
```

### Issue: Port Already in Use
```powershell
# Find process using port 9200
netstat -ano | findstr :9200

# Kill the process (use PID from above)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
# Change: "9200:9200"
# To:     "9201:9200"
```

### Issue: Images Not Downloading
```powershell
# Some Flickr images may be deleted (normal)
# Check error rate in logs - should be < 10%

# Verify CSV format
Get-Content data\csv\photo_metadata.csv -Head 5

# Test single image URL manually
curl "http://farm2.staticflickr.com/1152/5133463568_002f695b15.jpg" --output test.jpg
```

---

## 📚 Next Steps

### After successful setup:

1. **Add More Data**
   - Ingest full dataset: `python ingest_flickr_data.py --csv full_dataset.csv`

2. **Customize Frontend**
   - Edit `frontend/app/page.tsx`
   - Add map view, filters, etc.

3. **Optimize Performance**
   - Tune Elasticsearch settings
   - Add caching layer
   - Use GPU for faster VGG extraction

4. **Deploy to Production**
   - Use production-ready docker-compose
   - Add NGINX reverse proxy
   - Set up SSL certificates

---

## ✅ Success Checklist

- [ ] Docker Desktop installed and running
- [ ] Project directories created
- [ ] CSV data prepared
- [ ] Elasticsearch started and healthy
- [ ] Elasticsearch index created
- [ ] Sample data ingested (10+ images)
- [ ] Backend API running (http://localhost:8000)
- [ ] Frontend accessible (http://localhost:3000)
- [ ] Image search working
- [ ] No errors in logs

---

## 🆘 Getting Help

**Check logs first:**
```powershell
docker-compose logs elasticsearch
docker-compose logs backend
docker-compose logs frontend
```

**Test connections:**
```powershell
curl http://localhost:9200           # Elasticsearch
curl http://localhost:8000/health    # Backend
curl http://localhost:3000           # Frontend
```

**Common Commands Reference:**
```powershell
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# Restart service
docker-compose restart backend

# Rebuild service
docker-compose up -d --build backend

# View logs
docker-compose logs -f

# Remove all data
docker-compose down -v
```

---

**🎉 Congratulations! Your CBIR system is now running!**

Visit http://localhost:3000 to start searching images!
