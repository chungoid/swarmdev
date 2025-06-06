#!/usr/bin/env python3
"""
Test MCP Interaction - Shell Executor Focus

This script tests our new shell executor MCP server functionality, 
replacing the complex tmux-mcp implementation with simple, reliable shell execution.
"""

import json
import sys
import os
import time
from pathlib import Path

# Add SwarmDev source to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, 'src'))

from swarmdev.utils.mcp_manager import MCPManager
from swarmdev.utils.agent_logger import AgentLogger

class TestMCPInteraction:
    def __init__(self):
        # Ensure we're running from project root
        os.chdir(project_root)
        
        # Set up AgentLogger project directory
        AgentLogger.set_project_dir(".")
        
        # Initialize MCP Manager
        mcp_config = {'enabled': True, 'project_dir': '.'}
        self.mcp_manager = MCPManager(config=mcp_config, project_dir=".")
        
        self.test_results = {}

    def log_info(self, message):
        print(f"[INFO] {message}")

    def log_warning(self, message):
        print(f"[WARNING] {message}")

    def log_error(self, message):
        print(f"[ERROR] {message}")

    def test_mcp_interaction(self):
        """Test shell executor MCP interaction comprehensively."""
        self.log_info("Starting comprehensive shell executor MCP interaction test")
        print("=" * 70)

        # Initialize MCP tools
        self.log_info("Initializing MCP Manager...")
        if not self.mcp_manager.initialize_tools():
            self.log_error("Failed to initialize MCP tools")
            return False

        available_tools = self.mcp_manager.get_available_tools()
        self.log_info(f"Available MCP tools: {available_tools}")

        if 'shell' not in available_tools:
            self.log_error("Shell executor not available - cannot proceed with tests")
            return False

        # Test 1: Basic Command Execution
        success = self.test_basic_command_execution()
        self.test_results['basic_command'] = success

        # Test 2: Command with Working Directory
        success = self.test_working_directory()
        self.test_results['working_directory'] = success

        # Test 3: Error Handling
        success = self.test_error_handling()
        self.test_results['error_handling'] = success

        # Test 4: Script Execution
        success = self.test_script_execution()
        self.test_results['script_execution'] = success

        # Test 5: Command with Input
        success = self.test_command_with_input()
        self.test_results['command_with_input'] = success

        # Test 6: Build/Test Simulation (what test agents would do)
        success = self.test_build_simulation()
        self.test_results['build_simulation'] = success

        # Generate final report
        self.generate_final_report()
        
        # Return overall success
        return all(self.test_results.values())

    def test_basic_command_execution(self):
        """Test basic shell command execution."""
        self.log_info("\n--- Test 1: Basic Command Execution ---")
        
        try:
            command = "echo 'Hello from Shell Executor MCP Server!'"
            self.log_info(f"Executing: {command}")
            
            result = self.mcp_manager.call_tool("shell", "tools/call", {
                "name": "execute_command",
                "arguments": {
                    "command": command,
                    "timeout": 10
                }
            })
            
            if result.get("error"):
                self.log_error(f"Tool call failed: {result['error']}")
                return False
            
            # Parse result
            content = result.get("result", {}).get("content", [])
            if not content:
                self.log_error("No content in response")
                return False
            
            tool_output = json.loads(content[0]["text"])
            self.log_info(f"Command result: {json.dumps(tool_output, indent=2)}")
            
            expected_output = "Hello from Shell Executor MCP Server!"
            if tool_output.get("success") and expected_output in tool_output.get("stdout", ""):
                self.log_info("✅ Basic command execution: PASSED")
                return True
            else:
                self.log_error(f"Unexpected output: {tool_output}")
                return False
                
        except Exception as e:
            self.log_error(f"Exception during basic command test: {e}")
            return False

    def test_working_directory(self):
        """Test command execution with working directory."""
        self.log_info("\n--- Test 2: Working Directory ---")
        
        try:
            # Test pwd in different directory
            result = self.mcp_manager.call_tool("shell", "tools/call", {
                "name": "execute_command",
                "arguments": {
                    "command": "pwd",
                    "cwd": "/tmp",
                    "timeout": 10
                }
            })
            
            content = result.get("result", {}).get("content", [])
            tool_output = json.loads(content[0]["text"])
            
            if tool_output.get("success") and "/tmp" in tool_output.get("stdout", ""):
                self.log_info("✅ Working directory test: PASSED")
                self.log_info(f"PWD output: {tool_output.get('stdout', '').strip()}")
                return True
            else:
                self.log_error(f"Working directory test failed: {tool_output}")
                return False
                
        except Exception as e:
            self.log_error(f"Exception during working directory test: {e}")
            return False

    def test_error_handling(self):
        """Test error handling with failing command."""
        self.log_info("\n--- Test 3: Error Handling ---")
        
        try:
            # Command that should fail
            result = self.mcp_manager.call_tool("shell", "tools/call", {
                "name": "execute_command",
                "arguments": {
                    "command": "exit 42",
                    "timeout": 10
                }
            })
            
            content = result.get("result", {}).get("content", [])
            tool_output = json.loads(content[0]["text"])
            
            # Should fail with return code 42
            if not tool_output.get("success") and tool_output.get("returncode") == 42:
                self.log_info("✅ Error handling test: PASSED")
                self.log_info(f"Correctly caught failure with return code: {tool_output.get('returncode')}")
                return True
            else:
                self.log_error(f"Error handling test failed: {tool_output}")
                return False
                
        except Exception as e:
            self.log_error(f"Exception during error handling test: {e}")
            return False

    def test_script_execution(self):
        """Test script execution capability."""
        self.log_info("\n--- Test 4: Script Execution ---")
        
        try:
            script_content = """
echo "Script execution test"
echo "Current directory: $(pwd)"
echo "Date: $(date)"
echo "Script completed successfully"
"""
            
            result = self.mcp_manager.call_tool("shell", "tools/call", {
                "name": "execute_script",
                "arguments": {
                    "script_content": script_content.strip(),
                    "script_type": "bash",
                    "timeout": 15
                }
            })
            
            content = result.get("result", {}).get("content", [])
            tool_output = json.loads(content[0]["text"])
            
            expected_text = "Script execution test"
            if tool_output.get("success") and expected_text in tool_output.get("stdout", ""):
                self.log_info("✅ Script execution test: PASSED")
                self.log_info(f"Script output preview: {tool_output.get('stdout', '')[:100]}...")
                return True
            else:
                self.log_error(f"Script execution test failed: {tool_output}")
                return False
                
        except Exception as e:
            self.log_error(f"Exception during script execution test: {e}")
            return False

    def test_command_with_input(self):
        """Test command execution with stdin input."""
        self.log_info("\n--- Test 5: Command with Input ---")
        
        try:
            # Use grep to search for text in stdin
            result = self.mcp_manager.call_tool("shell", "tools/call", {
                "name": "execute_with_input",
                "arguments": {
                    "command": "grep 'test'",
                    "stdin_input": "hello world\nthis is a test line\nanother line\n",
                    "timeout": 10
                }
            })
            
            content = result.get("result", {}).get("content", [])
            tool_output = json.loads(content[0]["text"])
            
            if tool_output.get("success") and "test line" in tool_output.get("stdout", ""):
                self.log_info("✅ Command with input test: PASSED")
                self.log_info(f"Grep output: {tool_output.get('stdout', '').strip()}")
                return True
            else:
                self.log_error(f"Command with input test failed: {tool_output}")
                return False
                
        except Exception as e:
            self.log_error(f"Exception during command with input test: {e}")
            return False

    def test_build_simulation(self):
        """Simulate what a test agent would do - run tests and analyze output."""
        self.log_info("\n--- Test 6: Build/Test Simulation ---")
        
        try:
            # Simulate running Python tests (even if none exist, we test the command)
            result = self.mcp_manager.call_tool("shell", "tools/call", {
                "name": "execute_command",
                "arguments": {
                    "command": "python --version && echo 'Python version check successful'",
                    "timeout": 15
                }
            })
            
            content = result.get("result", {}).get("content", [])
            tool_output = json.loads(content[0]["text"])
            
            if tool_output.get("success") and "Python" in tool_output.get("stdout", ""):
                self.log_info("✅ Build simulation test: PASSED")
                self.log_info(f"Build output: {tool_output.get('stdout', '').strip()}")
                
                # Test agents could use this output to make decisions
                python_version = tool_output.get("stdout", "").strip()
                self.log_info(f"Test agent could analyze: {python_version}")
                return True
            else:
                self.log_error(f"Build simulation test failed: {tool_output}")
                return False
                
        except Exception as e:
            self.log_error(f"Exception during build simulation test: {e}")
            return False

    def generate_final_report(self):
        """Generate comprehensive test report."""
        self.log_info("\n" + "=" * 70)
        self.log_info("FINAL MCP SHELL EXECUTOR TEST REPORT")
        self.log_info("=" * 70)
        
        passed = sum(1 for success in self.test_results.values() if success)
        total = len(self.test_results)
        
        for test_name, success in self.test_results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            self.log_info(f"  {test_name}: {status}")
        
        self.log_info("-" * 70)
        self.log_info(f"Overall Score: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            self.log_info("🎉 ALL TESTS PASSED! Shell Executor MCP is fully operational.")
            self.log_info("\nKey advantages over tmux-mcp:")
            self.log_info("  ✅ Simple Python subprocess execution")
            self.log_info("  ✅ Complete output capture (stdout, stderr, return code)")
            self.log_info("  ✅ No Docker complexity or socket mounting")
            self.log_info("  ✅ Perfect for test agents and build automation")
            self.log_info("  ✅ Reliable error handling and timeout support")
        else:
            self.log_error(f"❌ {total - passed} test(s) failed - shell executor needs attention")
        
        self.log_info("=" * 70)

def main():
    """Run the MCP shell executor interaction test."""
    tester = TestMCPInteraction()
    
    try:
        success = tester.test_mcp_interaction()
        
        if success:
            print("\n🎉 Shell Executor MCP Test Suite: PASSED")
            sys.exit(0)
        else:
            print("\n❌ Shell Executor MCP Test Suite: FAILED")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test Suite Crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main() 