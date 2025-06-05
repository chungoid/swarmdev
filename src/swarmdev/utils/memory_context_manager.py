"""
Memory-driven context manager for SwarmDev using knowledge graph MCP server.
Provides intelligent context awareness across workflow iterations.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid


@dataclass
class ContextMemory:
    """Structured memory context for workflow iterations."""
    entity_name: str
    entity_type: str
    observations: List[str]
    relations: List[Dict[str, str]]


class MemoryContextManager:
    """
    Manages context memory using knowledge graph MCP server.
    Stores file operations, task completions, and iteration context.
    """
    
    def __init__(self, mcp_manager, project_id: str, logger: Optional[logging.Logger] = None):
        self.mcp_manager = mcp_manager
        self.project_id = project_id
        self.logger = logger or logging.getLogger(__name__)
        self.project_node_name = f"project_node_{self.project_id}" # Define project_node_name
        self.memory_service_available = True # Assume true initially

        if self.mcp_manager and self.mcp_manager.is_enabled():
            memory_server_info = self.mcp_manager.get_tool_info("memory")
            if not memory_server_info or memory_server_info.get("status") == "discovery_failed":
                self.logger.critical("MEMORY_CONTEXT_INIT: Critical - MCP 'memory' server failed discovery or is not configured. MemoryContextManager will be non-operational.")
                self.memory_service_available = False
            else:
                # Further check if capabilities were actually discovered (not an empty list of tools if discovery succeeded)
                memory_capabilities = self.mcp_manager.get_server_capabilities("memory")
                if not memory_capabilities.get("tools") and not memory_capabilities.get("discovery_failed"):
                    # This case implies discovery 'succeeded' but returned no tools, which is also problematic.
                    self.logger.warning("MEMORY_CONTEXT_INIT: Warning - MCP 'memory' server reported successful discovery but no tools listed. Assuming non-operational.")
                    self.memory_service_available = False
                elif memory_capabilities.get("discovery_failed"): # Redundant check, but explicit
                     self.logger.critical("MEMORY_CONTEXT_INIT: Critical - MCP 'memory' server capabilities show discovery_failed=True. MemoryContextManager will be non-operational.")
                     self.memory_service_available = False

            if self.memory_service_available:
                 self._initialize_project_memory()
            else:
                self.logger.warning("MEMORY_CONTEXT_INIT: Skipping _initialize_project_memory as memory service is not available.")
        elif self.mcp_manager and not self.mcp_manager.is_enabled():
            self.logger.warning("MEMORY_CONTEXT_INIT: MCPManager is disabled. MemoryContextManager will be non-operational.")
            self.memory_service_available = False
        else: # No mcp_manager
            self.logger.warning("MEMORY_CONTEXT_INIT: No MCPManager provided. MemoryContextManager will be non-operational.")
            self.memory_service_available = False
    
    def _initialize_project_memory(self):
        """Initialize project-level memory entities."""
        if not self.memory_service_available:
            self.logger.warning("MEMORY: Skipping project memory initialization as service is unavailable.")
            return
        try:
            # Check if project_node already exists
            node_check_result = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "get_node",
                "arguments": {"node_id": self.project_node_name}
            })
            if self._is_mcp_success(node_check_result) and node_check_result.get("result"):
                self.logger.info(f"MEMORY: Project node {self.project_node_name} already exists for project {self.project_id}.")
                return

            # Create project entity using ContextMemory dataclass
            project_cm = ContextMemory(
                entity_name=self.project_node_name,
                entity_type="Project", # Standardized type
                observations=[
                    f"Project initialized: {datetime.now().isoformat()}",
                    f"Project ID: {self.project_id}"
                ],
                relations=[]
            )
            
            result = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "create_entities",
                "arguments": {"entities": [asdict(project_cm)]} # Convert to dict
            })
            
            if self._is_mcp_success(result):
                self.logger.info(f"MEMORY: Initialized project memory for {self.project_id} with node {self.project_node_name}")
            else:
                self.logger.warning(f"MEMORY: Failed to initialize project memory node {self.project_node_name}: {result.get('error', result)}")
                
        except Exception as e:
            self.logger.error(f"MEMORY: Project memory initialization failed: {e}", exc_info=True)
    
    def store_iteration_start(self, iteration_count: int, goal: str, workflow_type: str) -> bool:
        """Store iteration start context in memory."""
        if not self.memory_service_available:
            self.logger.warning(f"MEMORY: Memory service is not available. Skipping store_iteration_start for iteration {iteration_count}.")
            return False
        try:
            iteration_entity = {
                "name": f"iteration_{self.project_id}_{iteration_count}",
                "entityType": "iteration",
                "observations": [
                    f"Iteration {iteration_count} started: {datetime.now().isoformat()}",
                    f"Goal: {goal}",
                    f"Workflow type: {workflow_type}",
                    f"Status: started"
                ]
            }
            
            # Create iteration entity
            result = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "create_entities",
                "arguments": {"entities": [iteration_entity]}
            })
            
            if self._is_mcp_success(result):
                # Create relation to project
                self._create_project_relation(iteration_entity["name"], "contains_iteration")
                
                # Create relation to previous iteration if exists
                if iteration_count > 1:
                    prev_iteration = f"iteration_{self.project_id}_{iteration_count - 1}"
                    self._create_relation(iteration_entity["name"], prev_iteration, "follows_iteration")
                
                self.logger.info(f"MEMORY: Stored iteration {iteration_count} start context")
                return True
            else:
                self.logger.error(f"MEMORY: Failed to store iteration start: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"MEMORY: Iteration start storage failed: {e}")
            return False
    
    def store_task_completion(self, iteration_count: int, task_id: str, agent_type: str, 
                            result: Dict, files_affected: List[str] = None) -> bool:
        """Store task completion context in memory."""
        if not self.memory_service_available:
            self.logger.warning(f"MEMORY: Memory service is not available. Skipping store_task_completion for task {task_id}.")
            return False
        try:
            task_entity = {
                "name": f"task_{self.project_id}_{iteration_count}_{task_id}",
                "entityType": "task",
                "observations": [
                    f"Task completed: {datetime.now().isoformat()}",
                    f"Task ID: {task_id}",
                    f"Agent type: {agent_type}",
                    f"Status: {result.get('status', 'unknown')}",
                    f"Result summary: {str(result)[:200]}..."
                ]
            }
            
            # Add file information if available
            if files_affected:
                task_entity["observations"].extend([
                    f"Files affected: {len(files_affected)} files",
                    f"File list: {', '.join(files_affected[:5])}" + ("..." if len(files_affected) > 5 else "")
                ])
            
            # Create task entity
            result_store = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "create_entities",
                "arguments": {"entities": [task_entity]}
            })
            
            if self._is_mcp_success(result_store):
                # Create relation to iteration
                iteration_name = f"iteration_{self.project_id}_{iteration_count}"
                self._create_relation(iteration_name, task_entity["name"], "contains_task")
                
                # Store file entities and relations if files were affected
                if files_affected:
                    self._store_file_context(iteration_count, task_id, files_affected, agent_type)
                
                self.logger.info(f"MEMORY: Stored task completion context for {task_id}")
                return True
            else:
                self.logger.error(f"MEMORY: Failed to store task completion: {result_store}")
                return False
                
        except Exception as e:
            self.logger.error(f"MEMORY: Task completion storage failed: {e}")
            return False
    
    def store_file_operation(self, iteration_count: int, file_path: str, operation: str, 
                           task_id: str, content_summary: str = None) -> bool:
        """Store file operation context in memory using FileArtifact and FileOperation entities."""
        if not self.memory_service_available:
            self.logger.warning(f"MEMORY: Memory service is not available. Skipping store_file_operation for {file_path}.")
            return False
        if not self.mcp_manager: # Original check, kept for robustness
            self.logger.warning("MCP Manager not available. Cannot store file operation.")
            return False
        try:
            # Ensure file_path is relative to project root for consistency
            original_file_path = file_path # Keep original for logging if needed
            if file_path.startswith(("/workspace/", "workspace/")):
                file_path = file_path.replace("/workspace/", "", 1).replace("workspace/", "", 1)
            if file_path.startswith("./"):
                file_path = file_path[2:]
            file_path = file_path.strip('/')


            if not file_path:
                self.logger.warning(f"Cannot log file operation for invalid/root path: original was '{original_file_path}'.")
                return False

            file_entity_name = f"file_{self.project_id}_{file_path.replace('/', '_')}"
            op_entity_name = f"file_op_{self.project_id}_{operation}_{file_entity_name}_{task_id}_{iteration_count}_{uuid.uuid4().hex[:6]}"
            iteration_node_name = f"iteration_node_{self.project_id}_{iteration_count}"
            task_node_name = f"task_node_{self.project_id}_{task_id}_{iteration_count}"

            observations = [
                f"File operation '{operation}' performed on '{file_path}' (project: {self.project_id}).",
                f"Associated with task '{task_id}' in iteration {iteration_count}.",
                f"Operation occurred at {datetime.now().isoformat()}."
            ]
            if content_summary:
                observations.append(f"Content summary: {content_summary[:250]}...")

            relations = [
                {"from_entity": op_entity_name, "to_entity": file_entity_name, "type": "OPERATED_ON_FILE"},
                {"from_entity": op_entity_name, "to_entity": iteration_node_name, "type": "PART_OF_ITERATION"},
                {"from_entity": op_entity_name, "to_entity": task_node_name, "type": "GENERATED_BY_TASK"},
                {"from_entity": op_entity_name, "to_entity": self.project_node_name, "type": "PART_OF_PROJECT"}
            ]

            # Ensure iteration node exists (should be created by store_iteration_start)
            iter_exists_check = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "get_node",
                "arguments": {"node_id": iteration_node_name}
            })
            if not (self._is_mcp_success(iter_exists_check) and iter_exists_check.get("result")):
                self.logger.warning(f"Iteration node {iteration_node_name} not found. File op link might be incomplete.")
                # Optionally create it here if critical, or rely on store_iteration_start
                # For now, log a warning.

            # Ensure task node exists (should be created by store_task_completion)
            task_exists_check = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "get_node",
                "arguments": {"node_id": task_node_name}
            })
            if not (self._is_mcp_success(task_exists_check) and task_exists_check.get("result")):
                self.logger.warning(f"Task node {task_node_name} not found. File op link might be incomplete.")


            # Ensure file entity (FileArtifact) exists
            file_artifact_exists_check = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "get_node",
                "arguments": {"node_id": file_entity_name}
            })
            if not (self._is_mcp_success(file_artifact_exists_check) and file_artifact_exists_check.get("result")):
                file_artifact_cm = ContextMemory(
                    entity_name=file_entity_name, 
                    entity_type="FileArtifact", 
                    observations=[f"File artifact representing: {file_path} in project {self.project_id}"], 
                    relations=[{"from_entity": file_entity_name, "to_entity": self.project_node_name, "type": "BELONGS_TO_PROJECT"}]
                )
                create_file_artifact_result = self.mcp_manager.call_tool(
                    "memory", "tools/call", {
                        "name": "create_entities",
                        "arguments": {"entities": [asdict(file_artifact_cm)]} # Convert to dict
                    }
                )
                if self._is_mcp_success(create_file_artifact_result):
                    self.logger.debug(f"Created FileArtifact entity: {file_entity_name}")
                else:
                    self.logger.warning(f"Failed to create FileArtifact {file_entity_name}: {create_file_artifact_result.get('error')}")


            # Create the FileOperation entity
            file_op_cm = ContextMemory(
                entity_name=op_entity_name, 
                entity_type="FileOperation", 
                observations=observations, 
                relations=relations
            )
            create_op_result = self.mcp_manager.call_tool(
                "memory", "tools/call", {
                    "name": "create_entities",
                    "arguments": {"entities": [asdict(file_op_cm)]} # Convert to dict
                }
            )
            
            success = self._is_mcp_success(create_op_result)
            if success:
                self.logger.info(f"Stored file operation '{operation}' for '{file_path}' in iteration {iteration_count} linked to task '{task_id}'.")
            else:
                self.logger.warning(f"Failed to store file operation for '{file_path}': {create_op_result.get('error')}")
            return success
                
        except Exception as e:
            self.logger.error(f"MEMORY: File operation storage failed for {file_path}: {e}", exc_info=True)
            return False

    def store_directory_operation(self, iteration_count: int, dir_path: str, operation: str, task_id: str) -> bool:
        """Stores a directory operation (e.g., creation) in the memory graph."""
        if not self.memory_service_available:
            self.logger.warning(f"MEMORY: Memory service is not available. Skipping store_directory_operation for {dir_path}.")
            return False
        if not self.mcp_manager: # Original check
            self.logger.warning("MCP Manager not available. Cannot store directory operation.")
            return False
        try:
            original_dir_path = dir_path # Keep original for logging
            if dir_path.startswith(("/workspace/", "workspace/")):
                dir_path = dir_path.replace("/workspace/", "", 1).replace("workspace/", "", 1)
            if dir_path.startswith("./"):
                dir_path = dir_path[2:]
            dir_path = dir_path.strip('/')

            if not dir_path:
                self.logger.warning(f"Cannot log directory operation for invalid/root path: original was '{original_dir_path}'.")
                return False

            dir_entity_name = f"dir_{self.project_id}_{dir_path.replace('/', '_')}"
            op_entity_name = f"dir_op_{self.project_id}_{operation}_{dir_entity_name}_{task_id}_{iteration_count}_{uuid.uuid4().hex[:6]}"
            iteration_node_name = f"iteration_node_{self.project_id}_{iteration_count}"
            task_node_name = f"task_node_{self.project_id}_{task_id}_{iteration_count}"

            observations = [
                f"Directory operation '{operation}' performed on '{dir_path}' (project: {self.project_id}).",
                f"Associated with task '{task_id}' in iteration {iteration_count}.",
                f"Operation occurred at {datetime.now().isoformat()}."
            ]
            relations = [
                {"from_entity": op_entity_name, "to_entity": dir_entity_name, "type": "OPERATED_ON_DIRECTORY"},
                {"from_entity": op_entity_name, "to_entity": iteration_node_name, "type": "PART_OF_ITERATION"},
                {"from_entity": op_entity_name, "to_entity": task_node_name, "type": "GENERATED_BY_TASK"},
                {"from_entity": op_entity_name, "to_entity": self.project_node_name, "type": "PART_OF_PROJECT"}
            ]

            # Ensure directory entity (DirectoryArtifact) exists
            dir_artifact_exists_check = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "get_node",
                "arguments": {"node_id": dir_entity_name}
            })
            if not (self._is_mcp_success(dir_artifact_exists_check) and dir_artifact_exists_check.get("result")):
                dir_artifact_cm = ContextMemory(
                    entity_name=dir_entity_name,
                    entity_type="DirectoryArtifact",
                    observations=[f"Directory artifact representing: {dir_path} in project {self.project_id}"],
                    relations=[{"from_entity": dir_entity_name, "to_entity": self.project_node_name, "type": "BELONGS_TO_PROJECT"}]
                )
                create_dir_artifact_result = self.mcp_manager.call_tool(
                    "memory", "tools/call", {
                        "name": "create_entities",
                        "arguments": {"entities": [asdict(dir_artifact_cm)]} # Convert to dict
                    }
                )
                if self._is_mcp_success(create_dir_artifact_result):
                    self.logger.debug(f"Created DirectoryArtifact entity: {dir_entity_name}")
                else:
                    self.logger.warning(f"Failed to create DirectoryArtifact {dir_entity_name}: {create_dir_artifact_result.get('error')}")
            
            # Create the DirectoryOperation entity
            dir_op_cm = ContextMemory(
                entity_name=op_entity_name,
                entity_type="DirectoryOperation",
                observations=observations,
                relations=relations
            )
            create_op_result = self.mcp_manager.call_tool(
                "memory", "tools/call", {
                    "name": "create_entities",
                    "arguments": {"entities": [asdict(dir_op_cm)]} # Convert to dict
                }
            )

            success = self._is_mcp_success(create_op_result)
            if success:
                self.logger.info(f"Stored directory operation '{operation}' for '{dir_path}' in iteration {iteration_count} linked to task '{task_id}'.")
            else:
                self.logger.warning(f"Failed to store directory operation for '{dir_path}': {create_op_result.get('error')}")
            return success
        except Exception as e:
            self.logger.error(f"MEMORY: Directory operation storage for {dir_path} failed: {e}", exc_info=True)
            return False
    
    def retrieve_iteration_context(self, iteration_count: int) -> Dict:
        """Retrieve relevant context for current iteration."""
        if not self.memory_service_available:
            self.logger.warning(f"MEMORY: Memory service is not available. Skipping retrieve_iteration_context for iteration {iteration_count}.")
            return {}
        try:
            context = {
                "previous_iterations": [],
                "file_history": [],
                "task_patterns": [],
                "project_evolution": []
            }
            
            # Get previous iteration context
            if iteration_count > 1:
                prev_context = self._get_previous_iteration_context(iteration_count - 1)
                context["previous_iterations"] = prev_context
            
            # Get file evolution history
            file_history = self._get_file_evolution_history()
            context["file_history"] = file_history
            
            # Get task completion patterns
            task_patterns = self._get_task_completion_patterns(iteration_count)
            context["task_patterns"] = task_patterns
            
            # Get project evolution insights
            evolution = self._get_project_evolution_insights(iteration_count)
            context["project_evolution"] = evolution
            
            self.logger.info(f"MEMORY: Retrieved context for iteration {iteration_count}")
            self.logger.debug(f"MEMORY: Context summary - {len(context['previous_iterations'])} iterations, "
                            f"{len(context['file_history'])} files, {len(context['task_patterns'])} patterns")
            
            return context
            
        except Exception as e:
            self.logger.error(f"MEMORY: Context retrieval failed: {e}")
            return {}
    
    def get_file_conflict_context(self, file_path: str) -> Dict:
        """Get context about potential file conflicts and previous operations."""
        if not self.memory_service_available:
            self.logger.warning(f"MEMORY: Memory service is not available. Skipping get_file_conflict_context for {file_path}.")
            return {} # Return empty dict, which might be interpreted as "no context" or "is_new: True" by caller.
        try:
            # Search for file-related entities
            file_entity_name = f"file_{self.project_id}_{file_path.replace('/', '_').replace('.', '_')}"
            
            result = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "open_nodes",
                "arguments": {"names": [file_entity_name]}
            })
            
            if self._is_mcp_success(result):
                entities = result.get("result", {}).get("entities", [])
                relations = result.get("result", {}).get("relations", [])
                
                if entities:
                    file_entity = entities[0]
                    observations = file_entity.get("observations", [])
                    
                    # Parse observations to extract conflict context
                    operations = []
                    iterations = []
                    tasks = []
                    
                    for obs in observations:
                        if "File operation:" in obs:
                            operations.append(obs.split("File operation: ")[1])
                        elif "Iteration:" in obs:
                            iterations.append(obs.split("Iteration: ")[1])
                        elif "Task:" in obs:
                            tasks.append(obs.split("Task: ")[1])
                    
                    context = {
                        "file_path": file_path,
                        "previous_operations": operations,
                        "affected_iterations": iterations,
                        "related_tasks": tasks,
                        "total_modifications": len([op for op in operations if op in ["create", "modify"]]),
                        "relations": relations
                    }
                    
                    self.logger.info(f"MEMORY: Retrieved file conflict context for {file_path}")
                    return context
                else:
                    self.logger.info(f"MEMORY: No previous context found for {file_path}")
                    return {"file_path": file_path, "is_new": True}
            else:
                self.logger.warning(f"MEMORY: Failed to retrieve file context: {result}")
                return {}
                
        except Exception as e:
            self.logger.error(f"MEMORY: File conflict context retrieval failed: {e}")
            return {}
    
    def search_relevant_context(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for relevant context using semantic search."""
        if not self.memory_service_available:
            self.logger.warning(f"MEMORY: Memory service is not available. Skipping search_relevant_context for query '{query}'.")
            return []
        try:
            result = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "search_nodes",
                "arguments": {"query": query}
            })
            
            if self._is_mcp_success(result):
                entities = result.get("result", {}).get("entities", [])
                
                # Filter and format results
                relevant_context = []
                for entity in entities[:limit]:
                    context_item = {
                        "entity_name": entity.get("name", ""),
                        "entity_type": entity.get("entityType", ""),
                        "observations": entity.get("observations", []),
                        "relevance_score": 1.0  # Could be enhanced with actual scoring
                    }
                    relevant_context.append(context_item)
                
                self.logger.info(f"MEMORY: Found {len(relevant_context)} relevant context items for query: {query}")
                return relevant_context
            else:
                self.logger.warning(f"MEMORY: Context search failed: {result}")
                return []
                
        except Exception as e:
            self.logger.error(f"MEMORY: Context search failed: {e}")
            return []
    
    def store_analysis_insights(self, iteration_count: int, insights: Dict) -> bool:
        """Store analysis insights for future reference."""
        if not self.memory_service_available:
            self.logger.warning(f"MEMORY: Memory service is not available. Skipping store_analysis_insights for iteration {iteration_count}.")
            return False
        try:
            # Correctly access keys from the 'insights' dictionary passed by AnalysisAgent
            continuation_decision = insights.get('continuation_decision', {})
            should_continue_status = continuation_decision.get('should_continue', 'unknown')
            continuation_reason = continuation_decision.get('reason', 'N/A')
            
            evolved_goal_text = insights.get('evolved_goal')
            improvements_suggested_list = insights.get('improvements_suggested', [])

            observations = [
                f"Analysis completed: {datetime.now().isoformat()}",
                f"Iteration: {iteration_count}",
                f"Continuation Decision Status: {should_continue_status}",
                f"Continuation Reason: {continuation_reason[:200]}" # Truncate long reasons
            ]

            if evolved_goal_text:
                observations.append(f"Evolved Goal: {evolved_goal_text[:300]}") # Truncate long goals
            else:
                observations.append("Evolved Goal: Not set or N/A")

            observations.append(f"Improvements Suggested Count: {len(improvements_suggested_list)}")
            for i, improvement in enumerate(improvements_suggested_list[:3]): # Log top 3 improvements
                # 'improvement' is a dict, e.g., {'what': '...', 'why': '...', 'priority': '...'}
                improvement_desc = improvement.get('what', improvement.get('description', 'N/A'))
                priority = improvement.get('priority', 'N/A')
                observations.append(f"Improvement {i+1}: {improvement_desc[:150]} (Priority: {priority})")

            analysis_entity_name = f"analysis_{self.project_id}_{iteration_count}"
            analysis_entity_type = "analysis"
            
            # Use ContextMemory dataclass for consistency if MCP expects it,
            # otherwise, the dict format for create_entities is fine.
            # Assuming dict format is fine for create_entities based on other uses.
            analysis_entity_payload = {
                "name": analysis_entity_name,
                "entityType": analysis_entity_type,
                "observations": observations
                # Relations will be added by _create_relation if needed
            }
            
            result = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "create_entities",
                "arguments": {"entities": [analysis_entity_payload]} # Pass as a list
            })
            
            if self._is_mcp_success(result):
                # Create relation to iteration node
                # Assuming iteration nodes are named like f"iteration_node_{self.project_id}_{iteration_count}"
                # or f"iteration_{self.project_id}_{iteration_count}" - check consistency.
                # Based on store_iteration_start, it's f"iteration_{self.project_id}_{iteration_count}"
                iteration_name = f"iteration_{self.project_id}_{iteration_count}"
                self._create_relation(iteration_name, analysis_entity_name, "produces_analysis")
                
                self.logger.info(f"MEMORY: Stored analysis insights for iteration {iteration_count} as entity {analysis_entity_name}")
                return True
            else:
                error_details = result.get('error', result)
                self.logger.error(f"MEMORY: Failed to store analysis insights for iteration {iteration_count}. Entity: {analysis_entity_name}. Error: {error_details}")
                return False
                
        except Exception as e:
            self.logger.error(f"MEMORY: Analysis insights storage failed for iteration {iteration_count}: {e}", exc_info=True)
            return False
    
    # Private helper methods
    
    def _store_file_context(self, iteration_count: int, task_id: str, files: List[str], agent_type: str):
        """Store context for multiple files affected by a task."""
        for file_path in files:
            content_summary = f"File affected by {agent_type} agent in task {task_id}"
            self.store_file_operation(iteration_count, file_path, "modified", task_id, content_summary)
    
    def _get_previous_iteration_context(self, prev_iteration: int) -> List[Dict]:
        """Get context from previous iteration."""
        try:
            iteration_name = f"iteration_{self.project_id}_{prev_iteration}"
            result = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "open_nodes",
                "arguments": {"names": [iteration_name]}
            })
            
            if self._is_mcp_success(result):
                entities = result.get("result", {}).get("entities", [])
                if entities:
                    return [{
                        "iteration": prev_iteration,
                        "observations": entities[0].get("observations", [])
                    }]
            return []
        except Exception as e:
            self.logger.error(f"MEMORY: Previous iteration context retrieval failed: {e}")
            return []
    
    def _get_file_evolution_history(self) -> List[Dict]:
        """Get file evolution history across iterations."""
        try:
            result = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "search_nodes",
                "arguments": {"query": f"file_{self.project_id}"}
            })
            
            if self._is_mcp_success(result):
                entities = result.get("result", {}).get("entities", [])
                
                file_history = []
                for entity in entities:
                    if entity.get("entityType") == "file":
                        file_history.append({
                            "entity_name": entity.get("name", ""),
                            "observations": entity.get("observations", [])
                        })
                
                return file_history
            return []
        except Exception as e:
            self.logger.error(f"MEMORY: File evolution history retrieval failed: {e}")
            return []
    
    def _get_task_completion_patterns(self, current_iteration: int) -> List[Dict]:
        """Get patterns from previous task completions."""
        try:
            result = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "search_nodes",
                "arguments": {"query": f"task_{self.project_id}"}
            })
            
            if self._is_mcp_success(result):
                entities = result.get("result", {}).get("entities", [])
                
                patterns = []
                for entity in entities:
                    if entity.get("entityType") == "task":
                        patterns.append({
                            "entity_name": entity.get("name", ""),
                            "observations": entity.get("observations", [])
                        })
                
                return patterns
            return []
        except Exception as e:
            self.logger.error(f"MEMORY: Task patterns retrieval failed: {e}")
            return []
    
    def _get_project_evolution_insights(self, current_iteration: int) -> List[Dict]:
        """Get insights about project evolution."""
        try:
            # Get analysis entities for evolution insights
            result = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "search_nodes",
                "arguments": {"query": f"analysis_{self.project_id}"}
            })
            
            if self._is_mcp_success(result):
                entities = result.get("result", {}).get("entities", [])
                
                evolution = []
                for entity in entities:
                    if entity.get("entityType") == "analysis":
                        evolution.append({
                            "entity_name": entity.get("name", ""),
                            "observations": entity.get("observations", [])
                        })
                
                return evolution
            return []
        except Exception as e:
            self.logger.error(f"MEMORY: Project evolution insights retrieval failed: {e}")
            return []
    
    def _create_project_relation(self, entity_name: str, relation_type: str):
        """Create relation to project entity."""
        self._create_relation(f"project_{self.project_id}", entity_name, relation_type)
    
    def _create_relation(self, from_entity: str, to_entity: str, relation_type: str):
        """Create a relation between entities."""
        try:
            result = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "create_relations",
                "arguments": {"relations": [{"from": from_entity, "to": to_entity, "relationType": relation_type}]}
            })
            
            if self._is_mcp_success(result):
                self.logger.debug(f"MEMORY: Created relation {from_entity} --{relation_type}--> {to_entity}")
            else:
                self.logger.warning(f"MEMORY: Failed to create relation: {result}")
                
        except Exception as e:
            self.logger.error(f"MEMORY: Relation creation failed: {e}")
    
    def _is_mcp_success(self, result: Dict) -> bool:
        """Check if MCP call was successful."""
        # Check for error in result
        if result.get("error"):
            return False
        
        # Check for isError in nested result
        nested_result = result.get("result", {})
        if isinstance(nested_result, dict) and nested_result.get("isError", False):
            return False
        
        return True
    
    def get_memory_stats(self) -> Dict:
        """Get memory system statistics."""
        if not self.memory_service_available:
            self.logger.warning("MEMORY: Memory service is not available. Skipping get_memory_stats.")
            return {"error": "Memory service unavailable"}
        try:
            # Get entire graph to analyze
            result = self.mcp_manager.call_tool("memory", "tools/call", {
                "name": "read_graph",
                "arguments": {}
            })
            
            if self._is_mcp_success(result):
                graph = result.get("result", {})
                entities = graph.get("entities", [])
                relations = graph.get("relations", [])
                
                # Analyze by type
                entity_types = {}
                for entity in entities:
                    entity_type = entity.get("entityType", "unknown")
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                
                stats = {
                    "total_entities": len(entities),
                    "total_relations": len(relations),
                    "entity_types": entity_types,
                    "project_entities": len([e for e in entities if self.project_id in e.get("name", "")]),
                    "last_updated": datetime.now().isoformat()
                }
                
                self.logger.info(f"MEMORY: Memory stats - {stats['total_entities']} entities, "
                               f"{stats['total_relations']} relations, {stats['project_entities']} project-specific")
                
                return stats
            else:
                return {"error": "Failed to read memory graph"}
                
        except Exception as e:
            self.logger.error(f"MEMORY: Stats retrieval failed: {e}")
            return {"error": str(e)} 