"""
Workflow definitions for the SwarmDev platform.
This module provides workflow definitions for different project types.
"""

from typing import Dict, List, Optional, Any


class WorkflowDefinition:
    """
    Definition of a workflow for project development.
    
    This class provides a structured definition of a workflow,
    including tasks, dependencies, and execution rules.
    """
    
    def __init__(self, workflow_id: str, name: str, description: str):
        """
        Initialize a workflow definition.
        
        Args:
            workflow_id: Unique identifier for this workflow
            name: Human-readable name
            description: Description of the workflow
        """
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.initial_tasks = []
        self.dependent_tasks = []
    
    def add_initial_task(self, task_id: str, agent_type: str, agent_id: Optional[str] = None, data: Optional[Dict] = None):
        """
        Add an initial task to the workflow.
        
        Initial tasks have no dependencies and can start immediately.
        
        Args:
            task_id: Unique identifier for this task
            agent_type: Type of agent to execute this task
            agent_id: Specific agent ID (optional)
            data: Task-specific data
        """
        task = {
            "id": task_id,
            "agent_type": agent_type,
            "agent_id": agent_id,
            "data": data or {}
        }
        
        self.initial_tasks.append(task)
    
    def add_dependent_task(self, task_id: str, dependencies: List[str], agent_type: str, agent_id: Optional[str] = None, data: Optional[Dict] = None):
        """
        Add a dependent task to the workflow.
        
        Dependent tasks have dependencies and can only start when those dependencies are satisfied.
        
        Args:
            task_id: Unique identifier for this task
            dependencies: List of task IDs that this task depends on
            agent_type: Type of agent to execute this task
            agent_id: Specific agent ID (optional)
            data: Task-specific data
        """
        task = {
            "id": task_id,
            "dependencies": dependencies,
            "agent_type": agent_type,
            "agent_id": agent_id,
            "data": data or {}
        }
        
        self.dependent_tasks.append(task)
    
    def to_dict(self) -> Dict:
        """
        Convert the workflow definition to a dictionary.
        
        Returns:
            Dict: Dictionary representation of the workflow
        """
        return {
            "id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "initial_tasks": self.initial_tasks,
            "dependent_tasks": self.dependent_tasks
        }


class StandardProjectWorkflow(WorkflowDefinition):
    """
    Standard workflow for project development.
    
    This workflow includes research, planning, development, and documentation phases.
    """
    
    def __init__(self):
        """Initialize the standard project workflow."""
        super().__init__(
            workflow_id="standard_project",
            name="Standard Project Workflow",
            description="Standard workflow for project development with research, planning, development, and documentation phases."
        )
        
        # Add initial tasks
        self.add_initial_task(
            task_id="research",
            agent_type="research",
            data={
                "topic": "project_goal",
                "depth": "medium",
                "focus_areas": ["technologies", "best_practices", "similar_projects"]
            }
        )
        
        # Add dependent tasks
        self.add_dependent_task(
            task_id="planning",
            dependencies=["research"],
            agent_type="planning",
            data={
                "planning_depth": "detailed",
                "include_architecture": True,
                "include_timeline": True
            }
        )
        
        self.add_dependent_task(
            task_id="development",
            dependencies=["planning"],
            agent_type="development",
            data={
                "implementation_style": "modular",
                "include_tests": True,
                "code_quality": "high"
            }
        )
        
        self.add_dependent_task(
            task_id="documentation",
            dependencies=["development"],
            agent_type="documentation",
            data={
                "include_user_guide": True,
                "include_api_docs": True,
                "include_examples": True
            }
        )


class ResearchOnlyWorkflow(WorkflowDefinition):
    """
    Research-only workflow.
    
    This workflow only includes the research phase.
    """
    
    def __init__(self):
        """Initialize the research-only workflow."""
        super().__init__(
            workflow_id="research_only",
            name="Research Only Workflow",
            description="Workflow for conducting research without implementation."
        )
        
        # Add initial tasks
        self.add_initial_task(
            task_id="research",
            agent_type="research",
            data={
                "topic": "project_goal",
                "depth": "deep",
                "focus_areas": ["technologies", "best_practices", "similar_projects", "academic_papers", "industry_trends"]
            }
        )


class DevelopmentOnlyWorkflow(WorkflowDefinition):
    """
    Development-only workflow.
    
    This workflow assumes research and planning are already done and focuses on development.
    """
    
    def __init__(self):
        """Initialize the development-only workflow."""
        super().__init__(
            workflow_id="development_only",
            name="Development Only Workflow",
            description="Workflow for implementing a project with existing research and planning."
        )
        
        # Add initial tasks
        self.add_initial_task(
            task_id="development",
            agent_type="development",
            data={
                "implementation_style": "modular",
                "include_tests": True,
                "code_quality": "high"
            }
        )
        
        # Add dependent tasks
        self.add_dependent_task(
            task_id="documentation",
            dependencies=["development"],
            agent_type="documentation",
            data={
                "include_user_guide": True,
                "include_api_docs": True,
                "include_examples": True
            }
        )


