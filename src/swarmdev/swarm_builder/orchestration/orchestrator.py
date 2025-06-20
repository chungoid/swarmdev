"""
Orchestration module for the SwarmDev platform.
This module provides the orchestrator for coordinating agent activities.
"""

import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING
import queue
import uuid
from concurrent.futures import ThreadPoolExecutor

from ..agents import BaseAgent
from ...utils.agent_logger import AgentLogger

if TYPE_CHECKING:
    from ...utils.mcp_manager import MCPManager
    from ...utils.memory_context_manager import MemoryContextManager


class Orchestrator:
    """
    Orchestrator for coordinating agent activities.
    
    This class manages the execution of workflows by coordinating
    the activities of multiple specialized agents.
    """
    
    def __init__(self, 
                 config: Optional[Dict] = None, 
                 mcp_manager: Optional['MCPManager'] = None, 
                 memory_manager: Optional['MemoryContextManager'] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config: Optional configuration dictionary
            mcp_manager: MCPManager instance
            memory_manager: Pre-initialized MemoryContextManager instance
        """
        self.config = config or {}
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, Dict] = {}
        self.tasks: Dict[str, Dict] = {}
        self.task_queue = queue.Queue()
        self.active_executions: Dict[str, Dict] = {}
        self.task_results: Dict[str, Dict] = {}
        self.task_dependencies: Dict[str, List[str]] = {}
        self.execution_threads: Dict[str, threading.Thread] = {}
        self.stop_event = threading.Event()
        self.logger = logging.getLogger("swarmdev.orchestrator")
        self.thread_pool = ThreadPoolExecutor(max_workers=self.config.get("max_concurrent_tasks", 5))
        self.project_structure_cache: Dict[str, Dict] = {}
        self.mcp_manager = mcp_manager
        self.memory_manager = memory_manager
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def register_agent(self, agent: BaseAgent) -> bool:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent: Agent instance
            
        Returns:
            bool: True if registration was successful, False otherwise
        """
        if agent.agent_id in self.agents:
            self.logger.warning(f"Agent with ID {agent.agent_id} already registered")
            return False
        
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent {agent.agent_id} of type {agent.agent_type}")
        return True
    
    def register_workflow(self, workflow_id: str, workflow: Dict) -> bool:
        """
        Register a workflow with the orchestrator.
        
        Args:
            workflow_id: Workflow identifier
            workflow: Workflow definition
            
        Returns:
            bool: True if registration was successful, False otherwise
        """
        if workflow_id in self.workflows:
            self.logger.warning(f"Workflow with ID {workflow_id} already registered")
            return False
        
        self.workflows[workflow_id] = workflow
        self.logger.info(f"Registered workflow {workflow_id}")
        return True
    
    def start(self) -> bool:
        """
        Start the orchestrator.
        
        Returns:
            bool: True if start was successful, False otherwise
        """
        if self.running:
            self.logger.warning("Orchestrator already running")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info("Orchestrator started")
        return True
    
    def stop(self) -> bool:
        """
        Stop the orchestrator.
        
        Returns:
            bool: True if stop was successful, False otherwise
        """
        if not self.running:
            self.logger.warning("Orchestrator not running")
            return False
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=30)
        
        self.logger.info("Orchestrator stopped")
        return True
    
    def execute_workflow(self, workflow_id: str, context: Dict) -> str:
        """
        Execute a registered workflow.

        Args:
            workflow_id: ID of the workflow to execute
            context: Context for the workflow (e.g., goal, project_dir)

        Returns:
            str: Execution ID
        """
        if workflow_id not in self.workflows:
            self.logger.error(f"Workflow {workflow_id} not registered.")
            raise ValueError(f"Workflow {workflow_id} not registered.")

        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        workflow_definition = self.workflows[workflow_id]

        self.active_executions[execution_id] = {
            "status": "starting",
            "tasks": {},
            "context": context,
            "workflow_id": workflow_id,
            "start_time": time.time(),
            "total_tasks_in_workflow": len(workflow_definition.get("tasks", {}))
        }
        self.logger.info(f"Workflow {workflow_id} starting with execution ID: {execution_id}")

        self._create_initial_tasks(workflow_definition, execution_id, context)
        
        return execution_id
    
    def get_execution_status(self, execution_id: str) -> Dict:
        """
        Get the status of a workflow execution.
        
        Args:
            execution_id: Execution identifier
            
        Returns:
            Dict: Execution status
        """
        # Filter tasks for this execution - include iteration cycle tasks
        execution_tasks = {}
        for task_id, task in self.tasks.items():
            task_exec_id = task.get("execution_id", "")
            # Include base execution tasks and iteration cycle tasks
            if task_exec_id == execution_id or task_exec_id.startswith(f"{execution_id}_cycle_"):
                execution_tasks[task_id] = task
        
        # Calculate overall status
        total_tasks = len(execution_tasks)
        completed_tasks = sum(1 for task in execution_tasks.values() if task.get("status") == "completed")
        failed_tasks = sum(1 for task in execution_tasks.values() if task.get("status") == "failed")
        in_progress_tasks = sum(1 for task in execution_tasks.values() if task.get("status") in ["ready", "waiting", "processing"])
        
        if total_tasks == 0:
            overall_status = "not_found"
        elif failed_tasks > 0:
            overall_status = "failed"
        elif in_progress_tasks > 0:
            overall_status = "in_progress"
        elif completed_tasks == total_tasks:
            overall_status = "completed"
        else:
            overall_status = "in_progress"
        
        # Collect MCP and LLM metrics from agents
        mcp_metrics = self._collect_mcp_metrics()
        llm_metrics = self._collect_llm_metrics()
        
        # Prepare status report
        status = {
            "execution_id": execution_id,
            "status": overall_status,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "tasks": {task_id: task.get("status") for task_id, task in execution_tasks.items()},
            "mcp_metrics": mcp_metrics,
            "llm_metrics": llm_metrics
        }
        
        return status
    
    def _run(self):
        """Main orchestrator loop."""
        while self.running:
            try:
                # Process task queue
                self._process_task_queue()
                
                # Check for task dependencies
                self._check_task_dependencies()
                
                # Sleep to avoid high CPU usage
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in orchestrator loop: {e}")
    
    def _process_task_queue(self):
        """Process the task queue."""
        if self.task_queue.empty():
            return
        
        # Get the next task
        try:
            task_id = self.task_queue.get_nowait()
        except queue.Empty:
            return
            
        task = self.tasks.get(task_id)
        
        if not task:
            # Task not found, it might have been removed or is an error
            self.logger.warning(f"Task ID {task_id} retrieved from queue but not found in self.tasks.")
            return
        
        if task.get("status") != "ready":
            # Task not ready, put it back if it's not already completed or failed
            # This scenario should ideally be handled by _check_task_dependencies ensuring only ready tasks are processed.
            # However, if a task was put on the queue and its status changed, this handles it.
            if task.get("status") not in ["completed", "failed"]:
                 self.task_queue.put(task_id) # Put back if not terminally processed
            return
        
        # Get the agent - try agent_id first, then find by agent_type
        agent_id = task.get("agent_id")
        agent = self.agents.get(agent_id)
        
        if not agent:
            # Try to find agent by type
            agent_type = task.get("agent_type")
            self.logger.debug(f"Agent ID {agent_id} not found directly for task {task_id}. Trying by type: {agent_type}")
            for aid, a in self.agents.items():
                if a.agent_type == agent_type:
                    agent = a
                    # Update agent_id in the task if found by type, for logging/consistency
                    task["agent_id"] = aid 
                    agent_id = aid # Update agent_id for subsequent logging
                    self.logger.debug(f"Found agent by type: {aid} for task {task_id}")
                    break
        
        if not agent:
            # Agent not found by ID or type, mark task as failed
            task["status"] = "failed"
            task["error"] = f"Agent with ID '{agent_id}' or type '{task.get('agent_type')}' not found for task '{task_id}'."
            # Task was already removed by get_nowait(), and it's failed, so do not put back.
            self.logger.error(task["error"])
            return
        
        # Execute the task
        try:
            task["status"] = "processing"
            AgentLogger.log_task_start(agent.logger, task) # Logging task start
            start_time = time.time()

            result = agent.process_task(task) # Agent processes task

            duration = time.time() - start_time
            AgentLogger.log_task_complete(agent.logger, task, result, duration) # Logging task completion

            task["result"] = result
            task["status"] = "completed" # Task marked completed
            task["completed_at"] = datetime.now().isoformat()
            
            # Artifacts are now saved directly by the agents using tools

            # Store task completion in memory
            if self.memory_manager:
                iteration_count_from_task_attr = task.get("iteration_count") # Check direct attribute first
                iteration_count_from_context = task.get("context", {}).get("iteration_count")
                iteration_count = 0 # Default

                if iteration_count_from_task_attr is not None:
                    try:
                        iteration_count = int(iteration_count_from_task_attr)
                    except ValueError:
                        self.logger.warning(f"Could not parse iteration_count '{iteration_count_from_task_attr}' from task attribute.")
                        iteration_count = 0 
                elif iteration_count_from_context is not None:
                    try:
                        iteration_count = int(iteration_count_from_context)
                    except ValueError:
                        self.logger.warning(f"Could not parse iteration_count '{iteration_count_from_context}' from task context.")
                        iteration_count = 0
                else:
                    # Fallback to parsing from execution_id if not explicitly provided
                    execution_id_str = task.get("execution_id", "")
                    if "_cycle_" in execution_id_str:
                        try:
                            # e.g., exec_..._cycle_1 or exec_..._cycle_1_completion_evaluation
                            cycle_part = execution_id_str.split("_cycle_")[1]
                            iteration_count = int(cycle_part.split("_")[0])
                        except (IndexError, ValueError) as e_parse:
                            self.logger.warning(f"Could not parse iteration_count from execution_id '{execution_id_str}': {e_parse}")
                            iteration_count = 0 # Fallback
                    # If no _cycle_, it's part of the main flow or iteration 0 implicitly
                
                files_created = result.get("files_created", [])
                files_modified = result.get("files_modified", [])
                files_affected = list(set(files_created + files_modified)) # Use set to avoid duplicates, then list

                agent_type_for_memory = task.get("agent_type", "unknown_agent")
                
                # Extract the short task ID from the full task ID
                # task["execution_id"] is the specific execution ID for this task (e.g., exec_datetime_uuid_cycle_N)
                # task_id is the full unique ID (e.g., exec_datetime_uuid_cycle_N_short_task_name)
                task_execution_id_prefix = task.get("execution_id", "") + "_"
                short_task_id_for_memory = task_id.replace(task_execution_id_prefix, "", 1) if task_id.startswith(task_execution_id_prefix) else task_id
                
                # If replacement didn't change anything and execution_id is part of task_id, try splitting
                if short_task_id_for_memory == task_id and task.get("execution_id","") in task_id :
                     parts = task_id.split(task.get("execution_id","") + "_")
                     if len(parts) > 1:
                         short_task_id_for_memory = parts[1]


                self.logger.debug(f"Storing task completion in memory: iteration={iteration_count}, short_task_id='{short_task_id_for_memory}', full_task_id='{task_id}', agent='{agent_type_for_memory}'")
                self.memory_manager.store_task_completion(
                    iteration_count=iteration_count,
                    task_id=short_task_id_for_memory, 
                    agent_type=agent_type_for_memory,
                    result=result, 
                    files_affected=files_affected
                )
            
            # Check if this is an analysis task that should trigger workflow continuation
            self._check_workflow_continuation(task) 
            
            # Check for dependent tasks
            self._handle_task_completion(task_id) 
            
        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)
            self.logger.error(f"Error executing task {task_id}: {e}")
    
    def _check_task_dependencies(self):
        """Check for tasks with satisfied dependencies."""
        for task_id, task in self.tasks.items():
            if task.get("status") == "waiting":
                # Check if all dependencies are completed
                dependencies = task.get("dependencies", [])
                all_completed = all(
                    self.tasks.get(dep, {}).get("status") == "completed"
                    for dep in dependencies
                )
                
                if all_completed:
                    # All dependencies completed, mark as ready
                    task["status"] = "ready"
                    self.task_queue.put(task_id)
    
    def _handle_task_completion(self, task_id: str):
        """
        Handle the completion of a task.
        
        Args:
            task_id: Task identifier
        """
        # Check for tasks that depend on this task
        for dependent_id, dependent in self.tasks.items():
            if dependent.get("status") == "waiting" and task_id in dependent.get("dependencies", []):
                # Check if all dependencies are completed
                dependencies = dependent.get("dependencies", [])
                all_completed = all(
                    self.tasks.get(dep, {}).get("status") == "completed"
                    for dep in dependencies
                )
                
                if all_completed:
                    # Collect results from dependency tasks and add to context
                    dependency_results = self._collect_dependency_results(dependencies)
                    if dependency_results:
                        dependent_context = dependent.get("context", {})
                        dependent_context.update(dependency_results)
                        dependent["context"] = dependent_context
                        self.logger.info(f"Added dependency results to task {dependent_id}: {list(dependency_results.keys())}")
                    
                    # All dependencies completed, mark as ready
                    dependent["status"] = "ready"
                    self.task_queue.put(dependent_id)
        
        # Check if this completed task should trigger workflow continuation
        completed_task = self.tasks.get(task_id)
        if completed_task:
            self._check_workflow_continuation(completed_task)
    
    def _create_initial_tasks(self, workflow: Dict, execution_id: str, context: Dict):
        """
        Create initial tasks for a workflow.
        
        Args:
            workflow: Workflow definition
            execution_id: Execution identifier
            context: Execution context
        """
        # Get the initial tasks
        initial_tasks = workflow.get("initial_tasks", [])
        
        for task_def in initial_tasks:
            task_id = f"{execution_id}_{task_def['id']}"
            
            # Create the task
            task = {
                "task_id": task_id,
                "execution_id": execution_id,
                "workflow_id": workflow.get("id"),
                "agent_id": task_def.get("agent_id"),
                "agent_type": task_def.get("agent_type"),
                "dependencies": [],
                "status": "ready",
                "created_at": datetime.now().isoformat(),
                "context": context,
                "goal": context.get("goal"),  # Include the actual goal text
                "project_dir": context.get("project_dir")  # Include project directory
            }
            
            # Add task-specific data
            task.update(task_def.get("data", {}))
            
            # Add to tasks and queue
            self.tasks[task_id] = task
            self.task_queue.put(task_id)
            self.logger.info(f"Created initial task: {task_id} (agent_type: {task_def.get('agent_type')})")
        
        # Create dependent tasks
        dependent_tasks = workflow.get("dependent_tasks", [])
        
        for task_def in dependent_tasks:
            task_id = f"{execution_id}_{task_def['id']}"
            
            # Create the task
            task = {
                "task_id": task_id,
                "execution_id": execution_id,
                "workflow_id": workflow.get("id"),
                "agent_id": task_def.get("agent_id"),
                "agent_type": task_def.get("agent_type"),
                "dependencies": [f"{execution_id}_{dep}" for dep in task_def.get("dependencies", [])],
                "status": "waiting",
                "created_at": datetime.now().isoformat(),
                "context": context,
                "goal": context.get("goal"),  # Include the actual goal text
                "project_dir": context.get("project_dir")  # Include project directory
            }
            
            # Add task-specific data
            task.update(task_def.get("data", {}))
            
            # Add to tasks
            self.tasks[task_id] = task
    
    def _collect_dependency_results(self, dependencies: List[str]) -> Dict:
        """
        Collect results from dependency tasks to pass to dependent tasks.
        
        Args:
            dependencies: List of dependency task IDs
            
        Returns:
            Dict: Collected results from dependencies
        """
        collected_results = {}
        
        for dep_task_id in dependencies:
            dep_task = self.tasks.get(dep_task_id)
            if not dep_task or dep_task.get("status") != "completed":
                continue
            
            dep_result = dep_task.get("result", {})
            dep_agent_type = dep_task.get("agent_type", "unknown")
            
            # Map agent results to expected context keys
            if dep_agent_type == "analysis":
                collected_results["analysis_results"] = dep_result
            elif dep_agent_type == "research":
                collected_results["research_results"] = dep_result
            elif dep_agent_type == "planning":
                collected_results["planning_results"] = dep_result
            elif dep_agent_type == "development":
                collected_results["development_results"] = dep_result
            elif dep_agent_type == "documentation":
                collected_results["documentation_results"] = dep_result
            
            self.logger.debug(f"Collected {dep_agent_type} results from task {dep_task_id}")
        
        return collected_results
    
    def _save_task_artifacts(self, task: Dict, result: Dict):
        """
        Save artifacts generated by a task to the project directory using proper project structure.
        
        Args:
            task: Task information
            result: Task result containing artifacts
        """
        try:
            # Get project directory and goal from task context
            context = task.get("context", {})
            project_dir = context.get("project_dir", ".")
            goal = context.get("goal", "")
            
            # Determine project structure based on goal and result
            project_structure = self._determine_project_structure(goal, result)
            
            # Extract artifacts from result
            artifacts = self._extract_artifacts_from_result(result, project_structure)
            
            # Save all artifacts with proper structure
            for artifact in artifacts:
                if artifact.get("type") == "file":
                    file_path = os.path.join(project_dir, artifact["path"])
                    
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Write the file
                    with open(file_path, 'w') as f:
                        f.write(artifact["content"])
                    
                    self.logger.info(f"Saved artifact: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving task artifacts: {e}")
    
    def _determine_project_structure(self, goal: str, result: Dict) -> Dict:
        """
        Determine the appropriate project structure based on goal and project analysis.
        
        Args:
            goal: Project goal text
            result: Task result (may contain project analysis)
            
        Returns:
            Dict: Project structure mapping
        """
        # Check if development agent provided project analysis
        if "implementation" in result and "project_analysis" in result["implementation"]:
            analysis = result["implementation"]["project_analysis"]
            language = analysis.get("language", "").lower()
            project_type = analysis.get("project_type", "").lower()
        else:
            # Fallback analysis based on goal
            goal_lower = goal.lower()
            if "python" in goal_lower or "pip" in goal_lower or "cli" in goal_lower:
                language = "python"
                project_type = "cli_tool"
            elif "web" in goal_lower or "html" in goal_lower or "browser" in goal_lower:
                language = "web"
                project_type = "web_app"
            elif "api" in goal_lower or "rest" in goal_lower or "fastapi" in goal_lower:
                language = "python"
                project_type = "api"
            elif "go" in goal_lower or "golang" in goal_lower:
                language = "go"
                project_type = "application"
            elif "rust" in goal_lower:
                language = "rust"
                project_type = "application"
            elif "java" in goal_lower:
                language = "java"
                project_type = "application"
            else:
                language = "python"
                project_type = "application"
        
        # Define structure based on language and project type
        if language == "python":
            return {
                "source_dir": "src/",
                "docs_dir": "docs/",
                "research_dir": "research/",
                "planning_dir": "planning/",
                "tests_dir": "tests/",
                "config_files_root": True
            }
        elif language == "web":
            return {
                "source_dir": "src/",
                "docs_dir": "docs/",
                "research_dir": "research/",
                "planning_dir": "planning/",
                "assets_dir": "src/assets/",
                "css_dir": "src/css/",
                "js_dir": "src/js/",
                "config_files_root": True
            }
        elif language == "go":
            return {
                "source_dir": "cmd/",
                "internal_dir": "internal/",
                "pkg_dir": "pkg/",
                "docs_dir": "docs/",
                "research_dir": "research/",
                "planning_dir": "planning/",
                "config_files_root": True
            }
        elif language == "rust":
            return {
                "source_dir": "src/",
                "docs_dir": "docs/",
                "research_dir": "research/",
                "planning_dir": "planning/",
                "tests_dir": "tests/",
                "config_files_root": True
            }
        elif language == "java":
            return {
                "source_dir": "src/main/java/",
                "resources_dir": "src/main/resources/",
                "test_dir": "src/test/java/",
                "docs_dir": "docs/",
                "research_dir": "research/",
                "planning_dir": "planning/",
                "config_files_root": True
            }
        else:
            # Generic structure
            return {
                "source_dir": "src/",
                "docs_dir": "docs/",
                "research_dir": "research/",
                "planning_dir": "planning/",
                "config_files_root": True
            }
    
    def _extract_artifacts_from_result(self, result: Dict, structure: Dict) -> List[Dict]:
        """
        Extract artifacts from task result and map them to proper project structure.
        
        Args:
            result: Task result
            structure: Project structure mapping
            
        Returns:
            List[Dict]: List of artifacts with proper paths
        """
        artifacts = []
        
        # Direct artifacts
        artifacts.extend(result.get("artifacts", []))
        
        # Development artifacts (code files)
        if "implementation" in result and "files_created" in result["implementation"]:
            files_created = result["implementation"]["files_created"]
            for filename in files_created:
                # Determine proper location for this file
                if self._is_source_file(filename):
                    if filename.endswith(('.html', '.htm')):
                        # HTML files go to source root or index files
                        path = f"{structure.get('source_dir', '')}index.html" if filename == "index.html" else f"{structure.get('source_dir', '')}{filename}"
                    elif filename.endswith('.css'):
                        path = f"{structure.get('css_dir', structure.get('source_dir', ''))}{filename}"
                    elif filename.endswith('.js'):
                        path = f"{structure.get('js_dir', structure.get('source_dir', ''))}{filename}"
                    else:
                        path = f"{structure.get('source_dir', '')}{filename}"
                elif self._is_config_file(filename):
                    path = filename  # Config files stay at root
                else:
                    path = f"{structure.get('source_dir', '')}{filename}"
                
                # Don't add if we don't have the content - it was created directly by the agent
                # This avoids duplicate file creation
        
        # Research artifacts
        if "findings" in result:
            content = self._format_research_findings(result["findings"])
            artifacts.append({
                "type": "file",
                "path": f"{structure.get('research_dir', '')}findings.md",
                "content": content
            })
        
        # Planning artifacts
        if "blueprint" in result:
            content = self._format_blueprint(result["blueprint"])
            artifacts.append({
                "type": "file",
                "path": f"{structure.get('planning_dir', '')}blueprint.md",
                "content": content
            })
        
        if "implementation_plan" in result:
            content = self._format_implementation_plan(result["implementation_plan"])
            artifacts.append({
                "type": "file",
                "path": f"{structure.get('planning_dir', '')}implementation_plan.md",
                "content": content
            })
        
        # Documentation artifacts
        if "component_docs" in result:
            for doc in result["component_docs"]:
                if doc.get("content"):
                    artifacts.append({
                        "type": "file",
                        "path": f"{structure.get('docs_dir', '')}{doc.get('component_id', 'component')}.md",
                        "content": doc["content"]
                    })
        
        if "api_docs" in result and result["api_docs"].get("content"):
            artifacts.append({
                "type": "file",
                "path": f"{structure.get('docs_dir', '')}api.md",
                "content": result["api_docs"]["content"]
            })
        
        if "user_guide" in result and result["user_guide"].get("content"):
            artifacts.append({
                "type": "file",
                "path": f"{structure.get('docs_dir', '')}user_guide.md",
                "content": result["user_guide"]["content"]
            })
        
        return artifacts
    
    def _is_source_file(self, filename: str) -> bool:
        """Check if a file is a source code file."""
        source_extensions = {'.py', '.js', '.ts', '.html', '.css', '.go', '.rs', '.java', '.cpp', '.c', '.h'}
        return any(filename.endswith(ext) for ext in source_extensions)
    
    def _is_config_file(self, filename: str) -> bool:
        """Check if a file is a configuration file that should stay at project root."""
        config_files = {
            'requirements.txt', 'setup.py', 'pyproject.toml', 'package.json', 'Cargo.toml', 
            'go.mod', 'pom.xml', 'build.gradle', 'Makefile', 'Dockerfile', '.gitignore',
            'README.md', 'LICENSE'
        }
        return filename in config_files
    
    def _format_research_findings(self, findings: Dict) -> str:
        """Format research findings into markdown."""
        content = "# Research Findings\n\n"
        
        if findings.get("main_points"):
            content += "## Key Findings\n\n"
            for point in findings["main_points"]:
                content += f"- {point}\n"
        
        if findings.get("sources"):
            content += "\n## Sources\n\n"
            for source in findings["sources"]:
                content += f"- {source}\n"
        
        if findings.get("summary"):
            content += f"\n## Summary\n\n{findings['summary']}\n"
        
        return content
    
    def _format_blueprint(self, blueprint: Dict) -> str:
        """Format project blueprint into markdown."""
        content = "# Project Blueprint\n\n"
        content += f"## Overview\n{blueprint.get('overview', 'N/A')}\n\n"
        content += f"## Architecture\n{blueprint.get('architecture', 'N/A')}\n\n"
        
        if blueprint.get('key_features'):
            content += "## Key Features\n"
            for feature in blueprint['key_features']:
                content += f"- {feature}\n"
        
        if blueprint.get('technologies'):
            content += "\n## Technologies\n"
            for tech in blueprint['technologies']:
                content += f"- {tech}\n"
        
        if blueprint.get('full_description'):
            content += f"\n## Detailed Description\n\n{blueprint['full_description']}\n"
        
        return content
    
    def _format_implementation_plan(self, plan: Dict) -> str:
        """Format implementation plan into markdown."""
        content = "# Implementation Plan\n\n"
        
        if plan.get('phases'):
            for phase in plan['phases']:
                content += f"## {phase.get('name', 'Phase')}\n"
                content += f"{phase.get('description', 'No description')}\n\n"
                content += f"**Duration:** {phase.get('estimated_duration', 'Unknown')}\n\n"
                
                if phase.get('components'):
                    content += "**Components:**\n"
                    for component in phase['components']:
                        content += f"- {component}\n"
                    content += "\n"
        
        if plan.get('total_estimated_duration'):
            content += f"## Total Estimated Duration\n{plan['total_estimated_duration']}\n\n"
        
        return content
    
    def _check_workflow_continuation(self, task: Dict):
        """
        Check if a completed task should trigger workflow continuation.
        
        Args:
            task: Completed task information
        """
        try:
            # Check analysis tasks with completion evaluation
            if task.get("agent_type") == "analysis":
                task_id = task.get("task_id", "")
                
                # Check if this is a completion evaluation task
                if "completion_evaluation" in task_id:
                    result = task.get("result", {})
                    continuation_decision = result.get("continuation_decision", {})
                    should_continue = continuation_decision.get("should_continue", False)
                    
                    self.logger.info(f"Analysis completion evaluation: should_continue={should_continue}, reason={continuation_decision.get('reason', 'No reason provided')}")
                    
                    if should_continue:
                        execution_id = task.get("execution_id")
                        workflow_id = task.get("workflow_id")
                        context = task.get("context", {}).copy()  # Copy context to avoid mutation
                        
                        # Extract cycle information
                        if "_cycle_" in execution_id:
                            # This is already a cycle execution, extract the cycle number
                            base_execution = execution_id.split('_cycle_')[0]
                            current_cycle = int(execution_id.split('_cycle_')[1])
                            next_iteration = current_cycle + 1
                        else:
                            # This is the initial execution, next will be cycle 1
                            base_execution = execution_id
                            next_iteration = 1
                        
                        # Check adaptive vs fixed iteration limits
                        max_iterations = context.get("max_iterations")
                        adaptive = context.get("adaptive", True)
                        completion_strategy = context.get("completion_strategy", "smart")
                        
                        # Apply iteration limits based on strategy
                        if not adaptive and max_iterations and next_iteration > max_iterations:
                            self.logger.info(f"Non-adaptive mode: reached max iterations ({max_iterations}), stopping despite analysis suggesting continuation")
                            return
                        
                        if completion_strategy == "smart" and adaptive:
                            # Smart + adaptive: trust the analysis decision regardless of initial max_iterations
                            self.logger.info(f"Smart adaptive mode: continuing to iteration {next_iteration} based on analysis decision")
                        elif max_iterations and next_iteration > max_iterations * 2:
                            # Safety limit: even in adaptive mode, don't exceed 2x the initial estimate
                            self.logger.info(f"Safety limit reached: stopping at iteration {next_iteration} (2x initial estimate)")
                            return
                        
                        # Get evolved goal from the analysis result
                        evolved_goal = result.get("evolved_goal")
                        if evolved_goal:
                            context["goal"] = evolved_goal
                            context["evolved_goal"] = evolved_goal
                            self.logger.info(f"Updated context with evolved goal for iteration {next_iteration}")
                        
                        # Update iteration count in context
                        context["iteration_count"] = next_iteration
                        
                        # Create new workflow execution cycle
                        self._create_iteration_cycle(workflow_id, base_execution, context, next_iteration)
                        
                        self.logger.info(f"Started iteration cycle {next_iteration} for execution {base_execution}")
                    else:
                        self.logger.info(f"Analysis determined workflow is complete: {continuation_decision.get('reason', 'No reason provided')}")
                
                return
            
            # Legacy support: also check development tasks for backward compatibility
            elif task.get("agent_type") == "development":
                task_id = task.get("task_id", "")
                
                # Check if this is an implementation task that completes an iteration cycle
                iteration_task_names = [
                    "improvement_implementation",
                    "strategic_implementation",  # Enhanced iteration workflow task name
                    "smart_implementation"       # Standard iteration workflow task name
                ]
                
                if any(task_name in task_id for task_name in iteration_task_names):
                    # For development tasks, check if there's no analysis task to handle continuation
                    execution_id = task.get("execution_id")
                    
                    # Look for completion_evaluation analysis task in same execution
                    has_completion_analysis = any(
                        t.get("execution_id") == execution_id and 
                        t.get("agent_type") == "analysis" and 
                        "completion_evaluation" in t.get("task_id", "")
                        for t in self.tasks.values()
                    )
                    
                    if not has_completion_analysis:
                        # No analysis task found, fall back to legacy behavior
                        self.logger.info("No completion evaluation analysis found, using legacy development-based continuation")
                        # [Legacy logic would go here, but for now we'll just log and return]
                        return
                
        except Exception as e:
            self.logger.error(f"Error checking workflow continuation: {e}")
    
    def _get_most_recent_evolved_goal(self, base_execution_id: str, current_execution_id: str) -> Optional[str]:
        """
        Get the most recent evolved goal from completed analysis tasks in this execution family.
        
        Args:
            base_execution_id: Base execution ID
            current_execution_id: Current execution ID
            
        Returns:
            Optional[str]: Most recent evolved goal if available
        """
        try:
            most_recent_goal = None
            latest_timestamp = None
            
            # Look for completed analysis tasks in this execution family
            for task_id, task in self.tasks.items():
                task_exec_id = task.get("execution_id", "")
                
                # Check if this is an analysis task from the same execution family
                if (task.get("agent_type") == "analysis" and 
                    task.get("status") == "completed" and
                    (task_exec_id == base_execution_id or 
                     task_exec_id.startswith(f"{base_execution_id}_cycle_") or
                     task_exec_id == current_execution_id)):
                    
                    result = task.get("result", {})
                    evolved_goal = result.get("evolved_goal")
                    task_timestamp = task.get("completed_at")
                    
                    if evolved_goal and task_timestamp:
                        if latest_timestamp is None or task_timestamp > latest_timestamp:
                            most_recent_goal = evolved_goal
                            latest_timestamp = task_timestamp
                            self.logger.info(f"Found evolved goal from task {task_id} at {task_timestamp}")
            
            return most_recent_goal
            
        except Exception as e:
            self.logger.error(f"Error getting most recent evolved goal: {e}")
            return None
    
    def _create_iteration_cycle(self, workflow_id: str, base_execution_id: str, context: Dict, iteration_count: int):
        """
        Create a new iteration cycle for iterative workflows.
        
        Args:
            workflow_id: Workflow identifier
            base_execution_id: Base execution ID (should be the original, not nested)
            context: Execution context
            iteration_count: Current iteration number
        """
        try:
            # Get the workflow definition
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                self.logger.error(f"Workflow {workflow_id} not found for iteration")
                return
            
            # Extract the original execution ID (remove any existing cycle suffixes)
            original_execution_id = base_execution_id.split('_cycle_')[0]
            
            # Create new execution ID for this iteration - use original base + cycle number
            cycle_execution_id = f"{original_execution_id}_cycle_{iteration_count}"
            
            # Get evolved goal from previous analysis if available
            evolved_goal = self._get_evolved_goal_for_iteration(base_execution_id, iteration_count)
            if evolved_goal:
                context = context.copy()  # Don't modify original context
                context["goal"] = evolved_goal
                self.logger.info(f"Using evolved goal for iteration {iteration_count}")
            
            # Get improvement suggestions from previous analysis if available
            improvement_suggestions = self._get_previous_analysis_improvements(base_execution_id)
            if improvement_suggestions:
                context["improvement_suggestions"] = improvement_suggestions
                self.logger.info(f"Found {len(improvement_suggestions)} improvements from previous analysis")
            
            # Create analysis task for this iteration
            task_id = f"{cycle_execution_id}_completion_evaluation"  # Updated to match new workflow
            
            analysis_task = {
                "task_id": task_id,
                "execution_id": cycle_execution_id,
                "workflow_id": workflow_id,
                "agent_type": "analysis",
                "dependencies": [],
                "status": "ready",
                "created_at": datetime.now().isoformat(),
                "context": context,
                "goal": context.get("goal"),  # This will now be the evolved goal if available
                "project_dir": context.get("project_dir"),
                "iteration_count": iteration_count,
                "initial_iterations": context.get("initial_iterations", context.get("max_iterations", 3)),  # Enhanced workflow uses initial_iterations
                "workflow_type": context.get("workflow_type", "iteration"),
                "analysis_depth": "completion_focused",  # Enhanced workflow uses completion_focused
                "check_continue": True,
                # Enhanced workflow context
                "target_version": context.get("target_version"),
                "completion_strategy": context.get("completion_strategy", "smart"),
                "adaptive_planning": context.get("adaptive", True)
            }
            
            # Add task to execution
            self.tasks[task_id] = analysis_task
            self.task_queue.put(task_id)
            
            # If analysis suggests improvements, create planning and implementation tasks
            planning_task_id = f"{cycle_execution_id}_strategic_planning"  # Enhanced workflow task name
            implementation_task_id = f"{cycle_execution_id}_strategic_implementation"  # Enhanced workflow task name
            
            planning_task = {
                "task_id": planning_task_id,
                "execution_id": cycle_execution_id,
                "workflow_id": workflow_id,
                "agent_type": "planning",
                "dependencies": [task_id],
                "status": "waiting",
                "created_at": datetime.now().isoformat(),
                "context": context,
                "goal": context.get("goal"),  # This will now be the evolved goal if available
                "project_dir": context.get("project_dir"),
                "planning_type": "strategic_iteration",  # Enhanced workflow planning type
                "use_analysis_results": True,
                "use_research_results": True,  # Enhanced workflow uses research
                "preserve_functionality": True,
                "plan_incremental_steps": True,
                "risk_assessment": True,
                "plan_iteration_roadmap": True,
                "estimate_effort_distribution": True,
                "plan_completion_sequence": True
            }
            
            implementation_task = {
                "task_id": implementation_task_id,
                "execution_id": cycle_execution_id,
                "workflow_id": workflow_id,
                "agent_type": "development",
                "dependencies": [planning_task_id],
                "status": "waiting",
                "created_at": datetime.now().isoformat(),
                "context": context,
                "goal": context.get("goal"),  # This will now be the evolved goal if available
                "project_dir": context.get("project_dir"),
                "implementation_style": "adaptive",  # Enhanced workflow implementation style
                "preserve_existing": True,
                "incremental_refactor": True,
                "maintain_compatibility": True,
                "focus_on_improvements": True,
                "use_analysis_results": True,
                "use_research_results": True,
                "implementation_prioritization": "completion_focused"
            }
            
            # Add dependent tasks
            self.tasks[planning_task_id] = planning_task
            self.tasks[implementation_task_id] = implementation_task
            
            self.logger.info(f"Created iteration cycle {iteration_count} with {len([task_id, planning_task_id, implementation_task_id])} tasks")
            
        except Exception as e:
            self.logger.error(f"Error creating iteration cycle: {e}")
    
    def _get_evolved_goal_for_iteration(self, execution_id: str, iteration_count: int) -> Optional[str]:
        """
        Get the evolved goal for the current iteration from previous analysis results.
        
        Args:
            execution_id: Current or previous execution ID
            iteration_count: Current iteration number
            
        Returns:
            Optional[str]: Evolved goal text if available
        """
        try:
            # Look for completed analysis tasks in this execution family
            base_execution = execution_id.split('_cycle_')[0]
            
            # Check for evolved goal from the most recent analysis task
            for task_id, task in self.tasks.items():
                task_exec_id = task.get("execution_id", "")
                
                # Check if this is a recent analysis task from the same execution family
                if (task.get("agent_type") == "analysis" and 
                    task.get("status") == "completed" and
                    (task_exec_id == base_execution or task_exec_id.startswith(f"{base_execution}_cycle_"))):
                    
                    result = task.get("result", {})
                    evolved_goal = result.get("evolved_goal")
                    
                    if evolved_goal:
                        self.logger.info(f"Found evolved goal from task {task_id}")
                        return evolved_goal
            
            # Also check for goal files on disk (check both goals directory and project root for backward compatibility)
            try:
                import os
                
                # Get project_dir from any task in this execution family
                project_dir = "."
                for task_id, task in self.tasks.items():
                    task_exec_id = task.get("execution_id", "")
                    if (task_exec_id == base_execution or task_exec_id.startswith(f"{base_execution}_cycle_")):
                        project_dir = task.get("project_dir", ".")
                        break
                
                # First check .swarmdev/goals directory (new location)
                goals_dir_path = os.path.join(project_dir, ".swarmdev", "goals", f"goal_iteration_{iteration_count}.txt")
                if os.path.exists(goals_dir_path):
                    with open(goals_dir_path, 'r') as f:
                        evolved_goal = f.read().strip()
                        if evolved_goal:
                            self.logger.info(f"Found evolved goal from file: {goals_dir_path}")
                            return evolved_goal
                
                # Fallback to project root (old location for backward compatibility)
                goal_file_path = f"goal_iteration_{iteration_count}.txt"
                if os.path.exists(goal_file_path):
                    with open(goal_file_path, 'r') as f:
                        evolved_goal = f.read().strip()
                        if evolved_goal:
                            self.logger.info(f"Found evolved goal from file: {goal_file_path}")
                            return evolved_goal
            except Exception as e:
                self.logger.warning(f"Could not read evolved goal file: {e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting evolved goal: {e}")
            return None
    
    def _get_previous_analysis_improvements(self, execution_id: str) -> List[Dict]:
        """
        Get improvement suggestions from previous analysis tasks in the same execution family.
        
        Args:
            execution_id: Current or previous execution ID
            
        Returns:
            List[Dict]: List of improvement suggestions
        """
        improvements = []
        
        try:
            # Look for completed analysis tasks in this execution family
            base_execution = execution_id.split('_cycle_')[0]
            
            for task_id, task in self.tasks.items():
                task_exec_id = task.get("execution_id", "")
                
                # Check if this is an analysis task from the same execution family
                if (task.get("agent_type") == "analysis" and 
                    task.get("status") == "completed" and
                    (task_exec_id == base_execution or task_exec_id.startswith(f"{base_execution}_cycle_"))):
                    
                    result = task.get("result", {})
                    if "improvements_suggested" in result:
                        improvements.extend(result["improvements_suggested"])
                    elif "improvement_analysis" in result:
                        analysis = result["improvement_analysis"]
                        if "improvements" in analysis:
                            improvements.extend(analysis["improvements"])
            
            # Remove duplicates
            unique_improvements = []
            seen_descriptions = set()
            
            for imp in improvements:
                desc = imp.get("what", imp.get("description", ""))
                if desc and desc not in seen_descriptions:
                    unique_improvements.append(imp)
                    seen_descriptions.add(desc)
            
            return unique_improvements
            
        except Exception as e:
            self.logger.error(f"Error getting previous analysis improvements: {e}")
            return []

    def _collect_mcp_metrics(self) -> Dict:
        """Collect metrics from all agents related to MCP (Machine Learning and AI) usage."""
        metrics = {}
        for agent_id, agent in self.agents.items():
            if hasattr(agent, 'collect_mcp_metrics'):
                metrics[agent_id] = agent.collect_mcp_metrics()
        return metrics

    def _collect_llm_metrics(self) -> Dict:
        """Collect metrics from all agents related to LLM (Large Language Model) usage."""
        metrics = {}
        for agent_id, agent in self.agents.items():
            if hasattr(agent, 'collect_llm_metrics'):
                metrics[agent_id] = agent.collect_llm_metrics()
        return metrics
