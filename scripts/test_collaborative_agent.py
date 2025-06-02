#!/usr/bin/env python3
"""
Comprehensive test for the Collaborative Agent's MCP tool integration.
This verifies that all 7 MCP tools work correctly with the agent and 
diagnoses any Docker infrastructure issues.
"""

import sys
import os
import json
import time
import traceback

# Add SwarmDev source to path and ensure we're running from project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Parent of scripts/ directory
sys.path.insert(0, os.path.join(project_root, 'src'))

# Change to project root directory to ensure .swarmdev is created in the right place
original_cwd = os.getcwd()
os.chdir(project_root)

from swarmdev.utils.mcp_manager import MCPManager
from swarmdev.interactive_agent.collaborative_agent import CollaborativeAgent

class CollaborativeAgentTester:
    """Test the collaborative agent's MCP tool integration."""
    
    def __init__(self):
        self.mcp_manager = None
        self.agent = None
        self.results = {}
        self.infrastructure_issues = {}
        self.detailed_failures = {}
    
    def setup(self):
        """Set up the test environment."""
        print("Setting up Collaborative Agent Test Environment")
        print("=" * 60)
        
        # Initialize MCP Manager
        config = {'enabled': True}
        self.mcp_manager = MCPManager(config)
        success = self.mcp_manager.initialize_tools()
        
        if not success:
            print("Failed to initialize MCP tools")
            return False
        
        available_tools = self.mcp_manager.get_available_tools()
        print(f"MCP Tools Available: {available_tools}")
        
        # Set up a mock LLM provider
        self.llm_provider = MockLLMProvider()
        
        # Initialize collaborative agent
        self.agent = CollaborativeAgent(
            llm_provider=self.llm_provider,
            mcp_manager=self.mcp_manager,
            project_dir=".",
            config={"verbose": True}  # Enable verbose for debugging
        )
        
        # Set available tools for MockLLMProvider to prevent recursion
        available_tools = self.mcp_manager.get_available_tools()
        self.llm_provider.set_available_tools(available_tools)
        
        print("Collaborative Agent initialized")
        print(f"Agent tool catalog: {list(self.agent.mcp_tool_catalog.keys())}")
        return True
    
    def test_mcp_infrastructure(self):
        """Test the underlying MCP Docker infrastructure."""
        print(f"\nTesting MCP Docker Infrastructure")
        print("-" * 50)
        
        expected_tools = ['memory', 'sequential-thinking', 'context7', 'git', 'time', 'fetch', 'filesystem']
        available_tools = self.mcp_manager.get_available_tools()
        
        for tool_id in expected_tools:
            print(f"\nTesting {tool_id} Docker container...")
            
            if tool_id not in available_tools:
                print(f"{tool_id} - Container failed to start or initialize")
                self.infrastructure_issues[tool_id] = "Container not available"
                continue
            
            # Test basic connectivity with detailed debugging
            success, error_details = self._test_docker_connectivity_detailed(tool_id)
            if success:
                print(f"{tool_id} - Docker container working")
            else:
                print(f"{tool_id} - Container available but has connectivity issues")
                print(f"    Error details: {error_details}")
                self.infrastructure_issues[tool_id] = f"Connectivity issues: {error_details}"
    
    def _test_docker_connectivity_detailed(self, tool_id):
        """Test basic Docker container connectivity with detailed error reporting."""
        try:
            print(f"    → Checking server capabilities...")
            capabilities = self.mcp_manager.get_server_capabilities(tool_id)
            print(f"    → Capabilities: {capabilities}")
            
            print(f"    → Getting tool info...")
            tool_info = self.mcp_manager.get_tool_info(tool_id)
            print(f"    → Tool info: {tool_info}")
            
            print(f"    → Testing basic connectivity...")
            common_tests = self._get_common_tests_for_tool(tool_id)
            if not common_tests:
                return True, "No tests available"
                
            # Try the first test with detailed timing
            first_test_name = list(common_tests.keys())[0]
            first_test = common_tests[first_test_name]
            print(f"    → Running {first_test_name} test...")
            
            start_time = time.time()
            result = self.mcp_manager.call_tool(
                tool_id,
                "tools/call", 
                first_test,
                timeout=5
            )
            elapsed = time.time() - start_time
            
            print(f"    → Test completed in {elapsed:.2f}s")
            print(f"    → Result type: {type(result)}")
            print(f"    → Result preview: {str(result)[:200]}...")
            
            if result and not result.get("error"):
                return True, None
            else:
                error = result.get("error", "Unknown error") if result else "No result"
                return False, error
                
        except Exception as e:
            print(f"    → Exception during test: {e}")
            traceback.print_exc()
            return False, str(e)
    
    def test_collaborative_agent(self):
        """Test all MCP tools through the collaborative agent."""
        print(f"\nTesting Collaborative Agent Integration")
        print("-" * 50)
        
        expected_tools = ['memory', 'sequential-thinking', 'context7', 'git', 'time', 'fetch', 'filesystem']
        available_tools = self.mcp_manager.get_available_tools()
        
        for tool_id in expected_tools:
            print(f"\nTesting {tool_id} through collaborative agent...")
            
            if tool_id not in available_tools:
                print(f"{tool_id} - Skipped (Docker infrastructure issue)")
                self.results[tool_id] = False
                continue
                
            success, details = self._test_agent_tool_detailed(tool_id)
            self.results[tool_id] = success
            
            if success:
                print(f"{tool_id} - Agent integration working")
            else:
                print(f"{tool_id} - Agent integration failed")
                print(f"    Failure details: {details}")
                self.detailed_failures[tool_id] = details
    
    def _test_agent_tool_detailed(self, tool_id):
        """Test a single tool through the collaborative agent with detailed debugging."""
        try:
            print(f"    → Checking agent's tool catalog...")
            if tool_id not in self.agent.mcp_tool_catalog:
                return False, f"Tool {tool_id} not in agent catalog: {list(self.agent.mcp_tool_catalog.keys())}"
            
            catalog_entry = self.agent.mcp_tool_catalog[tool_id]
            print(f"    → Catalog entry: {catalog_entry}")
            
            print(f"    → Testing simple tool call mapping...")
            method_name, params = self.agent._get_simple_tool_call(tool_id, f"Test message for {tool_id}")
            print(f"    → Method: {method_name}, Params: {params}")
            
            print(f"    → Testing direct call_mcp_tool...")
            start_time = time.time()
            direct_result = self.agent.call_mcp_tool(tool_id, method_name, params, timeout=10)
            elapsed = time.time() - start_time
            
            print(f"    → Direct call completed in {elapsed:.2f}s")
            print(f"    → Direct result: {str(direct_result)[:200]}...")
            
            if direct_result.get("error"):
                return False, f"Direct call error: {direct_result['error']}"
            
            print(f"    → Testing through _call_tool_safely...")
            start_time = time.time()
            safe_result = self.agent._call_tool_safely(tool_id, f"Test message for {tool_id}")
            elapsed = time.time() - start_time
            
            print(f"    → Safe call completed in {elapsed:.2f}s")
            print(f"    → Safe result: {str(safe_result)[:200]}...")
            
            if safe_result and not safe_result.get("error"):
                return True, None
            else:
                error = safe_result.get("error", "Unknown error") if safe_result else "No result"
                return False, f"Safe call error: {error}"
                
        except Exception as e:
            print(f"    → Exception during agent test: {e}")
            traceback.print_exc()
            return False, str(e)
    
    def _get_common_tests_for_tool(self, tool_id):
        """Get common test cases for each tool."""
        tests = {}
        
        if tool_id == "memory":
            tests["read_graph"] = {"name": "read_graph", "arguments": {}}
            
        elif tool_id == "sequential-thinking":
            tests["sequentialthinking"] = {
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "Test thought",
                    "nextThoughtNeeded": False,
                    "thoughtNumber": 1,
                    "totalThoughts": 1
                }
            }
            
        elif tool_id == "time":
            tests["get_current_time"] = {"name": "get_current_time", "arguments": {"timezone": "UTC"}}
            
        elif tool_id == "git":
            tests["git_status"] = {"name": "git_status", "arguments": {"repo_path": "."}}
            
        elif tool_id == "filesystem":
            tests["list_directory"] = {"name": "list_directory", "arguments": {"path": "."}}
            
        elif tool_id == "fetch":
            tests["fetch"] = {
                "name": "fetch",
                "arguments": {"url": "https://httpbin.org/json", "max_length": 500}
            }
            
        elif tool_id == "context7":
            tests["resolve-library-id"] = {
                "name": "resolve-library-id",
                "arguments": {"libraryName": "python"}
            }
        
        return tests
    
    def test_agent_conversation(self):
        """Test the collaborative agent's conversation capabilities with tools."""
        print(f"\nTesting Agent Conversation with Tools")
        print("-" * 50)
        
        # Test cases that should trigger different tools (only test available tools)
        available_tools = self.mcp_manager.get_available_tools()
        test_conversations = []
        
        if "sequential-thinking" in available_tools:
            test_conversations.append({
                "message": "Can you analyze this step by step?",
                "expected_tool": "sequential-thinking",
                "description": "Sequential thinking trigger"
            })
        
        if "time" in available_tools:
            test_conversations.append({
                "message": "What time is it?", 
                "expected_tool": "time",
                "description": "Time tool trigger"
            })
        
        if "filesystem" in available_tools:
            test_conversations.append({
                "message": "What files are in this directory?",
                "expected_tool": "filesystem", 
                "description": "Filesystem tool trigger"
            })
        elif "git" in available_tools:
            test_conversations.append({
                "message": "What files are in this directory?",
                "expected_tool": "git", 
                "description": "Git tool fallback for filesystem"
            })
        
        if not test_conversations:
            print("No available tools for conversation testing")
            return
        
        for test in test_conversations:
            print(f"\nTesting: {test['description']}")
            print(f"   Message: \"{test['message']}\"")
            
            try:
                # Start a session
                self.agent.start_session()
                
                # Send the message (this should be brief since we're just testing tool triggers)
                response = self.agent.send_message(test['message'])
                
                # Check if it triggered the expected tool (this is a simple heuristic)
                expected_tool = test['expected_tool']
                if expected_tool in self.mcp_manager.get_available_tools():
                    print(f"Message processed successfully")
                else:
                    print(f"Expected tool {expected_tool} not available")
                    
            except Exception as e:
                print(f"Conversation test failed: {e}")
                traceback.print_exc()
    
    def compare_mcp_vs_agent_calls(self):
        """Compare direct MCP calls vs agent calls to identify mismatches."""
        print(f"\nComparing Direct MCP vs Agent Tool Calls")
        print("-" * 50)
        
        available_tools = self.mcp_manager.get_available_tools()
        
        for tool_id in available_tools:
            print(f"\nComparing {tool_id}...")
            
            # Get test parameters
            tests = self._get_common_tests_for_tool(tool_id)
            if not tests:
                print(f"    No tests available for {tool_id}")
                continue
            
            test_name = list(tests.keys())[0]
            test_params = tests[test_name]
            
            try:
                # Direct MCP call
                print(f"    → Direct MCP call...")
                start_time = time.time()
                mcp_result = self.mcp_manager.call_tool(
                    tool_id,
                    "tools/call",
                    test_params,
                    timeout=10
                )
                mcp_time = time.time() - start_time
                print(f"    → MCP call: {mcp_time:.2f}s, Success: {not mcp_result.get('error') if mcp_result else False}")
                
                # Agent call (using the simplified interface)
                print(f"    → Agent call...")
                method_name, params = self.agent._get_simple_tool_call(tool_id, "Test message")
                start_time = time.time()
                agent_result = self.agent.call_mcp_tool(tool_id, method_name, params, timeout=10)
                agent_time = time.time() - start_time
                print(f"    → Agent call: {agent_time:.2f}s, Success: {not agent_result.get('error') if agent_result else False}")
                
                # Compare results
                mcp_success = mcp_result and not mcp_result.get('error')
                agent_success = agent_result and not agent_result.get('error')
                
                if mcp_success == agent_success:
                    print(f"    ✓ Results match: Both {'succeed' if mcp_success else 'fail'}")
                else:
                    print(f"    ✗ MISMATCH: MCP {'succeeds' if mcp_success else 'fails'}, Agent {'succeeds' if agent_success else 'fails'}")
                    if not mcp_success:
                        print(f"      MCP Error: {mcp_result.get('error') if mcp_result else 'No result'}")
                    if not agent_success:
                        print(f"      Agent Error: {agent_result.get('error') if agent_result else 'No result'}")
                        
            except Exception as e:
                print(f"    Exception during comparison: {e}")
                traceback.print_exc()
    
    def generate_report(self):
        """Generate a comprehensive test report."""
        print(f"\n" + "=" * 70)
        print("COLLABORATIVE AGENT COMPREHENSIVE TEST REPORT")
        print("=" * 70)
        
        # Infrastructure Report
        print(f"\nDocker Infrastructure Status:")
        expected_tools = ['memory', 'sequential-thinking', 'context7', 'git', 'time', 'fetch', 'filesystem']
        available_tools = self.mcp_manager.get_available_tools()
        
        working_containers = 0
        for tool_id in expected_tools:
            if tool_id in available_tools and tool_id not in self.infrastructure_issues:
                print(f"  {tool_id}: Container running")
                working_containers += 1
            elif tool_id in self.infrastructure_issues:
                issue = self.infrastructure_issues[tool_id]
                print(f"  {tool_id}: {issue}")
            else:
                print(f"  {tool_id}: Unknown issue")
        
        print(f"\nInfrastructure Score: {working_containers}/{len(expected_tools)} containers working")
        
        # Agent Integration Report
        print(f"\nAgent Integration Status:")
        total_tools = len(expected_tools)
        passed_tools = sum(1 for success in self.results.values() if success)
        
        for tool_id in expected_tools:
            if tool_id in self.results:
                status = "PASS" if self.results[tool_id] else "FAIL"
                print(f"  {tool_id}: {status}")
                if not self.results[tool_id] and tool_id in self.detailed_failures:
                    print(f"    → {self.detailed_failures[tool_id]}")
            else:
                print(f"  {tool_id}: NOT TESTED")
        
        print(f"\nAgent Integration Score: {passed_tools}/{total_tools} tools working")
        print(f"Success Rate: {(passed_tools/total_tools*100):.1f}%")
        
        # Overall Assessment - STRICT: Only 100% is acceptable
        print(f"\nOverall Assessment:")
        if working_containers == len(expected_tools) and passed_tools == total_tools:
            print(f"PASS: All MCP tools and agent integration working perfectly!")
            assessment = "pass"
        else:
            print(f"FAIL: System unreliable with {len(expected_tools) - working_containers} broken containers and {total_tools - passed_tools} failed integrations")
            print(f"      Production systems require 100% reliability - partial failures are unacceptable")
            assessment = "fail"
        
        # Recommendations
        print(f"\nCritical Issues to Fix:")
        if self.infrastructure_issues:
            broken_containers = list(self.infrastructure_issues.keys())
            print(f"  • BROKEN DOCKER CONTAINERS: {', '.join(broken_containers)}")
            for tool, issue in self.infrastructure_issues.items():
                print(f"    - {tool}: {issue}")
        
        if passed_tools < total_tools:
            failed_tools = [tool for tool, success in self.results.items() if not success]
            if failed_tools:
                print(f"  • FAILED AGENT INTEGRATIONS: {', '.join(failed_tools)}")
        
        if assessment == "pass":
            print(f"  • No issues found - system ready for production use!")
        else:
            print(f"  • SYSTEM NOT PRODUCTION READY - Fix all issues before deployment")
        
        return assessment == "pass"


