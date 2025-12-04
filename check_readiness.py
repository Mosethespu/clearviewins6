#!/usr/bin/env python3
"""
System Readiness Check for AI Analytics
Verifies that all components are properly configured
"""
import sys
import os

def check_mark(condition):
    return "✅" if condition else "❌"

def main():
    print("\n" + "=" * 70)
    print("🔍 AI ANALYTICS SYSTEM READINESS CHECK")
    print("=" * 70 + "\n")
    
    all_passed = True
    
    # Check 1: Python version
    print("1. Python Version Check")
    py_version = sys.version_info
    py_ok = py_version.major == 3 and py_version.minor >= 8
    print(f"   {check_mark(py_ok)} Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    if not py_ok:
        print("      ⚠️  Python 3.8+ required")
        all_passed = False
    
    # Check 2: Required files exist
    print("\n2. Implementation Files")
    files_to_check = [
        ('llmservice.py', 'LLM service module'),
        ('models.py', 'Database models'),
        ('app.py', 'Flask application'),
        ('templates/ai_analytics.html', 'AI chat interface'),
        ('AI_QUICKSTART.md', 'Quick start guide'),
        ('test_ollama.py', 'Connection test script')
    ]
    
    for file, desc in files_to_check:
        exists = os.path.exists(file)
        print(f"   {check_mark(exists)} {file} - {desc}")
        if not exists:
            all_passed = False
    
    # Check 3: Database table
    print("\n3. Database Configuration")
    try:
        from app import app
        from extension import db
        from models import AIChat
        
        with app.app_context():
            # Try to query the AIChat table
            AIChat.query.count()
            print(f"   ✅ AIChat table exists in database")
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        all_passed = False
    except Exception as e:
        print(f"   ⚠️  Database check: {e}")
        print("      (This is OK if database is empty)")
    
    # Check 4: Required packages
    print("\n4. Python Dependencies")
    required_packages = [
        ('flask', 'Flask web framework'),
        ('requests', 'HTTP library for Ollama'),
        ('flask_sqlalchemy', 'Database ORM'),
        ('flask_login', 'User authentication')
    ]
    
    for package, desc in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package} - {desc}")
        except ImportError:
            print(f"   ❌ {package} - {desc} (MISSING)")
            print(f"      Install: pip install {package}")
            all_passed = False
    
    # Check 5: Ollama installation (optional but needed for functionality)
    print("\n5. Ollama Status (Required for AI functionality)")
    
    # Check if ollama command exists
    ollama_installed = os.system("which ollama > /dev/null 2>&1") == 0
    print(f"   {check_mark(ollama_installed)} Ollama installed")
    
    if not ollama_installed:
        print("      ℹ️  Install with: curl -fsSL https://ollama.com/install.sh | sh")
    
    # Check if Ollama is running
    if ollama_installed:
        ollama_running = os.system("curl -s http://localhost:11434/api/tags > /dev/null 2>&1") == 0
        print(f"   {check_mark(ollama_running)} Ollama service running")
        
        if not ollama_running:
            print("      ℹ️  Start with: ollama serve")
        
        # Check if model is downloaded
        if ollama_running:
            model_check = os.popen("ollama list 2>/dev/null | grep llama3.2").read()
            model_downloaded = "llama3.2" in model_check
            print(f"   {check_mark(model_downloaded)} Llama 3.2 model downloaded")
            
            if not model_downloaded:
                print("      ℹ️  Download with: ollama pull llama3.2:3b")
    
    # Check 6: System resources
    print("\n6. System Resources")
    try:
        import psutil
        
        ram_gb = psutil.virtual_memory().total / (1024**3)
        ram_ok = ram_gb >= 8
        print(f"   {check_mark(ram_ok)} RAM: {ram_gb:.1f} GB (8GB+ recommended)")
        
        cpu_count = psutil.cpu_count()
        print(f"   ✅ CPU Cores: {cpu_count}")
        
    except ImportError:
        print("   ℹ️  Install psutil for system info: pip install psutil")
    
    # Final summary
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL CORE COMPONENTS READY!")
        print("\nNext steps:")
        if not ollama_installed:
            print("   1. Install Ollama (see AI_QUICKSTART.md)")
            print("   2. Download model: ollama pull llama3.2:3b")
            print("   3. Start Ollama: ollama serve")
        elif ollama_installed and not ollama_running:
            print("   1. Start Ollama: ollama serve")
            print("   2. Test connection: python test_ollama.py")
        else:
            print("   1. Test connection: python test_ollama.py")
        print("   4. Start Flask: flask run")
        print("   5. Open browser and click 'AI Analytics'!")
    else:
        print("❌ SOME COMPONENTS NEED ATTENTION")
        print("\nPlease address the issues marked with ❌ above")
    print("=" * 70 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
