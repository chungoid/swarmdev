"""
Workflow module initialization for the SwarmDev platform.
This module provides workflow definitions for different project types.
"""

from .workflow_definitions import (
    WorkflowDefinition,
    StandardProjectWorkflow,
    ResearchOnlyWorkflow,
    DevelopmentOnlyWorkflow,
    IndefiniteWorkflow,
    IterationWorkflow,
    RefactorWorkflow,
    VersionedWorkflow,
    get_workflow_by_id,
    list_available_workflows
)

__all__ = [
    "WorkflowDefinition",
    "StandardProjectWorkflow",
    "ResearchOnlyWorkflow",
    "DevelopmentOnlyWorkflow",
    "IndefiniteWorkflow",
    "IterationWorkflow",
    "RefactorWorkflow",
    "VersionedWorkflow", 
    "get_workflow_by_id",
    "list_available_workflows"
]
