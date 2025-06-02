#!/usr/bin/env python3
"""
Comprehensive test for SwarmDev Agents' MCP tool integration.
This verifies that all MCP tools work correctly with various agents and 
diagnoses any Docker infrastructure issues.
"""

import sys
import os
import json
import time
import traceback
import shutil
from typing import Optional, Tuple, Dict, List, Type, Any

# Add SwarmDev source to path and ensure we're running from project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Parent of scripts/ directory
sys.path.insert(0, os.path.join(project_root, 'src'))

# Change to project root directory to ensure .swarmdev is created in the right place
original_cwd = os.getcwd()
os.chdir(project_root)

from swarmdev.utils.mcp_manager import MCPManager
from swarmdev.utils.agent_logger import AgentLogger
from swarmdev.interactive_agent.collaborative_agent import CollaborativeAgent
from swarmdev.swarm_builder.agents.specialized_agents import (
    ResearchAgent,
    PlanningAgent,
    DevelopmentAgent,
    AnalysisAgent,
    DocumentationAgent
)
# BaseAgent might be needed if we need to check instance types, but not for instantiation directly
# from swarmdev.swarm_builder.agents.base_agent import BaseAgent 

# List of agent classes to test
AGENT_CLASSES_TO_TEST: List[Type] = [ # Explicitly type hint
    CollaborativeAgent,
    ResearchAgent,
    PlanningAgent,
    DevelopmentAgent,
    AnalysisAgent,
    DocumentationAgent
]

# --- Helper function (moved from CollaborativeAgentTester to module level) ---
def _get_basic_connectivity_test_for_tool(tool_id: str) -> tuple[str, dict, str]:
    """Returns a simple, read-only (method, params, description) for basic connectivity test."""
    if tool_id == "memory":
        return "tools/call", {"name": "read_graph", "arguments": {}}, "read_graph"
    elif tool_id == "sequential-thinking":
        return "tools/call", {"name": "sequentialthinking", "arguments": {"thought": "test", "nextThoughtNeeded": False, "thoughtNumber": 1, "totalThoughts": 1}}, "sequentialthinking (minimal)"
    elif tool_id == "context7":
        return "tools/call", {"name": "resolve-library-id", "arguments": {"libraryName": "test"}}, "resolve-library-id"
    elif tool_id == "git":
        return "tools/call", {"name": "git_status", "arguments": {"repo_path": "/workspace"}}, "git_status"
    elif tool_id == "time":
        return "tools/call", {"name": "get_current_time", "arguments": {"timezone": "UTC"}}, "get_current_time"
    elif tool_id == "fetch":
        return "tools/call", {"name": "fetch", "arguments": {"url": "https://example.com"}}, "fetch example.com"
    elif tool_id == "filesystem":
        return "tools/call", {"name": "list_directory", "arguments": {"path": "."}}, "list_directory (.)"
    elif tool_id == "everything":
        return "tools/list", {}, "tools/list (ping)"
    else:
        return "tools/list", {}, f"tools/list for {tool_id}"

# --- MockLLMProvider (module level) ---
class MockLLMProvider:
    """Mock LLM provider for testing."""
    
    def __init__(self):
        self.available_tools = []
    
    def set_available_tools(self, tools):
        self.available_tools = tools
    
    def generate_text(self, prompt, **kwargs):
        if "Tool names separated by commas" in prompt and "NO_TOOLS" in prompt:
            if "files" in prompt.lower() and "directory" in prompt.lower():
                if "filesystem" in self.available_tools: return "filesystem"
                elif "git" in self.available_tools: return "git"
                else: return "NO_TOOLS"
            elif "time" in prompt.lower():
                if "time" in self.available_tools: return "time"
                else: return "NO_TOOLS"
            elif "analyze" in prompt.lower() or "step by step" in prompt.lower():
                if "sequential-thinking" in self.available_tools: return "sequential-thinking"
                else: return "NO_TOOLS"
            else: return "NO_TOOLS"
        return "I understand your request and will help accordingly."
    
    def generate_chat(self, messages, **kwargs):
        return "I'm here to help with your request."
    
    def get_capabilities(self):
        return {"text_generation": True, "chat": True}

# --- Main Test Suite Structure ---

