#!/usr/bin/env python3
"""
Setup Script for Financial Document Analyzer with Queue System
This script helps set up the enhanced version with Redis queue and database
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr.strip()}")
        return False

def check_redis():
    """Check if Redis is available"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running and accessible")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    # Upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    if Path("requirements.txt").exists():
        return run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing dependencies")
    else:
        print("❌ requirements.txt not found")
        return False

def setup_database():
    """Initialize database"""
    print("\n🗄️ Setting up database...")
    try:
        from database import create_tables
        create_tables()
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("\n📝 Creating .env file from template...")
            with open(".env.example", "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print("✅ .env file created from .env.example")
            print("⚠️  Please edit .env file and add your API keys")
            return True
        else:
            print("❌ .env.example file not found")
            return False
    else:
        print("✅ .env file already exists")
        return True

def setup_directories():
    """Create necessary directories"""
    dirs = ["data", "outputs", "logs"]
    print(f"\n📁 Creating directories: {', '.join(dirs)}")
    
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Directory '{dir_name}' ready")
    
    return True

def print_instructions():
    """Print setup completion instructions"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 NEXT STEPS:")
    print("1. Edit the .env file and add your API keys:")
    print("   - GOOGLE_API_KEY (for AI analysis)")
    print("   - SERPER_API_KEY (for web search)")
    
    print("\n2. Install and start Redis (if not already running):")
    
    if platform.system() == "Windows":
        print("   - Download Redis from: https://github.com/microsoftarchive/redis/releases")
        print("   - Or use Docker: docker run -p 6379:6379 redis:alpine")
    elif platform.system() == "Darwin":  # macOS
        print("   - brew install redis")
        print("   - brew services start redis")
    else:  # Linux
        print("   - sudo apt-get install redis-server (Ubuntu/Debian)")
        print("   - sudo systemctl start redis")
    
    print("\n3. Start the application:")
    print("   Terminal 1 (API Server):")
    print("   python main.py")
    print("")
    print("   Terminal 2 (Worker):")
    print("   python start_worker.py")
    
    print("\n4. Optional - Monitor with Flower:")
    print("   celery -A celery_config flower --port=5555")
    print("   Then visit: http://localhost:5555")
    
    print("\n5. Access the application:")
    print("   API: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print("   Health: http://localhost:8000/health")
    
    print("\n📊 NEW FEATURES:")
    print("✨ Queue-based processing for concurrent requests")
    print("✨ Database storage for analysis history")
    print("✨ Real-time status monitoring")
    print("✨ Background worker processing")
    print("✨ System health checks and statistics")
    
    print("\n" + "="*60)

def main():
    """Main setup function"""
    print("🚀 Financial Document Analyzer Setup")
    print("Setting up enhanced version with Queue System and Database")
    print("="*60)
    
    success = True
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python {sys.version}")
    
    # Setup steps
    success &= create_env_file()
    success &= setup_directories()
    success &= install_dependencies()
    success &= setup_database()
    
    # Check Redis (optional - will warn if not available)
    redis_available = check_redis()
    if not redis_available:
        print("⚠️  Redis not available - queue features will not work until Redis is installed")
    
    if success:
        print_instructions()
        return True
    else:
        print("\n❌ Setup encountered errors. Please check the output above.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)