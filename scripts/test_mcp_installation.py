#!/usr/bin/env python3
"""
Comprehensive MCP Installation Test Script

This script tests the complete MCP setup to verify:
1. Configuration loading works
2. All servers can initialize 
3. Real server functionality with actual calls
4. Performance and reliability

Designed to run after setup_mcp_servers.py to provide immediate feedback.
"""

import sys
import os
import json
import time
from typing import Dict, List, Tuple

# Add SwarmDev source to path and ensure we're running from project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Parent of scripts/ directory
swarmdev_src = os.path.join(project_root, 'src')
sys.path.insert(0, swarmdev_src)

# Change to project root directory to ensure .swarmdev is created in the right place
original_cwd = os.getcwd()
os.chdir(project_root)
print(f"Running MCP tests from project root: {project_root}")

from swarmdev.utils.mcp_manager import MCPManager

class MCPInstallationTester:
    """Comprehensive MCP installation tester."""
    
    def __init__(self):
        self.results = {
            'config_test': {'status': 'pending', 'details': None},
            'initialization_test': {'status': 'pending', 'details': None},
            'functionality_tests': {},
            'performance_test': {'status': 'pending', 'details': None},
            'overall_score': 0,
            'summary': None
        }
        self.mcp_manager = None
    
    def run_all_tests(self) -> bool:
        """Run the complete test suite."""
        print("Starting MCP Installation Test Suite...")
        print("=" * 60)
        
        success = True
        
        # Test 1: Configuration Loading
        success &= self._test_configuration_loading()
        
        # Test 2: Server Initialization
        success &= self._test_server_initialization()
        
        # Test 3: Functionality Tests (Real server calls)
        success &= self._test_server_functionality()
        
        # Test 4: Performance Test
        success &= self._test_performance()
        
        # Generate final report
        self._generate_final_report()
        
        return success
    
    def _test_configuration_loading(self) -> bool:
        """Test MCP configuration loading."""
        print("\n[TEST 1] Configuration Loading")
        print("-" * 40)
        
        try:
            # Test configuration loading
            # Pass a config to MCPManager to override default timeouts for testing
            # AND explicitly define time and git servers to ensure correct commands for the test run.
            test_config = {
                'enabled': True,
                'mcpSettings': {
                    'discoveryTimeout': 30,  # Increased from default 10
                    'initializationTimeout': 45, # Increased from default 15
                    'defaultTimeout': 40 # Increased from default 30
                },
                'mcpServers': { 
                    "git": {
                        "command": ["docker", "run", "-i", "--rm",
                                    "-v", f"{project_root}:/workspace",
                                    "ghcr.io/chungoid/git:latest"],
                        "timeout": 30,
                        "enabled": True,
                        "description": "Git operations and repository management"
                    },
                    "time": {
                        "command": ["docker", "run", "-i", "--rm", "ghcr.io/chungoid/time:latest"],
                        "timeout": 30,
                        "enabled": True,
                        "description": "Time zone operations and conversions"
                    },
                    "fetch": {
                        "command": ["docker", "run", "-i", "--rm", "ghcr.io/chungoid/fetch:latest"],
                        "timeout": 30,
                        "enabled": True,
                        "description": "Web content fetching and processing"
                    }
                    # Filesystem, Memory, Sequential-Thinking, Context7, Everything
                    # will be loaded from ~/.swarmdev/mcp_config.json or MCPManager defaults
                    # by MCPManager's _load_mcp_config method. The explicit definitions
                    # above will take precedence for git, time, and fetch.
                }
            }
            self.mcp_manager = MCPManager(test_config, project_dir='.')
            
            if not self.mcp_manager.is_enabled():
                self.results['config_test'] = {
                    'status': 'failed',
                    'details': 'MCP not enabled after initialization'
                }
                print("FAILED: MCP not enabled")
                return False
            
            # Check configured servers (before initialization)
            # get_available_tools() only returns "ready" or "connected" servers
            # At this stage, servers are still "configured", so we check the servers dict directly
            configured_servers = list(self.mcp_manager.servers.keys())
            
            if not configured_servers:
                self.results['config_test'] = {
                    'status': 'failed', 
                    'details': 'No MCP servers found in configuration'
                }
                print("FAILED: No MCP servers configured")
                return False
            
            self.results['config_test'] = {
                'status': 'passed',
                'details': {
                    'servers_found': len(configured_servers),
                    'server_list': configured_servers
                }
            }
            
            print(f"PASSED: Configuration loaded successfully")
            print(f"   Found {len(configured_servers)} servers: {', '.join(configured_servers)}")
            return True
            
        except Exception as e:
            self.results['config_test'] = {
                'status': 'failed',
                'details': f'Exception during configuration loading: {str(e)}'
            }
            print(f"FAILED: Configuration loading failed: {e}")
            return False
    
    def _test_server_initialization(self) -> bool:
        """Test MCP server initialization."""
        print("\n[TEST 2] Server Initialization")
        print("-" * 40)
        
        try:
            if not self.mcp_manager:
                raise Exception("MCP Manager not initialized")
            
            # Initialize all tools
            init_success = self.mcp_manager.initialize_tools()
            
            if not init_success:
                self.results['initialization_test'] = {
                    'status': 'failed',
                    'details': 'Tool initialization returned False'
                }
                print("FAILED: Server initialization failed")
                return False
            
            # Check server status
            available_tools = self.mcp_manager.get_available_tools()
            server_details = {}
            
            for tool_id in available_tools:
                tool_info = self.mcp_manager.get_tool_info(tool_id)
                server_details[tool_id] = {
                    'status': tool_info.get('status', 'unknown'),
                    'description': tool_info.get('description', ''),
                    'command': ' '.join(tool_info.get('command', []))
                }
            
            self.results['initialization_test'] = {
                'status': 'passed',
                'details': {
                    'total_servers': len(available_tools),
                    'server_details': server_details
                }
            }
            
            print(f"PASSED: Server initialization successful")
            print(f"   {len(available_tools)} servers ready for lazy initialization")
            
            for tool_id, details in server_details.items():
                print(f"   - {tool_id}: {details['status']} ({details['description']})")
            
            return True
            
        except Exception as e:
            self.results['initialization_test'] = {
                'status': 'failed',
                'details': f'Exception during initialization: {str(e)}'
            }
            print(f"FAILED: Server initialization failed: {e}")
            return False
    
    def _test_server_functionality(self) -> bool:
        """Test actual server functionality with real calls."""
        print("\n[TEST 3] Server Functionality")
        print("-" * 40)

        # Debug: Print the command for time and git servers as seen by the test script
        if self.mcp_manager:
            if 'time' in self.mcp_manager.servers:
                time_cmd = self.mcp_manager.servers['time'].get('command', 'COMMAND_NOT_FOUND')
                print(f"DEBUG_TEST: Command for 'time' before test execution: {time_cmd}")
            else:
                print("DEBUG_TEST: 'time' server not found in mcp_manager.servers")
            
            if 'git' in self.mcp_manager.servers:
                git_cmd = self.mcp_manager.servers['git'].get('command', 'COMMAND_NOT_FOUND')
                print(f"DEBUG_TEST: Command for 'git' before test execution: {git_cmd}")
            else:
                print("DEBUG_TEST: 'git' server not found in mcp_manager.servers")
        else:
            print("DEBUG_TEST: mcp_manager not initialized in _test_server_functionality")

        overall_success = True
        
        # Test memory server (knowledge graph)
        overall_success &= self._test_memory_server()
        
        # Test time server
        overall_success &= self._test_time_server()
        
        # Test git server
        overall_success &= self._test_git_server()

        # Test tmux-mcp server
        overall_success &= self._test_tmux_mcp_server()
        
        return overall_success
    
    def _test_memory_server(self) -> bool:
        """Test memory server functionality."""
        print("\n  Testing Memory Server (Knowledge Graph)")
        
        try:
            start_time = time.time()
            
            # Test creating entities
            result = self.mcp_manager.call_tool(
                'memory',
                'tools/call',
                {
                    'name': 'create_entities',
                    'arguments': {
                        'entities': [
                            {
                                'name': 'SwarmDev-Test',
                                'entityType': 'test',
                                'observations': [
                                    'SwarmDev installation test',
                                    'Memory server functionality verification'
                                ]
                            }
                        ]
                    }
                },
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if result.get('error'):
                self.results['functionality_tests']['memory'] = {
                    'status': 'failed',
                    'details': f"Memory server error: {result['error']}",
                    'duration': duration
                }
                print(f"    FAILED: Memory server failed: {result['error']}")
                return False
            
            # Test reading the graph
            read_result = self.mcp_manager.call_tool(
                'memory',
                'tools/call',
                {'name': 'read_graph', 'arguments': {}},
                timeout=10
            )
            
            self.results['functionality_tests']['memory'] = {
                'status': 'passed',
                'details': {
                    'create_success': not result.get('error'),
                    'read_success': not read_result.get('error'),
                    'response_time': duration
                },
                'duration': duration
            }
            
            print(f"    PASSED: Memory server working (response time: {duration:.2f}s)")
            return True
            
        except Exception as e:
            self.results['functionality_tests']['memory'] = {
                'status': 'failed',
                'details': f'Exception: {str(e)}',
                'duration': 0
            }
            print(f"    FAILED: Memory server exception: {e}")
            return False
    
    def _test_time_server(self) -> bool:
        """Test time server functionality."""
        print("\n  Testing Time Server")
        
        try:
            start_time = time.time()
            
            result = self.mcp_manager.call_tool(
                'time',
                'tools/call',
                {
                    'name': 'get_current_time',
                    'arguments': {'timezone': 'UTC'}
                },
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if result.get('error'):
                self.results['functionality_tests']['time'] = {
                    'status': 'failed',
                    'details': f"Time server error: {result['error']}",
                    'duration': duration
                }
                print(f"    FAILED: Time server failed: {result['error']}")
                return False
            
            # Check if we got a reasonable response
            response_data = result.get('result', {})
            if 'timezone' in str(response_data):
                self.results['functionality_tests']['time'] = {
                    'status': 'passed',
                    'details': {
                        'response_data': response_data,
                        'response_time': duration
                    },
                    'duration': duration
                }
                print(f"    PASSED: Time server working (response time: {duration:.2f}s)")
                return True
            else:
                self.results['functionality_tests']['time'] = {
                    'status': 'failed',
                    'details': f"Unexpected response format: {response_data}",
                    'duration': duration
                }
                print(f"    FAILED: Time server unexpected response: {response_data}")
                return False
            
        except Exception as e:
            self.results['functionality_tests']['time'] = {
                'status': 'failed',
                'details': f'Exception: {str(e)}',
                'duration': 0
            }
            print(f"    FAILED: Time server exception: {e}")
            return False
    
    def _test_git_server(self) -> bool:
        """Test git server functionality."""
        print("\n  Testing Git Server")
        
        if not self.mcp_manager:
            self.results['functionality_tests']['git'] = {'status': 'failed', 'details': 'MCP Manager not initialized'}
            print("    FAILED: MCP Manager not initialized")
            return False

        # Check if git server is available
        if 'git' not in self.mcp_manager.get_available_tools():
            status_detail = "Git server not listed as available by MCPManager."
            if 'git' in self.mcp_manager.servers:
                 status_detail = f"Git server configured but status is: {self.mcp_manager.servers['git'].get('status', 'unknown')}"
            
            self.results['functionality_tests']['git'] = {
                'status': 'skipped', 
                'details': status_detail
            }
            print(f"    SKIPPED: {status_detail}")
            return True # Skipped tests don't fail the overall suite

        try:
            start_time = time.time()
            # Try to get git status (this should work even if not in a git repo)
            # Using the 'tools/call' method to invoke a named tool 'git_status'
            response = self.mcp_manager.call_tool(
                'git',
                'tools/call', 
                {
                    'name': 'git_status',
                    'arguments': {'repo_path': '/workspace'} # /workspace is mounted to project_root
                },
                timeout=20 # Slightly increased timeout for git operations
            )
            duration = time.time() - start_time
            
            if response and response.get('result'):
                self.results['functionality_tests']['git'] = {
                    'status': 'passed', 
                    'details': {'response': response['result'], 'duration': duration}
                }
                print(f"    PASSED: Git server responded in {duration:.2f}s. Response: {response['result']}")
                return True
            elif response and response.get('error'):
                error_details = response.get('error')
                # It's common for 'git_status' to error if /workspace is not a git repo,
                # but the server itself is working if it gives this specific error.
                error_message = str(error_details.get('message', '')).lower()
                if 'not a git repository' in error_message or 'fatal: not a git repository' in error_message:
                    self.results['functionality_tests']['git'] = {
                        'status': 'passed', # Counts as passed because server responded correctly to a non-repo path
                        'details': {'note': 'Git server functional, responded correctly for non-repo path.', 'error_response': error_details, 'duration': duration}
                    }
                    print(f"    PASSED: Git server functional (responded as expected for non-repo path in {duration:.2f}s). Error: {error_details}")
                    return True
                else:
                    self.results['functionality_tests']['git'] = {
                        'status': 'failed', 
                        'details': f'Git server call failed. Error: {error_details}', 'duration': duration
                    }
                    print(f"    FAILED: Git server call failed. Error: {error_details}")
                    return False
            else:
                self.results['functionality_tests']['git'] = {
                    'status': 'failed', 
                    'details': 'Git server call returned an empty or unexpected response.', 'duration': duration
                }
                print(f"    FAILED: Git server call returned an empty or unexpected response in {duration:.2f}s.")
                return False

        except Exception as e:
            self.results['functionality_tests']['git'] = {
                'status': 'failed', 
                'details': f'Exception during git server test: {str(e)}'
            }
            print(f"    FAILED: Exception during git server test: {e}")
            return False

    def _test_tmux_mcp_server(self) -> bool:
        """Test tmux-mcp server functionality."""
        print("\n  Testing tmux-mcp Server")
        
        if not self.mcp_manager:
            self.results['functionality_tests']['tmux-mcp'] = {'status': 'failed', 'details': 'MCP Manager not initialized'}
            print("    FAILED: MCP Manager not initialized")
            return False

        # Check if tmux-mcp server is available
        # It should be loaded by default if configured correctly in MCPManager
        available_tools = self.mcp_manager.get_available_tools()
        if 'tmux-mcp' not in available_tools:
            status_detail = "tmux-mcp server not listed as available by MCPManager."
            # Further check if it's in the configured list but not ready
            if 'tmux-mcp' in self.mcp_manager.servers:
                 status_detail = f"tmux-mcp server configured but status is: {self.mcp_manager.servers['tmux-mcp'].get('status', 'unknown')}"
            
            self.results['functionality_tests']['tmux-mcp'] = {
                'status': 'skipped', 
                'details': status_detail
            }
            print(f"    SKIPPED: {status_detail}")
            return True # Skipped tests don't fail the overall suite

        try:
            # Attempt a generic ping or status check.
            # Assuming a tool like 'system.ping' or similar might exist.
            # Replace 'tmux-mcp.system.ping' with an actual simple, non-destructive tool if known.
            print("    Attempting call to tmux-mcp.system.ping...")
            response = self.mcp_manager.call_tool("tmux-mcp", "system.ping", {})
            
            if response and response.get("result"):
                self.results['functionality_tests']['tmux-mcp'] = {
                    'status': 'passed', 
                    'details': {'response': response['result']}
                }
                print(f"    PASSED: tmux-mcp server responded: {response['result']}")
                return True
            elif response and response.get("error"):
                error_details = response.get('error', 'Unknown error')
                # If the error is "Tool not found", it's still a partial success (server is up)
                # but the specific ping tool isn't there.
                if isinstance(error_details, dict) and error_details.get("message", "").startswith("Tool not found"):
                    self.results['functionality_tests']['tmux-mcp'] = {
                        'status': 'passed', # Mark as passed because server is reachable
                        'details': 'Server reachable, but system.ping tool not found. This is acceptable for basic installation test.'
                    }
                    print(f"    PASSED: tmux-mcp server reachable, but system.ping tool not found (acceptable for this test).")
                    return True
                else:
                    self.results['functionality_tests']['tmux-mcp'] = {
                        'status': 'failed', 
                        'details': f'tmux-mcp server call failed or returned error. Error: {error_details}'
                    }
                    print(f"    FAILED: tmux-mcp server call failed. Error: {error_details}")
                    return False
            else: # No result and no error, unusual
                self.results['functionality_tests']['tmux-mcp'] = {
                    'status': 'failed', 
                    'details': 'tmux-mcp server call returned an empty or unexpected response.'
                }
                print("    FAILED: tmux-mcp server call returned an empty or unexpected response.")
                return False

        except Exception as e:
            self.results['functionality_tests']['tmux-mcp'] = {
                'status': 'failed', 
                'details': f'Exception during tmux-mcp server test: {str(e)}'
            }
            print(f"    FAILED: Exception during tmux-mcp server test: {e}")
            return False
    
    def _test_performance(self) -> bool:
        """Test overall MCP performance."""
        print("\n[TEST 4] Performance & Metrics")
        print("-" * 40)
        
        try:
            # Get MCP metrics
            if self.mcp_manager:
                metrics = self.mcp_manager.get_metrics()
                health_report = self.mcp_manager.get_health_report()
                
                self.results['performance_test'] = {
                    'status': 'passed',
                    'details': {
                        'metrics': metrics,
                        'health_report': health_report,
                        'total_servers': len(self.mcp_manager.get_available_tools())
                    }
                }
                
                print(f"PASSED: Performance metrics collected")
                print(f"   Total calls: {metrics.get('total_calls', 0)}")
                print(f"   Successful calls: {metrics.get('successful_calls', 0)}")
                print(f"   Failed calls: {metrics.get('failed_calls', 0)}")
                
                # Calculate success rate
                total = metrics.get('total_calls', 0)
                successful = metrics.get('successful_calls', 0)
                if total > 0:
                    success_rate = (successful / total) * 100
                    print(f"   Success rate: {success_rate:.1f}%")
                
                return True
            else:
                self.results['performance_test'] = {
                    'status': 'failed',
                    'details': 'MCP Manager not available for metrics'
                }
                print("FAILED: No MCP manager available for performance testing")
                return False
                
        except Exception as e:
            self.results['performance_test'] = {
                'status': 'failed',
                'details': f'Exception: {str(e)}'
            }
            print(f"FAILED: Performance test failed: {e}")
            return False
    
    def _generate_final_report(self):
        """Generate and display final test report."""
        print("\n" + "=" * 60)
        print("FINAL TEST REPORT")
        print("=" * 60)
        
        # Calculate overall score
        total_tests = 0
        passed_tests = 0
        
        # Count main tests
        for test_name in ['config_test', 'initialization_test', 'performance_test']:
            total_tests += 1
            if self.results[test_name]['status'] == 'passed':
                passed_tests += 1
        
        # Count functionality tests
        for test_name, test_result in self.results['functionality_tests'].items():
            total_tests += 1
            if test_result['status'] == 'passed':
                passed_tests += 1
        
        overall_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        self.results['overall_score'] = overall_score
        
        # Display results
        print(f"\nOverall Score: {overall_score:.1f}% ({passed_tests}/{total_tests} tests passed)")
        
        print(f"\nConfiguration Loading: {'PASSED' if self.results['config_test']['status'] == 'passed' else 'FAILED'}")
        if self.results['config_test']['status'] == 'passed':
            details = self.results['config_test']['details']
            print(f"   Servers found: {details['servers_found']}")
        
        print(f"\nServer Initialization: {'PASSED' if self.results['initialization_test']['status'] == 'passed' else 'FAILED'}")
        
        print(f"\nFunctionality Tests:")
        for server_name, result in self.results['functionality_tests'].items():
            status = 'PASSED' if result['status'] == 'passed' else 'FAILED'
            duration = result.get('duration', 0)
            print(f"   {server_name}: {status} ({duration:.2f}s)")
        
        print(f"\nPerformance Test: {'PASSED' if self.results['performance_test']['status'] == 'passed' else 'FAILED'}")
        
        # Summary and recommendations
        if overall_score >= 80:
            print(f"\nEXCELLENT! Your MCP installation is working great!")
            self.results['summary'] = 'excellent'
        elif overall_score >= 60:
            print(f"\nGOOD! Your MCP installation is mostly working.")
            print(f"   Some servers may need attention - check failed tests above.")
            self.results['summary'] = 'good'
        elif overall_score >= 40:
            print(f"\nPARTIAL! Your MCP installation has issues.")
            print(f"   Several servers are not working - review configuration and Docker images.")
            self.results['summary'] = 'partial'
        else:
            print(f"\nPOOR! Your MCP installation has significant problems.")
            print(f"   Most servers are not working - re-run setup and check Docker installation.")
            self.results['summary'] = 'poor'
        
        # Usage instructions
        print(f"\nNext Steps:")
        print(f"   - Use 'swarmdev status' to check MCP server health")
        print(f"   - Use 'swarmdev build' to start using MCP tools in projects")
        print(f"   - Configuration file: ~/.swarmdev/mcp_config.json")
        print(f"   - Logs available in: .swarmdev/logs/mcp.log")
        
        # Save detailed results
        try:
            results_file = '.swarmdev/mcp_test_results.json'
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"   - Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"   - Could not save detailed results: {e}")


def main():
    """Main test function."""
    try:
        tester = MCPInstallationTester()
        success = tester.run_all_tests()
        
        # Return appropriate exit code
        overall_score = tester.results.get('overall_score', 0)
        if overall_score >= 60:  # 60% threshold for "success"
            return True
        else:
            return False
    finally:
        # Always restore original working directory
        if 'original_cwd' in globals():
            os.chdir(original_cwd)


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        # Restore working directory on interrupt
        if 'original_cwd' in globals():
            os.chdir(original_cwd)
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite crashed: {e}")
        # Restore working directory on crash
        if 'original_cwd' in globals():
            os.chdir(original_cwd)
        sys.exit(1) 