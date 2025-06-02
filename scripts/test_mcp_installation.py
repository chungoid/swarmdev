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

# Add SwarmDev source to path
script_dir = os.path.dirname(os.path.abspath(__file__))
swarmdev_src = os.path.join(os.path.dirname(script_dir), 'src')
sys.path.insert(0, swarmdev_src)

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
            config = {'enabled': True}
            self.mcp_manager = MCPManager(config, project_dir='.')
            
            if not self.mcp_manager.is_enabled():
                self.results['config_test'] = {
                    'status': 'failed',
                    'details': 'MCP not enabled after initialization'
                }
                print("FAILED: MCP not enabled")
                return False
            
            # Check available servers
            available_tools = self.mcp_manager.get_available_tools()
            
            if not available_tools:
                self.results['config_test'] = {
                    'status': 'failed', 
                    'details': 'No MCP servers found in configuration'
                }
                print("FAILED: No MCP servers configured")
                return False
            
            self.results['config_test'] = {
                'status': 'passed',
                'details': {
                    'servers_found': len(available_tools),
                    'server_list': available_tools
                }
            }
            
            print(f"PASSED: Configuration loaded successfully")
            print(f"   Found {len(available_tools)} servers: {', '.join(available_tools)}")
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
        
        overall_success = True
        
        # Test memory server (knowledge graph)
        overall_success &= self._test_memory_server()
        
        # Test time server
        overall_success &= self._test_time_server()
        
        # Test git server
        overall_success &= self._test_git_server()
        
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
        
        try:
            start_time = time.time()
            
            # Try to get git status (this should work even if not in a git repo)
            result = self.mcp_manager.call_tool(
                'git',
                'tools/call',
                {
                    'name': 'git_status',
                    'arguments': {'repo_path': '.'}
                },
                timeout=10
            )
            
            duration = time.time() - start_time
            
            # Git server should respond (either with status or error about not being a git repo)
            if result.get('error'):
                # Check if it's just because we're not in a git repo
                error_msg = str(result.get('error', ''))
                if 'not a git repository' in error_msg.lower() or 'invalid repository' in error_msg.lower():
                    self.results['functionality_tests']['git'] = {
                        'status': 'passed',
                        'details': {
                            'note': 'Git server working (not in git repo is expected)',
                            'response_time': duration
                        },
                        'duration': duration
                    }
                    print(f"    PASSED: Git server working (response time: {duration:.2f}s)")
                    print(f"    INFO: Not in git repository (this is normal for the test)")
                    return True
                else:
                    self.results['functionality_tests']['git'] = {
                        'status': 'failed',
                        'details': f"Git server error: {result['error']}",
                        'duration': duration
                    }
                    print(f"    FAILED: Git server failed: {result['error']}")
                    return False
            else:
                self.results['functionality_tests']['git'] = {
                    'status': 'passed',
                    'details': {
                        'response_data': result.get('result', {}),
                        'response_time': duration
                    },
                    'duration': duration
                }
                print(f"    PASSED: Git server working (response time: {duration:.2f}s)")
                return True
            
        except Exception as e:
            self.results['functionality_tests']['git'] = {
                'status': 'failed',
                'details': f'Exception: {str(e)}',
                'duration': 0
            }
            print(f"    FAILED: Git server exception: {e}")
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
    tester = MCPInstallationTester()
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    overall_score = tester.results.get('overall_score', 0)
    if overall_score >= 60:  # 60% threshold for "success"
        return True
    else:
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite crashed: {e}")
        sys.exit(1) 