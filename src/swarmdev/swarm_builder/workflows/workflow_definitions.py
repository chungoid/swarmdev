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
    Ultimate iteration workflow combining the best patterns from refactor, versioned, and iteration workflows.
    
    Features:
    - Handles new projects AND existing codebases
    - Smart completion planning (no more "coat tails")  
    - Dynamic iteration adjustment (no upfront guessing)
    - Version-aware development with semantic targets
    - Risk assessment and compatibility preservation
    - Comprehensive project analysis with architecture focus
    """
    
    def __init__(self, 
                 initial_iterations: int = 3,
                 target_version: Optional[str] = None,
                 adaptive: bool = True,
                 completion_strategy: str = "smart"):
        """
        Initialize the ultimate iteration workflow.
        
        Args:
            initial_iterations: Starting estimate for iterations (can be adjusted)
            target_version: Optional semantic version target (e.g. "2.0", "1.5")
            adaptive: Whether to dynamically adjust iteration count
            completion_strategy: "smart" (assess readiness), "fixed" (respect initial_iterations), "version_driven"
        """
        description = f"Adaptive iteration workflow handling new/existing projects with smart completion planning"
        if target_version:
            description += f" targeting version {target_version}"
        
        super().__init__(
            workflow_id="iteration",
            name="Ultimate Iteration Workflow",
            description=description
        )
        
        self.initial_iterations = initial_iterations
        self.target_version = target_version
        self.adaptive = adaptive
        self.completion_strategy = completion_strategy
        
        # PHASE 1: COMPREHENSIVE PROJECT DISCOVERY (borrowing from RefactorWorkflow + VersionedWorkflow)
        self.add_initial_task(
            task_id="project_discovery",
            agent_type="analysis", 
            data={
                "workflow_type": "iteration",
                "iteration_count": 0,
                "initial_iterations": initial_iterations,
                "target_version": target_version,
                "adaptive_planning": adaptive,
                "completion_strategy": completion_strategy,
                
                # From RefactorWorkflow: existing project analysis
                "analysis_depth": "comprehensive",
                "focus_on_existing": True,
                "analyze_architecture": True,
                "identify_pain_points": True,
                "detect_project_type": True,
                
                # From VersionedWorkflow: version analysis
                "detect_current_version": target_version is not None,
                "plan_version_roadmap": target_version is not None,
                "assess_version_completion": target_version is not None,
                
                # NEW: Smart completion planning
                "estimate_iteration_needs": True,
                "assess_completion_scope": True,
                "plan_completion_strategy": True
            }
        )
        
        # PHASE 2: INTELLIGENT RESEARCH (borrowing RefactorWorkflow's research phase)
        self.add_dependent_task(
            task_id="strategic_research",
            dependencies=["project_discovery"],
            agent_type="research",
            data={
                # From RefactorWorkflow: comprehensive research
                "research_type": "adaptive_strategy",
                "use_analysis_results": True,
                "focus_on_architecture": True,
                "research_best_practices": True,
                
                # From VersionedWorkflow: version-aware research
                "research_semantic_versioning": target_version is not None,
                "identify_breaking_changes": target_version is not None,
                
                # NEW: Completion-focused research
                "research_completion_patterns": True,
                "identify_technical_debt": True
            }
        )
        
        # PHASE 3: STRATEGIC PLANNING (best of all workflows)
        self.add_dependent_task(
            task_id="strategic_planning",
            dependencies=["strategic_research"],
            agent_type="planning",
            data={
                # From RefactorWorkflow: comprehensive planning
                "planning_type": "strategic_iteration",
                "use_analysis_results": True,
                "use_research_results": True,
                "preserve_functionality": True,
                "plan_incremental_steps": True,
                "risk_assessment": True,
                
                # From VersionedWorkflow: version planning
                "scope_to_current_version": target_version is not None,
                "plan_version_increment": target_version is not None,
                "define_completion_criteria": True,
                "create_version_blueprint": target_version is not None,
                
                # NEW: Adaptive iteration planning
                "plan_iteration_roadmap": True,
                "estimate_effort_distribution": True,
                "plan_completion_sequence": True
            }
        )
        
        # PHASE 4: SMART IMPLEMENTATION (synthesis of all approaches)
        self.add_dependent_task(
            task_id="strategic_implementation",
            dependencies=["strategic_planning"],
            agent_type="development",
            data={
                # From RefactorWorkflow: safe implementation
                "implementation_style": "adaptive",  # Can be "new_project", "refactor", or "incremental"
                "preserve_existing": True,
                "incremental_refactor": True,
                "maintain_compatibility": True,
                "focus_on_improvements": True,
                
                # From VersionedWorkflow: version-aware implementation
                "version_aware": target_version is not None,
                "update_version_files": target_version is not None,
                "maintain_backwards_compatibility": True,
                "focus_on_version_goals": target_version is not None,
                
                # NEW: Completion-aware implementation
                "use_analysis_results": True,
                "use_research_results": True,
                "implementation_prioritization": "completion_focused"
            }
        )
        
        # PHASE 5: COMPLETION-AWARE EVALUATION (solving the "coat tails" problem)
        self.add_dependent_task(
            task_id="completion_evaluation",
            dependencies=["strategic_implementation"],
            agent_type="analysis",
            data={
                # From all workflows: comprehensive evaluation
                "workflow_type": "iteration",
                "analysis_depth": "completion_focused",
                "check_continue": True,
                "initial_iterations": initial_iterations,
                "target_version": target_version,
                "adaptive_planning": adaptive,
                "completion_strategy": completion_strategy,
                
                # From RefactorWorkflow: improvement evaluation
                "evaluate_improvements": True,
                "assess_goal_completion": True,
                
                # From VersionedWorkflow: version evaluation
                "check_version_complete": target_version is not None,
                "check_target_reached": target_version is not None,
                "plan_next_version": target_version is not None,
                "evaluate_stopping_criteria": True,
                
                # NEW: Smart completion logic
                "assess_completion_readiness": True,
                "calculate_remaining_effort": True,
                "determine_completion_mode": True,
                "plan_final_iteration": True
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
        "iteration": IterationWorkflow(
            initial_iterations=max_iterations,
            target_version=kwargs.get("target_version"),
            adaptive=kwargs.get("adaptive", True),
            completion_strategy=kwargs.get("completion_strategy", "smart")
        ),
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
            "name": "Ultimate Iteration Workflow",
            "description": "Adaptive iteration workflow handling new/existing projects with smart completion planning"
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
