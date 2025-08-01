#!/usr/bin/env python3
"""
StudyMate Demo Script
Run this script to test the installation and basic functionality
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if all dependencies are installed"""
    try:
        import streamlit
        import openai
        import PyPDF2
        import sentence_transformers
        import faiss
        import speech_recognition
        import pydub
        
        print("✅ All core dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def check_env_file():
    """Check if .env file exists"""
    env_path = Path('.env')
    if env_path.exists():
        print("✅ .env file found")
        return True
    else:
        print("⚠️  .env file not found - copy .env.template to .env and add your OpenAI API key")
        return False

def check_openai_key():
    """Check if OpenAI API key is configured"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key.startswith('sk-'):
            print("✅ OpenAI API key configured")
            return True
        else:
            print("⚠️  OpenAI API key not properly configured")
            return False
    except Exception as e:
        print(f"⚠️  Could not check OpenAI API key: {e}")
        return False

def test_modules():
    """Test core module imports"""
    try:
        from utils.pdf_processor import PDFProcessor
        from utils.vector_store import VectorStore
        from utils.speech_handler import SpeechHandler
        
        print("✅ All custom modules can be imported")
        return True
    except ImportError as e:
        print(f"❌ Module import error: {e}")
        return False

def run_basic_tests():
    """Run basic functionality tests"""
    try:
        # Test PDF Processor
        from utils.pdf_processor import PDFProcessor
        processor = PDFProcessor()
        print("✅ PDF Processor initialized")
        
        # Test Vector Store
        from utils.vector_store import VectorStore
        vector_store = VectorStore()
        print("✅ Vector Store initialized")
        
        # Test Speech Handler
        from utils.speech_handler import SpeechHandler
        speech_handler = SpeechHandler()
        print("✅ Speech Handler initialized")
        
        return True
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False

def main():
    """Main demo function"""
    print("🔍 StudyMate Installation Check")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("OpenAI API Key", check_openai_key),
        ("Module Imports", test_modules),
        ("Basic Functionality", run_basic_tests)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n📋 {name}:")
        if check_func():
            passed += 1
        else:
            print(f"   Issue with {name}")
    
    print("\n" + "=" * 40)
    print(f"📊 Summary: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! StudyMate is ready to use.")
        print("\n🚀 To start StudyMate, run:")
        print("   streamlit run app.py")
    else:
        print("⚠️  Some issues need to be resolved before using StudyMate.")
        print("\n🔧 Common solutions:")
        print("   1. Install missing dependencies: pip install -r requirements.txt")
        print("   2. Copy .env.template to .env and add your OpenAI API key")
        print("   3. Ensure you have Python 3.8 or higher")
    
    print("\n📚 For more help, see the README.md file")

if __name__ == "__main__":
    main()
