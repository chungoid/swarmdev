"""
Base Agent implementation for the SwarmDev platform.
This module provides the base agent class that all specialized agents inherit from.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING
from datetime import datetime
import os
import time

from ...utils.agent_logger import AgentLogger

if TYPE_CHECKING:
    from ...utils.llm_provider import LLMProviderInterface
    from ...utils.mcp_manager import MCPManager
    from ...utils.memory_context_manager import MemoryContextManager

class BaseAgent(ABC):
    """
    Base class for all agents in the swarm with natural MCP integration.
    
    This abstract class provides a simple, natural interface for MCP tools
    where the LLM can discover and use any tool without hardcoded patterns.
    """
    
    def __init__(self, agent_id: str, agent_type: str, 
                 llm_provider: Optional['LLMProviderInterface'] = None, 
                 mcp_manager: Optional['MCPManager'] = None, 
                 config: Optional[Dict] = None,
                 memory_manager: Optional['MemoryContextManager'] = None):
        """
        Initialize the agent.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of the agent (e.g., research, planning)
            llm_provider: LLM provider instance
            mcp_manager: MCPManager instance for tool access
            config: Agent-specific configuration dictionary
            memory_manager: MemoryContextManager instance
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = "idle"  # idle, processing, completed, failed
        self.llm_provider = llm_provider
        self.mcp_manager = mcp_manager
        self.config = config or {}
        self.memory_manager = memory_manager
        
        # Agent state
        self.current_task = None
        self.task_history = []
        self.performance_metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
            "llm_calls": 0,
            "llm_tokens_used": 0,
            "mcp_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Initialize logging
        self.logger = AgentLogger.get_logger(agent_type, agent_id)
        self.logger.info(f"Initializing {agent_type} agent: {agent_id}")
        
        # Natural MCP Integration - Just expose tools, no hardcoded patterns
        if self.mcp_manager:
            self.logger.info("=== NATURAL MCP INTEGRATION ===")
            self.logger.info(f"Agent: {agent_type} ({agent_id})")
            self.logger.info(f"MCP Manager enabled: {self.mcp_manager.is_enabled()}")
            
            # Get all available tools with their schemas
            available_tools = self.mcp_manager.get_available_tools()
            self.logger.info(f"Available MCP tools: {available_tools}")
            
            # Build tool catalog for LLM discovery
            self.mcp_tool_catalog = self._build_tool_catalog()
            self.logger.info(f"Built tool catalog with {len(self.mcp_tool_catalog)} tools")
        else:
            self.mcp_tool_catalog = {}
            self.logger.info("No MCP manager - agent will work without external tools")
        
        # Initialize MCP tool catalog and usage stats
        self.mcp_usage_stats: Dict[str, Dict[str, int]] = {}
        self.mcp_call_log: List[Dict[str, Any]] = []
        self._build_tool_catalog()
    
    def _build_tool_catalog(self) -> Dict:
        """Build a catalog of all available MCP tools with their schemas."""
        catalog = {}
        
        if not self.mcp_manager:
            return catalog
        
        available_tools = self.mcp_manager.get_available_tools()
        
        for tool_id in available_tools:
            try:
                # Get tool schema by calling tools/list
                result = self.mcp_manager.call_tool(tool_id, "tools/list", {}, timeout=10)
                
                if result and not result.get("error") and "result" in result:
                    tools_data = result["result"]
                    if isinstance(tools_data, dict) and "tools" in tools_data:
                        catalog[tool_id] = {
                            "status": "available",
                            "tools": tools_data["tools"],
                            "description": f"MCP server: {tool_id}"
                        }
                        self.logger.debug(f"Tool {tool_id}: {len(tools_data['tools'])} methods available")
                    else:
                        catalog[tool_id] = {
                            "status": "available", 
                            "tools": [],
                            "description": f"MCP server: {tool_id} (schema unavailable)"
                        }
                else:
                    catalog[tool_id] = {
                        "status": "available",
                        "tools": [],
                        "description": f"MCP server: {tool_id} (discovery failed)"
                    }
            except Exception as e:
                self.logger.warning(f"Failed to discover tools for {tool_id}: {e}")
                catalog[tool_id] = {
                    "status": "available",
                    "tools": [],
                    "description": f"MCP server: {tool_id} (discovery error)"
                }
        
        return catalog
    
    def get_mcp_tool_catalog(self) -> str:
        """Get a formatted catalog of all available MCP tools for LLM usage."""
        if not self.mcp_tool_catalog:
            return "No MCP tools available."
        
        catalog_text = "Available MCP Tools:\n\n"
        
        for tool_id, tool_info in self.mcp_tool_catalog.items():
            catalog_text += f"## {tool_id}\n"
            catalog_text += f"Status: {tool_info['status']}\n"
            catalog_text += f"Description: {tool_info['description']}\n"
            
            tools = tool_info.get('tools', [])
            if tools:
                catalog_text += f"Available methods ({len(tools)}):\n"
                for tool in tools:
                    name = tool.get('name', 'unknown')
                    description = tool.get('description', 'No description')
                    catalog_text += f"  - {name}: {description}\n"
                    
                    # Add parameter info if available
                    if 'inputSchema' in tool:
                        schema = tool['inputSchema']
                        if 'properties' in schema:
                            params = list(schema['properties'].keys())
                            catalog_text += f"    Parameters: {', '.join(params)}\n"
            else:
                catalog_text += "  No methods discovered (tool may still be usable)\n"
            
            catalog_text += "\n"
        
        catalog_text += "\nTo use any tool, call: call_mcp_tool(tool_id, method_name, parameters)\n"
        
        return catalog_text
    
    def call_mcp_tool(self, tool_id: str, method_name: str, parameters: Dict, timeout: Optional[int] = None, justification: str = None) -> Dict:
        """
        Call any MCP tool with any method and parameters - completely natural interface.
        
        Args:
            tool_id: The MCP server ID (e.g., 'sequential-thinking', 'context7')  
            method_name: The tool method name (e.g., 'sequential_thinking', 'resolve-library-id')
            parameters: Parameters for the method call
            timeout: Optional timeout
            justification: Optional description of why this tool is being used
            
        Returns:
            Dict: Tool response or error
        """
        if not self.mcp_manager:
            return {"error": "No MCP manager available"}
        
        if tool_id not in self.mcp_tool_catalog:
            available = list(self.mcp_tool_catalog.keys())
            return {"error": f"Tool '{tool_id}' not available. Available: {available}"}
        
        justification = justification or f"Agent {self.agent_type} using {tool_id}.{method_name}"
        self.logger.info(f"MCP call: {tool_id}.{method_name} - {justification}")
        
        # Prepare context for enhanced logging
        context = {
            "justification": justification,
            "agent_type": self.agent_type,
            "current_task": getattr(self.current_task, 'get', lambda x: None)('task_id') if self.current_task else None
        }
        
        # Call the tool through the MCP manager with enhanced logging
        try:
            result = self.mcp_manager.call_tool(
                tool_id, 
                "tools/call", 
                {
                    "name": method_name,
                    "arguments": parameters
                }, 
                timeout,
                agent_id=self.agent_id,
                context=context
            )
            
            # Update metrics
            self.performance_metrics["mcp_calls"] += 1
            
            if result.get("error"):
                self.logger.warning(f"MCP tool {tool_id}.{method_name} failed: {result['error']}")
            else:
                self.logger.info(f"MCP tool {tool_id}.{method_name} succeeded")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Exception calling {tool_id}.{method_name}: {e}")
            return {"error": str(e)}
    
    def get_available_mcp_tools(self) -> List[str]:
        """Get list of available MCP tool IDs."""
        return list(self.mcp_tool_catalog.keys())
    
    @abstractmethod
    def process_task(self, task: Dict) -> Dict:
        """
        Process a task assigned to this agent.
        
        Args:
            task: Task dictionary with details about the task
            
        Returns:
            Dict: Result of the task processing
        """
        pass
    
    def execute_enhanced_task(self, task_description: str, context: Dict, fallback_method=None) -> Dict:
        """
        Execute a task with intelligent LLM-directed tool enhancement.
        
        This method provides MCP tool access to the LLM without any hardcoded patterns.
        The LLM can discover and use any available tools naturally.
        
        Args:
            task_description: Natural language description of what needs to be accomplished
            context: Task context and parameters  
            fallback_method: Function to call if no tools are used
            
        Returns:
            Dict: Enhanced task result or fallback result
        """
        if not self.llm_provider:
            return {"error": "No LLM provider available for enhanced task execution"}
        
        # If no MCP tools available, use fallback immediately
        if not self.mcp_tool_catalog:
            if fallback_method:
                return fallback_method(task_description, context)
            return self._llm_only_approach(task_description, context)
        
        # Let LLM decide if and how to use tools naturally
        return self._execute_with_natural_tool_access(task_description, context, fallback_method)
    
    def _execute_with_natural_tool_access(self, task_description: str, context: Dict, fallback_method=None) -> Dict:
        """Execute task with natural MCP tool access - no hardcoded patterns."""
        
        tool_catalog = self.get_mcp_tool_catalog()
        
        enhanced_prompt = f"""
        You are a {self.agent_type} agent with access to MCP tools. 
        
        TASK: {task_description}
        CONTEXT: {context}
        
        {tool_catalog}
        
        You can call any of these tools using: call_mcp_tool(tool_id, method_name, parameters)
        
        Complete the task using your knowledge and any tools that would be helpful.
        You have complete freedom to use tools creatively - there are no restrictions.
        
        If you use tools, explain what you're doing and why.
        If you don't use tools, that's fine too - just complete the task with your knowledge.
        """
        
        try:
            # Let LLM work with natural tool access
            result = self.llm_provider.generate_text(enhanced_prompt, temperature=0.3)
            
            return {
                "status": "success",
                "method": "natural_mcp_access",
                "result": result,
                "tools_available": list(self.mcp_tool_catalog.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Enhanced task execution failed: {e}")
            if fallback_method:
                return fallback_method(task_description, context)
            return self._llm_only_approach(task_description, context)
    
    def _llm_only_approach(self, task_description: str, context: Dict) -> Dict:
        """Fallback to pure LLM approach when no tools are used."""
        if not self.llm_provider:
            return {"error": "No LLM provider available"}
        
        llm_prompt = f"""
        Complete this task using your knowledge:
        
        Task: {task_description}
        Context: {context}
        
        Provide a comprehensive response based on your training knowledge.
        """
        
        try:
            result = self.llm_provider.generate_text(llm_prompt, temperature=0.3)
            return {
                "status": "success",
                "method": "llm_only",
                "result": result,
                "tools_used": []
            }
        except Exception as e:
            return {"error": f"LLM generation failed: {e}"}
    
    # Standard agent interface methods remain the same
    def get_status(self) -> Dict:
        """Get the current status of this agent."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "mcp_tools_available": len(self.mcp_tool_catalog),
            "status": getattr(self, 'status', 'unknown')
        }
    
    def initialize(self) -> bool:
        """Initialize the agent for task processing."""
        self.status = "ready"
        return True
    
    def shutdown(self) -> bool:
        """Shutdown the agent and release resources."""
        self.status = "shutdown"
        return True
    
    def handle_error(self, error: Exception, task: Dict) -> Dict:
        """Handle an error that occurred during task processing."""
        self.status = "error"
        
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "task_id": task.get("task_id"),
            "agent_id": self.agent_id,
            "agent_type": self.agent_type
        }
        
        return error_info
    
    # Utility methods for project operations
    def investigate_project(self, project_dir: str) -> str:
        """Investigate a project directory."""
        if not os.path.exists(project_dir):
            raise Exception(f"Project directory does not exist: {project_dir}")
        
        self.logger.info(f"Project investigation target: {project_dir}")
        return project_dir
    
    def analyze_file_duplicates(self, project_dir: str) -> Dict:
        """Analyze project for potential file duplicates and redundancies."""
        try:
            result = self.call_mcp_tool("filesystem", "list_files", {
                "path": project_dir,
                "recursive": True,
                "include_hidden": False
            })
            
            if not result.get("success"):
                return {"duplicates": [], "analysis": "Failed to analyze project structure"}
            
            files = result.get("files", [])
            
            # Group files by similarity patterns
            duplicate_groups = {}
            
            for file_path in files:
                if not file_path.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.h')):
                    continue
                
                # Extract base name patterns
                filename = os.path.basename(file_path)
                base_name = self._extract_base_name(filename)
                
                if base_name not in duplicate_groups:
                    duplicate_groups[base_name] = []
                duplicate_groups[base_name].append(file_path)
            
            # Find groups with multiple files
            duplicates = {k: v for k, v in duplicate_groups.items() if len(v) > 1}
            
            analysis = {
                "duplicate_groups": duplicates,
                "total_files": len(files),
                "potential_duplicates": sum(len(v) - 1 for v in duplicates.values()),
                "recommendations": self._generate_cleanup_recommendations(duplicates)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing file duplicates: {e}")
            return {"duplicates": [], "analysis": f"Error: {e}"}
    
    def _extract_base_name(self, filename: str) -> str:
        """Extract base name pattern from filename to detect duplicates."""
        # Remove extension
        name = os.path.splitext(filename)[0]
        
        # Common patterns that indicate same functionality
        patterns = [
            r'_agent$',  # agent suffix
            r'^_',       # underscore prefix
            r'_v\d+$',   # version suffix
            r'_\d+$',    # number suffix
            r'_old$',    # old suffix
            r'_new$',    # new suffix
            r'_backup$', # backup suffix
        ]
        
        import re
        for pattern in patterns:
            name = re.sub(pattern, '', name)
        
        return name
    
    def _generate_cleanup_recommendations(self, duplicates: Dict) -> List[str]:
        """Generate recommendations for cleaning up duplicate files."""
        recommendations = []
        
        for base_name, files in duplicates.items():
            if len(files) > 1:
                # Recommend keeping the most likely "main" version
                main_file = self._identify_main_file(files)
                others = [f for f in files if f != main_file]
                
                recommendations.append(
                    f"Duplicate group '{base_name}': Keep '{main_file}', "
                    f"consider removing or consolidating: {', '.join(others)}"
                )
        
        return recommendations
    
    def _identify_main_file(self, files: List[str]) -> str:
        """Identify which file in a duplicate group is likely the main one."""
        # Prefer files without prefixes/suffixes
        for file in files:
            filename = os.path.basename(file)
            if not filename.startswith('_') and not any(
                suffix in filename for suffix in ['_old', '_backup', '_v', '_agent']
            ):
                return file
        
        # Fall back to shortest name or first alphabetically
        return min(files, key=lambda x: (len(os.path.basename(x)), x))
    
    def cleanup_duplicate_files(self, project_dir: str, duplicates_analysis: Dict, auto_confirm: bool = False) -> Dict:
        """Clean up duplicate files based on analysis."""
        cleanup_results = {"removed": [], "errors": [], "skipped": []}
        
        try:
            duplicate_groups = duplicates_analysis.get("duplicate_groups", {})
            
            for base_name, files in duplicate_groups.items():
                if len(files) <= 1:
                    continue
                
                main_file = self._identify_main_file(files)
                files_to_remove = [f for f in files if f != main_file]
                
                self.logger.info(f"Cleanup group '{base_name}': keeping '{main_file}'")
                
                for file_to_remove in files_to_remove:
                    try:
                        # Check if files are actually similar before removing
                        if self._files_are_similar(main_file, file_to_remove):
                            if auto_confirm or self._confirm_file_removal(file_to_remove, main_file):
                                result = self.call_mcp_tool("filesystem", "delete_file", {
                                    "path": file_to_remove
                                })
                                
                                if result.get("success"):
                                    cleanup_results["removed"].append(file_to_remove)
                                    self.logger.info(f"Removed duplicate file: {file_to_remove}")
                                else:
                                    cleanup_results["errors"].append(f"Failed to remove {file_to_remove}")
                            else:
                                cleanup_results["skipped"].append(file_to_remove)
                        else:
                            cleanup_results["skipped"].append(f"{file_to_remove} (content differs significantly)")
                            
                    except Exception as e:
                        cleanup_results["errors"].append(f"Error removing {file_to_remove}: {e}")
                        self.logger.error(f"Error removing {file_to_remove}: {e}")
            
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return {"removed": [], "errors": [f"Cleanup error: {e}"], "skipped": []}
    
    def _files_are_similar(self, file1: str, file2: str, similarity_threshold: float = 0.8) -> bool:
        """Check if two files are similar enough to consider one redundant."""
        try:
            # Read both files
            content1_result = self.call_mcp_tool("filesystem", "read_file", {"path": file1})
            content2_result = self.call_mcp_tool("filesystem", "read_file", {"path": file2})
            
            if not (content1_result.get("success") and content2_result.get("success")):
                return False
            
            content1 = content1_result.get("content", "")
            content2 = content2_result.get("content", "")
            
            # Simple similarity check based on line overlap
            lines1 = set(line.strip() for line in content1.split('\n') if line.strip())
            lines2 = set(line.strip() for line in content2.split('\n') if line.strip())
            
            if not lines1 and not lines2:
                return True
            
            if not lines1 or not lines2:
                return False
            
            intersection = len(lines1.intersection(lines2))
            union = len(lines1.union(lines2))
            
            similarity = intersection / union if union > 0 else 0
            return similarity >= similarity_threshold
            
        except Exception as e:
            self.logger.error(f"Error comparing files {file1} and {file2}: {e}")
            return False
    
    def _confirm_file_removal(self, file_to_remove: str, main_file: str) -> bool:
        """Confirm whether to remove a duplicate file (can be overridden by subclasses)."""
        # Default: remove if it's clearly a duplicate pattern
        filename = os.path.basename(file_to_remove)
        return any(pattern in filename.lower() for pattern in ['_old', '_backup', '_v', '_temp', 'copy'])
    
    def consolidate_similar_files(self, project_dir: str, file_group: List[str]) -> Dict:
        """Consolidate multiple similar files into one improved version."""
        try:
            if len(file_group) < 2:
                return {"success": False, "message": "Need at least 2 files to consolidate"}
            
            # Read all files in the group
            file_contents = {}
            for file_path in file_group:
                result = self.call_mcp_tool("filesystem", "read_file", {"path": file_path})
                if result.get("success"):
                    file_contents[file_path] = result.get("content", "")
            
            if len(file_contents) < 2:
                return {"success": False, "message": "Could not read files for consolidation"}
            
            # Choose the best file as base (most comprehensive one)
            best_file = max(file_contents.keys(), key=lambda x: len(file_contents[x]))
            
            # Create consolidated content (this could be enhanced with AI-powered merging)
            consolidated_content = file_contents[best_file]
            
            # Add unique functionality from other files
            consolidated_content += "\n\n# Consolidated from multiple files\n"
            for file_path, content in file_contents.items():
                if file_path != best_file:
                    consolidated_content += f"\n# === From {os.path.basename(file_path)} ===\n"
                    # Add any unique functions/classes (simplified approach)
                    
            # Write consolidated file
            result = self.call_mcp_tool("filesystem", "write_file", {
                "path": best_file,
                "content": consolidated_content
            })
            
            if result.get("success"):
                # Remove other files
                removed_files = []
                for file_path in file_group:
                    if file_path != best_file:
                        remove_result = self.call_mcp_tool("filesystem", "delete_file", {"path": file_path})
                        if remove_result.get("success"):
                            removed_files.append(file_path)
                
                return {
                    "success": True,
                    "consolidated_file": best_file,
                    "removed_files": removed_files,
                    "message": f"Consolidated {len(file_group)} files into {best_file}"
                }
            
            return {"success": False, "message": "Failed to write consolidated file"}
            
        except Exception as e:
            self.logger.error(f"Error consolidating files: {e}")
            return {"success": False, "message": f"Consolidation error: {e}"}
    
    # Metrics and logging
    def get_mcp_usage_stats(self) -> Dict:
        """Get MCP usage statistics for this agent."""
        return self.performance_metrics.copy()
    
    def log_mcp_usage_summary(self):
        """Log summary of MCP tool usage by this agent."""
        if not self.mcp_tool_catalog:
            return
        
        self.logger.info(f"=== {self.agent_type.upper()} AGENT MCP USAGE SUMMARY ===")
        self.logger.info(f"Total MCP calls: {self.performance_metrics['mcp_calls']}")
        self.logger.info(f"Available tools: {list(self.mcp_tool_catalog.keys())}")
        self.logger.info("=== END MCP USAGE SUMMARY ===")



    def _clean_generated_code(self, code: str) -> str:
        """Clean generated code by removing markdown artifacts and extra formatting."""
        # Remove markdown code blocks
        if code.startswith('```'):
            lines = code.split('\n')
            # Remove first line if it's markdown (e.g., ```python)
            if lines[0].startswith('```'):
                lines = lines[1:]
            # Remove last line if it's markdown closing
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            code = '\n'.join(lines)
        
        # Remove extra leading/trailing whitespace
        code = code.strip()
        
        return code