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


class RefactorWorkflow(WorkflowDefinition):
    """
    Refactor workflow for improving existing codebases.
    
    This workflow analyzes an existing project and refactors it according 
    to a specified goal, running multiple improvement cycles as needed.
    """
    
    def __init__(self, max_iterations: int = 3):
        """
        Initialize the refactor workflow.
        
        Args:
            max_iterations: Maximum number of refactor iterations to run
        """
        super().__init__(
            workflow_id="refactor",
            name="Refactor Workflow",
            description=f"Analyzes existing codebase and refactors it according to goal over {max_iterations} iterations."
        )
        
        self.max_iterations = max_iterations
        
        # Start with comprehensive codebase analysis
        self.add_initial_task(
            task_id="codebase_analysis",
            agent_type="analysis",
            data={
                "workflow_type": "refactor",
                "iteration_count": 0,
                "max_iterations": max_iterations,
                "analysis_depth": "comprehensive",
                "focus_on_existing": True,
                "analyze_architecture": True,
                "identify_pain_points": True
            }
        )
        
        # Research refactor approaches and best practices
        self.add_dependent_task(
            task_id="refactor_research",
            dependencies=["codebase_analysis"],
            agent_type="research",
            data={
                "research_type": "refactor_approaches",
                "use_analysis_results": True,
                "focus_on_architecture": True,
                "research_best_practices": True
            }
        )
        
        # Plan the refactor strategy
        self.add_dependent_task(
            task_id="refactor_planning",
            dependencies=["refactor_research"],
            agent_type="planning",
            data={
                "planning_type": "refactor",
                "use_analysis_results": True,
                "use_research_results": True,
                "preserve_functionality": True,
                "plan_incremental_steps": True,
                "risk_assessment": True
            }
        )
        
        # Implement the refactor
        self.add_dependent_task(
            task_id="refactor_implementation",
            dependencies=["refactor_planning"],
            agent_type="development",
            data={
                "implementation_style": "refactor",
                "preserve_existing": True,
                "incremental_refactor": True,
                "maintain_compatibility": True,
                "focus_on_improvements": True
            }
        )
        
        # Analyze refactor results and plan next iteration if needed
        self.add_dependent_task(
            task_id="refactor_evaluation",
            dependencies=["refactor_implementation"],
            agent_type="analysis",
            data={
                "workflow_type": "refactor",
                "analysis_depth": "focused",
                "check_continue": True,
                "max_iterations": max_iterations,
                "evaluate_improvements": True,
                "assess_goal_completion": True
            }
        )


class VersionedWorkflow(WorkflowDefinition):
    """
    Versioned workflow for milestone-driven development.
    
    This workflow works through incremental versions (1.3 → 1.4 → 1.5 → 2.0)
    and stops when the target version is reached, regardless of iteration count.
    Can overshoot max_iterations if target version not reached, or stop early if target reached.
    """
    
    def __init__(self, target_version: str = "1.0", current_version: str = None, max_iterations: int = 10):
        """
        Initialize the versioned workflow.
        
        Args:
            target_version: Target version to reach (e.g., "2.0", "1.5")
            current_version: Current version (auto-detected if None)
            max_iterations: Soft limit on iterations (can be exceeded for version completion)
        """
        super().__init__(
            workflow_id="versioned",
            name="Versioned Workflow",
            description=f"Version-driven development targeting {target_version} with incremental version progression."
        )
        
        self.target_version = target_version
        self.current_version = current_version
        self.max_iterations = max_iterations
        
        # Start with version analysis and planning
        self.add_initial_task(
            task_id="version_analysis",
            agent_type="analysis",
            data={
                "workflow_type": "versioned",
                "target_version": target_version,
                "current_version": current_version,
                "max_iterations": max_iterations,
                "analysis_depth": "version_focused",
                "detect_current_version": current_version is None,
                "plan_version_roadmap": True,
                "assess_version_completion": True
            }
        )
        
        # Research version-specific requirements and best practices
        self.add_dependent_task(
            task_id="version_research",
            dependencies=["version_analysis"],
            agent_type="research",
            data={
                "research_type": "version_requirements",
                "use_analysis_results": True,
                "focus_on_versioning": True,
                "research_semantic_versioning": True,
                "identify_breaking_changes": True
            }
        )
        
        # Plan version-scoped development
        self.add_dependent_task(
            task_id="version_planning",
            dependencies=["version_research"],
            agent_type="planning",
            data={
                "planning_type": "version_scoped",
                "use_analysis_results": True,
                "use_research_results": True,
                "scope_to_current_version": True,
                "plan_version_increment": True,
                "define_completion_criteria": True,
                "create_version_blueprint": True
            }
        )
        
        # Implement version-specific features
        self.add_dependent_task(
            task_id="version_implementation",
            dependencies=["version_planning"],
            agent_type="development",
            data={
                "implementation_style": "version_scoped",
                "preserve_existing": True,
                "version_aware": True,
                "update_version_files": True,
                "maintain_backwards_compatibility": True,
                "focus_on_version_goals": True
            }
        )
        
        # Evaluate version completion and plan next increment
        self.add_dependent_task(
            task_id="version_evaluation",
            dependencies=["version_implementation"],
            agent_type="analysis",
            data={
                "workflow_type": "versioned",
                "analysis_depth": "version_completion",
                "check_version_complete": True,
                "check_target_reached": True,
                "target_version": target_version,
                "max_iterations": max_iterations,
                "plan_next_version": True,
                "evaluate_stopping_criteria": True
            }
        )


def get_workflow_by_id(workflow_id: str, max_iterations: int = 3, **kwargs) -> Optional[Dict]:
    """
    Get a workflow definition by ID.
    
    Args:
        workflow_id: Workflow identifier
        max_iterations: Maximum iterations for iteration workflow
        **kwargs: Additional workflow parameters (e.g., target_version, current_version)
        
    Returns:
        Optional[Dict]: Workflow definition or None if not found
    """
    workflows = {
        "standard_project": StandardProjectWorkflow(),
        "research_only": ResearchOnlyWorkflow(),
        "development_only": DevelopmentOnlyWorkflow(),
        "indefinite": IndefiniteWorkflow(),
        "iteration": IterationWorkflow(max_iterations),
        "refactor": RefactorWorkflow(max_iterations),
        "versioned": VersionedWorkflow(
            target_version=kwargs.get("target_version", "1.0"),
            current_version=kwargs.get("current_version"),
            max_iterations=max_iterations
        )
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
        },
        {
            "id": "refactor",
            "name": "Refactor Workflow",
            "description": "Analyzes existing codebase and refactors it according to specified goal."
        },
        {
            "id": "versioned",
            "name": "Versioned Workflow",
            "description": "Version-driven development with incremental progression and target version completion."
        }
    ]
    
    return workflows
