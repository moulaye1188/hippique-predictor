#!/usr/bin/env python3
"""
Quick setup script for Hippique Predictor
Runs on host machine before Docker launch
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def check_docker():
    """Check if Docker is installed"""
    try:
        subprocess.run(['docker', '--version'], capture_output=True, check=True)
        print("✅ Docker is installed")
        return True
    except:
        print("❌ Docker is not installed")
        print("   Install from: https://www.docker.com/products/docker-desktop")
        return False

def check_docker_daemon():
    """Check if Docker daemon is running"""
    try:
        subprocess.run(['docker', 'info'], capture_output=True, check=True)
        print("✅ Docker daemon is running")
        return True
    except:
        print("❌ Docker daemon is not running")
        print("   Please start Docker Desktop")
        return False

def build_and_launch():
    """Build and launch the application"""
    print_header("Building Docker Image")
    try:
        subprocess.run(['docker-compose', 'build', '--no-cache'], check=True)
        print("✅ Build successful\n")
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return False
    
    print_header("Launching Application")
    try:
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        print("✅ Application launched\n")
    except Exception as e:
        print(f"❌ Launch failed: {e}")
        return False
    
    print("⏳ Waiting for application to be ready (30-40 seconds)...")
    import time
    time.sleep(40)
    
    print_header("Checking Health")
    for i in range(5):
        try:
            import urllib.request
            response = urllib.request.urlopen('http://localhost:5000/api/health', timeout=5)
            if response.status == 200:
                print("✅ Application is healthy\n")
                return True
        except:
            if i < 4:
                print(f"Attempt {i+1}/5...")
                time.sleep(5)
            else:
                print("⚠️ Application is starting but not fully ready")
                print("Check logs: docker-compose logs -f app\n")
                return True
    
    return True

def print_success():
    """Print success message"""
    print_header("🎉 Setup Complete!")
    print("Access the application:")
    print("  🌐 Frontend: http://localhost:5000")
    print("  🔌 API Health: http://localhost:5000/api/health\n")
    print("Useful commands:")
    print("  docker-compose logs -f app    - View logs")
    print("  docker-compose down           - Stop application")
    print("  docker-compose ps             - Check status\n")

def main():
    print_header("Hippique Predictor Setup")
    
    # Check Docker installation
    if not check_docker():
        return False
    
    # Check Docker daemon
    if not check_docker_daemon():
        return False
    
    # Build and launch
    if not build_and_launch():
        return False
    
    print_success()
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
