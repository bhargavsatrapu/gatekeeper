#!/usr/bin/env python3
"""
GATEKEEPER Setup Script
Quick setup script for the GATEKEEPER API testing framework
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def print_banner():
    print("🚀 GATEKEEPER - API Testing Framework Setup")
    print("=" * 50)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    print("✅ Python version:", sys.version)
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_database():
    """Setup database connection"""
    print("\n🗄️ Setting up database...")
    
    # Check if PostgreSQL is available
    try:
        import psycopg2
        print("✅ PostgreSQL driver available")
        
        # Try to connect to default database
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="0000",
                host="localhost",
                port="5432"
            )
            conn.close()
            print("✅ PostgreSQL connection successful")
            
            # Create gatekeeper database if it doesn't exist
            try:
                conn = psycopg2.connect(
                    dbname="postgres",
                    user="postgres",
                    password="0000",
                    host="localhost",
                    port="5432"
                )
                conn.autocommit = True
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM pg_database WHERE datname = 'gatekeeper'")
                if not cur.fetchone():
                    cur.execute("CREATE DATABASE gatekeeper")
                    print("✅ Created 'gatekeeper' database")
                else:
                    print("✅ 'gatekeeper' database already exists")
                cur.close()
                conn.close()
                return True
            except Exception as e:
                print(f"❌ Failed to create database: {e}")
                return False
                
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            print("💡 Please ensure PostgreSQL is running and accessible")
            return False
            
    except ImportError:
        print("❌ PostgreSQL driver not available")
        print("💡 Install with: pip install psycopg2-binary")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    directories = ["uploads", "screenshots", "reports"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/ directory")

def setup_environment():
    """Setup environment variables"""
    print("\n⚙️ Setting up environment...")
    
    env_file = ".env"
    env_content = """# GATEKEEPER Environment Configuration
DB_NAME=gatekeeper
DB_USER=postgres
DB_PASSWORD=0000
DB_HOST=localhost
DB_PORT=5432
API_BASE_URL=http://localhost:8000
SCREENSHOT_DIR=screenshots
MAX_TEST_TIMEOUT=30
ENABLE_SCREENSHOTS=true
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Created {env_file} file")
        print("💡 You can modify these values as needed")
        return True
    except Exception as e:
        print(f"❌ Failed to create {env_file}: {e}")
        return False

def run_tests():
    """Run basic tests to verify setup"""
    print("\n🧪 Running basic tests...")
    try:
        # Test database connection
        from app.db.pool import init_pool, close_pool
        init_pool()
        print("✅ Database connection test passed")
        close_pool()
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start the server:")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n2. Open your browser and navigate to:")
    print("   Main Interface: http://localhost:8000/ui/")
    print("   Testing Interface: http://localhost:8000/ui/testing.html")
    print("\n3. Upload a Swagger/OpenAPI specification file")
    print("4. Generate test cases and start testing!")
    print("\n📚 For more information, see README.md")

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("\n❌ Database setup failed. Please check PostgreSQL configuration.")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup environment
    if not setup_environment():
        print("\n⚠️ Environment setup failed, but continuing...")
    
    # Run tests
    if not run_tests():
        print("\n⚠️ Basic tests failed, but setup may still work...")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
