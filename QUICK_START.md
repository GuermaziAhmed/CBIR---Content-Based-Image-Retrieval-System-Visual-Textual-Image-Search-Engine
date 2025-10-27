# ⚡ CBIR Quick Start - Copy & Paste Commands

**For users who just want to get started quickly!**

---

## 🎯 Prerequisites

✅ Docker Desktop installed and **RUNNING** (check system tray)  
✅ Python 3.11+ installed  
✅ In project directory: `cd C:\projects\CBIR`

---

## 🚀 Full Setup (Copy-Paste All)

```powershell
# ============================================
# STEP 1: Create directories
# ============================================
New-Item -ItemType Directory -Force -Path data\csv, data\images, data\temp, data\models, logstash\pipeline, logstash\config

# ============================================
# STEP 2: Create sample CSV data
# ============================================
@"
id,userid,title,tags,latitude,longitude,views,date_taken,date_uploaded,accuracy,flickr_secret,flickr_server,flickr_farm
5133463568,78697380@N00,"Tunisi 2010","{tunisia,carthage}",36.85,10.33,6,"2010-10-23 11:50:06","2010-10-31 21:42:28",14,002f695b15,1152,2
8733984273,92847362@N01,"Paris Eiffel","{paris,france,eiffel}",48.858370,2.294481,125,"2012-06-15 14:20:00","2012-06-20 10:30:00",16,a1b2c3d4e5,2341,3
3928473821,73829103@N02,"NYC Statue","{newyork,statue,liberty}",40.689247,-74.044502,89,"2011-08-10 09:15:00","2011-08-12 18:45:00",15,f6g7h8i9j0,4521,5
"@ | Out-File -FilePath data\csv\sample_photo_metadata.csv -Encoding UTF8

# ============================================
# STEP 3: Start Elasticsearch
# ============================================
docker-compose up -d elasticsearch
Write-Host "`n⏳ Waiting 60 seconds for Elasticsearch to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# ============================================
# STEP 4: Verify Elasticsearch
# ============================================
curl http://localhost:9200
docker-compose ps elasticsearch

# ============================================
# STEP 5: Setup Python and create index
# ============================================
cd scripts
pip install -r requirements.txt
python elasticsearch_mapping.py

# ============================================
# STEP 6: Ingest sample data (10 images)
# ============================================
python ingest_flickr_data.py --csv ..\data\csv\sample_photo_metadata.csv --limit 10 --batch-size 5
cd ..

# ============================================
# STEP 7: Start backend and frontend
# ============================================
docker-compose up -d backend frontend
Write-Host "`n⏳ Waiting 30 seconds for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# ============================================
# STEP 8: Check status
# ============================================
docker-compose ps
Write-Host "`n✅ Setup Complete!" -ForegroundColor Green
Write-Host "`n🌐 Opening application..." -ForegroundColor Cyan
Start-Process http://localhost:3000
Start-Process http://localhost:8000/docs
```

---

## 🔧 Individual Commands (Run One at a Time)

### 1. Start Docker Desktop
```powershell
# Check if Docker is running
docker version

# If error, start Docker Desktop manually:
# Press Windows Key → Search "Docker Desktop" → Open
# Wait for whale icon in system tray
```

### 2. Start Elasticsearch Only
```powershell
docker-compose up -d elasticsearch
Start-Sleep -Seconds 60
curl http://localhost:9200
```

### 3. Create Index
```powershell
cd scripts
pip install -r requirements.txt
python elasticsearch_mapping.py
```

### 4. Ingest Data
```powershell
# Small test (10 images, ~5 minutes)
python ingest_flickr_data.py --csv ..\data\csv\sample_photo_metadata.csv --limit 10

# Full dataset (may take hours)
python ingest_flickr_data.py --csv ..\data\csv\photo_metadata.csv

cd ..
```

### 5. Start Services
```powershell
# Start backend
docker-compose up -d backend

# Start frontend
docker-compose up -d frontend

# Start all at once
docker-compose up -d
```

### 6. Access Application
```powershell
# Open frontend
Start-Process http://localhost:3000

# Open API docs
Start-Process http://localhost:8000/docs
```

---

## 📊 Useful Commands

### Check Status
```powershell
# See all containers
docker-compose ps

# See resource usage
docker stats

# Check Elasticsearch
curl http://localhost:9200/_cluster/health

# Check document count
curl http://localhost:9200/flickr_images/_count
```

### View Logs
```powershell
# All logs (live)
docker-compose logs -f

