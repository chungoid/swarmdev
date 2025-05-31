#!/usr/bin/env python3
"""
Blueprint Manager for SwarmDev

Manages project blueprints that track progress across iteration cycles and 
enable human-in-the-loop feedback for project direction.
"""

import os
import re
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import logging


@dataclass
class BlueprintItem:
    """Individual item within a blueprint phase."""
    id: str
    description: str
    status: str  # 'complete', 'in_progress', 'not_started', 'removed', 'high_priority'
    priority: str  # 'high', 'medium', 'low'
    estimated_effort: str
    files_affected: List[str] = field(default_factory=list)
    notes: str = ""
    completion_date: Optional[str] = None


@dataclass
class BlueprintPhase:
    """Phase containing multiple related blueprint items."""
    id: str
    name: str
    status: str  # 'complete', 'in_progress', 'not_started'
    priority: str
    estimated_effort: str
    items: List[BlueprintItem] = field(default_factory=list)
    description: str = ""


@dataclass
class UserFeedback:
    """User feedback for directing project development."""
    run_number: int
    timestamp: str
    feedback_text: str
    parsed_actions: List[Dict] = field(default_factory=list)


@dataclass
class ProjectBlueprint:
    """Complete project blueprint with phases, items, and feedback."""
    project_name: str
    created_date: str
    last_updated: str
    run_number: int
    project_vision: str
    human_feedback: List[UserFeedback] = field(default_factory=list)
    phases: List[BlueprintPhase] = field(default_factory=list)
    original_goal: str = ""


