#!/usr/bin/env python3
"""
Test script to verify Ollama connection and model availability
Run this after installing Ollama to ensure everything is working
"""
import sys
from llmservice import ollama_service

def main():
    print("=" * 60)
    print("OLLAMA CONNECTION TEST")
    print("=" * 60)
    
    # Test 1: Check if Ollama is running
    print("\n1. Testing Ollama availability...")
    if ollama_service.check_availability():
        print("   ✅ Ollama is running and accessible")
    else:
        print("   ❌ Ollama is not running or not accessible")
        print("   💡 Please ensure Ollama is installed and running:")
        print("      - Install: curl -fsSL https://ollama.com/install.sh | sh")
        print("      - Run: ollama serve (in another terminal)")
        sys.exit(1)
    
    # Test 2: Test basic prompt
    print("\n2. Testing basic AI response...")
    test_prompt = "Hello! Please respond with 'AI Analytics is working!' to confirm you're operational."
    
    print(f"   Sending test prompt: '{test_prompt}'")
    response = ollama_service.generate_response(test_prompt)
    
    if response and not response.startswith("Error:"):
        print(f"   ✅ Response received: {response[:100]}...")
        print("   🎉 AI Analytics is fully operational!")
    else:
        print(f"   ❌ Error: {response}")
        print("   💡 Try pulling the model: ollama pull llama3.2:3b")
        sys.exit(1)
    
    # Test 3: Test with context
    print("\n3. Testing AI with insurance context...")
    context = {
        'role': 'admin',
        'data_summary': '- Total Policies: 150\n- Active Claims: 12\n- Total Customers: 85'
    }
    
    analytics_prompt = "Based on the data, what insights can you provide?"
    response = ollama_service.generate_response(analytics_prompt, context=context)
    
    if response and not response.startswith("Error:"):
        print(f"   ✅ Context-aware response received!")
        print(f"   Response preview: {response[:200]}...")
    else:
        print(f"   ⚠️  Warning: {response}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE - AI Analytics is ready to use!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("   1. Start your Flask app: flask run")
    print("   2. Login to any dashboard")
    print("   3. Click the 'AI Analytics' button")
    print("   4. Start asking questions about your data!")
    print("\n")

if __name__ == "__main__":
    main()
