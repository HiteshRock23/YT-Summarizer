#!/usr/bin/env python
"""
Test script for the AI Student Django web application.
"""

import os
import sys
import subprocess
from pathlib import Path

def test_django_setup():
    """Test Django project setup"""
    print("🔍 Testing Django project setup...")
    
    try:
        # Test Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_student_web.settings')
        import django
        django.setup()
        print("✅ Django settings loaded successfully")
        
        # Test URL configuration
        from django.urls import get_resolver
        resolver = get_resolver()
        print("✅ URL configuration loaded successfully")
        
        # Test template loading
        from django.template.loader import get_template
        template = get_template('base.html')
        print("✅ Templates loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def test_static_files():
    """Test static files configuration"""
    print("\n📁 Testing static files...")
    
    static_dir = Path(__file__).parent / 'static'
    css_file = static_dir / 'css' / 'styles.css'
    js_file = static_dir / 'js' / 'main.js'
    
    if css_file.exists():
        print("✅ CSS file found")
    else:
        print("❌ CSS file not found")
        return False
    
    if js_file.exists():
        print("✅ JavaScript file found")
    else:
        print("❌ JavaScript file not found")
        return False
    
    return True

def test_templates():
    """Test template files"""
    print("\n📄 Testing template files...")
    
    templates_dir = Path(__file__).parent / 'templates'
    base_template = templates_dir / 'base.html'
    home_template = templates_dir / 'summarizer' / 'home.html'
    result_template = templates_dir / 'summarizer' / 'result_simple.html'
    
    templates = [base_template, home_template, result_template]
    
    for template in templates:
        if template.exists():
            print(f"✅ {template.name} found")
        else:
            print(f"❌ {template.name} not found")
            return False
    
    return True

def test_dependencies():
    """Test required dependencies"""
    print("\n📦 Testing dependencies...")
    
    required_packages = [
        'django',
        'youtube_transcript_api',
        'google.generativeai',
        'together',
        'reportlab'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements_web.txt")
        return False
    
    return True

def test_api_keys():
    """Test API key configuration"""
    print("\n🔑 Testing API keys...")
    
    env_file = Path(__file__).parent / '.env'
    
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("Create .env file with:")
        print("GOOGLE_API_KEY=your_gemini_api_key")
        print("TOGETHER_API_KEY=your_together_api_key")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    google_key = os.getenv('GOOGLE_API_KEY')
    together_key = os.getenv('TOGETHER_API_KEY')
    
    if google_key:
        print("✅ Google API key found")
    else:
        print("❌ Google API key not found")
    
    if together_key:
        print("✅ Together API key found")
    else:
        print("❌ Together API key not found")
    
    return bool(google_key or together_key)

def test_core_modules():
    """Test core summarizer modules"""
    print("\n🧠 Testing core modules...")
    
    try:
        from core_summarizer import process_video
        print("✅ core_summarizer module loaded")
    except ImportError as e:
        print(f"❌ core_summarizer module failed: {e}")
        return False
    
    try:
        from llm_handler import MultiLLMHandler
        print("✅ llm_handler module loaded")
    except ImportError as e:
        print(f"❌ llm_handler module failed: {e}")
        return False
    
    try:
        from pdf_generator import generate_pdf
        print("✅ pdf_generator module loaded")
    except ImportError as e:
        print(f"❌ pdf_generator module failed: {e}")
        return False
    
    return True

def run_django_checks():
    """Run Django system checks"""
    print("\n🔧 Running Django system checks...")
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'check'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Django system checks passed")
            return True
        else:
            print(f"❌ Django system checks failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Django checks timed out")
        return False
    except Exception as e:
        print(f"❌ Django checks failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 AI Student Web Application - System Test")
    print("=" * 60)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Django Setup", test_django_setup),
        ("Static Files", test_static_files),
        ("Templates", test_templates),
        ("API Keys", test_api_keys),
        ("Core Modules", test_core_modules),
        ("Django Checks", run_django_checks),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The web application is ready to run.")
        print("\n🚀 To start the application:")
        print("   python run_web.py")
        print("\n🌐 Then open: http://localhost:8000")
    else:
        print("⚠️  Some tests failed. Please fix the issues before running the application.")
    
    print("=" * 60)

if __name__ == '__main__':
    main() 