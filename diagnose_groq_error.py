#!/usr/bin/env python3
"""
Diagnostic script to troubleshoot Groq API 400 errors
"""
import os
import sys
import json
from pathlib import Path

# Add the source directory to Python path
source_dir = Path(__file__).parent
sys.path.insert(0, str(source_dir))

try:
    import groq
    
    def test_api_key_format():
        """Test if API key format is correct"""
        print("🔍 Checking API Key Format...")
        
        # Common API key formats
        valid_formats = [
            "gsk_",  # Groq API keys start with this
        ]
        
        # Check environment variable
        env_key = os.environ.get('GROQ_API_KEY')
        if env_key:
            print(f"   📋 Found in environment: {env_key[:10]}...")
            if env_key.startswith('gsk_'):
                print("   ✅ Format looks correct (starts with gsk_)")
            else:
                print("   ❌ Invalid format - should start with 'gsk_'")
                return False
        else:
            print("   ⚠️  No API key in environment variables")
        
        return True
    
    def test_groq_models():
        """Test available models on Groq"""
        print("\n🤖 Testing Available Models...")
        
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            print("   ❌ No API key found - set GROQ_API_KEY environment variable")
            return False
        
        try:
            client = groq.Groq(api_key=api_key)
            
            # Test model list
            models = client.models.list()
            print("   ✅ Successfully connected to Groq API")
            
            # Find Llama models
            llama_models = [model.id for model in models.data if 'llama' in model.id.lower()]
            print(f"   🤖 Available Llama models: {llama_models}")
            
            # Check if our target model exists
            target_model = "llama3-8b-8192"
            if target_model in llama_models:
                print(f"   ✅ Target model '{target_model}' is available")
            else:
                print(f"   ⚠️  Target model '{target_model}' not found")
                print(f"   💡 Available models: {[m.id for m in models.data[:5]]}")  # Show first 5
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error listing models: {e}")
            return False
    
    def test_simple_completion():
        """Test a simple API completion"""
        print("\n💬 Testing Simple Completion...")
        
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            print("   ❌ No API key found")
            return False
        
        try:
            client = groq.Groq(api_key=api_key)
            
            # Simple test completion
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "user", "content": "Say 'Hello' in one word."}
                ],
                temperature=0.7,
                max_tokens=10,
            )
            
            response = completion.choices[0].message.content
            print(f"   ✅ Response: {response}")
            return True
            
        except Exception as e:
            error_str = str(e)
            print(f"   ❌ Completion failed: {e}")
            
            # Parse specific errors
            if "400" in error_str:
                print("\n🔍 400 Error Analysis:")
                if "api_key" in error_str.lower():
                    print("   🔑 Issue: Invalid API key format or permissions")
                elif "model" in error_str.lower():
                    print("   🤖 Issue: Model not available or incorrect model name")
                elif "messages" in error_str.lower():
                    print("   💬 Issue: Message format incorrect")
                else:
                    print("   ❓ Issue: Request format problem")
            
            return False
    
    def check_secrets_config():
        """Check secrets.toml configuration"""
        print("\n📁 Checking Secrets Configuration...")
        
        secrets_path = source_dir / ".streamlit" / "secrets.toml"
        if secrets_path.exists():
            print("   ✅ secrets.toml file exists")
            print("   🔒 Contents are hidden for security")
            print("   💡 Verify your API key is correctly formatted in the file")
        else:
            print("   ❌ secrets.toml not found")
            print("   💡 Copy secrets.toml.example to secrets.toml and add your API key")
        
        return secrets_path.exists()
    
    def main():
        print("🚀 Groq API 400 Error Diagnostic Tool")
        print("=" * 50)
        
        # Run all diagnostic tests
        tests = [
            ("API Key Format", test_api_key_format),
            ("Secrets Configuration", check_secrets_config),
            ("Groq Models", test_groq_models),
            ("Simple Completion", test_simple_completion),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"   ❌ {test_name} failed with error: {e}")
                results[test_name] = False
        
        print("\n" + "=" * 50)
        print("📊 Diagnostic Summary:")
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status}: {test_name}")
        
        print("\n🔧 Common 400 Error Solutions:")
        print("   1. **Invalid API Key**:")
        print("      - Get a new key from https://console.groq.com/")
        print("      - Ensure it starts with 'gsk_'")
        print("      - Check for extra spaces or quotes")
        
        print("\n   2. **Model Issues**:")
        print("      - Verify 'llama3-8b-8192' is available")
        print("      - Try alternative model: 'llama-3.1-8b-instant'")
        
        print("\n   3. **Configuration**:")
        print("      - Check .streamlit/secrets.toml format")
        print("      - Restart Streamlit after changing secrets")
        print("      - Ensure no syntax errors in TOML file")
        
        print("\n   4. **Rate Limits**:")
        print("      - Free tier: 30 requests/minute")
        print("      - Wait a moment between requests")
        
        # Quick fix suggestions
        if not results.get("API Key Format", False):
            print("\n🎯 Quick Fix: Check your API key format")
        elif not results.get("Groq Models", False):
            print("\n🎯 Quick Fix: Test with a different model")
        elif not results.get("Simple Completion", False):
            print("\n🎯 Quick Fix: Check Groq service status")

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Please install: pip install groq")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