class MockLLMProvider:
    """Mock LLM provider for testing."""
    
    def __init__(self):
        self.available_tools = []  # Will be set by the test
    
    def set_available_tools(self, tools):
        """Set which tools are actually available to avoid suggesting unavailable ones."""
        self.available_tools = tools
    
    def generate_text(self, prompt, **kwargs):
        # Check if this is a tool selection prompt
        if "Tool names separated by commas" in prompt and "NO_TOOLS" in prompt:
            # For filesystem requests, suggest filesystem if available, otherwise git for directory info
            if "files" in prompt.lower() and "directory" in prompt.lower():
                if "filesystem" in self.available_tools:
                    return "filesystem"
                elif "git" in self.available_tools:
                    return "git"  # git can show files too
                else:
                    return "NO_TOOLS"
            # For time requests
            elif "time" in prompt.lower():
                if "time" in self.available_tools:
                    return "time"
                else:
                    return "NO_TOOLS"
            # For analysis requests
            elif "analyze" in prompt.lower() or "step by step" in prompt.lower():
                if "sequential-thinking" in self.available_tools:
                    return "sequential-thinking"
                else:
                    return "NO_TOOLS"
            # Default to NO_TOOLS for other cases to prevent recursion
            else:
                return "NO_TOOLS"
        # For other prompts, return generic response
        return "I understand your request and will help accordingly."
    
    def generate_chat(self, messages, **kwargs):
        return "I'm here to help with your request."
    
    def get_capabilities(self):
        return {"text_generation": True, "chat": True}


def main():
    """Run the comprehensive collaborative agent tests."""
    tester = CollaborativeAgentTester()
    
    try:
        # Setup
        if not tester.setup():
            print("Setup failed")
            return False
        
        # Test Docker infrastructure
        tester.test_mcp_infrastructure()
        
        # Test collaborative agent integration
        tester.test_collaborative_agent()
        
        # Compare direct MCP vs agent calls
        tester.compare_mcp_vs_agent_calls()
        
        # Test conversation capabilities
        tester.test_agent_conversation()
        
        # Generate comprehensive report
        success = tester.generate_report()
        
        return success
        
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


if __name__ == "__main__":
    try:
        success = main()
        if success:
            print(f"\nTEST SUITE: PASS - All systems operational")
            sys.exit(0)
        else:
            print(f"\nTEST SUITE: FAIL - System has critical issues")
            sys.exit(1)
    except Exception as e:
        print(f"\nTEST SUITE: CRASHED - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 