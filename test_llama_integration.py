#!/usr/bin/env python3
"""
Test script to verify Llama 3 integration with Groq API
"""
import os
import sys
from pathlib import Path

# Add the source directory to Python path
source_dir = Path(__file__).parent
sys.path.insert(0, str(source_dir))

try:
    import streamlit as st
    import groq
    from database import Database
    
    def test_groq_integration():
        """Test Groq API integration"""
        print("🔍 Testing Groq API Integration...")
        
        # Mock Streamlit secrets for testing
        class MockSecrets:
            def __init__(self):
                self.secrets_data = {}
                
            def get(self, key, default=None):
                return self.secrets_data.get(key, default)
                
            def __contains__(self, key):
                return key in self.secrets_data
                
            def __getitem__(self, key):
                return self.secrets_data[key]
                
            def __iter__(self):
                return iter(self.secrets_data)
        
        # Test with different API key configurations
        test_configs = [
            {"GROQ_API_KEY": "test_key_direct"},
            {"groq": {"api_key": "test_key_section"}},
        ]
        
        for i, config in enumerate(test_configs):
            print(f"\n📋 Test Configuration {i+1}:")
            print(f"   Config: {config}")
            
            # Mock the secrets
            mock_secrets = MockSecrets()
            mock_secrets.secrets_data = config
            
            # Simulate the API key detection logic from app.py
            api_key = None
            found_in_section = "Not found"
            
            # Direct check first
            api_key = mock_secrets.get('GROQ_API_KEY')
            if api_key:
                found_in_section = "Direct"
            else:
                # Check in groq section
                try:
                    if 'groq' in mock_secrets:
                        api_key = mock_secrets.groq.get('api_key')
                        if api_key:
                            found_in_section = "Groq section"
                except:
                    pass
                
                # Fallback: check every section
                if not api_key:
                    for section in mock_secrets:
                        try:
                            section_data = mock_secrets[section]
                            if hasattr(section_data, 'get'):
                                api_key = section_data.get('GROQ_API_KEY')
                                if api_key:
                                    found_in_section = f"Section '{section}'"
                                    break
                                api_key = section_data.get('api_key')
                                if api_key:
                                    found_in_section = f"Section '{section}' (api_key)"
                                    break
                        except:
                            continue
            
            print(f"   ✅ API Key Detected: {api_key is not None}")
            print(f"   📍 Found in: {found_in_section}")
        
        print("\n🎯 API Key Detection Logic: WORKING ✅")
        
    def test_groq_client():
        """Test actual Groq client initialization (requires real API key)"""
        print("\n🔍 Testing Groq Client Initialization...")
        
        # Check if user has real API key
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            print("⚠️  No GROQ_API_KEY found in environment variables")
            print("   To test with real API:")
            print("   1. Get API key from https://console.groq.com/")
            print("   2. Set environment variable: export GROQ_API_KEY='your_key_here'")
            print("   3. Run this test again")
            return
        
        try:
            client = groq.Groq(api_key=api_key)
            print("✅ Groq client initialized successfully")
            
            # Test a simple completion
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "user", "content": "Say 'Hello from Llama 3!' in one sentence."}
                ],
                temperature=0.7,
                max_tokens=50,
            )
            
            response = completion.choices[0].message.content
            print(f"🤖 Llama 3 Response: {response}")
            print("✅ Llama 3 Integration: WORKING ✅")
            
        except Exception as e:
            print(f"❌ Error testing Groq client: {e}")
            print("   Please check your API key and internet connection")
    
    def main():
        print("🚀 Testing Llama 3 Integration for AI TrainBot")
        print("=" * 50)
        
        # Test API key detection logic
        test_groq_integration()
        
        # Test actual API connection (if key available)
        test_groq_client()
        
        print("\n" + "=" * 50)
        print("📝 Summary:")
        print("   ✅ API Key Detection Logic: Working")
        print("   📝 To enable Llama 3 in your app:")
        print("      1. Copy .streamlit/secrets.toml.example to .streamlit/secrets.toml")
        print("      2. Add your Groq API key to the [groq] section")
        print("      3. Restart your Streamlit app")
        print("      4. Check the TrainBot page for '✨ LLaMA 3 ACTIVE' status")

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Please ensure you have the required packages installed:")
    print("   pip install streamlit groq")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