class AgentMCPTester:
    """Tests MCP integration for a single agent instance."""
    def __init__(self, agent_class: Type, agent_type_name: str, global_mcp_manager: MCPManager, mock_llm: MockLLMProvider):
        self.agent_class = agent_class
        self.agent_type_name = agent_type_name
        self.global_mcp_manager = global_mcp_manager 
        self.mock_llm = mock_llm
        
        self.agent_instance: Optional[Any] = None # Using Any for now as BaseAgent/CollabAgent differ slightly
        self.agent_mcp_manager: Optional[MCPManager] = None 
        
        self.test_results: Dict[str, bool] = {} 
        self.detailed_failures: Dict[str, List[str]] = {}

    def setup_agent(self) -> bool:
        print(f"--- Setting up for {self.agent_type_name} ---")
        try:
            # For now, we assume all agents will use the global_mcp_manager.
            # If specialized agents were to have their *own* MCPManager with different configs,
            # a new MCPManager instance would be created here for self.agent_mcp_manager.
            self.agent_mcp_manager = self.global_mcp_manager

            # Instantiate the specific agent
            # CollaborativeAgent has a slightly different constructor signature (no agent_id, agent_type explicitly)
            # Specialized agents (from BaseAgent) expect agent_id and agent_type.
            if self.agent_class == CollaborativeAgent:
                self.agent_instance = self.agent_class(
                    llm_provider=self.mock_llm,
                    mcp_manager=self.agent_mcp_manager,
                    project_dir=".", 
                    config={"verbose": True, "agent_type": self.agent_type_name} # Pass agent_type in config for consistency
                )
            else: # Assumes BaseAgent derived specialized agents
                self.agent_instance = self.agent_class(
                    agent_id=f"test_{self.agent_type_name.lower()}",
                    agent_type=self.agent_type_name,
                    llm_provider=self.mock_llm,
                    mcp_manager=self.agent_mcp_manager,
                    config={"verbose": True, "project_dir": "."} # Pass project_dir via config if needed by BaseAgent
                )
            
            print(f"{self.agent_type_name} initialized.")
            
            if not hasattr(self.agent_instance, 'mcp_manager') or self.agent_instance.mcp_manager is None:
                print(f"  ERROR: {self.agent_type_name} instance does not have an active mcp_manager.")
                return False

            available_tools = self.agent_instance.mcp_manager.get_available_tools()
            self.mock_llm.set_available_tools(available_tools) # Update mock LLM for this agent's context
            print(f"  {self.agent_type_name} MCP tools available via its manager: {available_tools}")
            if not available_tools:
                 print(f"  WARNING: No MCP tools available to {self.agent_type_name} via its manager at setup.")

            return True
        except Exception as e:
            print(f"  ERROR setting up {self.agent_type_name}: {e}")
            traceback.print_exc()
            return False

    def test_all_mcp_tools_for_agent(self):
        """Tests if the current agent can use all expected MCP tools via its MCP Manager."""
        print(f"--- Testing MCP Integration for {self.agent_type_name} ---")
        expected_tools = ['memory', 'sequential-thinking', 'context7', 'git', 'time', 'fetch', 'filesystem']
        
        # Ensure the agent's mcp_manager is the one we expect to be populated by infra checks
        if not self.agent_instance or not self.agent_instance.mcp_manager:
            print(f"  Skipping MCP tests for {self.agent_type_name} - agent or its MCP manager not initialized.")
            for tool_id in expected_tools: self.test_results[tool_id] = False
            return

        for tool_id in expected_tools:
            print(f"  Testing {tool_id} through {self.agent_type_name}...")
            success, details = self._test_one_tool(tool_id)
            self.test_results[tool_id] = success
            if success:
                print(f"    ✓ {tool_id} - {self.agent_type_name} integration working")
            else:
                print(f"    ✗ {tool_id} - {self.agent_type_name} integration FAILED")
                if details:
                    print(f"      Failure details: {details}")
                    self.detailed_failures.setdefault(tool_id, []).append(details)
                else:
                    self.detailed_failures.setdefault(tool_id, []).append("Unknown test failure")


    def _test_one_tool(self, tool_id: str) -> Tuple[bool, Optional[str]]:
        """Helper to test a single MCP tool for the current agent."""
        try:
            # The self.global_mcp_manager is the one that _check_mcp_infrastructure validated.
            # We need to ensure the tool is *actually* running and available in that primary manager.
            if tool_id not in self.global_mcp_manager.get_available_tools() or \
               self.global_mcp_manager.get_tool_info(tool_id).get('status') != 'running':
                return False, f"Tool {tool_id} is not in 'running' state in the global MCP Manager. Infra issue."

            # Now check if the agent's OWN mcp_manager lists it.
            # This is crucial if agents were to have differently configured managers.
            # For now, agent_instance.mcp_manager IS global_mcp_manager.
            if tool_id not in self.agent_instance.mcp_manager.get_available_tools():
                return False, f"Tool {tool_id} confirmed RUNNING globally, but NOT in {self.agent_type_name}'s mcp_manager tool list: {list(self.agent_instance.mcp_manager.get_available_tools())}"
            
            print(f"    → Tool {tool_id} confirmed in {self.agent_type_name}'s MCP manager tool list.")

            test_method, test_params, test_name = _get_basic_connectivity_test_for_tool(tool_id)
            print(f"    → Using test: '{test_name}' (Method: {test_method}, Params: {test_params}) for {self.agent_type_name} call.")
            
            print(f"    → Testing {self.agent_type_name}.mcp_manager.call_tool for {tool_id}...")
            start_time = time.time()
            result = self.agent_instance.mcp_manager.call_tool(tool_id, test_method, test_params, timeout=15)
            elapsed = time.time() - start_time
            
            print(f"    → {self.agent_type_name} call for {tool_id} completed in {elapsed:.2f}s. Result preview: {str(result)[:150]}...")
            
            if result.get("error"):
                return False, f"Call to {tool_id} via {self.agent_type_name} MCP manager returned error: {result['error']}"
            return True, None # Success
        except Exception as e:
            print(f"    → Exception during {self.agent_type_name} test for {tool_id}: {e}")
            traceback.print_exc()
            return False, str(e)

