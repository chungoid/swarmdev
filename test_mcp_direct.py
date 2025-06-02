#!/usr/bin/env python3
"""
Direct MCP Tool Testing Script
Test each MCP tool individually to identify specific issues
"""

import sys
import os
sys.path.insert(0, '/home/flip/Documents/swarmdev/src')

from swarmdev.utils.mcp_manager import MCPManager
import json
import time

def test_single_tool(manager, tool_id):
    """Test a single MCP tool with comprehensive logging."""
    print(f"\n=== TESTING {tool_id.upper()} ===")
    
    # Check if tool is registered
    if tool_id not in manager.mcp_tools:
        print(f"❌ {tool_id} not registered")
        return False
    
    tool_info = manager.mcp_tools[tool_id]
    print(f"✅ {tool_id} registered: {tool_info['command']} {tool_info['args']}")
    print(f"   Status: {tool_info['status']}")
    print(f"   Timeout: {tool_info['timeout']}s")
    
    # Test connection with tools/list
    print(f"🔗 Testing connection...")
    start_time = time.time()
    
    try:
        result = manager.call_tool(
            tool_id=tool_id,
            method="tools/list", 
            params={},
            timeout=15,  # Shorter timeout for testing
            agent_id="test_script"
        )
        
        duration = time.time() - start_time
        print(f"⏱️  Response time: {duration:.2f}s")
        
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
            return False
        else:
            print(f"✅ Success!")
            if "result" in result and "tools" in result.get("result", {}):
                tools = result["result"]["tools"]
                print(f"   Found {len(tools)} available tools:")
                for tool in tools[:3]:  # Show first 3
                    print(f"     - {tool.get('name', 'unknown')}: {tool.get('description', '')[:50]}...")
            return True
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Exception after {duration:.2f}s: {e}")
        return False

def main():
    print("=== DIRECT MCP TOOL TESTING ===")
    
    # Initialize MCP manager
    config = {
        "enabled": True,
        "docker_enabled": True,
        "global_timeout": 120,
        "persistent_connections": True
    }
    
    manager = MCPManager(config, "/home/flip/Documents/test_configs")
    
    # Initialize tools
    print(f"\nInitializing MCP tools...")
    manager.initialize_tools()
    
    available_tools = manager.get_available_tools()
    print(f"Available tools: {available_tools}")
    
    # Test each tool individually
    results = {}
    for tool_id in ["git", "time", "fetch", "sequentialthinking", "memory", "filesystem"]:
        success = test_single_tool(manager, tool_id)
        results[tool_id] = success
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print(f"\n=== TEST RESULTS SUMMARY ===")
    working_tools = [tool for tool, success in results.items() if success]
    failing_tools = [tool for tool, success in results.items() if not success]
    
    print(f"✅ Working tools ({len(working_tools)}): {working_tools}")
    print(f"❌ Failing tools ({len(failing_tools)}): {failing_tools}")
    print(f"Success rate: {len(working_tools)}/{len(results)} ({len(working_tools)/len(results)*100:.1f}%)")
    
    # Show metrics
    metrics = manager.get_metrics()
    print(f"\nFinal Metrics:")
    print(f"  Total calls: {metrics['total_calls']}")
    print(f"  Successful: {metrics['successful_calls']}")
    print(f"  Failed: {metrics['failed_calls']}")
    
    if metrics['total_calls'] > 0:
        success_rate = metrics['successful_calls'] / metrics['total_calls'] * 100
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Avg response time: {metrics['average_response_time']:.2f}s")

if __name__ == "__main__":
    main() 