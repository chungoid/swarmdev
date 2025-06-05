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
    Enhanced iteration workflow with intelligent completion strategies and parameter-aware agents.
    Handles both new projects and existing codebase improvements with smart stopping criteria.
    """
    
    def __init__(self):
        """Initialize the enhanced iteration workflow."""
        super().__init__(
            workflow_id="iteration",
            name="Enhanced Iteration Workflow",
            description="Advanced iteration workflow with smart completion strategies, parameter-aware agents, and file cleanup capabilities"
        )
        
        # Add enhanced analysis task with cleanup capabilities
        self.add_initial_task(
            task_id="enhanced_analysis",
            agent_type="analysis",
            data={
                "workflow_type": "iteration",
                "analysis_depth": "comprehensive",
                "focus_on_existing": True,
                "analyze_architecture": True,
                "identify_pain_points": True,
                "detect_project_type": True,
                "cleanup_duplicates": True,  # NEW: Enable automatic duplicate cleanup
                "auto_cleanup": False  # Require confirmation for cleanup by default
            }
        )
        
        # Add strategic planning task
        self.add_dependent_task(
            task_id="strategic_planning",
            dependencies=["enhanced_analysis"],
            agent_type="planning",
            data={
                "planning_type": "strategic_iteration",
                "use_analysis_results": True,
                "preserve_functionality": True,
                "plan_incremental_steps": True,
                "risk_assessment": True,
                "include_cleanup_plan": True  # NEW: Include file cleanup in planning
            }
        )
        
        # Add smart implementation task
        self.add_dependent_task(
            task_id="smart_implementation",
            dependencies=["strategic_planning"],
            agent_type="development",
            data={
                "implementation_style": "adaptive",
                "use_planning_results": True,
                "maintain_compatibility": True,
                "optimize_for_maintainability": True,
                "prefer_modification_over_creation": True,  # NEW: Prefer modifying existing files
                "cleanup_obsolete_files": True  # NEW: Clean up files made obsolete by improvements
            }
        )
        
        # Add completion evaluation task
        self.add_dependent_task(
            task_id="completion_evaluation",
            dependencies=["smart_implementation"],
            agent_type="analysis",
            data={
                "evaluate_improvements": True,
                "assess_completion_readiness": True,
                "calculate_remaining_effort": True,
                "determine_completion_mode": True,
                "plan_final_iteration": True,
                "final_cleanup_check": True  # NEW: Final cleanup verification
            }
        )


def get_workflow_by_id(workflow_id: str, max_iterations: int = 3, **kwargs) -> Optional[Dict]:
    """
    Get a workflow definition by ID.
    
    Args:
        workflow_id: Workflow identifier
        max_iterations: Maximum iterations for iteration workflow (now called initial_iterations)
        **kwargs: Additional workflow parameters (e.g., target_version, completion_strategy, adaptive)
        
    Returns:
        Optional[Dict]: Workflow definition or None if not found
    """
    # Handle deprecated workflow types with automatic migration
    if workflow_id == "refactor":
        print("⚠️  WARNING: 'refactor' workflow is deprecated. Using enhanced 'iteration' workflow instead.")
        print("   The iteration workflow now includes all refactor patterns and more.")
        workflow_id = "iteration"
        # Automatically set parameters that make sense for refactor use case
        kwargs.setdefault("completion_strategy", "smart")
        kwargs.setdefault("adaptive", True)
        
    elif workflow_id == "versioned":
        print("⚠️  WARNING: 'versioned' workflow is deprecated. Using enhanced 'iteration' workflow instead.")
        print("   The iteration workflow now includes all versioned patterns and more.")
        workflow_id = "iteration"
        # Automatically set parameters that make sense for versioned use case
        kwargs.setdefault("completion_strategy", "version_driven")
        kwargs.setdefault("adaptive", True)
        if not kwargs.get("target_version"):
            kwargs["target_version"] = "1.0"  # Default target version
    
    workflows = {
        "standard_project": StandardProjectWorkflow(),
        "research_only": ResearchOnlyWorkflow(),
        "development_only": DevelopmentOnlyWorkflow(),
        "indefinite": IndefiniteWorkflow(),
        "iteration": IterationWorkflow(),
        # Legacy workflows removed - they now redirect to enhanced iteration workflow
    }
    
    if workflow_id in workflows:
        return workflows[workflow_id].to_dict()
    
    return None


def list_available_workflows() -> List[Dict]:
    """
    Get a list of all available workflows.
    
    Returns:
        List[Dict]: List of workflow definitions
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
            "name": "Enhanced Iteration Workflow",
            "description": "Advanced iteration workflow with smart completion strategies, parameter-aware agents, and file cleanup capabilities"
        }
        # Deprecated workflows (refactor, versioned) are hidden from main listing but still work for backward compatibility
    ]
    
    return workflows


def list_all_workflows_including_deprecated() -> List[Dict]:
    """
    Get a list of ALL workflows including deprecated ones.
    Used for backward compatibility and --show-deprecated flag.
    
    Returns:
        List[Dict]: List of all workflow definitions including deprecated
    """
    workflows = list_available_workflows()  # Get main workflows
    
    # Add deprecated workflows
    deprecated_workflows = [
        {
            "id": "refactor",
            "name": "Refactor Workflow (DEPRECATED)",
            "description": "DEPRECATED: Use 'iteration' workflow instead. Analyzes existing codebase and refactors it according to specified goal."
        },
        {
            "id": "versioned", 
            "name": "Versioned Workflow (DEPRECATED)",
            "description": "DEPRECATED: Use 'iteration' workflow with --target-version instead. Version-driven development with incremental progression."
        }
    ]
    
    return workflows + deprecated_workflows

# Remove the old workflow classes - they are no longer needed
# RefactorWorkflow and VersionedWorkflow have been merged into the enhanced IterationWorkflow

# === DEPRECATED WORKFLOW CLASSES REMOVED ===
#
# The following workflow classes have been removed and their functionality
# merged into the enhanced IterationWorkflow:
#
# 1. RefactorWorkflow: 
#    - Use: --workflow iteration --completion-strategy smart --adaptive
#    - All refactor patterns are now included in the iteration workflow
#
# 2. VersionedWorkflow:
#    - Use: --workflow iteration --target-version X.Y --completion-strategy version_driven
#    - All versioned patterns are now included in the iteration workflow
#
# Benefits of the unified approach:
# - Single superior workflow instead of three similar ones
# - Cleaner architecture and maintenance
# - Better feature combination (can use refactor + versioned patterns together)
# - Automatic migration for existing users via deprecation warnings
#
# For existing configurations using "refactor" or "versioned", the system will
# automatically migrate to the enhanced iteration workflow with appropriate settings.
