"""
Goal storage implementation for the SwarmDev platform.
This module provides functionality for storing and retrieving project goals.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, Optional, List


class GoalStorage:
    """
    Storage system for project goals.
    
    This class provides functionality for storing, retrieving, and managing
    project goals, including versioning and backup capabilities.
    """
    
    def __init__(self, base_dir: str = "./goals"):
        """
        Initialize the goal storage system.
        
        Args:
            base_dir: Base directory for goal storage
        """
        self.base_dir = base_dir
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure that the necessary directories exist."""
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "versions"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "backups"), exist_ok=True)
    
    def store_goal(self, goal_text: str, goal_id: Optional[str] = None) -> str:
        """
        Store a goal to a file.
        
        Args:
            goal_text: Goal text content
            goal_id: Optional goal ID (generated if not provided)
            
        Returns:
            str: Goal ID
        """
        # Generate a goal ID if not provided
        if goal_id is None:
            goal_id = f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create the goal file path
        goal_file = os.path.join(self.base_dir, f"{goal_id}.txt")
        
        # Store the goal
        with open(goal_file, 'w') as f:
            f.write(goal_text)
        
        # Create a version
        self._create_version(goal_id, goal_text)
        
        return goal_id
    
    def get_goal(self, goal_id: str) -> Optional[str]:
        """
        Retrieve a goal by ID.
        
        Args:
            goal_id: Goal ID
            
        Returns:
            Optional[str]: Goal text if found, None otherwise
        """
        goal_file = os.path.join(self.base_dir, f"{goal_id}.txt")
        
        if not os.path.exists(goal_file):
            return None
        
        with open(goal_file, 'r') as f:
            return f.read()
    
    def update_goal(self, goal_id: str, goal_text: str) -> bool:
        """
        Update an existing goal.
        
        Args:
            goal_id: Goal ID
            goal_text: New goal text
            
        Returns:
            bool: True if successful, False otherwise
        """
        goal_file = os.path.join(self.base_dir, f"{goal_id}.txt")
        
        if not os.path.exists(goal_file):
            return False
        
        # Create a version before updating
        self._create_version(goal_id, self.get_goal(goal_id))
        
        # Update the goal
        with open(goal_file, 'w') as f:
            f.write(goal_text)
        
        return True
    
    def delete_goal(self, goal_id: str) -> bool:
        """
        Delete a goal.
        
        Args:
            goal_id: Goal ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        goal_file = os.path.join(self.base_dir, f"{goal_id}.txt")
        
        if not os.path.exists(goal_file):
            return False
        
        # Create a backup before deleting
        self._create_backup(goal_id)
        
        # Delete the goal
        os.remove(goal_file)
        
        return True
    
    def list_goals(self) -> List[str]:
        """
        List all available goals.
        
        Returns:
            List[str]: List of goal IDs
        """
        goals = []
        
        for filename in os.listdir(self.base_dir):
            if filename.endswith(".txt") and os.path.isfile(os.path.join(self.base_dir, filename)):
                goals.append(filename[:-4])  # Remove .txt extension
        
        return goals
    
    def _create_version(self, goal_id: str, goal_text: str):
        """
        Create a version of a goal.
        
        Args:
            goal_id: Goal ID
            goal_text: Goal text
        """
        version_dir = os.path.join(self.base_dir, "versions", goal_id)
        os.makedirs(version_dir, exist_ok=True)
        
        version_number = len(os.listdir(version_dir)) + 1
        version_file = os.path.join(version_dir, f"v{version_number}.txt")
        
        with open(version_file, 'w') as f:
            f.write(goal_text)
    
    def _create_backup(self, goal_id: str):
        """
        Create a backup of a goal.
        
        Args:
            goal_id: Goal ID
        """
        goal_file = os.path.join(self.base_dir, f"{goal_id}.txt")
        backup_dir = os.path.join(self.base_dir, "backups")
        backup_file = os.path.join(backup_dir, f"{goal_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        shutil.copy2(goal_file, backup_file)
    
    def get_versions(self, goal_id: str) -> List[str]:
        """
        Get all versions of a goal.
        
        Args:
            goal_id: Goal ID
            
        Returns:
            List[str]: List of version IDs
        """
        version_dir = os.path.join(self.base_dir, "versions", goal_id)
        
        if not os.path.exists(version_dir):
            return []
        
        versions = []
        for filename in os.listdir(version_dir):
            if filename.endswith(".txt") and os.path.isfile(os.path.join(version_dir, filename)):
                versions.append(filename[:-4])  # Remove .txt extension
        
        return sorted(versions)
    
    def get_version(self, goal_id: str, version_id: str) -> Optional[str]:
        """
        Get a specific version of a goal.
        
        Args:
            goal_id: Goal ID
            version_id: Version ID
            
        Returns:
            Optional[str]: Goal text if found, None otherwise
        """
        version_file = os.path.join(self.base_dir, "versions", goal_id, f"{version_id}.txt")
        
        if not os.path.exists(version_file):
            return None
        
        with open(version_file, 'r') as f:
            return f.read()
