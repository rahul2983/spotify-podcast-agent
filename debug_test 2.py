#!/usr/bin/env python3
"""
Minimal debug test to identify the root cause
"""
import sys
from unittest.mock import patch, Mock

def test_minimal_patch():
    """Test patching without importing problematic modules"""
    print("=== Minimal Patch Test ===")
    
    # Test 1: Can we patch at all?
    try:
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            import os
            result = os.path.exists("/fake/path")
            print(f"✓ Basic patching works: {result}")
    except Exception as e:
        print(f"✗ Basic patching failed: {e}")
        return
    
    # Test 2: Can we patch a module that doesn't exist yet?
    try:
        with patch('spotify_agent.fake_module.FakeClass') as MockClass:
            MockClass.return_value = Mock()
            print("✓ Can patch non-existent modules")
    except Exception as e:
        print(f"✓ Expected error for non-existent module: {e}")
    
    # Test 3: Check if your modules are even importable
    print("\n=== Module Import Test ===")
    try:
        print("Attempting to import spotify_agent...")
        import spotify_agent
        print(f"✓ spotify_agent imported: {spotify_agent}")
    except Exception as e:
        print(f"✗ Cannot import spotify_agent: {e}")
        return
    
    try:
        print("Attempting to import spotify_agent.config...")
        from spotify_agent.config import AgentConfig
        print("✓ AgentConfig imported successfully")
    except Exception as e:
        print(f"✗ Cannot import AgentConfig: {e}")
        return
    
    # Test 4: Check what happens when we try to create config
    try:
        print("Creating AgentConfig with fake keys...")
        config = AgentConfig(
            openai_api_key="fake_key",
            spotify_client_id="fake_id",
            spotify_client_secret="fake_secret"
        )
        print("✓ AgentConfig created without issues")
    except Exception as e:
        print(f"✗ AgentConfig creation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n=== Test Complete - Basic setup is working ===")

def test_individual_imports():
    """Test importing each problematic module individually"""
    print("\n=== Individual Import Test ===")
    
    modules_to_test = [
        'spotify_agent.spotify_client',
        'spotify_agent.llm_agent', 
        'spotify_agent.queue_manager',
        'spotify_agent.agent'
    ]
    
    for module_name in modules_to_test:
        try:
            print(f"Importing {module_name}...")
            __import__(module_name)
            print(f"✓ {module_name} imported successfully")
        except Exception as e:
            print(f"✗ {module_name} import failed: {e}")
            if "API" in str(e) or "401" in str(e) or "key" in str(e).lower():
                print("  ^ This module is making API calls during import!")
            import traceback
            traceback.print_exc()
            print()

if __name__ == "__main__":
    print("Starting minimal debug test...")
    test_minimal_patch()
    test_individual_imports()