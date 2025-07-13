#!/usr/bin/env python
"""
Simple script to run the AI Student Django web application.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the Django development server."""
    
    # Get the project directory
    project_dir = Path(__file__).parent
    
    # Check if we're in the right directory
    if not (project_dir / 'manage.py').exists():
        print("❌ Error: manage.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Virtual environment not detected. It's recommended to activate your virtual environment.")
    
    # Check if .env file exists
    env_file = project_dir / '.env'
    if not env_file.exists():
        print("⚠️  Warning: .env file not found. Please create one with your API keys.")
        print("   Required keys: GOOGLE_API_KEY, TOGETHER_API_KEY")
    
    # Install requirements if needed
    requirements_file = project_dir / 'requirements_web.txt'
    if requirements_file.exists():
        print("📦 Installing/updating requirements...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)], 
                         check=True, capture_output=True)
            print("✅ Requirements installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing requirements: {e}")
            sys.exit(1)
    
    # Run Django migrations
    print("🔄 Running Django migrations...")
    try:
        subprocess.run([sys.executable, 'manage.py', 'migrate'], 
                      check=True, capture_output=True)
        print("✅ Migrations completed!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running migrations: {e}")
        sys.exit(1)
    
    # Collect static files
    print("📁 Collecting static files...")
    try:
        subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], 
                      check=True, capture_output=True)
        print("✅ Static files collected!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error collecting static files: {e}")
        sys.exit(1)
    
    # Start the development server
    print("🚀 Starting AI Student web application...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        subprocess.run([sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'])
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 