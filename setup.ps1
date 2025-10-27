# CBIR Setup Script for Windows PowerShell
# This script helps you get started with the CBIR system

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   CBIR Image Search Engine Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker is installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not installed!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Ask if user wants to generate sample images
$generateSamples = Read-Host "Do you want to generate sample images? (y/n)"
if ($generateSamples -eq "y" -or $generateSamples -eq "Y") {
    Write-Host "Generating 100 sample images..." -ForegroundColor Yellow
    python generate_samples.py
    Write-Host ""
}

# Start services
Write-Host "Starting Docker services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if services are running
$backendRunning = docker ps --filter "name=cbir_backend" --format "{{.Status}}" | Select-String "Up"
$frontendRunning = docker ps --filter "name=cbir_frontend" --format "{{.Status}}" | Select-String "Up"
$dbRunning = docker ps --filter "name=cbir_db" --format "{{.Status}}" | Select-String "Up"

if ($backendRunning) {
    Write-Host "✓ Backend is running" -ForegroundColor Green
} else {
    Write-Host "✗ Backend failed to start" -ForegroundColor Red
}

if ($frontendRunning) {
    Write-Host "✓ Frontend is running" -ForegroundColor Green
} else {
    Write-Host "✗ Frontend failed to start" -ForegroundColor Red
}

if ($dbRunning) {
    Write-Host "✓ Database is running" -ForegroundColor Green
} else {
    Write-Host "✗ Database failed to start" -ForegroundColor Red
}

Write-Host ""

# Check if there are images to index
$imageCount = (Get-ChildItem -Path "data\images" -Filter *.jpg,*.png,*.bmp -ErrorAction SilentlyContinue | Measure-Object).Count

if ($imageCount -gt 0) {
    Write-Host "Found $imageCount images to index" -ForegroundColor Green
    $buildIndex = Read-Host "Do you want to build the search indexes now? (y/n)"
    
    if ($buildIndex -eq "y" -or $buildIndex -eq "Y") {
        Write-Host "Building search indexes (this may take a few minutes)..." -ForegroundColor Yellow
        docker-compose exec -T backend python utils/build_index.py
        Write-Host "✓ Index building completed" -ForegroundColor Green
    } else {
        Write-Host "You can build indexes later with: docker-compose exec backend python utils/build_index.py" -ForegroundColor Yellow
    }
} else {
    Write-Host "No images found in data/images directory" -ForegroundColor Yellow
    Write-Host "Add some images first, then run: docker-compose exec backend python utils/build_index.py" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access the application:" -ForegroundColor White
Write-Host "  Frontend:     http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend API:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor White
Write-Host "  View logs:    docker-compose logs -f" -ForegroundColor Gray
Write-Host "  Stop:         docker-compose down" -ForegroundColor Gray
Write-Host "  Restart:      docker-compose restart" -ForegroundColor Gray
Write-Host "  Build index:  docker-compose exec backend python utils/build_index.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"