class TestSuiteRunner:
    """Orchestrates the entire test suite for MCP infrastructure and multiple agent types."""
    
    def __init__(self):
        self.global_mcp_manager: Optional[MCPManager] = None
        self.mock_llm = MockLLMProvider() # Single mock LLM for all agents for now
        
        self.infrastructure_issues: Dict[str, str] = {} 
        self.all_agent_test_results: Dict[str, Dict[str, Any]] = {} # agent_type_name -> {"status": "COMPLETED/FAILED", "tests": {tool_id: bool}, "failures": {tool_id: [details]}}
        
        project_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.test_artifacts_dir = os.path.join(project_root_path, "test_agents_artifacts") # New name
        if os.path.exists(self.test_artifacts_dir):
            shutil.rmtree(self.test_artifacts_dir)
        os.makedirs(self.test_artifacts_dir, exist_ok=True)

    def setup_suite(self) -> bool:
        print("Setting up Test Suite Environment (Global MCP Manager & LLM)")
        print("=" * 60)

        # Ensure AgentLogger knows the project directory.
        # This needs to be done before any agent (or MCPManager if it uses AgentLogger)
        # tries to get a logger. Since CWD is already project root, "." is fine.
        AgentLogger.set_project_dir(".")
        print(f"AgentLogger project directory set to: {os.getcwd()}")

        mcp_config = {'enabled': True, 'project_dir': '.'} # Ensure project_dir is passed if MCPManager uses it for logs
        self.global_mcp_manager = MCPManager(config=mcp_config, project_dir=".") # Explicitly pass project_dir
        
        if not self.global_mcp_manager.initialize_tools(): # This just marks them 'ready'
            print("FATAL: Failed to initialize Global MCP Manager for suite (mark tools as ready).")
            return False
        
        print(f"Global MCP Manager tools initially marked ready: {self.global_mcp_manager.get_available_tools()}")
        # The actual check for 'running' state will be in _check_mcp_infrastructure
        return True

    def _check_mcp_infrastructure(self):
        print("\nTesting MCP Docker Infrastructure (Global MCP Manager)")
        print("-" * 50 + "\n")
        expected_docker_tools = ['memory', 'sequential-thinking', 'context7', 'git', 'time', 'fetch', 'filesystem']

        for tool_id in expected_docker_tools:
            print(f"INFRA_TEST: Testing {tool_id} Docker container...")
            print("  → Checking server capabilities (forces full init & handshake)...")
            try:
                # This series of calls will force the global_mcp_manager to fully initialize each server.
                capabilities = self.global_mcp_manager.get_server_capabilities(tool_id)
                if capabilities and capabilities.get('tools') is not None:
                    print(f"  → Capabilities for {tool_id} retrieved.")
                else:
                     print(f"  → Capabilities for {tool_id}: {str(capabilities)}")


                tool_info = self.global_mcp_manager.get_tool_info(tool_id)
                print(f"  → Tool info for {tool_id}: status '{tool_info.get('status') if tool_info else 'N/A'}'")

                if tool_info and tool_info.get('status') == 'running':
                    print(f"  → Testing basic connectivity for {tool_id}...")
                    test_method, test_params, test_name = _get_basic_connectivity_test_for_tool(tool_id)
                    print(f"    → Running '{test_name}' test for {tool_id}...")
                    
                    response = self.global_mcp_manager.call_tool(tool_id, test_method, test_params, timeout=15)
                    
                    if response and not response.get("error"):
                        print(f"  ✓ {tool_id} - Docker container working and basic call successful.")
                    else:
                        err_msg = response.get('error', 'Unknown error during connectivity test')
                        failure_detail = f"Connectivity test for {tool_id} failed or returned error: {err_msg}"
                        print(f"  ✗ {tool_id} - Container available but basic call FAILED: {failure_detail}")
                        self.infrastructure_issues[tool_id] = failure_detail
                elif tool_info:
                    failure_detail = f"Server {tool_id} status is '{tool_info.get('status')}', expected 'running'. Last error: {tool_info.get('last_error', 'N/A')}"
                    print(f"  ✗ {tool_id} - Container started but not in 'running' state: {failure_detail}")
                    self.infrastructure_issues[tool_id] = failure_detail
                else:
                    failure_detail = f"Tool info not found for {tool_id} after capability check."
                    print(f"  ✗ {tool_id} - FAILED (Tool info not found): {failure_detail}")
                    self.infrastructure_issues[tool_id] = failure_detail
            except Exception as e:
                failure_detail = f"Exception during infrastructure check for {tool_id}: {str(e)}"
                print(f"  ✗ {tool_id} - FAILED ({failure_detail})")
                # self.global_mcp_manager.mcp_logger.error(f"Exception in _check_mcp_infrastructure for {tool_id}", exc_info=True) # Already logged by MCPManager
                self.infrastructure_issues[tool_id] = failure_detail
            print("")

    def run_all_agent_tests(self):
        if not self.setup_suite():
            sys.exit(1) # Critical setup failure
        
        self._check_mcp_infrastructure() # Validate and fully initialize all tools via global manager

        any_agent_setup_failed = False
        for agent_class in AGENT_CLASSES_TO_TEST:
            agent_type_name = agent_class.__name__
            print(f"\n{'='*20} Starting Tests for Agent: {agent_type_name.upper()} {'='*20}")
            
            # Pass the already initialized global_mcp_manager to each agent tester
            # The agent_tester will then assign this to its agent_instance.mcp_manager
            agent_tester = AgentMCPTester(agent_class, agent_type_name, self.global_mcp_manager, self.mock_llm)
            
            current_agent_results = {"status": "PENDING", "tests": {}, "failures": {}}
            if not agent_tester.setup_agent():
                print(f"SKIPPING tests for {agent_type_name} due to agent setup failure.")
                current_agent_results["status"] = "AGENT_SETUP_FAILED"
                any_agent_setup_failed = True
            else:
                agent_tester.test_all_mcp_tools_for_agent()
                current_agent_results["status"] = "COMPLETED" # Mark as completed even if tests fail
                current_agent_results["tests"] = agent_tester.test_results
                current_agent_results["failures"] = agent_tester.detailed_failures
            
            self.all_agent_test_results[agent_type_name] = current_agent_results
        
        return self.generate_comprehensive_report(any_agent_setup_failed)

    def generate_comprehensive_report(self, any_agent_setup_failed: bool) -> bool:
        print("\n" + "=" * 70)
        print("COMPREHENSIVE AGENT MCP INTEGRATION TEST SUITE REPORT")
        print("=" * 70)

        # 1. Infrastructure Report
        expected_docker_tools = ['memory', 'sequential-thinking', 'context7', 'git', 'time', 'fetch', 'filesystem']
        print("\n--- MCP Docker Infrastructure Status ---")
        working_infra_count = 0
        for tool_id in expected_docker_tools:
            if tool_id in self.infrastructure_issues:
                print(f"  ✗ {tool_id}: FAILED - {self.infrastructure_issues[tool_id]}")
            else: # If not in issues, it means it passed the checks
                print(f"  ✓ {tool_id}: PASSED")
                working_infra_count += 1
        print(f"Infrastructure Score: {working_infra_count}/{len(expected_docker_tools)} containers working and responsive.")
        all_infra_ok = working_infra_count == len(expected_docker_tools)
        if not all_infra_ok:
            print("  CRITICAL: MCP Infrastructure is NOT fully operational. Agent tests may be unreliable.")

        # 2. Per-Agent MCP Integration Report
        print("\n--- Specialized Agent MCP Tool Integration Status ---")
        overall_all_agent_integrations_passed = True
        
        for agent_type_name, result_data in self.all_agent_test_results.items():
            print(f"\n  Agent Type: {agent_type_name}")
            if result_data["status"] == "AGENT_SETUP_FAILED":
                print("    STATUS: AGENT SETUP FAILED - Tests SKIPPED.")
                overall_all_agent_integrations_passed = False
                continue
            
            agent_tool_tests = result_data["tests"]
            agent_tool_failures = result_data["failures"]
            passed_count = sum(1 for success in agent_tool_tests.values() if success)
            total_tools_for_agent = len(expected_docker_tools) # Each agent is tested against all tools

            for tool_id in expected_docker_tools:
                test_passed = agent_tool_tests.get(tool_id, False) # Default to False if somehow missing
                status_char = "✓" if test_passed else "✗"
                print(f"    {status_char} {tool_id}: {'PASS' if test_passed else 'FAIL'}")
                if not test_passed and tool_id in agent_tool_failures:
                    for detail in agent_tool_failures[tool_id]:
                        print(f"      → {detail}")
            
            agent_success_rate = (passed_count / total_tools_for_agent * 100) if total_tools_for_agent > 0 else 0
            print(f"    Score for {agent_type_name}: {passed_count}/{total_tools_for_agent} tools integrated ({agent_success_rate:.1f}%)")
            if passed_count != total_tools_for_agent:
                overall_all_agent_integrations_passed = False

        # 3. Overall Assessment
        final_suite_success = all_infra_ok and overall_all_agent_integrations_passed and not any_agent_setup_failed
        
        print("\n" + "=" * 70)
        if final_suite_success:
            print("TEST SUITE: PASS - All infrastructure and all agent integrations successful.")
        else:
            print("TEST SUITE: FAIL - Issues detected.")
            if not all_infra_ok:
                print("  REASON: Critical MCP infrastructure failures.")
            if any_agent_setup_failed:
                print("  REASON: One or more agents failed to set up.")
            if not overall_all_agent_integrations_passed:
                print("  REASON: One or more agents failed MCP tool integration tests.")
            print("  Please review logs for specific error details.")
        print("=" * 70)
        return final_suite_success

# --- Main Execution Logic ---
def main():
    """Run the comprehensive agent tests."""
    # Preserve original CWD and ensure we run from project root for consistency
    original_working_directory = os.getcwd()
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_dir = os.path.dirname(current_script_dir)
    os.chdir(project_root_dir)
    print(f"Changed CWD to project root: {os.getcwd()}")

    suite_runner = TestSuiteRunner()
    
    try:
        success = suite_runner.run_all_agent_tests()
        
        if success:
            print(f"\nTEST SUITE FINAL RESULT: PASS - All systems operational for all tested agents.")
            sys.exit(0)
        else:
            print(f"\nTEST SUITE FINAL RESULT: FAIL - System has critical issues. Review report above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nTEST SUITE: CRASHED UNEXPECTEDLY - {e}")
        traceback.print_exc()
        sys.exit(2) # Different exit code for crash
    finally:
        os.chdir(original_working_directory)
        print(f"Restored CWD to: {os.getcwd()}")


if __name__ == "__main__":
    main()

# The old CollaborativeAgentTester class and its methods were here.
# They have been successfully superseded by TestSuiteRunner and AgentMCPTester.
# All its functionality is now covered by the new structure. 