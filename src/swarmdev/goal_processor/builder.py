"""
SwarmBuilder implementation for the SwarmDev platform.
This module provides functionality for building projects based on goals.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List, TYPE_CHECKING

from .storage import GoalStorage
from ..utils.llm_provider import ProviderRegistry, LLMProviderInterface
from swarmdev.swarm_builder.orchestration import Orchestrator
from swarmdev.swarm_builder.agents import ResearchAgent, PlanningAgent, DevelopmentAgent, DocumentationAgent, AnalysisAgent
from swarmdev.swarm_builder.workflows import get_workflow_by_id
from ..utils.memory_context_manager import MemoryContextManager

if TYPE_CHECKING:
    from ..utils.mcp_manager import MCPManager

class SwarmBuilder:
    """
    Builder for autonomous project development.
    
    This class coordinates the swarm of agents to build a project based on a goal.
    """
    
    def __init__(
        self,
        project_dir: str,
        goal_file: Optional[str] = None,
        goal_id: Optional[str] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize the SwarmBuilder.
        
        Args:
            project_dir: Directory for project files
            goal_file: Path to goal file (mutually exclusive with goal_id)
            goal_id: Goal ID in storage (mutually exclusive with goal_file)
            config: Optional configuration dictionary
        """
        if goal_file and goal_id:
            raise ValueError("Cannot specify both goal_file and goal_id")
        
        self.project_dir = project_dir
        self.goal_file = goal_file
        self.goal_id = goal_id
        self.config = config or {}
        self.goal_storage = GoalStorage(os.path.join(project_dir, ".swarmdev", "goals"))
        self.logger = logging.getLogger("swarmdev.builder")
        
        # Create project directory if it doesn't exist
        os.makedirs(project_dir, exist_ok=True)
        
        # Initialize components
        self.llm_provider = None
        self.orchestrator = None
        self.execution_id = None
        
    def build(self) -> str:
        """
        Start the build process.
        
        Returns:
            str: Project ID
        """
        # Load the goal
        goal_text = self._load_goal()
        
        # Generate a project ID
        project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create project metadata
        metadata = {
            "project_id": project_id,
            "goal": goal_text,
            "created_at": datetime.now().isoformat(),
            "status": "initializing",
            "config": self.config
        }
        
        # Save project metadata
        self._update_metadata(metadata)
        
        # Initialize the orchestrator and start the build process
        self._initialize_orchestrator(project_id, goal_text)
        
        return project_id
    
    def _initialize_orchestrator(self, project_id: str, goal_text: str):
        """
        Initialize the orchestrator for the build process.
        
        Args:
            project_id: Project ID
            goal_text: Goal text
        """
        try:
            # Initialize LLM provider
            self._setup_llm_provider()
            
            if not self.llm_provider:
                self.logger.error("No LLM provider available - cannot start build process")
                self._update_project_status("failed", error="No LLM provider available")
                return
            
            # Initialize MCP manager
            self._setup_mcp_manager()
            
            # Create MemoryContextManager instance
            # Ensure self.mcp_manager is initialized by _setup_mcp_manager()
            memory_manager_instance: Optional[MemoryContextManager] = None
            if self.mcp_manager and self.mcp_manager.is_enabled():
                memory_manager_instance = MemoryContextManager(
                    mcp_manager=self.mcp_manager, 
                    project_id=project_id, 
                    logger=self.logger
                )
                self.logger.info(f"MemoryContextManager created for project {project_id}")
            else:
                self.logger.info("MCP Manager not available or disabled, MemoryContextManager not created.")

            # Initialize orchestrator, passing the memory_manager_instance
            self.orchestrator = Orchestrator(
                config=self.config, 
                mcp_manager=self.mcp_manager, 
                memory_manager=memory_manager_instance
            )
            
            # Register specialized agents with LLM provider, MCP manager, and memory_manager_instance
            self._register_agents(memory_manager_instance)
            
            # Register workflow
            self._register_workflow()
            
            # Start orchestrator
            self.orchestrator.start()
            
            # Execute the configured workflow
            workflow_type = self.config.get("workflow", "standard_project")
            context = {
                "project_id": project_id,
                "goal": goal_text,
                "project_dir": self.project_dir,
                "config": self.config,
                "workflow_type": workflow_type,
                "max_iterations": self.config.get("max_iterations", 3)
            }
            
            self.execution_id = self.orchestrator.execute_workflow(workflow_type, context)
            
            # Update project status
            self._update_project_status("in_progress", execution_id=self.execution_id)
            
            self.logger.info(f"Build process started for project {project_id} with execution {self.execution_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize orchestrator: {e}")
            self._update_project_status("failed", error=str(e))
    
    def _setup_llm_provider(self):
        """Set up the LLM provider for the build process."""
        try:
            # Get provider settings from config
            provider_name = self.config.get('llm_provider', 'auto')
            model_name = self.config.get('llm_model')
            
            self.logger.info(f"Setting up LLM provider: {provider_name}, model: {model_name}")
            
            if provider_name == 'auto':
                # Use provider registry to auto-detect available providers
                registry = ProviderRegistry()
                registry.discover_providers()
                self.llm_provider = registry.get_provider()
                
                # If a specific model is configured, update the provider's model
                if model_name and self.llm_provider:
                    self.llm_provider.model = model_name
                    self.logger.info(f"Updated auto-detected provider model to: {model_name}")
            else:
                # Create provider directly with configured model
                from ..utils.llm_provider import OpenAIProvider, AnthropicProvider, GoogleProvider
                import os
                
                if provider_name == 'openai':
                    api_key = os.environ.get('OPENAI_API_KEY')
                    if not api_key:
                        raise ValueError("OPENAI_API_KEY environment variable not set")
                    self.llm_provider = OpenAIProvider(api_key=api_key, model=model_name or 'o4-mini-2025-04-16')
                
                elif provider_name == 'anthropic':
                    api_key = os.environ.get('ANTHROPIC_API_KEY')
                    if not api_key:
                        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
                    self.llm_provider = AnthropicProvider(api_key=api_key, model=model_name or 'claude-3-opus-20240229')
                
                elif provider_name == 'google':
                    api_key = os.environ.get('GOOGLE_API_KEY')
                    if not api_key:
                        raise ValueError("GOOGLE_API_KEY environment variable not set")
                    self.llm_provider = GoogleProvider(api_key=api_key, model=model_name or 'gemini-2.0-flash-001')
                
                else:
                    raise ValueError(f"Unknown provider: {provider_name}")
            
            if self.llm_provider:
                actual_model = getattr(self.llm_provider, 'model', 'unknown')
                self.logger.info(f"LLM provider initialized successfully: {provider_name} with model: {actual_model}")
            else:
                self.logger.warning("No LLM provider available")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM provider: {e}")
            self.llm_provider = None
    
    def _setup_mcp_manager(self):
        """Set up the MCP manager for the build process."""
        try:
            from ..utils.mcp_manager import MCPManager
            
            mcp_config = self.config.get('mcp', {
                'enabled': True,
                'docker_enabled': True,
                'docker_network': None
            })
            
            self.mcp_manager = MCPManager(mcp_config, self.project_dir)
            
            if self.mcp_manager.is_enabled():
                if not self.mcp_manager.initialize_tools():
                    self.logger.warning("MCP manager enabled, but failed to initialize all tools. Some MCP functionalities may be impaired.")
                else:
                    self.logger.info("MCP manager initialized successfully with tools.")
            else:
                self.logger.info("MCP tools are disabled")
                
        except Exception as e:
            self.logger.warning(f"Failed to initialize MCP manager: {e}")
            self.mcp_manager = None
    
    def _register_agents(self, memory_manager: Optional[MemoryContextManager]):
        """Register specialized agents with the orchestrator."""
        try:
            from ..utils.agent_logger import AgentLogger
            AgentLogger.set_project_dir(self.project_dir)
            
            common_agent_args = {
                "llm_provider": self.llm_provider,
                "mcp_manager": self.mcp_manager,
                "config": self.config,
                "memory_manager": memory_manager
            }
            
            research_agent = ResearchAgent("research_agent_1", "research", **common_agent_args)
            planning_agent = PlanningAgent("planning_agent_1", "planning", **common_agent_args)
            development_agent = DevelopmentAgent("development_agent_1", "development", **common_agent_args)
            documentation_agent = DocumentationAgent("documentation_agent_1", "documentation", **common_agent_args)
            analysis_agent = AnalysisAgent("analysis_agent_1", "analysis", **common_agent_args)
            
            self.orchestrator.register_agent(research_agent)
            self.orchestrator.register_agent(planning_agent)
            self.orchestrator.register_agent(development_agent)
            self.orchestrator.register_agent(documentation_agent)
            self.orchestrator.register_agent(analysis_agent)
            
            self.logger.info("All specialized agents registered successfully with memory manager.")
            
        except Exception as e:
            self.logger.error(f"Failed to register agents: {e}")
            raise e
    
    def _register_workflow(self):
        """Register the workflow with the orchestrator."""
        try:
            # Get the configured workflow type
            workflow_type = self.config.get("workflow", "standard_project")
            max_iterations = self.config.get("max_iterations", 3)
            
            # Get enhanced iteration workflow parameters
            workflow_kwargs = {}
            if workflow_type == "iteration":
                workflow_kwargs["target_version"] = self.config.get("target_version")
                workflow_kwargs["completion_strategy"] = self.config.get("completion_strategy", "smart")
                workflow_kwargs["adaptive"] = self.config.get("adaptive", True)
            elif workflow_type == "versioned":
                # Handle deprecated versioned workflow with migration
                self.logger.warning("'versioned' workflow is deprecated. Migrating to enhanced 'iteration' workflow.")
                workflow_type = "iteration"
                workflow_kwargs["target_version"] = self.config.get("target_version", "1.0")
                workflow_kwargs["completion_strategy"] = "version_driven"
                workflow_kwargs["adaptive"] = self.config.get("adaptive", True)
            elif workflow_type == "refactor":
                # Handle deprecated refactor workflow with migration  
                self.logger.warning("'refactor' workflow is deprecated. Migrating to enhanced 'iteration' workflow.")
                workflow_type = "iteration"
                workflow_kwargs["completion_strategy"] = "smart"
                workflow_kwargs["adaptive"] = self.config.get("adaptive", True)
            
            # Get the workflow definition
            workflow = get_workflow_by_id(workflow_type, max_iterations, **workflow_kwargs)
            
            if not workflow:
                raise ValueError(f"Workflow '{workflow_type}' not found")
            
            # Register workflow with orchestrator
            self.orchestrator.register_workflow(workflow_type, workflow)
            
            self.logger.info(f"Workflow '{workflow_type}' registered successfully with params: {workflow_kwargs}")
            
        except Exception as e:
            self.logger.error(f"Failed to register workflow: {e}")
            raise e
    
    def _update_project_status(self, status: str, execution_id: Optional[str] = None, error: Optional[str] = None):
        """Update the project status in metadata."""
        # Use .swarmdev directory for internal metadata, create if needed
        swarmdev_dir = os.path.join(self.project_dir, ".swarmdev")
        os.makedirs(swarmdev_dir, exist_ok=True)
        metadata_file = os.path.join(swarmdev_dir, "project_metadata.json")
        
        # Check for legacy location and migrate if needed
        legacy_metadata = os.path.join(self.project_dir, "project_metadata.json")
        if os.path.exists(legacy_metadata) and not os.path.exists(metadata_file):
            import shutil
            shutil.move(legacy_metadata, metadata_file)
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            metadata["status"] = status
            metadata["updated_at"] = datetime.now().isoformat()
            
            if execution_id:
                metadata["execution_id"] = execution_id
                metadata["started_at"] = datetime.now().isoformat()
            
            if error:
                metadata["error"] = error
                metadata["failed_at"] = datetime.now().isoformat()
            
            if status == "completed":
                metadata["completed_at"] = datetime.now().isoformat()
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to update project status: {e}")
    
    def _update_metadata(self, metadata: Dict):
        """Update the project metadata file."""
        # Use .swarmdev directory for internal metadata
        swarmdev_dir = os.path.join(self.project_dir, ".swarmdev")
        os.makedirs(swarmdev_dir, exist_ok=True)
        metadata_file = os.path.join(swarmdev_dir, "project_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_goal(self) -> str:
        """
        Load the goal from file or storage.
        
        Returns:
            str: Goal text
            
        Raises:
            ValueError: If goal cannot be loaded
        """
        if self.goal_file:
            # Load from file
            if not os.path.exists(self.goal_file):
                raise ValueError(f"Goal file not found: {self.goal_file}")
            
            with open(self.goal_file, 'r') as f:
                goal_text = f.read()
            
            # Store the goal for future reference
            self.goal_id = self.goal_storage.store_goal(goal_text)
            
        elif self.goal_id:
            # Load from storage
            goal_text = self.goal_storage.get_goal(self.goal_id)
            if goal_text is None:
                raise ValueError(f"Goal not found in storage: {self.goal_id}")
        else:
            raise ValueError("Must specify either goal_file or goal_id")
        
        return goal_text
    
    def get_status(self) -> Dict:
        """
        Get the status of the build process.
        
        Returns:
            Dict: Status information including orchestrator execution status
        """
        # Look in .swarmdev first, then fallback to legacy location
        metadata_file = os.path.join(self.project_dir, ".swarmdev", "project_metadata.json")
        if not os.path.exists(metadata_file):
            metadata_file = os.path.join(self.project_dir, "project_metadata.json")
        
        if not os.path.exists(metadata_file):
            return {"status": "not_found"}
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # If we have an execution ID and orchestrator, get execution status
            if self.orchestrator and metadata.get("execution_id"):
                execution_status = self.orchestrator.get_execution_status(metadata["execution_id"])
                
                # Merge execution status into metadata
                metadata["execution_status"] = execution_status
                metadata["tasks"] = execution_status.get("tasks", {})
                
                # Include MCP and LLM metrics in status
                if "mcp_metrics" in execution_status:
                    metadata["mcp_metrics"] = execution_status["mcp_metrics"]
                
                if "llm_metrics" in execution_status:
                    metadata["llm_metrics"] = execution_status["llm_metrics"]
                
                # Update overall status based on execution status
                exec_status = execution_status.get("status")
                if exec_status in ["completed", "failed"]:
                    metadata["status"] = exec_status
                    if exec_status == "completed":
                        metadata["completed_at"] = datetime.now().isoformat()
                    
                    # Update metadata file
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {"status": "error", "error": str(e)}
    
    def cancel(self) -> bool:
        """
        Cancel the build process.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Look in .swarmdev first, then fallback to legacy location
            metadata_file = os.path.join(self.project_dir, ".swarmdev", "project_metadata.json")
            if not os.path.exists(metadata_file):
                metadata_file = os.path.join(self.project_dir, "project_metadata.json")
            
            if not os.path.exists(metadata_file):
                return False
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            if metadata["status"] not in ["initializing", "in_progress"]:
                return False
            
            # Stop the orchestrator if running
            if self.orchestrator:
                self.orchestrator.stop()
            
            # Update status
            metadata["status"] = "cancelled"
            metadata["cancelled_at"] = datetime.now().isoformat()
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info("Build process cancelled by user")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling build process: {e}")
            return False