class IndefiniteWorkflow(WorkflowDefinition):
    """
    Indefinite workflow for continuous project improvement.
    
    This workflow continuously analyzes the project state and makes improvements
    until manually stopped by the user.
    """
    
    def __init__(self):
        """Initialize the indefinite workflow."""
        super().__init__(
            workflow_id="indefinite",
            name="Indefinite Improvement Workflow", 
            description="Continuously analyzes and improves the project until manually stopped."
        )
        
        # Add initial task - analyze current project state
        self.add_initial_task(
            task_id="initial_analysis",
            agent_type="analysis",
            data={
                "workflow_type": "indefinite",
                "iteration_count": 0,
                "max_iterations": None,
                "analysis_depth": "comprehensive"
            }
        )
        
        # Add dependent tasks based on analysis
        self.add_dependent_task(
            task_id="improvement_planning",
            dependencies=["initial_analysis"],
            agent_type="planning",
            data={
                "planning_type": "improvement",
                "use_analysis_results": True,
                "focus_on_incremental": True
            }
        )
        
        self.add_dependent_task(
            task_id="improvement_implementation", 
            dependencies=["improvement_planning"],
            agent_type="development",
            data={
                "implementation_style": "incremental",
                "preserve_existing": True,
                "focus_on_improvements": True
            }
        )
        
        self.add_dependent_task(
            task_id="iteration_analysis",
            dependencies=["improvement_implementation"],
            agent_type="analysis",
            data={
                "workflow_type": "indefinite",
                "analysis_depth": "focused",
                "check_continue": True
            }
        )


class IterationWorkflow(WorkflowDefinition):
    """
    Iteration workflow for configurable improvement cycles.
    
    This workflow runs a specified number of improvement iterations,
    analyzing and enhancing the project with each cycle.
    """
    
    def __init__(self, max_iterations: int = 3):
        """
        Initialize the iteration workflow.
        
        Args:
            max_iterations: Maximum number of iterations to run
        """
        super().__init__(
            workflow_id="iteration",
            name="Iteration Improvement Workflow",
            description=f"Runs {max_iterations} cycles of project analysis and improvement."
        )
        
        self.max_iterations = max_iterations
        
        # Add initial task - analyze current project state
        self.add_initial_task(
            task_id="initial_analysis",
            agent_type="analysis",
            data={
                "workflow_type": "iteration", 
                "iteration_count": 0,
                "max_iterations": max_iterations,
                "analysis_depth": "comprehensive"
            }
        )
        
        # Add dependent tasks based on analysis
        self.add_dependent_task(
            task_id="improvement_planning",
            dependencies=["initial_analysis"],
            agent_type="planning",
            data={
                "planning_type": "improvement",
                "use_analysis_results": True,
                "focus_on_incremental": True
            }
        )
        
        self.add_dependent_task(
            task_id="improvement_implementation",
            dependencies=["improvement_planning"], 
            agent_type="development",
            data={
                "implementation_style": "incremental",
                "preserve_existing": True,
                "focus_on_improvements": True
            }
        )
        
        self.add_dependent_task(
            task_id="iteration_analysis",
            dependencies=["improvement_implementation"],
            agent_type="analysis",
            data={
                "workflow_type": "iteration",
                "analysis_depth": "focused",
                "check_continue": True,
                "max_iterations": max_iterations
            }
        )


def get_workflow_by_id(workflow_id: str, max_iterations: int = 3) -> Optional[Dict]:
    """
    Get a workflow definition by ID.
    
    Args:
        workflow_id: Workflow identifier
        max_iterations: Maximum iterations for iteration workflow
        
    Returns:
        Optional[Dict]: Workflow definition or None if not found
    """
    workflows = {
        "standard_project": StandardProjectWorkflow(),
        "research_only": ResearchOnlyWorkflow(),
        "development_only": DevelopmentOnlyWorkflow(),
        "indefinite": IndefiniteWorkflow(),
        "iteration": IterationWorkflow(max_iterations)
    }
    
    if workflow_id in workflows:
        return workflows[workflow_id].to_dict()
    
    return None


def list_available_workflows() -> List[Dict]:
    """
    List all available workflows.
    
    Returns:
        List[Dict]: List of workflow summaries
    """
    workflows = [
        {
            "id": "standard_project",
            "name": "Standard Project Workflow",
            "description": "Standard workflow for project development with research, planning, development, and documentation phases."
        },
        {
            "id": "research_only",
            "name": "Research Only Workflow",
            "description": "Workflow for conducting research without implementation."
        },
        {
            "id": "development_only",
            "name": "Development Only Workflow",
            "description": "Workflow for implementing a project with existing research and planning."
        },
        {
            "id": "indefinite",
            "name": "Indefinite Improvement Workflow",
            "description": "Continuously analyzes and improves the project until manually stopped."
        },
        {
            "id": "iteration",
            "name": "Iteration Improvement Workflow", 
            "description": "Runs a configurable number of improvement cycles on the project."
        }
    ]
    
    return workflows
