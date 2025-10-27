#!/usr/bin/env python3
"""
CBIR Project Verification Script
Checks that all components are properly set up
"""

import os
import sys
from pathlib import Path
import json

def print_header(text):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_mark(condition):
    """Return checkmark or X based on condition"""
    return "✓" if condition else "✗"

def check_files():
    """Verify all required files exist"""
    print_header("Checking Project Files")
    
    required_files = {
        "Backend": [
            "backend/main.py",
            "backend/config.py",
            "backend/database.py",
            "backend/requirements.txt",
            "backend/Dockerfile",
            "backend/init.sql",
            "backend/.env",
        ],
        "Frontend": [
            "frontend/package.json",
            "frontend/next.config.js",
            "frontend/tsconfig.json",
            "frontend/Dockerfile",
            "frontend/app/page.tsx",
            "frontend/app/layout.tsx",
            "frontend/.env.local",
        ],
        "Backend Routers": [
            "backend/routers/__init__.py",
            "backend/routers/search.py",
            "backend/routers/images.py",
            "backend/routers/index.py",
        ],
        "Backend Utils": [
            "backend/utils/__init__.py",
            "backend/utils/descriptor_extractor.py",
            "backend/utils/faiss_search.py",
            "backend/utils/build_index.py",
        ],
        "Frontend Components": [
            "frontend/components/ImageUploader.tsx",
            "frontend/components/DescriptorSelector.tsx",
            "frontend/components/ResultsGrid.tsx",
        ],
        "Frontend Lib": [
            "frontend/lib/api.ts",
            "frontend/lib/types.ts",
        ],
        "Documentation": [
            "README.md",
            "QUICKSTART.md",
            "API.md",
            "STRUCTURE.md",
            "ARCHITECTURE.md",
            "TROUBLESHOOTING.md",
            "PROJECT_SUMMARY.md",
            "DOCUMENTATION_INDEX.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            "LICENSE",
            "START_HERE.md",
        ],
        "Root Files": [
            "docker-compose.yml",
            ".gitignore",
            "demo.py",
            "generate_samples.py",
            "setup.ps1",
        ],
        "Data Directories": [
            "data/images/.gitkeep",
            "data/descriptors/.gitkeep",
            "data/indexes/.gitkeep",
            "data/db/.gitkeep",
        ],
    }
    
    total_files = 0
    missing_files = 0
    
    for category, files in required_files.items():
        print(f"\n{category}:")
        category_missing = 0
        
        for file_path in files:
            exists = os.path.exists(file_path)
            total_files += 1
            if not exists:
                missing_files += 1
                category_missing += 1
            
            status = check_mark(exists)
            print(f"  {status} {file_path}")
        
        if category_missing == 0:
            print(f"  ✓ All {len(files)} files present")
    
    print(f"\nTotal: {total_files - missing_files}/{total_files} files present")
    
    if missing_files > 0:
        print(f"\n⚠️  Warning: {missing_files} files are missing!")
        return False
    else:
        print("\n✓ All required files are present!")
        return True

def check_directories():
    """Verify directory structure"""
    print_header("Checking Directory Structure")
    
    required_dirs = [
        "backend",
        "backend/routers",
        "backend/models",
        "backend/utils",
        "frontend",
        "frontend/app",
        "frontend/components",
        "frontend/lib",
        "data",
        "data/images",
        "data/descriptors",
        "data/indexes",
        "data/db",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        exists = os.path.isdir(dir_path)
        all_exist = all_exist and exists
        status = check_mark(exists)
        print(f"  {status} {dir_path}/")
    
    if all_exist:
        print("\n✓ All directories present!")
    else:
        print("\n✗ Some directories are missing!")
    
    return all_exist

def check_docker_compose():
    """Check docker-compose.yml configuration"""
    print_header("Checking Docker Compose Configuration")
    
    if not os.path.exists("docker-compose.yml"):
        print("✗ docker-compose.yml not found!")
        return False
    
    try:
        with open("docker-compose.yml", 'r') as f:
            content = f.read()
        
        required_services = ["backend", "frontend", "db"]
        all_present = True
        
        for service in required_services:
            present = f"  {service}:" in content or f"  {service}:\n" in content
            all_present = all_present and present
            status = check_mark(present)
            print(f"  {status} Service: {service}")
        
        # Check for volumes
        volumes_present = "volumes:" in content
        status = check_mark(volumes_present)
        print(f"  {status} Volume mounts configured")
        
        # Check for ports
        ports_check = all([
            "3000" in content,  # Frontend
            "8000" in content,  # Backend
            "5432" in content,  # Database
        ])
        status = check_mark(ports_check)
        print(f"  {status} Port mappings configured")
        
        if all_present and volumes_present and ports_check:
            print("\n✓ Docker Compose configuration looks good!")
            return True
        else:
            print("\n✗ Docker Compose configuration has issues!")
            return False
            
    except Exception as e:
        print(f"✗ Error reading docker-compose.yml: {e}")
        return False

def check_image_count():
    """Count images in data directory"""
    print_header("Checking Image Data")
    
    image_dir = Path("data/images")
    if not image_dir.exists():
        print("✗ data/images directory not found!")
        return 0
    
    extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
    image_files = []
    
    for ext in extensions:
        image_files.extend(list(image_dir.glob(f'*{ext}')))
        image_files.extend(list(image_dir.glob(f'*{ext.upper()}')))
    
    count = len(image_files)
    
    if count == 0:
        print("  ⚠️  No images found in data/images/")
        print("  💡 Run: python generate_samples.py")
    elif count < 10:
        print(f"  ⚠️  Only {count} images found")
        print("  💡 Add more images for better testing")
    else:
        print(f"  ✓ {count} images found")
    
    return count

def generate_report():
    """Generate comprehensive verification report"""
    print("\n" + "="*60)
    print("  CBIR PROJECT VERIFICATION REPORT")
    print("="*60)
    
    results = {
        "files": check_files(),
        "directories": check_directories(),
        "docker": check_docker_compose(),
    }
    
    image_count = check_image_count()
    results["images"] = image_count > 0
    
    print_header("Summary")
    
    print("\nComponent Status:")
    for component, status in results.items():
        mark = check_mark(status)
        print(f"  {mark} {component.capitalize()}: {'PASS' if status else 'FAIL'}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("  ✅ ALL CHECKS PASSED!")
        print("="*60)
        print("\n🎉 Your CBIR project is ready!")
        print("\nNext steps:")
        print("  1. Run: .\\setup.ps1")
        print("  2. Or follow QUICKSTART.md")
        print("  3. Open: http://localhost:3000")
    else:
        print("  ⚠️  SOME CHECKS FAILED")
        print("="*60)
        print("\n⚠️  Please review the failures above")
        print("\nTroubleshooting:")
        print("  1. Check TROUBLESHOOTING.md")
        print("  2. Ensure all files were created")
        print("  3. Run setup again if needed")
    
    print("\n" + "="*60)
    
    return all_passed

if __name__ == "__main__":
    success = generate_report()
    sys.exit(0 if success else 1)
