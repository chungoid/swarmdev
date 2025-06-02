#!/usr/bin/env python3
"""
Debug script to test context7 and filesystem containers specifically
"""

import sys
import os
import json
import time

# Add SwarmDev source to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, 'src'))
os.chdir(project_root)

from swarmdev.utils.mcp_manager import MCPManager

def test_single_container(tool_id: str, test_call: dict):
    """Test a single container with detailed debugging."""
    print(f"\n{'='*60}")
    print(f"TESTING: {tool_id}")
    print(f"{'='*60}")
    
    # Initialize MCP Manager
    config = {'enabled': True}
    mcp_manager = MCPManager(config)
    
    print("1. Configuration loading...")
    init_success = mcp_manager.initialize_tools()
    print(f"   Initialize tools: {init_success}")
    
    available_tools = mcp_manager.get_available_tools()
    print(f"   Available tools: {available_tools}")
    
    if tool_id not in available_tools:
        print(f"   ❌ {tool_id} not in available tools")
        return False
    
    tool_info = mcp_manager.get_tool_info(tool_id)
    print(f"   Tool info: {tool_info}")
    print(f"   Command: {' '.join(tool_info.get('command', []))}")
    
    print(f"\n2. Testing {tool_id} with call:")
    print(f"   Method: tools/call")
    print(f"   Params: {json.dumps(test_call, indent=2)}")
    
    print(f"\n3. Making actual call...")
    start_time = time.time()
    try:
        result = mcp_manager.call_tool(
            tool_id,
            "tools/call", 
            test_call,
            timeout=30  # Longer timeout for debugging
        )
        duration = time.time() - start_time
        
        print(f"   Duration: {duration:.2f}s")
        print(f"   Result type: {type(result)}")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        if result.get("error"):
            print(f"   ❌ Error: {result['error']}")
            return False
        else:
            print(f"   ✅ Success!")
            # Print first 200 chars of result
            result_str = str(result)
            if len(result_str) > 200:
                print(f"   Result preview: {result_str[:200]}...")
            else:
                print(f"   Result: {result_str}")
            return True
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"   Duration: {duration:.2f}s")
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Docker Container Debug Test")
    print("Testing problematic containers: context7 and filesystem")
    
    # Test context7
    context7_success = test_single_container("context7", {
        "name": "resolve-library-id",
        "arguments": {"libraryName": "python"}
    })
    
    # Test filesystem  
    filesystem_success = test_single_container("filesystem", {
        "name": "list_directory", 
        "arguments": {"path": "."}
    })
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"context7: {'✅ PASS' if context7_success else '❌ FAIL'}")
    print(f"filesystem: {'✅ PASS' if filesystem_success else '❌ FAIL'}")
    
    if context7_success and filesystem_success:
        print("\n🎉 Both containers work when called individually!")
    else:
        print("\n💀 Container initialization issues confirmed")
        print("\nPossible causes:")
        print("- Docker container startup timeout")
        print("- Container communication/networking issues")
        print("- Missing dependencies in containers")
        print("- Docker daemon configuration problems")

if __name__ == "__main__":
    main() 