# Specific service
docker-compose logs -f elasticsearch
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 50 lines
docker-compose logs --tail=50 elasticsearch
```

### Restart Services
```powershell
# Restart all
docker-compose restart

# Restart one service
docker-compose restart backend

# Rebuild and restart
docker-compose up -d --build backend
```

### Stop Services
```powershell
# Stop all (keeps data)
docker-compose down

# Stop all and delete data (⚠️ WARNING)
docker-compose down -v

# Stop one service
docker-compose stop frontend
```

---

## 🐛 Quick Fixes

### Problem: Docker Error
```powershell
# Check Docker is running
docker version

# If error, restart Docker Desktop
# Windows Key → Docker Desktop → Restart
```

### Problem: Port Already in Use
```powershell
# Find what's using port 9200
netstat -ano | findstr :9200

# Kill process (replace <PID> with actual number)
taskkill /PID <PID> /F
```

### Problem: Elasticsearch Won't Start
```powershell
# Check logs
docker-compose logs elasticsearch

# Increase Docker memory
# Docker Desktop → Settings → Resources → Memory → 8GB

# Clean restart
docker-compose down -v
docker-compose up -d elasticsearch
```

### Problem: Out of Memory
```powershell
# Reduce batch size
cd scripts
python ingest_flickr_data.py --csv ..\data\csv\sample_photo_metadata.csv --batch-size 20 --workers 2
```

---

## 🔄 Daily Workflow

### Starting Work
```powershell
# 1. Start Docker Desktop (if not running)
# 2. Start all services
docker-compose up -d

# 3. Wait for Elasticsearch
Start-Sleep -Seconds 30

# 4. Open application
Start-Process http://localhost:3000
```

### Ending Work
```powershell
# Stop all containers (keeps data)
docker-compose down

# Or leave running in background
```

---

## 📈 Performance Tips

### Fast Processing (Good PC: 16GB+ RAM)
```powershell
cd scripts
python ingest_flickr_data.py `
  --csv ..\data\csv\photo_metadata.csv `
  --batch-size 500 `
  --workers 8
```

### Slow Processing (Basic PC: 8GB RAM)
```powershell
cd scripts
python ingest_flickr_data.py `
  --csv ..\data\csv\photo_metadata.csv `
  --batch-size 20 `
  --workers 2
```

### Using GPU (10x faster)
```powershell
# Requires NVIDIA GPU + CUDA
# VGG extraction will automatically use GPU if available
python ingest_flickr_data.py --csv ..\data\csv\photo_metadata.csv
```

---

## 🎯 Testing

### Quick Test (5 minutes)
```powershell
# Ingest just 5 images
cd scripts
python ingest_flickr_data.py --csv ..\data\csv\sample_photo_metadata.csv --limit 5
cd ..

# Start services
docker-compose up -d backend frontend
Start-Sleep -Seconds 30

# Open browser
Start-Process http://localhost:3000
```

### API Testing
```powershell
# Test text search
curl -X POST http://localhost:8000/api/search/text `
  -H "Content-Type: application/json" `
  -d '{"query": "paris", "top_k": 5}'

# Test health
curl http://localhost:8000/health
```

---

## 🌐 URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Search interface |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Backend** | http://localhost:8000 | REST API |
| **Elasticsearch** | http://localhost:9200 | Search engine |
| **Kibana** | http://localhost:5601 | Admin panel (optional) |

---

## ✅ Success Checklist

```powershell
# Run this to check everything is working:
Write-Host "`n=== CBIR System Status Check ===`n" -ForegroundColor Cyan

# 1. Docker
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
docker version | Select-Object -First 3

# 2. Containers
Write-Host "`n2. Checking Containers..." -ForegroundColor Yellow
docker-compose ps

# 3. Elasticsearch
Write-Host "`n3. Checking Elasticsearch..." -ForegroundColor Yellow
curl http://localhost:9200

# 4. Document count
Write-Host "`n4. Checking Documents..." -ForegroundColor Yellow
curl http://localhost:9200/flickr_images/_count

# 5. Backend
Write-Host "`n5. Checking Backend..." -ForegroundColor Yellow
curl http://localhost:8000/health

Write-Host "`n✅ All checks complete!`n" -ForegroundColor Green
```

---

**💡 Tip:** Bookmark this file for quick reference!

**📖 Full Guide:** See `SETUP_GUIDE.md` for detailed explanations

**🆘 Issues?** Run status check above and check logs: `docker-compose logs -f`