class BlueprintManager:
    """
    Manages project blueprints for cross-run persistence and human feedback integration.
    """
    
    def __init__(self, project_dir: str = ".", logger: Optional[logging.Logger] = None):
        """
        Initialize the BlueprintManager.
        
        Args:
            project_dir: Project directory path
            logger: Logger instance for debug output
        """
        self.project_dir = project_dir
        self.swarmdev_dir = os.path.join(project_dir, ".swarmdev")
        self.blueprint_file = os.path.join(self.swarmdev_dir, "project_blueprint.md")
        self.feedback_file = os.path.join(self.swarmdev_dir, "user_feedback.txt")
        self.logger = logger or logging.getLogger(__name__)
        
        # Ensure .swarmdev directory exists
        os.makedirs(self.swarmdev_dir, exist_ok=True)
    
    def load_existing_blueprint(self) -> Optional[ProjectBlueprint]:
        """
        Load existing blueprint from disk.
        
        Returns:
            Optional[ProjectBlueprint]: Existing blueprint or None if not found
        """
        self.logger.info("BLUEPRINT: Checking for existing project blueprint")
        
        if not os.path.exists(self.blueprint_file):
            self.logger.info("BLUEPRINT: No existing blueprint found")
            return None
        
        try:
            self.logger.info(f"BLUEPRINT: Loading blueprint from {self.blueprint_file}")
            with open(self.blueprint_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            blueprint = self._parse_blueprint_markdown(content)
            self._log_blueprint_details(blueprint)
            
            return blueprint
            
        except Exception as e:
            self.logger.error(f"BLUEPRINT: Failed to load existing blueprint: {e}")
            return None
    
    def create_initial_blueprint(self, goal: str, project_state: Dict, 
                               project_name: str = None) -> ProjectBlueprint:
        """
        Create initial blueprint from goal and project analysis.
        
        Args:
            goal: Project goal text
            project_state: Current project state analysis
            project_name: Optional project name
            
        Returns:
            ProjectBlueprint: Newly created blueprint
        """
        self.logger.info("BLUEPRINT: Creating initial project blueprint")
        
        # Determine project name
        if not project_name:
            project_name = self._extract_project_name(goal, project_state)
        
        # Create blueprint structure
        blueprint = ProjectBlueprint(
            project_name=project_name,
            created_date=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            run_number=1,
            project_vision=goal,
            original_goal=goal
        )
        
        # Generate phases based on project analysis
        phases = self._generate_initial_phases(goal, project_state)
        blueprint.phases = phases
        
        self.logger.info(f"BLUEPRINT: Created blueprint with {len(phases)} phases")
        self._log_blueprint_creation(blueprint)
        
        # Save blueprint
        self.save_blueprint(blueprint)
        
        return blueprint
    
    def load_user_feedback(self) -> List[UserFeedback]:
        """
        Load user feedback from disk.
        
        Returns:
            List[UserFeedback]: List of user feedback entries
        """
        self.logger.info("FEEDBACK: Loading user feedback")
        
        if not os.path.exists(self.feedback_file):
            self.logger.info("FEEDBACK: No feedback file found")
            return []
        
        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            feedback_list = self._parse_feedback_text(content)
            self.logger.info(f"FEEDBACK: Loaded {len(feedback_list)} feedback entries")
            self._log_feedback_details(feedback_list)
            
            return feedback_list
            
        except Exception as e:
            self.logger.error(f"FEEDBACK: Failed to load feedback: {e}")
            return []
    
    def add_user_feedback(self, feedback_text: str, run_number: int) -> bool:
        """
        Add new user feedback.
        
        Args:
            feedback_text: User feedback content
            run_number: Current run number
            
        Returns:
            bool: True if successful
        """
        self.logger.info(f"FEEDBACK: Adding feedback for run {run_number}")
        
        try:
            # Create feedback entry
            timestamp = datetime.now().isoformat()
            feedback_entry = f"\nRUN {run_number} FEEDBACK ({timestamp[:10]}):\n{feedback_text}\n"
            
            # Append to feedback file
            with open(self.feedback_file, 'a', encoding='utf-8') as f:
                f.write(feedback_entry)
            
            self.logger.info("FEEDBACK: Successfully added user feedback")
            return True
            
        except Exception as e:
            self.logger.error(f"FEEDBACK: Failed to add feedback: {e}")
            return False
    
    def apply_user_feedback(self, blueprint: ProjectBlueprint, 
                          feedback_list: List[UserFeedback]) -> ProjectBlueprint:
        """
        Apply user feedback to blueprint, modifying items based on feedback.
        
        Args:
            blueprint: Current blueprint
            feedback_list: List of user feedback
            
        Returns:
            ProjectBlueprint: Updated blueprint
        """
        self.logger.info("BLUEPRINT: Applying user feedback to blueprint")
        
        # Process feedback in chronological order
        for feedback in sorted(feedback_list, key=lambda x: x.timestamp):
            self.logger.debug(f"FEEDBACK: Processing feedback from run {feedback.run_number}")
            
            # Parse feedback for actionable items
            actions = self._parse_feedback_actions(feedback.feedback_text)
            
            for action in actions:
                self._apply_feedback_action(blueprint, action, feedback.run_number)
        
        # Update blueprint metadata
        blueprint.last_updated = datetime.now().isoformat()
        blueprint.human_feedback = feedback_list
        
        self.logger.info("BLUEPRINT: Successfully applied user feedback")
        return blueprint
    
    def get_incomplete_items(self, blueprint: ProjectBlueprint) -> List[BlueprintItem]:
        """
        Get all incomplete blueprint items.
        
        Args:
            blueprint: Project blueprint
            
        Returns:
            List[BlueprintItem]: Incomplete items
        """
        self.logger.info("BLUEPRINT: Identifying incomplete items")
        
        incomplete_items = []
        for phase in blueprint.phases:
            for item in phase.items:
                if item.status in ['not_started', 'in_progress', 'high_priority']:
                    incomplete_items.append(item)
        
        self.logger.info(f"BLUEPRINT: Found {len(incomplete_items)} incomplete items")
        self.logger.debug(f"BLUEPRINT: Incomplete items: {[item.description[:50] for item in incomplete_items]}")
        
        return incomplete_items
    
    def update_item_status(self, blueprint: ProjectBlueprint, item_description: str, 
                          new_status: str, completion_date: str = None) -> bool:
        """
        Update the status of a specific blueprint item.
        
        Args:
            blueprint: Project blueprint
            item_description: Description of item to update
            new_status: New status value
            completion_date: Optional completion date
            
        Returns:
            bool: True if item was found and updated
        """
        self.logger.info(f"BLUEPRINT_UPDATE: Updating item status: {item_description[:50]}")
        
        for phase in blueprint.phases:
            for item in phase.items:
                if item_description.lower() in item.description.lower():
                    old_status = item.status
                    item.status = new_status
                    if completion_date:
                        item.completion_date = completion_date
                    
                    self.logger.info(f"BLUEPRINT_UPDATE: {item.description[:50]} -> {old_status} to {new_status}")
                    
                    # Update phase status if all items complete
                    self._update_phase_status(phase)
                    return True
        
        self.logger.warning(f"BLUEPRINT_UPDATE: Item not found: {item_description[:50]}")
        return False
    
    def save_blueprint(self, blueprint: ProjectBlueprint) -> bool:
        """
        Save blueprint to disk as markdown.
        
        Args:
            blueprint: Blueprint to save
            
        Returns:
            bool: True if successful
        """
        self.logger.info("BLUEPRINT: Saving blueprint to disk")
        
        try:
            markdown_content = self._generate_blueprint_markdown(blueprint)
            
            with open(self.blueprint_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.logger.info(f"BLUEPRINT: Successfully saved to {self.blueprint_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"BLUEPRINT: Failed to save blueprint: {e}")
            return False
    
    def get_blueprint_status(self, blueprint: ProjectBlueprint) -> Dict:
        """
        Get detailed status summary of blueprint.
        
        Args:
            blueprint: Project blueprint
            
        Returns:
            Dict: Status summary
        """
        total_items = 0
        complete_items = 0
        in_progress_items = 0
        high_priority_items = 0
        removed_items = 0
        
        for phase in blueprint.phases:
            for item in phase.items:
                total_items += 1
                if item.status == 'complete':
                    complete_items += 1
                elif item.status == 'in_progress':
                    in_progress_items += 1
                elif item.status == 'high_priority':
                    high_priority_items += 1
                elif item.status == 'removed':
                    removed_items += 1
        
        completion_percentage = (complete_items / total_items * 100) if total_items > 0 else 0
        
        return {
            'total_items': total_items,
            'complete_items': complete_items,
            'in_progress_items': in_progress_items,
            'high_priority_items': high_priority_items,
            'removed_items': removed_items,
            'completion_percentage': completion_percentage,
            'total_phases': len(blueprint.phases),
            'feedback_entries': len(blueprint.human_feedback)
        }
    
    # Private helper methods
    
    def _parse_blueprint_markdown(self, content: str) -> ProjectBlueprint:
        """Parse blueprint from markdown content."""
        self.logger.debug("BLUEPRINT: Parsing markdown content")
        
        lines = content.split('\n')
        
        # Extract header information
        project_name = ""
        created_date = ""
        last_updated = ""
        run_number = 1
        project_vision = ""
        
        # Parse header
        for line in lines[:10]:
            if line.startswith('# Project Blueprint:'):
                project_name = line.replace('# Project Blueprint:', '').strip()
            elif 'Generated:' in line:
                parts = line.split('|')
                for part in parts:
                    if 'Generated:' in part:
                        created_date = part.replace('Generated:', '').strip()
                    elif 'Last Updated:' in part:
                        last_updated = part.replace('Last Updated:', '').strip()
                    elif 'Run:' in part:
                        try:
                            run_number = int(part.replace('Run:', '').strip())
                        except ValueError:
                            run_number = 1
        
        # Extract project vision
        vision_start = False
        for line in lines:
            if line.strip() == "## Project Vision":
                vision_start = True
                continue
            elif vision_start and line.startswith('##'):
                break
            elif vision_start and line.strip():
                project_vision += line.strip() + " "
        
        # Parse phases
        phases = self._parse_phases_from_markdown(lines)
        
        # Parse feedback
        feedback = self._parse_feedback_from_markdown(lines)
        
        blueprint = ProjectBlueprint(
            project_name=project_name,
            created_date=created_date,
            last_updated=last_updated,
            run_number=run_number,
            project_vision=project_vision.strip(),
            phases=phases,
            human_feedback=feedback
        )
        
        return blueprint
    
    def _parse_phases_from_markdown(self, lines: List[str]) -> List[BlueprintPhase]:
        """Parse phases from markdown lines."""
        phases = []
        current_phase = None
        
        for line in lines:
            # Phase header: ## Phase 1: Foundation [status]
            phase_match = re.match(r'^## Phase \d+: (.+?)\s*(.*?)$', line)
            if phase_match:
                if current_phase:
                    phases.append(current_phase)
                
                phase_name = phase_match.group(1)
                status_part = phase_match.group(2).strip()
                
                # Extract status symbol
                status = 'not_started'
                if 'complete' in status_part or '[check]' in status_part:
                    status = 'complete'
                elif 'progress' in status_part or '[partial]' in status_part:
                    status = 'in_progress'
                
                current_phase = BlueprintPhase(
                    id=f"phase_{len(phases) + 1}",
                    name=phase_name,
                    status=status,
                    priority='medium',
                    estimated_effort='unknown'
                )
                continue
            
            # Phase metadata: **Status**: Complete | **Priority**: High
            if current_phase and line.startswith('**Status**:'):
                parts = line.split('|')
                for part in parts:
                    if '**Status**:' in part:
                        status_text = part.replace('**Status**:', '').strip().lower()
                        if 'complete' in status_text:
                            current_phase.status = 'complete'
                        elif 'progress' in status_text:
                            current_phase.status = 'in_progress'
                    elif '**Priority**:' in part:
                        current_phase.priority = part.replace('**Priority**:', '').strip().lower()
                    elif '**Estimated Effort**:' in part:
                        current_phase.estimated_effort = part.replace('**Estimated Effort**:', '').strip()
                continue
            
            # Phase items: - [X] Item description
            if current_phase and re.match(r'^- \[(.)\] (.+)$', line):
                item_match = re.match(r'^- \[(.)\] (.+)$', line)
                status_char = item_match.group(1)
                description = item_match.group(2)
                
                # Determine status from checkbox
                if status_char.lower() == 'x' or status_char == '[check]':
                    status = 'complete'
                elif status_char == '~':
                    status = 'in_progress'
                elif status_char == '-':
                    status = 'removed'
                elif status_char == '!':
                    status = 'high_priority'
                else:
                    status = 'not_started'
                
                item = BlueprintItem(
                    id=f"{current_phase.id}_item_{len(current_phase.items) + 1}",
                    description=description,
                    status=status,
                    priority='medium',
                    estimated_effort='unknown'
                )
                current_phase.items.append(item)
        
        if current_phase:
            phases.append(current_phase)
        
        return phases
    
    def _parse_feedback_from_markdown(self, lines: List[str]) -> List[UserFeedback]:
        """Parse feedback section from markdown lines."""
        feedback_list = []
        in_feedback_section = False
        
        for line in lines:
            if line.strip() == "## Human Feedback History":
                in_feedback_section = True
                continue
            elif in_feedback_section and line.startswith('##'):
                break
            elif in_feedback_section and line.startswith('- **Run'):
                # Parse: - **Run 2 Feedback**: "Remove CLI component..."
                match = re.match(r'- \*\*Run (\d+) Feedback\*\*: "(.*?)"', line)
                if match:
                    run_num = int(match.group(1))
                    feedback_text = match.group(2)
                    
                    feedback = UserFeedback(
                        run_number=run_num,
                        timestamp=datetime.now().isoformat(),
                        feedback_text=feedback_text
                    )
                    feedback_list.append(feedback)
        
        return feedback_list
    
    def _parse_feedback_text(self, content: str) -> List[UserFeedback]:
        """Parse feedback from text file content."""
        feedback_list = []
        
        # Split by RUN X FEEDBACK patterns
        sections = re.split(r'\nRUN (\d+) FEEDBACK', content)
        
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                run_number = int(sections[i])
                feedback_content = sections[i + 1]
                
                # Extract timestamp from first line
                lines = feedback_content.strip().split('\n')
                timestamp_line = lines[0] if lines else ""
                feedback_text = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                
                # Parse timestamp
                timestamp_match = re.search(r'\(([^)]+)\):', timestamp_line)
                timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().isoformat()
                
                feedback = UserFeedback(
                    run_number=run_number,
                    timestamp=timestamp,
                    feedback_text=feedback_text.strip()
                )
                feedback_list.append(feedback)
        
        return feedback_list
    
    def _parse_feedback_actions(self, feedback_text: str) -> List[Dict]:
        """Parse actionable items from feedback text."""
        actions = []
        text_lower = feedback_text.lower()
        
        # Look for common action patterns
        if 'remove' in text_lower or 'delete' in text_lower:
            # Find what to remove
            remove_matches = re.findall(r'remove\s+(?:the\s+)?([^,.]+)', text_lower)
            for match in remove_matches:
                actions.append({
                    'action': 'remove',
                    'target': match.strip(),
                    'reason': 'user requested removal'
                })
        
        if 'priority' in text_lower or 'important' in text_lower:
            # Find what to prioritize
            priority_matches = re.findall(r'(?:priority|important|focus on)\s+(?:the\s+)?([^,.]+)', text_lower)
            for match in priority_matches:
                actions.append({
                    'action': 'prioritize',
                    'target': match.strip(),
                    'reason': 'user requested high priority'
                })
        
        if 'skip' in text_lower or 'ignore' in text_lower:
            # Find what to skip
            skip_matches = re.findall(r'skip\s+(?:the\s+)?([^,.]+)', text_lower)
            for match in skip_matches:
                actions.append({
                    'action': 'skip',
                    'target': match.strip(),
                    'reason': 'user requested to skip'
                })
        
        return actions
    
    def _apply_feedback_action(self, blueprint: ProjectBlueprint, action: Dict, run_number: int):
        """Apply a specific feedback action to the blueprint."""
        target = action['target']
        action_type = action['action']
        
        self.logger.debug(f"FEEDBACK: Applying {action_type} action for '{target}'")
        
        # Find matching items in blueprint
        for phase in blueprint.phases:
            for item in phase.items:
                if target in item.description.lower():
                    if action_type == 'remove':
                        item.status = 'removed'
                        item.notes += f" [REMOVED per run {run_number} feedback]"
                    elif action_type == 'prioritize':
                        item.status = 'high_priority'
                        item.priority = 'high'
                        item.notes += f" [HIGH PRIORITY per run {run_number} feedback]"
                    elif action_type == 'skip':
                        item.status = 'removed'
                        item.notes += f" [SKIPPED per run {run_number} feedback]"
                    
                    self.logger.debug(f"FEEDBACK: Applied {action_type} to '{item.description[:50]}'")
    
    def _generate_initial_phases(self, goal: str, project_state: Dict) -> List[BlueprintPhase]:
        """Generate initial blueprint phases from goal and project state."""
        self.logger.debug("BLUEPRINT: Generating initial phases")
        
        # Basic phase structure - can be enhanced with LLM in future
        phases = [
            BlueprintPhase(
                id="phase_1",
                name="Foundation",
                status="not_started",
                priority="high",
                estimated_effort="1-2 days",
                description="Basic project setup and structure",
                items=[
                    BlueprintItem(
                        id="foundation_1",
                        description="Project structure setup",
                        status="not_started",
                        priority="high",
                        estimated_effort="2 hours"
                    ),
                    BlueprintItem(
                        id="foundation_2", 
                        description="Dependencies and configuration",
                        status="not_started",
                        priority="high",
                        estimated_effort="1 hour"
                    ),
                    BlueprintItem(
                        id="foundation_3",
                        description="Initial documentation",
                        status="not_started",
                        priority="medium",
                        estimated_effort="1 hour"
                    )
                ]
            ),
            BlueprintPhase(
                id="phase_2",
                name="Core Implementation",
                status="not_started", 
                priority="high",
                estimated_effort="3-5 days",
                description="Main functionality implementation",
                items=[
                    BlueprintItem(
                        id="core_1",
                        description="Core feature implementation",
                        status="not_started",
                        priority="high",
                        estimated_effort="4 hours"
                    ),
                    BlueprintItem(
                        id="core_2",
                        description="Integration and testing",
                        status="not_started",
                        priority="high", 
                        estimated_effort="2 hours"
                    )
                ]
            ),
            BlueprintPhase(
                id="phase_3",
                name="Enhancement",
                status="not_started",
                priority="medium",
                estimated_effort="2-3 days",
                description="Additional features and polish",
                items=[
                    BlueprintItem(
                        id="enhancement_1",
                        description="Advanced features",
                        status="not_started",
                        priority="medium",
                        estimated_effort="3 hours"
                    ),
                    BlueprintItem(
                        id="enhancement_2",
                        description="Performance optimization",
                        status="not_started",
                        priority="low",
                        estimated_effort="2 hours"
                    )
                ]
            )
        ]
        
        return phases
    
    def _extract_project_name(self, goal: str, project_state: Dict) -> str:
        """Extract project name from goal and project state."""
        # Simple extraction - can be enhanced
        words = goal.split()[:5]  # First 5 words
        return ' '.join(words).replace('Create', '').replace('Build', '').strip()
    
    def _update_phase_status(self, phase: BlueprintPhase):
        """Update phase status based on item completion."""
        total_items = len(phase.items)
        if total_items == 0:
            return
        
        complete_items = len([item for item in phase.items if item.status == 'complete'])
        
        if complete_items == total_items:
            phase.status = 'complete'
        elif complete_items > 0:
            phase.status = 'in_progress'
        else:
            phase.status = 'not_started'
    
    def _generate_blueprint_markdown(self, blueprint: ProjectBlueprint) -> str:
        """Generate markdown content from blueprint."""
        content = []
        
        # Header
        content.append(f"# Project Blueprint: {blueprint.project_name}")
        content.append(f"Generated: {blueprint.created_date[:10]} | Last Updated: {blueprint.last_updated[:10]} | Run: {blueprint.run_number}")
        content.append("")
        
        # Project Vision
        content.append("## Project Vision")
        content.append(blueprint.project_vision)
        content.append("")
        
        # Human Feedback History
        if blueprint.human_feedback:
            content.append("## Human Feedback History")
            for feedback in blueprint.human_feedback:
                content.append(f'- **Run {feedback.run_number} Feedback**: "{feedback.feedback_text}"')
            content.append("")
        
        # Phases
        for phase in blueprint.phases:
            # Phase header with status
            status_symbol = {
                'complete': 'complete',
                'in_progress': 'in_progress', 
                'not_started': 'not_started'
            }.get(phase.status, 'not_started')
            
            content.append(f"## {phase.name} {status_symbol}")
            content.append(f"**Status**: {phase.status.title()} | **Priority**: {phase.priority.title()} | **Estimated Effort**: {phase.estimated_effort}")
            
            if phase.description:
                content.append(phase.description)
            
            # Phase items
            for item in phase.items:
                # Status checkbox
                checkbox = {
                    'complete': '[x]',
                    'in_progress': '[~]',
                    'not_started': '[ ]',
                    'removed': '[-]',
                    'high_priority': '[!]'
                }.get(item.status, '[ ]')
                
                item_line = f"- {checkbox} {item.description}"
                if item.notes:
                    item_line += f" ({item.notes})"
                content.append(item_line)
            
            content.append("")
        
        return '\n'.join(content)
    
    # Logging helpers
    
    def _log_blueprint_details(self, blueprint: ProjectBlueprint):
        """Log detailed blueprint information."""
        self.logger.info(f"BLUEPRINT: Loaded '{blueprint.project_name}' blueprint")
        self.logger.debug(f"BLUEPRINT: Created: {blueprint.created_date}")
        self.logger.debug(f"BLUEPRINT: Run #: {blueprint.run_number}")
        self.logger.debug(f"BLUEPRINT: Phases: {len(blueprint.phases)}")
        
        for i, phase in enumerate(blueprint.phases):
            complete_items = len([item for item in phase.items if item.status == 'complete'])
            total_items = len(phase.items)
            self.logger.debug(f"BLUEPRINT: Phase {i+1} ({phase.name}): {complete_items}/{total_items} complete")
    
    def _log_blueprint_creation(self, blueprint: ProjectBlueprint):
        """Log blueprint creation details."""
        self.logger.info(f"BLUEPRINT: Created blueprint for '{blueprint.project_name}'")
        self.logger.debug(f"BLUEPRINT: Total phases: {len(blueprint.phases)}")
        
        total_items = sum(len(phase.items) for phase in blueprint.phases)
        self.logger.debug(f"BLUEPRINT: Total items: {total_items}")
    
    def _log_feedback_details(self, feedback_list: List[UserFeedback]):
        """Log feedback loading details."""
        for feedback in feedback_list:
            self.logger.debug(f"FEEDBACK: Run {feedback.run_number}: {feedback.feedback_text[:50]}...") 