"""
Specialized agent implementations for the SwarmDev platform.
This module provides specialized agent classes for different tasks.
"""

import os
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json

from swarmdev.utils.llm_provider import LLMProviderInterface
from .base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """
    Research Agent for gathering information and conducting research.
    
    This agent specializes in searching for information, analyzing sources,
    and synthesizing findings to support project development.
    """
    
    def __init__(self, agent_id: str, llm_provider: LLMProviderInterface, config: Optional[Dict] = None):
        """
        Initialize the Research Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider instance
            config: Optional configuration dictionary
        """
        super().__init__(agent_id, "research", config)
        self.llm_provider = llm_provider
        self.search_tools = []  # Would be initialized with actual search tools
    
    def process_task(self, task: Dict) -> Dict:
        """
        Process a research task.
        
        Args:
            task: Task dictionary with details about the research task
            
        Returns:
            Dict: Research findings and results
        """
        self.status = "processing"
        
        try:
            # Extract task details and goal
            goal = task.get("goal", "")
            topic = task.get("topic", goal)  # Use goal if topic not specified
            depth = task.get("depth", "medium")
            focus_areas = task.get("focus_areas", [])
            
            # Conduct research based on the actual goal
            sources = self._conduct_research(goal, topic, depth, focus_areas)
            
            # Analyze sources
            analyzed_sources = self._analyze_sources(sources)
            
            # Synthesize findings
            findings = self._synthesize_findings(analyzed_sources)
            
            # Prepare result
            result = {
                "task_id": task.get("task_id"),
                "status": "completed",
                "findings": findings,
                "sources": [source["url"] for source in sources],
                "summary": self._generate_summary(findings)
            }
            
            self.status = "ready"
            return result
            
        except Exception as e:
            return self.handle_error(e, task)
    
    def _conduct_research(self, goal: str, topic: str, depth: str, focus_areas: List[str]) -> List[Dict]:
        """
        Conduct research on a topic based on a specific goal.
        
        Args:
            goal: The specific project goal to research
            topic: Research topic
            depth: Research depth (shallow, medium, deep)
            focus_areas: Specific areas to focus on
            
        Returns:
            List[Dict]: List of sources with their content
        """
        # Use LLM to conduct research based on the actual goal
        research_prompt = f"""
        Conduct research for the following project goal:
        
        GOAL: {goal}
        
        Focus Areas: {', '.join(focus_areas)}
        Research Depth: {depth}
        
        Based on this goal, identify key technologies, best practices, and approaches needed.
        Provide detailed research findings that would help in implementing this specific project.
        """
        
        research_findings = self.llm_provider.generate_text(research_prompt, temperature=0.3)
        
        # Structure the research as sources
        sources = [
            {
                "url": "research://generated",
                "title": f"Research Analysis for: {goal[:50]}...",
                "content": research_findings,
                "relevance": 1.0
            }
        ]
        
        return sources
    
    def _analyze_sources(self, sources: List[Dict]) -> List[Dict]:
        """
        Analyze research sources.
        
        Args:
            sources: List of sources to analyze
            
        Returns:
            List[Dict]: Analyzed sources with extracted information
        """
        # This is a placeholder implementation
        # In a real implementation, this would use the LLM to analyze sources
        
        analyzed_sources = []
        
        for source in sources:
            # Use LLM to analyze the source
            prompt = f"Analyze the following content and extract key information:\n\n{source['content']}"
            analysis = self.llm_provider.generate_text(prompt, temperature=0.3)
            
            analyzed_source = source.copy()
            analyzed_source["analysis"] = analysis
            analyzed_sources.append(analyzed_source)
        
        return analyzed_sources
    
    def _synthesize_findings(self, analyzed_sources: List[Dict]) -> Dict:
        """
        Synthesize findings from analyzed sources.
        
        Args:
            analyzed_sources: List of analyzed sources
            
        Returns:
            Dict: Synthesized findings
        """
        # This is a placeholder implementation
        # In a real implementation, this would use the LLM to synthesize findings
        
        # Combine all analyses
        combined_analysis = "\n\n".join([source["analysis"] for source in analyzed_sources])
        
        # Use LLM to synthesize findings
        prompt = f"Synthesize the following analyses into a coherent set of findings:\n\n{combined_analysis}"
        synthesis = self.llm_provider.generate_text(prompt, temperature=0.5)
        
        # Structure the findings
        findings = {
            "main_points": synthesis.split("\n"),
            "sources": [source["url"] for source in analyzed_sources],
            "confidence": 0.8
        }
        
        return findings
    
    def _generate_summary(self, findings: Dict) -> str:
        """
        Generate a summary of the findings.
        
        Args:
            findings: Synthesized findings
            
        Returns:
            str: Summary of findings
        """
        # This is a placeholder implementation
        # In a real implementation, this would use the LLM to generate a summary
        
        # Use LLM to generate a summary
        prompt = f"Generate a concise summary of the following findings:\n\n{findings}"
        summary = self.llm_provider.generate_text(prompt, temperature=0.5)
        
        return summary


class PlanningAgent(BaseAgent):
    """
    Planning Agent for creating project blueprints and implementation plans.
    
    This agent specializes in analyzing requirements, designing system architecture,
    and creating detailed implementation plans.
    """
    
    def __init__(self, agent_id: str, llm_provider: LLMProviderInterface, config: Optional[Dict] = None):
        """
        Initialize the Planning Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider instance
            config: Optional configuration dictionary
        """
        super().__init__(agent_id, "planning", config)
        self.llm_provider = llm_provider
    
    def process_task(self, task: Dict) -> Dict:
        """
        Process a planning task.
        
        Args:
            task: Task dictionary with details about the planning task
            
        Returns:
            Dict: Planning results including blueprint and implementation plan
        """
        self.status = "processing"
        
        try:
            # Extract task details and goal
            goal = task.get("goal", "")
            requirements = task.get("requirements", [])
            research_findings = task.get("research_findings", {})
            constraints = task.get("constraints", [])
            
            # Create blueprint based on the actual goal
            blueprint = self._create_blueprint(goal, requirements, research_findings, constraints)
            
            # Define components
            components = self._define_components(blueprint)
            
            # Create implementation plan
            implementation_plan = self._create_implementation_plan(components)
            
            # Prepare result
            result = {
                "task_id": task.get("task_id"),
                "status": "completed",
                "blueprint": blueprint,
                "components": components,
                "implementation_plan": implementation_plan
            }
            
            self.status = "ready"
            return result
            
        except Exception as e:
            return self.handle_error(e, task)
    
    def _create_blueprint(self, goal: str, requirements: List[str], research_findings: Dict, constraints: List[str]) -> Dict:
        """
        Create a project blueprint based on goal, requirements and research findings.
        
        Args:
            goal: The specific project goal
            requirements: List of project requirements
            research_findings: Research findings
            constraints: List of constraints
            
        Returns:
            Dict: Project blueprint
        """
        # Use LLM to create detailed blueprint for the specific goal
        blueprint_prompt = f"""
        Create a detailed project blueprint for the following goal:
        
        GOAL: {goal}
        
        Requirements: {requirements}
        Research Findings: {research_findings}
        Constraints: {constraints}
        
        Provide a comprehensive blueprint including:
        1. Project overview and objectives
        2. System architecture and components
        3. Key features to implement
        4. Technology stack recommendations
        5. Development approach
        
        Focus on the specific requirements mentioned in the goal.
        """
        
        blueprint_text = self.llm_provider.generate_text(blueprint_prompt, temperature=0.3)
        
        # Extract structured information using LLM
        extraction_prompt = f"""
        From the following blueprint, extract structured information:
        
        {blueprint_text}
        
        Extract:
        - Overview (1-2 sentences)
        - Architecture (brief description)
        - Key Features (list of 4-6 specific features)
        - Technologies (list of 3-5 technologies)
        
        Format as a clear, structured response.
        """
        
        structured_text = self.llm_provider.generate_text(extraction_prompt, temperature=0.2)
        
        # Parse the structured response (simplified parsing)
        lines = structured_text.split('\n')
        overview = ""
        architecture = ""
        key_features = []
        technologies = []
        
        current_section = ""
        for line in lines:
            line = line.strip()
            if 'overview' in line.lower():
                current_section = "overview"
            elif 'architecture' in line.lower():
                current_section = "architecture"  
            elif 'features' in line.lower():
                current_section = "features"
            elif 'technologies' in line.lower():
                current_section = "technologies"
            elif line.startswith('-') or line.startswith('•'):
                item = line.lstrip('-•').strip()
                if current_section == "features":
                    key_features.append(item)
                elif current_section == "technologies":
                    technologies.append(item)
            elif line and not line.startswith('#'):
                if current_section == "overview":
                    overview += line + " "
                elif current_section == "architecture":
                    architecture += line + " "
        
        blueprint = {
            "overview": overview.strip() or "Project blueprint for task management application",
            "architecture": architecture.strip() or "Frontend web application architecture", 
            "key_features": key_features or ["Task creation and editing", "Task categorization", "Due date tracking", "Task filtering"],
            "technologies": technologies or ["HTML5", "CSS3", "JavaScript", "LocalStorage"],
            "constraints": constraints,
            "full_description": blueprint_text
        }
        
        return blueprint
    
    def _define_components(self, blueprint: Dict) -> List[Dict]:
        """
        Define system components based on the blueprint.
        
        Args:
            blueprint: Project blueprint
            
        Returns:
            List[Dict]: List of component definitions
        """
        # This is a placeholder implementation
        # In a real implementation, this would use the LLM to define components
        
        # Use LLM to define components
        prompt = f"Define the components needed for the following blueprint:\n\n{blueprint}"
        components_text = self.llm_provider.generate_text(prompt, temperature=0.5)
        
        # Structure the components
        components = [
            {
                "id": "component_1",
                "name": "Component 1",
                "description": "Description of Component 1",
                "dependencies": []
            },
            {
                "id": "component_2",
                "name": "Component 2",
                "description": "Description of Component 2",
                "dependencies": ["component_1"]
            },
            {
                "id": "component_3",
                "name": "Component 3",
                "description": "Description of Component 3",
                "dependencies": ["component_1", "component_2"]
            }
        ]
        
        return components
    
    def _create_implementation_plan(self, components: List[Dict]) -> Dict:
        """
        Create an implementation plan based on components.
        
        Args:
            components: List of component definitions
            
        Returns:
            Dict: Implementation plan
        """
        # This is a placeholder implementation
        # In a real implementation, this would use the LLM to create an implementation plan
        
        # Use LLM to create implementation plan
        prompt = f"Create an implementation plan for the following components:\n\n{components}"
        plan_text = self.llm_provider.generate_text(prompt, temperature=0.5)
        
        # Structure the implementation plan
        implementation_plan = {
            "phases": [
                {
                    "id": "phase_1",
                    "name": "Phase 1",
                    "description": "Description of Phase 1",
                    "components": ["component_1"],
                    "estimated_duration": "2 days"
                },
                {
                    "id": "phase_2",
                    "name": "Phase 2",
                    "description": "Description of Phase 2",
                    "components": ["component_2"],
                    "estimated_duration": "3 days"
                },
                {
                    "id": "phase_3",
                    "name": "Phase 3",
                    "description": "Description of Phase 3",
                    "components": ["component_3"],
                    "estimated_duration": "4 days"
                }
            ],
            "total_estimated_duration": "9 days",
            "dependencies": [
                {"from": "phase_1", "to": "phase_2"},
                {"from": "phase_2", "to": "phase_3"}
            ]
        }
        
        return implementation_plan


class DevelopmentAgent(BaseAgent):
    """
    Development Agent for implementing project components.
    
    This agent specializes in writing code, testing implementations,
    and integrating components using MCP tools.
    """
    
    def __init__(self, agent_id: str, llm_provider: LLMProviderInterface, config: Optional[Dict] = None):
        """
        Initialize the Development Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider instance
            config: Optional configuration dictionary
        """
        super().__init__(agent_id, "development", config)
        self.llm_provider = llm_provider
        
        # Initialize logger
        self.logger = logging.getLogger(f"swarmdev.agents.{agent_id}")
    
    def process_task(self, task: Dict) -> Dict:
        """
        Process a development task.
        
        Args:
            task: Task dictionary with details about the development task
            
        Returns:
            Dict: Development results including code and tests
        """
        self.status = "processing"
        
        # DEBUG: Add basic logging to track execution
        print(f"[DEBUG] DevelopmentAgent.process_task called with task: {task.get('task_id', 'unknown')}")
        self.logger.info(f"DevelopmentAgent processing task: {task.get('task_id', 'unknown')}")
        
        try:
            # Extract task details and goal
            goal = task.get("goal", "")
            project_dir = task.get("project_dir", ".")
            
            print(f"[DEBUG] Development task details: goal='{goal[:50]}...', project_dir='{project_dir}'")
            
            # Check if this is an incremental improvement task
            implementation_style = task.get("implementation_style", "")
            focus_on_improvements = task.get("focus_on_improvements", False)
            
            # Set incremental task flag if needed
            self._is_incremental_task = (implementation_style == "incremental" or focus_on_improvements)
            
            print(f"[DEBUG] Incremental task: {self._is_incremental_task}")
            
            # Get improvement suggestions from various sources
            self._improvement_suggestions = self._get_improvement_suggestions(task)
            
            print(f"[DEBUG] Found {len(self._improvement_suggestions)} improvement suggestions")
            self.logger.info(f"Development task: incremental={self._is_incremental_task}, "
                           f"improvements={len(self._improvement_suggestions)}")
            
            # Create implementation directly using MCP tools
            implementation = self._create_implementation_with_tools(goal, project_dir)
            
            print(f"[DEBUG] Implementation completed")
            
            # Prepare result
            result = {
                "task_id": task.get("task_id"),
                "status": "completed",
                "implementation": implementation,
                "files_created": implementation.get("files_created", []),
                "files_modified": implementation.get("files_modified", []),
                "improvement_type": implementation.get("improvement_type", "new_project"),
                "improvements_implemented": len(self._improvement_suggestions)
            }
            
            # Save iteration progress for future reference
            iteration_count = task.get("iteration_count", 0)
            if hasattr(self, '_improvement_suggestions'):
                self._save_iteration_progress(
                    iteration_count,
                    implementation.get("files_created", []),
                    implementation.get("files_modified", []),
                    self._improvement_suggestions
                )
            
            print(f"[DEBUG] DevelopmentAgent task completed successfully")
            self.status = "ready"
            return result
            
        except Exception as e:
            print(f"[DEBUG] DevelopmentAgent error: {e}")
            return self.handle_error(e, task)
    
    def _get_improvement_suggestions(self, task: Dict) -> List[Dict]:
        """
        Get improvement suggestions from multiple sources.
        
        Args:
            task: Current task information
            
        Returns:
            List[Dict]: List of improvement suggestions
        """
        improvements = []
        
        # 1. Direct improvement suggestions in task context
        context = task.get("context", {})
        if "improvement_suggestions" in context:
            improvements.extend(context["improvement_suggestions"])
            self.logger.info(f"Found {len(context['improvement_suggestions'])} improvements in task context")
        
        # 2. Look for recent analysis results in the same execution
        execution_id = task.get("execution_id", "")
        if execution_id and hasattr(self, 'orchestrator'):
            recent_improvements = self._get_recent_analysis_results(execution_id)
            improvements.extend(recent_improvements)
            self.logger.info(f"Found {len(recent_improvements)} improvements from recent analysis")
        
        # 3. Check if improvements are stored in a shared location
        try:
            import os
            agent_work_dir = os.path.join(".", "agent_work")
            if os.path.exists(agent_work_dir):
                improvements_from_files = self._load_improvements_from_artifacts(agent_work_dir)
                improvements.extend(improvements_from_files)
                self.logger.info(f"Found {len(improvements_from_files)} improvements from artifacts")
        except Exception as e:
            self.logger.error(f"Failed to load improvements from artifacts: {e}")
        
        # Remove duplicates and return
        unique_improvements = []
        seen_descriptions = set()
        
        for imp in improvements:
            desc = imp.get("what", imp.get("description", ""))
            if desc and desc not in seen_descriptions:
                unique_improvements.append(imp)
                seen_descriptions.add(desc)
        
        self.logger.info(f"Total unique improvements found: {len(unique_improvements)}")
        return unique_improvements
    
    def _load_improvements_from_artifacts(self, agent_work_dir: str) -> List[Dict]:
        """Load improvement suggestions from analysis artifacts."""
        improvements = []
        
        try:
            import os
            import json
            import re
            
            # Look for recent analysis files
            analysis_files = [f for f in os.listdir(agent_work_dir) 
                            if f.startswith("analysis_iteration_") and f.endswith(".md")]
            
            # Sort by modification time, get most recent
            if analysis_files:
                analysis_files.sort(key=lambda f: os.path.getmtime(os.path.join(agent_work_dir, f)), reverse=True)
                latest_analysis = os.path.join(agent_work_dir, analysis_files[0])
                
                with open(latest_analysis, 'r') as f:
                    content = f.read()
                
                # Try to extract improvements from the analysis
                # Look for JSON-like structures or numbered lists
                json_matches = re.findall(r'\[.*?\]', content, re.DOTALL)
                for match in json_matches:
                    try:
                        parsed = json.loads(match)
                        if isinstance(parsed, list):
                            for item in parsed:
                                if isinstance(item, dict) and "what" in item:
                                    improvements.append(item)
                    except:
                        continue
                
                # If no JSON found, parse text-based improvements
                if not improvements:
                    improvements = self._parse_text_improvements(content)
                
        except Exception as e:
            self.logger.error(f"Failed to parse improvements from artifacts: {e}")
        
        return improvements
    
    def _parse_text_improvements(self, text: str) -> List[Dict]:
        """Parse improvements from text-based analysis."""
        improvements = []
        lines = text.split('\n')
        
        current_improvement = {}
        for line in lines:
            line = line.strip()
            
            # Look for numbered or bulleted improvements
            if re.match(r'^[1-9]\.\s', line) or line.startswith('*') or line.startswith('-'):
                if current_improvement and "what" in current_improvement:
                    improvements.append(current_improvement)
                
                current_improvement = {
                    "what": re.sub(r'^[1-9*-]\.\s*', '', line),
                    "priority": "medium",
                    "effort": "medium",
                    "impact": "medium"
                }
            
            # Extract additional details
            elif current_improvement:
                if "priority" in line.lower():
                    if "high" in line.lower():
                        current_improvement["priority"] = "high"
                    elif "critical" in line.lower():
                        current_improvement["priority"] = "critical"
                    elif "low" in line.lower():
                        current_improvement["priority"] = "low"
                
                elif "why:" in line.lower():
                    current_improvement["why"] = line.split(":", 1)[1].strip()
                
                elif "how:" in line.lower():
                    current_improvement["how"] = line.split(":", 1)[1].strip()
        
        if current_improvement and "what" in current_improvement:
            improvements.append(current_improvement)
        
        return improvements
    
    def _get_recent_analysis_results(self, execution_id: str) -> List[Dict]:
        """
        Get improvement suggestions from recent analysis tasks in the same execution.
        
        Args:
            execution_id: Current execution ID
            
        Returns:
            List[Dict]: List of improvement suggestions
        """
        # This would ideally access the orchestrator's task results
        # For now, return empty list as fallback
        # In a real implementation, this would query recent analysis results
        return []
    
    def _create_implementation_with_tools(self, goal: str, project_dir: str) -> Dict:
        """
        Create implementation files using LLM to determine everything.
        
        Args:
            goal: The specific project goal
            project_dir: Project directory path
            
        Returns:
            Dict: Implementation details
        """
        files_created = []
        files_modified = []
        
        try:
            # Check if this is an incremental improvement task
            if hasattr(self, '_is_incremental_task') and self._is_incremental_task:
                return self._create_incremental_improvements(goal, project_dir)
            
            # Original implementation for new projects
            prompt = f"""
            Create a complete, production-ready project for this goal:
            
            {goal}
            
            Return your response with each file in this format:
            
            === FILENAME: path/filename.ext ===
            [complete file content]
            === END FILE ===
            
            Create all necessary files with proper structure and complete functional code.
            """
            
            response = self.llm_provider.generate_text(prompt, temperature=0.1)
            
            # Simple parsing
            current_content = []
            current_file = None
            
            for line in response.split('\n'):
                if line.startswith('=== FILENAME:') and line.endswith('==='):
                    # Save previous file
                    if current_file and current_content:
                        full_path = os.path.join(project_dir, current_file)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, 'w') as f:
                            f.write('\n'.join(current_content))
                        files_created.append(os.path.basename(current_file))
                    
                    # Start new file
                    current_file = line.replace('=== FILENAME:', '').replace('===', '').strip()
                    current_content = []
                    
                elif line.strip() == '=== END FILE ===':
                    continue
                    
                elif current_file:
                    current_content.append(line)
            
            # Save last file
            if current_file and current_content:
                full_path = os.path.join(project_dir, current_file)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write('\n'.join(current_content))
                files_created.append(os.path.basename(current_file))
            
        except Exception as e:
            self.logger.error(f"Error creating files: {e}")
        
        return {
            "files_created": files_created,
            "files_modified": files_modified,
            "total_files": len(files_created) + len(files_modified)
        }
    
    def _create_incremental_improvements(self, goal: str, project_dir: str) -> Dict:
        """
        Create incremental improvements to existing project files.
        
        Args:
            goal: The specific project goal
            project_dir: Project directory path
            
        Returns:
            Dict: Implementation details for improvements
        """
        files_created = []
        files_modified = []
        
        try:
            self.logger.info("Starting incremental improvements implementation")
            
            # Get previous iteration progress to understand what's been built
            previous_progress = self._get_previous_iteration_progress()
            previously_created_files = previous_progress.get("all_files_created", [])
            previously_modified_files = previous_progress.get("all_files_modified", [])
            
            self.logger.info(f"Previous iterations created {len(previously_created_files)} files, modified {len(previously_modified_files)}")
            
            # Read existing project files with better analysis
            existing_files = self._read_project_files(project_dir)
            self.logger.info(f"Read {len(existing_files)} existing files for analysis")
            
            # Get improvement suggestions from task context
            improvement_suggestions = getattr(self, '_improvement_suggestions', [])
            self.logger.info(f"Found {len(improvement_suggestions)} improvement suggestions")
            
            # Save development work plan for visibility
            work_plan = self._create_work_plan(goal, improvement_suggestions, existing_files, previous_progress)
            self._save_development_artifact(work_plan, "work_plan")
            
            if improvement_suggestions:
                # Implement specific improvements with detailed analysis
                implementation_result = self._implement_specific_improvements(
                    goal, improvement_suggestions, existing_files, project_dir
                )
            else:
                # Fallback: comprehensive analysis and improvement
                implementation_result = self._implement_comprehensive_improvements(
                    goal, existing_files, project_dir
                )
            
            files_created = implementation_result.get("files_created", [])
            files_modified = implementation_result.get("files_modified", [])
            
            # Save implementation summary
            summary = self._create_implementation_summary(implementation_result, improvement_suggestions)
            self._save_development_artifact(summary, "implementation_summary")
            
            self.logger.info(f"Completed improvements: {len(files_created)} created, {len(files_modified)} modified")
            
        except Exception as e:
            self.logger.error(f"Error creating incremental improvements: {e}")
        
        return {
            "files_created": files_created,
            "files_modified": files_modified,
            "total_files": len(files_created) + len(files_modified),
            "improvement_type": "incremental"
        }
    
    def _read_project_files(self, project_dir: str) -> Dict:
        """Read project files with better organization and analysis."""
        existing_files = {}
        
        for root, dirs, files in os.walk(project_dir):
            # Skip hidden and cache directories, agent work, and goals
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                      ['__pycache__', 'node_modules', 'target', 'build', 'dist', 'agent_work', 'goals']]
            
            for file in files:
                if file.startswith('.') or file.endswith(('.pyc', '.log')):
                    continue
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        existing_files[relative_path] = {
                            "content": content,
                            "size": len(content),
                            "lines": len(content.split('\n')),
                            "extension": os.path.splitext(file)[1]
                        }
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        return existing_files
    
    def _create_work_plan(self, goal: str, improvements: List[Dict], existing_files: Dict, previous_progress: Dict) -> str:
        """Create a detailed work plan showing what will be implemented."""
        plan = f"""# Development Agent Work Plan

**Goal:** {goal}
**Timestamp:** {datetime.now().isoformat()}
**Agent:** {self.agent_id}

## Current Project State
- **Files:** {len(existing_files)} files
- **Total Lines:** {sum(f.get('lines', 0) for f in existing_files.values())}
- **File Types:** {set(f.get('extension', '') for f in existing_files.values())}

## Previous Iteration History
- **Total Previous Iterations:** {len(previous_progress.get('iterations', []))}
- **Files Created Across All Iterations:** {len(previous_progress.get('all_files_created', []))}
- **Files Modified Across All Iterations:** {len(previous_progress.get('all_files_modified', []))}

### Previously Created Files:
"""
        
        for file in previous_progress.get('all_files_created', []):
            plan += f"- {file}\n"
        
        plan += "\n### Previously Modified Files:\n"
        for file in previous_progress.get('all_files_modified', []):
            plan += f"- {file}\n"
        
        plan += "\n## Existing Files Analysis\n"
        for file_path, file_info in list(existing_files.items())[:10]:
            plan += f"- **{file_path}**: {file_info.get('lines', 0)} lines\n"
        
        plan += "\n## Improvement Suggestions to Implement\n"
        
        if improvements:
            for i, imp in enumerate(improvements, 1):
                plan += f"""
### {i}. {imp.get('what', 'Unknown improvement')}
- **Priority:** {imp.get('priority', 'medium')}
- **Impact:** {imp.get('impact', 'medium')}
- **Effort:** {imp.get('effort', 'medium')}
- **Why:** {imp.get('why', 'No reason specified')}
- **How:** {imp.get('how', 'No implementation details')}
- **Files Affected:** {', '.join(imp.get('files_affected', ['unknown']))}
"""
        else:
            plan += "No specific improvement suggestions found. Will perform comprehensive analysis.\n"
        
        plan += "\n## Implementation Strategy\n"
        plan += "1. CHECK existing files to avoid overwriting\n"
        plan += "2. EXTEND existing files where possible instead of recreating\n"
        plan += "3. Create new files only for genuinely new capabilities\n"
        plan += "4. Preserve existing functionality\n"
        plan += "5. Build upon previous iterations' work\n"
        plan += "6. Focus on substantial new functionality\n"
        
        return plan
    
    def _implement_specific_improvements(self, goal: str, improvements: List[Dict], 
                                       existing_files: Dict, project_dir: str) -> Dict:
        """Implement specific improvements suggested by analysis."""
        self.logger.info(f"Implementing {len(improvements)} specific improvements")
        
        # Detect target technology for proper implementation
        target_technology = self._detect_target_technology()
        file_extension = self._get_file_extension_for_technology(target_technology)
        
        self.logger.info(f"Implementing for {target_technology} with {file_extension} files")
        
        # Create detailed implementation prompt
        improvements_text = '\n'.join([
            f"**{i+1}. {imp.get('what', 'Unknown')}**\n"
            f"- Why: {imp.get('why', 'No reason')}\n"
            f"- How: {imp.get('how', 'No details')}\n"
            f"- Priority: {imp.get('priority', 'medium')}\n"
            f"- Files: {', '.join(imp.get('files_affected', ['unknown']))}\n"
            for i, imp in enumerate(improvements)
        ])
        
        prompt = f"""
        BUILD NEW {target_technology.upper()} CAPABILITIES BASED ON CREATIVE EXPANSIONS:
        
        TARGET TECHNOLOGY: {target_technology}
        FILE EXTENSION: {file_extension}
        
        GOAL: {goal}
        
        CREATIVE EXPANSIONS TO BUILD INTO NEW FEATURES:
        {improvements_text}
        
        EXISTING PROJECT FILES TO BUILD UPON:
        {self._format_files_for_implementation(existing_files)}
        
        Your task is to BUILD these creative expansions into substantial new {target_technology} capabilities:
        
        CRITICAL REQUIREMENT: DO NOT recreate or overwrite existing files. BUILD UPON what exists.
        
        TECHNOLOGY-SPECIFIC REQUIREMENTS FOR {target_technology.upper()}:
        {self._get_technology_specific_requirements(target_technology)}
        
        BUILDING REQUIREMENTS:
        - Create 3-5 entirely new {target_technology} files with {file_extension} extension
        - Build substantial, functional {target_technology} code (not stubs or placeholders)
        - Follow {target_technology} best practices and conventions
        - Implement complete, working features using {target_technology} syntax
        - Create supporting files and configurations appropriate for {target_technology}
        - EXTEND existing files where appropriate instead of recreating them
        
        FORBIDDEN ACTIONS:
        - Creating files with wrong extensions (avoid .py if not Python)
        - Using syntax from other languages in {target_technology} files
        - Making small modifications to existing files
        - Creating incomplete stub functions
        - Generic technical improvements (error handling, logging, documentation)
        - Refactoring existing code without adding new functionality
        
        INTELLIGENT FILE HANDLING:
        1. If a file already exists, EXTEND it with new functionality using ACTION: MODIFY
        2. Only use ACTION: CREATE for genuinely new {target_technology} files
        3. Check existing files and build complementary features
        4. Create new directories/modules for major new capability areas
        5. Use {file_extension} extension for new {target_technology} files
        
        SUBSTANTIAL BUILDING FOCUS:
        1. Focus on the CREATIVE EXPANSIONS listed above, not technical improvements
        2. Build entirely NEW {target_technology} capabilities that users can interact with
        3. Create complete workflows and user experiences in {target_technology}
        4. Add substantial new functionality that expands project scope
        5. Implement features that transform what the project can do
        6. Build reusable {target_technology} components that enable future expansion
        
        For each new capability you build, return:
        
        === ACTION: CREATE ===  (only for new files)
        === FILENAME: path/filename{file_extension} ===
        === IMPROVEMENT: Description of new capability/expansion implemented ===
        [{target_technology} code with complete new functionality]
        === END FILE ===
        
        OR for extending existing files:
        
        === ACTION: MODIFY ===  (for existing files)
        === FILENAME: path/existing_filename{file_extension} ===
        === IMPROVEMENT: Description of new functionality added to existing file ===
        [{target_technology} code to add to the existing file]
        === END FILE ===
        
        BUILD SUBSTANTIAL NEW {target_technology.upper()} FEATURES that implement the creative expansions!
        """
        
        response = self.llm_provider.generate_text(prompt, temperature=0.2)
        
        # Save the LLM response for debugging
        self._save_development_artifact(response, "llm_implementation_response")
        
        return self._parse_implementation_response(response, project_dir)
    
    def _implement_comprehensive_improvements(self, goal: str, existing_files: Dict, project_dir: str) -> Dict:
        """Implement comprehensive improvements when no specific suggestions are available."""
        self.logger.info("Implementing comprehensive improvements")
        
        prompt = f"""
        SUBSTANTIAL FEATURE BUILDING TASK:
        
        GOAL: {goal}
        
        EXISTING PROJECT FILES:
        {self._format_files_for_implementation(existing_files)}
        
        Your role is to BUILD substantial new features that expand the project's capabilities.
        
        BUILDING REQUIREMENTS:
        - Create 500+ lines of new, working code this iteration
        - Build 3-5 entirely new modules/packages/components
        - Implement complete, functional features (not stubs or placeholders)
        - Create supporting infrastructure (configs, examples, utilities)
        - Focus on additive development that expands project scope
        
        FORBIDDEN ACTIONS:
        - Making small modifications to existing files
        - Creating incomplete stub functions
        - Generic improvements to existing code (error handling, logging, documentation)
        - Refactoring existing functionality
        - Adding just comments or documentation
        
        SUBSTANTIAL CREATION FOCUS:
        - Build complete, working systems that users can immediately benefit from
        - Create new directories/modules for major new capabilities
        - Implement full user workflows from start to finish
        - Add comprehensive functionality, not minimal examples
        - Build features that significantly expand what the project can do
        
        ARCHITECTURE THINKING:
        - Design new modules with clear interfaces and responsibilities
        - Create extensible systems that can grow over time
        - Build reusable components that other features can leverage
        - Implement proper separation of concerns for new capabilities
        - Focus on creating value-adding functionality
        
        BUILD NEW MAJOR CAPABILITIES:
        - Create entirely new functional modules
        - Add substantial user-facing features
        - Implement comprehensive workflows
        - Build supporting utilities and helpers
        - Create examples and usage scenarios
        
        For each file you create (focus on CREATE, not MODIFY), return:
        
        === ACTION: CREATE ===
        === FILENAME: path/filename.ext ===
        === IMPROVEMENT: Description of major new capability built ===
        [complete file content with substantial new functionality]
        === END FILE ===
        
        BUILD SUBSTANTIAL, WORKING NEW FEATURES that transform this project's capabilities!
        """
        
        response = self.llm_provider.generate_text(prompt, temperature=0.3)
        
        # Save the LLM response for debugging
        self._save_development_artifact(response, "llm_comprehensive_response")
        
        return self._parse_implementation_response(response, project_dir)
    
    def _parse_implementation_response(self, response: str, project_dir: str) -> Dict:
        """Parse the LLM implementation response and create/modify files."""
        files_created = []
        files_modified = []
        
        current_content = []
        current_file = None
        current_action = None
        current_improvement = None
        
        for line in response.split('\n'):
            # Handle both formats: === format and #### format
            if (line.startswith('=== ACTION:') and line.endswith('===')) or line.startswith('#### ACTION:'):
                if line.startswith('==='):
                    current_action = line.replace('=== ACTION:', '').replace('===', '').strip()
                else:
                    current_action = line.replace('#### ACTION:', '').strip()
                    
            elif (line.startswith('=== FILENAME:') and line.endswith('===')) or line.startswith('#### FILENAME:'):
                # Save previous file
                if current_file and current_content and current_action:
                    self._save_implementation_file(
                        current_file, current_content, current_action, current_improvement,
                        project_dir, files_created, files_modified
                    )
                
                # Start new file
                if line.startswith('==='):
                    current_file = line.replace('=== FILENAME:', '').replace('===', '').strip()
                else:
                    current_file = line.replace('#### FILENAME:', '').strip()
                current_content = []
                current_improvement = None
                
            elif (line.startswith('=== IMPROVEMENT:') and line.endswith('===')) or line.startswith('#### IMPROVEMENT:'):
                if line.startswith('==='):
                    current_improvement = line.replace('=== IMPROVEMENT:', '').replace('===', '').strip()
                else:
                    current_improvement = line.replace('#### IMPROVEMENT:', '').strip()
                    
            elif line.strip() == '=== END FILE ===' or line.startswith('#### END FILE'):
                continue
                
            elif current_file:
                # Skip markdown code block markers if present
                if line.strip() in ['```python', '```', '```bash', '```javascript', '```html']:
                    continue
                current_content.append(line)
        
        # Save last file
        if current_file and current_content and current_action:
            self._save_implementation_file(
                current_file, current_content, current_action, current_improvement,
                project_dir, files_created, files_modified
            )
        
        # Validate minimum code generation requirements
        total_lines_created = 0
        for file_path in files_created:
            try:
                full_path = os.path.join(project_dir, file_path)
                if os.path.exists(full_path):
                    with open(full_path, 'r') as f:
                        total_lines_created += len(f.readlines())
            except:
                pass
        
        self.logger.info(f"Generated {total_lines_created} lines of new code across {len(files_created)} new files")
        
        # Log warning if below minimum threshold
        if total_lines_created < 300:
            self.logger.warning(f"Generated only {total_lines_created} lines - below recommended minimum of 300+ lines per iteration")
        
        return {
            "files_created": files_created,
            "files_modified": files_modified,
            "total_lines_created": total_lines_created,
            "meets_minimum_threshold": total_lines_created >= 300
        }
    
    def _save_implementation_file(self, file_path: str, content_lines: List[str], 
                                action: str, improvement: str, project_dir: str,
                                files_created: List[str], files_modified: List[str]):
        """Save an implementation file and log the action."""
        try:
            full_path = os.path.join(project_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            content = '\n'.join(content_lines)
            
            # Check if file already exists
            file_exists = os.path.exists(full_path)
            
            if file_exists:
                # File exists - determine if we should extend or replace
                if action == "CREATE":
                    # Change action to MODIFY since file already exists
                    action = "MODIFY"
                    self.logger.info(f"File {file_path} already exists - changing CREATE to MODIFY")
                
                if action == "MODIFY":
                    # Read existing content to avoid overwriting
                    try:
                        with open(full_path, 'r') as f:
                            existing_content = f.read()
                        
                        # Check if this is just a duplicate of existing content
                        if content.strip() in existing_content or existing_content.strip() in content:
                            self.logger.info(f"SKIPPED: {file_path} - content already exists or is duplicate")
                            return
                        
                        # Append new content instead of overwriting
                        enhanced_content = self._merge_file_content(existing_content, content, file_path)
                        
                        with open(full_path, 'w') as f:
                            f.write(enhanced_content)
                        
                        files_modified.append(file_path)
                        self.logger.info(f"MODIFIED: {file_path} - {improvement}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to modify existing file {file_path}: {e}")
                        # Fallback to creating with timestamp
                        timestamp_path = file_path.replace('.py', f'_{datetime.now().strftime("%H%M%S")}.py')
                        full_timestamp_path = os.path.join(project_dir, timestamp_path)
                        with open(full_timestamp_path, 'w') as f:
                            f.write(content)
                        files_created.append(timestamp_path)
                        self.logger.info(f"CREATED: {timestamp_path} - {improvement} (timestamped due to merge conflict)")
                
            else:
                # File doesn't exist - create it
                with open(full_path, 'w') as f:
                    f.write(content)
                
                files_created.append(file_path)
                self.logger.info(f"CREATED: {file_path} - {improvement}")
            
        except Exception as e:
            self.logger.error(f"Failed to save {file_path}: {e}")
    
    def _merge_file_content(self, existing_content: str, new_content: str, file_path: str) -> str:
        """
        Intelligently merge new content with existing file content.
        
        Args:
            existing_content: Current file content
            new_content: New content to add
            file_path: File path for context
            
        Returns:
            str: Merged content
        """
        # For Python files, try to merge intelligently
        if file_path.endswith('.py'):
            return self._merge_python_content(existing_content, new_content)
        
        # For other files, append with separator
        return f"{existing_content}\n\n# === ADDED CONTENT ===\n{new_content}"
    
    def _merge_python_content(self, existing_content: str, new_content: str) -> str:
        """
        Merge Python file content intelligently by combining imports, classes, and functions.
        
        Args:
            existing_content: Existing Python code
            new_content: New Python code to merge
            
        Returns:
            str: Merged Python content
        """
        try:
            import ast
            import re
            
            # Parse existing and new content
            existing_lines = existing_content.split('\n')
            new_lines = new_content.split('\n')
            
            # Extract imports from both
            existing_imports = []
            existing_code = []
            new_imports = []
            new_code = []
            
            # Simple parsing for imports and code
            for line in existing_lines:
                if line.strip().startswith(('import ', 'from ')):
                    existing_imports.append(line)
                elif line.strip():
                    existing_code.append(line)
            
            for line in new_lines:
                if line.strip().startswith(('import ', 'from ')):
                    if line not in existing_imports:  # Avoid duplicate imports
                        new_imports.append(line)
                elif line.strip():
                    new_code.append(line)
            
            # Combine imports (existing first, then new unique ones)
            all_imports = existing_imports + new_imports
            
            # Check for function/class conflicts
            existing_definitions = self._extract_definitions(existing_content)
            new_definitions = self._extract_definitions(new_content)
            
            # If there are conflicting definitions, create versioned functions
            merged_code = existing_code.copy()
            
            for definition in new_definitions:
                if definition['name'] in [d['name'] for d in existing_definitions]:
                    # Rename conflicting definition
                    timestamp = datetime.now().strftime("%H%M")
                    new_name = f"{definition['name']}_v{timestamp}"
                    
                    # Replace the definition name in new_code
                    pattern = rf"\b{re.escape(definition['name'])}\b"
                    new_code_str = '\n'.join(new_code)
                    new_code_str = re.sub(pattern, new_name, new_code_str, count=1)
                    new_code = new_code_str.split('\n')
                    
                    self.logger.info(f"Renamed conflicting {definition['type']} '{definition['name']}' to '{new_name}'")
            
            # Combine all content
            result_lines = []
            
            # Add imports
            if all_imports:
                result_lines.extend(all_imports)
                result_lines.append('')  # Blank line after imports
            
            # Add existing code
            if existing_code:
                result_lines.extend(existing_code)
                result_lines.append('')  # Blank line
            
            # Add separator comment
            result_lines.append('# === ADDED FUNCTIONALITY ===')
            result_lines.append('')
            
            # Add new code
            if new_code:
                result_lines.extend(new_code)
            
            return '\n'.join(result_lines)
            
        except Exception as e:
            self.logger.error(f"Failed to merge Python content intelligently: {e}")
            # Fallback to simple append
            return f"{existing_content}\n\n# === ADDED CONTENT ===\n{new_content}"
    
    def _extract_definitions(self, content: str) -> List[Dict]:
        """Extract function and class definitions from Python content."""
        definitions = []
        
        try:
            import re
            
            # Find class definitions
            class_matches = re.finditer(r'^class\s+(\w+)', content, re.MULTILINE)
            for match in class_matches:
                definitions.append({
                    'type': 'class',
                    'name': match.group(1),
                    'line': content[:match.start()].count('\n') + 1
                })
            
            # Find function definitions
            func_matches = re.finditer(r'^def\s+(\w+)', content, re.MULTILINE)
            for match in func_matches:
                definitions.append({
                    'type': 'function',
                    'name': match.group(1),
                    'line': content[:match.start()].count('\n') + 1
                })
                
        except Exception as e:
            self.logger.error(f"Failed to extract definitions: {e}")
        
        return definitions
    
    def _format_files_for_implementation(self, existing_files: Dict) -> str:
        """Format existing files for implementation analysis."""
        formatted = ""
        for file_path, file_info in list(existing_files.items())[:10]:  # Limit to first 10 files
            content = file_info["content"]
            if len(content) > 2000:  # Show more content for better analysis
                content = content[:2000] + f"... [truncated, total {file_info['lines']} lines]"
            formatted += f"\n--- {file_path} ({file_info['lines']} lines) ---\n{content}\n"
        return formatted
    
    def _create_implementation_summary(self, implementation_result: Dict, improvements: List[Dict]) -> str:
        """Create a summary of what was implemented."""
        summary = f"""# Development Agent Implementation Summary

**Timestamp:** {datetime.now().isoformat()}
**Agent:** {self.agent_id}

## Implementation Results
- **Files Created:** {len(implementation_result.get('files_created', []))}
- **Files Modified:** {len(implementation_result.get('files_modified', []))}

### Files Created:
"""
        
        for file in implementation_result.get('files_created', []):
            summary += f"- {file}\n"
        
        summary += "\n### Files Modified:\n"
        for file in implementation_result.get('files_modified', []):
            summary += f"- {file}\n"
        
        summary += "\n## Improvements Implemented:\n"
        for i, imp in enumerate(improvements, 1):
            summary += f"{i}. {imp.get('what', 'Unknown improvement')}\n"
        
        return summary
    
    def _save_development_artifact(self, content: str, artifact_type: str):
        """Save development work artifacts for visibility."""
        try:
            # Create agent work directory
            agent_work_dir = os.path.join(".", "agent_work")
            os.makedirs(agent_work_dir, exist_ok=True)
            
            # Save artifact with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            artifact_file = os.path.join(agent_work_dir, f"development_{artifact_type}_{timestamp}.md")
            
            with open(artifact_file, 'w') as f:
                f.write(content)
            
            self.logger.info(f"Saved development artifact: {artifact_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save development artifact: {e}")
    
    def _save_iteration_progress(self, iteration_count: int, files_created: List[str], files_modified: List[str], improvements_implemented: List[Dict]):
        """Save iteration progress to prevent losing track of what's been built."""
        try:
            agent_work_dir = os.path.join(".", "agent_work")
            os.makedirs(agent_work_dir, exist_ok=True)
            
            progress_file = os.path.join(agent_work_dir, "iteration_progress.json")
            
            # Load existing progress
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    progress = json.loads(f.read())
            else:
                progress = {"iterations": [], "all_files_created": [], "all_files_modified": []}
            
            # Add current iteration
            current_iteration = {
                "iteration": iteration_count,
                "timestamp": datetime.now().isoformat(),
                "files_created": files_created,
                "files_modified": files_modified,
                "improvements": [imp.get('what', 'Unknown') for imp in improvements_implemented],
                "agent_id": self.agent_id
            }
            
            progress["iterations"].append(current_iteration)
            
            # Update cumulative lists
            for file in files_created:
                if file not in progress["all_files_created"]:
                    progress["all_files_created"].append(file)
            
            for file in files_modified:
                if file not in progress["all_files_modified"]:
                    progress["all_files_modified"].append(file)
            
            # Save updated progress
            with open(progress_file, 'w') as f:
                f.write(json.dumps(progress, indent=2))
            
            self.logger.info(f"Saved iteration progress: iteration {iteration_count}")
            
        except Exception as e:
            self.logger.error(f"Failed to save iteration progress: {e}")
    
    def _get_previous_iteration_progress(self) -> Dict:
        """Get previous iteration progress to understand what's been built."""
        try:
            progress_file = os.path.join(".", "agent_work", "iteration_progress.json")
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    return json.loads(f.read())
        except Exception as e:
            self.logger.error(f"Failed to load iteration progress: {e}")
        
        return {"iterations": [], "all_files_created": [], "all_files_modified": []}
    
    def _detect_target_technology(self) -> str:
        """Detect the target technology for the project from the goal."""
        try:
            # Read the goal file to understand what technology should be used
            goal_text = ""
            goal_files = ["goal.txt", "goal.md", "README.md"]
            
            for goal_file in goal_files:
                try:
                    with open(goal_file, 'r') as f:
                        goal_text = f.read()
                        break
                except FileNotFoundError:
                    continue
            
            if not goal_text:
                self.logger.warning("No goal file found, defaulting to Python")
                return "python"
            
            # Use LLM to detect the target technology dynamically
            detection_prompt = f"""
            Analyze this project goal and determine the primary programming language/technology that should be used:
            
            GOAL: {goal_text}
            
            Based on the goal description, what programming language, framework, or technology should be used for this project?
            
            Consider:
            - Explicit mentions of technologies (e.g., "use Python", "create in JavaScript", "build with Go")
            - Domain-specific technologies (e.g., PineScript for TradingView indicators, SQL for databases)
            - Implicit technology requirements based on the project type
            
            Return ONLY the primary technology name (e.g., "pinescript", "javascript", "python", "go", "rust", etc.)
            Be specific and concise - return just the technology name in lowercase.
            """
            
            detected_tech = self.llm_provider.generate_text(detection_prompt, temperature=0.1).strip().lower()
            
            # Clean up the response (remove extra text if any)
            tech_words = detected_tech.split()
            if tech_words:
                primary_tech = tech_words[0]
                self.logger.info(f"Detected target technology: {primary_tech}")
                return primary_tech
            
            # Fallback
            self.logger.warning("Could not detect technology from goal, defaulting to Python")
            return "python"
            
        except Exception as e:
            self.logger.error(f"Failed to detect target technology: {e}")
            return "python"
    
    def _get_file_extension_for_technology(self, technology: str) -> str:
        """Get the appropriate file extension for a technology using LLM."""
        try:
            extension_prompt = f"""
            What is the standard file extension for {technology} files?
            
            Return ONLY the file extension including the dot (e.g., ".py", ".js", ".pine", ".go", ".rs")
            Be precise and return just the extension.
            """
            
            extension = self.llm_provider.generate_text(extension_prompt, temperature=0.1).strip()
            
            # Ensure it starts with a dot
            if not extension.startswith('.'):
                extension = '.' + extension
            
            # Clean up any extra text
            if ' ' in extension:
                extension = extension.split()[0]
            
            self.logger.info(f"Determined file extension for {technology}: {extension}")
            return extension
            
        except Exception as e:
            self.logger.error(f"Failed to determine file extension for {technology}: {e}")
            return ".txt"
    
    def _get_technology_specific_requirements(self, technology: str) -> str:
        """Get technology-specific requirements and best practices using LLM."""
        try:
            requirements_prompt = f"""
            What are the key best practices, syntax requirements, and conventions for {technology} development?
            
            Provide a concise list of 5-8 important guidelines including:
            - Syntax and language-specific conventions
            - File structure and naming conventions
            - Key functions, libraries, or frameworks commonly used
            - Code organization patterns
            - Any domain-specific requirements
            
            Format as a bulleted list with specific, actionable guidelines.
            """
            
            requirements = self.llm_provider.generate_text(requirements_prompt, temperature=0.2)
            self.logger.info(f"Generated requirements for {technology}")
            return requirements
            
        except Exception as e:
            self.logger.error(f"Failed to generate requirements for {technology}: {e}")
            return f"Follow best practices for {technology} development."


class DocumentationAgent(BaseAgent):
    """
    Documentation Agent for creating project documentation.
    
    This agent specializes in creating user guides, API documentation,
    and other documentation artifacts.
    """
    
    def __init__(self, agent_id: str, llm_provider: LLMProviderInterface, config: Optional[Dict] = None):
        """
        Initialize the Documentation Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider instance
            config: Optional configuration dictionary
        """
        super().__init__(agent_id, "documentation", config)
        self.llm_provider = llm_provider
    
    def process_task(self, task: Dict) -> Dict:
        """
        Process a documentation task.
        
        Args:
            task: Task dictionary with details about the documentation task
            
        Returns:
            Dict: Documentation results including user guides and API docs
        """
        self.status = "processing"
        
        try:
            # Extract task details
            components = task.get("components", [])
            implementations = task.get("implementations", [])
            blueprint = task.get("blueprint", {})
            
            # Create component documentation
            component_docs = self._create_component_documentation(components, implementations)
            
            # Create API documentation
            api_docs = self._create_api_documentation(implementations)
            
            # Create user guide
            user_guide = self._create_user_guide(blueprint, components)
            
            # Prepare result
            result = {
                "task_id": task.get("task_id"),
                "status": "completed",
                "component_docs": component_docs,
                "api_docs": api_docs,
                "user_guide": user_guide
            }
            
            self.status = "ready"
            return result
            
        except Exception as e:
            return self.handle_error(e, task)
    
    def _create_component_documentation(self, components: List[Dict], implementations: List[Dict]) -> List[Dict]:
        """
        Create documentation for components.
        
        Args:
            components: List of component definitions
            implementations: List of component implementations
            
        Returns:
            List[Dict]: Component documentation
        """
        # This is a placeholder implementation
        # In a real implementation, this would use the LLM to create documentation
        
        component_docs = []
        
        for component in components:
            # Find the corresponding implementation
            implementation = next((impl for impl in implementations if impl["component_id"] == component["id"]), None)
            
            if implementation:
                # Use LLM to create documentation
                prompt = f"Create documentation for the following component and its implementation:\n\nComponent:\n{component}\n\nImplementation:\n{implementation}"
                doc_text = self.llm_provider.generate_text(prompt, temperature=0.5)
                
                component_docs.append({
                    "component_id": component["id"],
                    "title": f"Documentation for {component['name']}",
                    "content": doc_text,
                    "format": "markdown"
                })
        
        return component_docs
    
    def _create_api_documentation(self, implementations: List[Dict]) -> Dict:
        """
        Create API documentation.
        
        Args:
            implementations: List of component implementations
            
        Returns:
            Dict: API documentation
        """
        # This is a placeholder implementation
        # In a real implementation, this would use the LLM to create API documentation
        
        # Use LLM to create API documentation
        prompt = f"Create API documentation for the following implementations:\n\n{implementations}"
        api_doc_text = self.llm_provider.generate_text(prompt, temperature=0.5)
        
        # Structure the API documentation
        api_docs = {
            "title": "API Documentation",
            "content": api_doc_text,
            "format": "markdown",
            "endpoints": [
                {
                    "path": "/api/endpoint1",
                    "method": "GET",
                    "description": "Description of endpoint 1",
                    "parameters": [],
                    "responses": []
                },
                {
                    "path": "/api/endpoint2",
                    "method": "POST",
                    "description": "Description of endpoint 2",
                    "parameters": [],
                    "responses": []
                }
            ]
        }
        
        return api_docs
    
    def _create_user_guide(self, blueprint: Dict, components: List[Dict]) -> Dict:
        """
        Create a user guide.
        
        Args:
            blueprint: Project blueprint
            components: List of component definitions
            
        Returns:
            Dict: User guide
        """
        # This is a placeholder implementation
        # In a real implementation, this would use the LLM to create a user guide
        
        # Use LLM to create user guide
        prompt = f"Create a user guide for the following project:\n\nBlueprint:\n{blueprint}\n\nComponents:\n{components}"
        user_guide_text = self.llm_provider.generate_text(prompt, temperature=0.5)
        
        # Structure the user guide
        user_guide = {
            "title": "User Guide",
            "content": user_guide_text,
            "format": "markdown",
            "sections": [
                {
                    "title": "Introduction",
                    "content": "Introduction to the project"
                },
                {
                    "title": "Installation",
                    "content": "Installation instructions"
                },
                {
                    "title": "Usage",
                    "content": "Usage instructions"
                },
                {
                    "title": "Features",
                    "content": "Description of features"
                },
                {
                    "title": "Troubleshooting",
                    "content": "Troubleshooting guide"
                }
            ]
        }
        
        return user_guide


class AnalysisAgent(BaseAgent):
    """
    Analysis Agent for analyzing project state and suggesting improvements.
    
    This agent specializes in examining existing project files, comparing
    against goals, and suggesting specific improvements or new features.
    """
    
    def __init__(self, agent_id: str, llm_provider: LLMProviderInterface, config: Optional[Dict] = None):
        """
        Initialize the Analysis Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider instance
            config: Optional configuration dictionary
        """
        super().__init__(agent_id, "analysis", config)
        self.llm_provider = llm_provider
        
        # Initialize logger
        self.logger = logging.getLogger(f"swarmdev.agents.{agent_id}")
    
    def process_task(self, task: Dict) -> Dict:
        """
        Process an analysis task.
        
        Args:
            task: Task dictionary with details about the analysis task
            
        Returns:
            Dict: Analysis results including improvement suggestions and evolved goal
        """
        self.status = "processing"
        
        # DEBUG: Add basic logging to track execution
        print(f"[DEBUG] AnalysisAgent.process_task called with task: {task.get('task_id', 'unknown')}")
        self.logger.info(f"AnalysisAgent processing task: {task.get('task_id', 'unknown')}")
        
        try:
            # Extract task details
            goal = task.get("goal", "")
            project_dir = task.get("project_dir", ".")
            iteration_count = task.get("iteration_count", 0)
            max_iterations = task.get("max_iterations", None)
            workflow_type = task.get("workflow_type", "indefinite")
            
            print(f"[DEBUG] Analysis task details: goal='{goal[:50]}...', iteration={iteration_count}")
            
            # Analyze current project state
            project_state = self._analyze_project_state(project_dir)
            
            print(f"[DEBUG] Project state analyzed: {project_state.get('file_count', 0)} files")
            
            # Compare against original goal and suggest improvements
            improvement_analysis = self._analyze_improvements(goal, project_state, iteration_count)
            
            print(f"[DEBUG] Improvements analyzed: {improvement_analysis.get('improvement_count', 0)} suggestions")
            
            # Create evolved goal for next iteration (if not the final iteration)
            evolved_goal = None
            if iteration_count > 0 and iteration_count < (max_iterations or 10):
                evolved_goal = self._create_evolved_goal(goal, project_state, improvement_analysis, iteration_count)
                print(f"[DEBUG] Evolved goal created for iteration {iteration_count + 1}")
            
            # Determine if another iteration is needed
            should_continue = self._should_continue_iteration(
                improvement_analysis, iteration_count, max_iterations, workflow_type
            )
            
            print(f"[DEBUG] Should continue: {should_continue}")
            
            # Prepare result
            result = {
                "task_id": task.get("task_id"),
                "status": "completed",
                "project_state": project_state,
                "improvement_analysis": improvement_analysis,
                "should_continue": should_continue,
                "iteration_count": iteration_count + 1,
                "improvements_suggested": improvement_analysis.get("improvements", []),
                "evolved_goal": evolved_goal  # New: evolved goal for next iteration
            }
            
            print(f"[DEBUG] AnalysisAgent task completed successfully")
            self.status = "ready"
            return result
            
        except Exception as e:
            print(f"[DEBUG] AnalysisAgent error: {e}")
            return self.handle_error(e, task)
    
    def _analyze_project_state(self, project_dir: str) -> Dict:
        """
        Analyze the current state of the project.
        
        Args:
            project_dir: Project directory path
            
        Returns:
            Dict: Project state analysis
        """
        try:
            project_files = {}
            file_count = 0
            
            # Read all files in the project directory
            for root, dirs, files in os.walk(project_dir):
                # Skip hidden directories, build/cache directories, and agent work directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                          ['__pycache__', 'node_modules', 'target', 'build', 'dist', 'agent_work', 'goals']]
                
                for file in files:
                    if file.startswith('.') or file.endswith(('.pyc', '.log')):
                        continue
                    
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_dir)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            project_files[relative_path] = {
                                "content": content,
                                "size": len(content),
                                "lines": len(content.split('\n'))
                            }
                            file_count += 1
                            
                    except (UnicodeDecodeError, PermissionError):
                        # Skip binary files or files we can't read
                        continue
            
            # Read the goal to understand target technology BEFORE analyzing
            target_technology = self._detect_target_technology()
            
            # Use LLM to analyze the project structure and functionality with technology context
            analysis_prompt = f"""
            Analyze this project structure and content for a {target_technology} project:
            
            TARGET TECHNOLOGY: {target_technology}
            
            Files found: {list(project_files.keys())}
            
            File contents:
            {self._format_files_for_analysis(project_files)}
            
            Provide a comprehensive analysis including:
            1. Project type and technology stack (focus on {target_technology})
            2. Current functionality and features implemented in {target_technology}
            3. Code quality and structure assessment for {target_technology}
            4. Potential issues or limitations
            5. Architecture overview for {target_technology} projects
            
            Keep the analysis focused on {target_technology} development patterns and best practices.
            """
            
            analysis_text = self.llm_provider.generate_text(analysis_prompt, temperature=0.3)
            
            return {
                "files": list(project_files.keys()),
                "file_count": len(project_files),
                "total_lines": sum(f["lines"] for f in project_files.values()),
                "analysis": analysis_text,
                "target_technology": target_technology,
                "structure": self._identify_project_structure(project_files, target_technology)
            }
            
        except Exception as e:
            return {
                "files": [],
                "file_count": 0,
                "total_lines": 0,
                "analysis": f"Error analyzing project: {e}",
                "target_technology": "unknown",
                "structure": "unknown"
            }
    
    def _format_files_for_analysis(self, project_files: Dict) -> str:
        """Format project files for LLM analysis."""
        formatted = ""
        for file_path, file_info in list(project_files.items())[:10]:  # Limit to first 10 files
            content = file_info["content"]
            if len(content) > 1000:  # Truncate long files
                content = content[:1000] + "... [truncated]"
            formatted += f"\n--- {file_path} ---\n{content}\n"
        return formatted
    
    def _identify_project_structure(self, project_files: Dict, target_technology: str) -> str:
        """Identify the project structure type using LLM."""
        try:
            files = list(project_files.keys())
            
            structure_prompt = f"""
            Based on these files and the target technology '{target_technology}', what type of project structure is this?
            
            Files: {files}
            Target Technology: {target_technology}
            
            Return a brief description of the project structure type (e.g., "web application", "library", "CLI tool", "trading indicators", etc.)
            Be concise - just return the project type.
            """
            
            structure_type = self.llm_provider.generate_text(structure_prompt, temperature=0.1).strip()
            return structure_type
            
        except Exception as e:
            self.logger.error(f"Failed to identify project structure: {e}")
            return "unknown"
    
    def _detect_target_technology(self) -> str:
        """Detect the target technology for the project from the goal."""
        try:
            # Read the goal file to understand what technology should be used
            goal_text = ""
            goal_files = ["goal.txt", "goal.md", "README.md"]
            
            for goal_file in goal_files:
                try:
                    with open(goal_file, 'r') as f:
                        goal_text = f.read()
                        break
                except FileNotFoundError:
                    continue
            
            if not goal_text:
                self.logger.warning("No goal file found, defaulting to Python")
                return "python"
            
            # Use LLM to detect the target technology dynamically
            detection_prompt = f"""
            Analyze this project goal and determine the primary programming language/technology that should be used:
            
            GOAL: {goal_text}
            
            Based on the goal description, what programming language, framework, or technology should be used for this project?
            
            Consider:
            - Explicit mentions of technologies (e.g., "use Python", "create in JavaScript", "build with Go")
            - Domain-specific technologies (e.g., PineScript for TradingView indicators, SQL for databases)
            - Implicit technology requirements based on the project type
            
            Return ONLY the primary technology name (e.g., "pinescript", "javascript", "python", "go", "rust", etc.)
            Be specific and concise - return just the technology name in lowercase.
            """
            
            detected_tech = self.llm_provider.generate_text(detection_prompt, temperature=0.1).strip().lower()
            
            # Clean up the response (remove extra text if any)
            tech_words = detected_tech.split()
            if tech_words:
                primary_tech = tech_words[0]
                self.logger.info(f"Detected target technology: {primary_tech}")
                return primary_tech
            
            # Fallback
            self.logger.warning("Could not detect technology from goal, defaulting to Python")
            return "python"
            
        except Exception as e:
            self.logger.error(f"Failed to detect target technology: {e}")
            return "python"
    
    def _analyze_improvements(self, goal: str, project_state: Dict, iteration_count: int) -> Dict:
        """
        Analyze potential improvements for the project.
        
        Args:
            goal: Original project goal
            project_state: Current project state analysis
            iteration_count: Current iteration number
            
        Returns:
            Dict: Improvement analysis and suggestions
        """
        self.logger.info(f"Starting deep improvement analysis for iteration {iteration_count}")
        
        # Extract what's already been implemented to avoid repetitive suggestions
        implemented_features = self._extract_implemented_features(project_state)
        
        # Get target technology for context
        target_technology = project_state.get('target_technology', 'unknown')
        
        # Create creative expansion prompt that forces innovative thinking
        improvement_prompt = f"""
        CREATIVE {target_technology.upper()} PROJECT EXPANSION ANALYSIS (Iteration {iteration_count})
        
        TARGET TECHNOLOGY: {target_technology}
        ORIGINAL GOAL: {goal}
        
        CURRENT PROJECT STATE:
        - Files: {project_state.get('file_count', 0)} files, {project_state.get('total_lines', 0)} lines
        - Structure: {project_state.get('structure', 'unknown')}
        - Current Analysis: {project_state.get('analysis', 'No analysis available')}
        
        ALREADY IMPLEMENTED FEATURES (DO NOT SUGGEST THESE AGAIN):
        {implemented_features}
        
        Your role is to identify opportunities for CREATIVE EXPANSION of this {target_technology} project with substantial new capabilities.
        
        CRITICAL: DO NOT suggest features that are already implemented (listed above).
        
        FORBIDDEN SUGGESTIONS (NEVER suggest these repetitive improvements):
        - Error handling improvements
        - Documentation enhancements  
        - Logging improvements
        - Code refactoring
        - Performance optimizations
        - Testing improvements
        - Security enhancements
        - Configuration management
        - Code organization
        
        REQUIRED CREATIVE EXPANSION APPROACH FOR {target_technology.upper()}:
        1. **Understand the Domain**: What problem space does this {target_technology} project operate in?
        2. **Identify User Needs**: What do users in this domain typically struggle with?
        3. **Think Adjacent**: What related problems could this project solve?
        4. **Expand Scope**: What entirely NEW {target_technology} capabilities would be transformative?
        5. **Consider Workflows**: What new user workflows are missing?
        6. **Integration Opportunities**: What external systems or data sources could be leveraged?
        7. **{target_technology} Specific**: What advanced {target_technology} features could be implemented?
        
        CREATIVITY REQUIREMENTS:
        - Suggest 5+ entirely NEW {target_technology} capabilities that don't exist yet
        - Each suggestion must add substantial user value and expand project scope
        - Focus on features that would differentiate this project from similar tools
        - Think about what would make users say "I can't live without this feature"
        - Propose capabilities that would make this project a "must-have" tool
        
        PROVIDE SPECIFIC, CREATIVE {target_technology.upper()} EXPANSIONS:
        For each expansion, specify:
        - WHAT new {target_technology} capability to build (be very specific)
        - WHY users would find this transformative (real user value)
        - HOW to implement it (new {target_technology} modules, functions, features needed)
        - PRIORITY (critical/high/medium/low)
        - EFFORT level (small/medium/large)
        - IMPACT level (low/medium/high/transformative)
        - USER_BENEFIT (how this changes users' workflows)
        
        Focus on INNOVATIVE {target_technology} expansions that would make this project significantly more valuable!
        """
        
        self.logger.info("Sending analysis prompt to LLM...")
        analysis_text = self.llm_provider.generate_text(improvement_prompt, temperature=0.4)
        self.logger.info(f"Received analysis response: {len(analysis_text)} characters")
        
        # Save the full analysis as an artifact for visibility
        self._save_analysis_artifact(analysis_text, iteration_count)
        
        # Parse specific improvements from the analysis
        improvements = self._parse_specific_improvements(analysis_text)
        
        # Filter out any suggestions that match already implemented features
        filtered_improvements = self._filter_duplicate_improvements(improvements, implemented_features)
        
        self.logger.info(f"Parsed {len(improvements)} improvements, filtered to {len(filtered_improvements)} unique ones")
        for i, improvement in enumerate(filtered_improvements):
            self.logger.info(f"Improvement {i+1}: {improvement.get('what', 'Unknown')[:100]}...")
        
        return {
            "full_analysis": analysis_text,
            "improvements": filtered_improvements,
            "improvement_count": len(filtered_improvements),
            "has_significant_improvements": len(filtered_improvements) > 0,
            "analysis_depth": "comprehensive",
            "iteration": iteration_count,
            "implemented_features": implemented_features
        }
    
    def _extract_implemented_features(self, project_state: Dict) -> str:
        """Extract already implemented features from the project state."""
        try:
            files = project_state.get('files', [])
            analysis = project_state.get('analysis', '')
            target_tech = project_state.get('target_technology', 'unknown')
            
            # Use LLM to analyze what's been implemented
            extraction_prompt = f"""
            Based on this {target_tech} project analysis and file list, what features have been implemented?
            
            Files: {files}
            Analysis: {analysis}
            
            List the specific features/capabilities that are already working in this {target_tech} project.
            Focus on functional features, not just file existence.
            Format as a bulleted list.
            """
            
            implemented_features = self.llm_provider.generate_text(extraction_prompt, temperature=0.2)
            
            if not implemented_features.strip():
                return f"No major {target_tech} features implemented yet - this is a new project."
            
            return implemented_features
            
        except Exception as e:
            self.logger.error(f"Failed to extract implemented features: {e}")
            return "Unable to determine implemented features"
    
    def _filter_duplicate_improvements(self, improvements: List[Dict], implemented_features: str) -> List[Dict]:
        """Filter out improvements that match already implemented features."""
        filtered = []
        implemented_lower = implemented_features.lower()
        
        for improvement in improvements:
            what = improvement.get('what', '').lower()
            
            # Use LLM to check if this improvement is already implemented
            duplication_check = f"""
            Is this improvement already implemented based on the existing features?
            
            Proposed Improvement: {what}
            Existing Features: {implemented_features}
            
            Return only "YES" if already implemented, "NO" if it's a new feature.
            """
            
            try:
                result = self.llm_provider.generate_text(duplication_check, temperature=0.1).strip().upper()
                if result == "NO":
                    filtered.append(improvement)
                else:
                    self.logger.info(f"Filtered duplicate suggestion: {improvement.get('what', 'Unknown')[:50]}...")
            except:
                # If LLM call fails, include the improvement to be safe
                filtered.append(improvement)
        
        return filtered
    
    def _save_analysis_artifact(self, analysis_text: str, iteration_count: int):
        """Save analysis as an artifact for visibility into agent thinking."""
        try:
            import os
            
            # Create agent work directory
            agent_work_dir = os.path.join(".", "agent_work")
            os.makedirs(agent_work_dir, exist_ok=True)
            
            # Save detailed analysis
            analysis_file = os.path.join(agent_work_dir, f"analysis_iteration_{iteration_count}.md")
            with open(analysis_file, 'w') as f:
                f.write(f"# Analysis Agent Work - Iteration {iteration_count}\n\n")
                f.write(f"**Timestamp:** {datetime.now().isoformat()}\n\n")
                f.write(f"**Agent:** {self.agent_id}\n\n")
                f.write("## Detailed Analysis\n\n")
                f.write(analysis_text)
            
            self.logger.info(f"Saved analysis artifact to: {analysis_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save analysis artifact: {e}")
    
    def _parse_specific_improvements(self, analysis_text: str) -> List[Dict]:
        """Parse specific, actionable improvements from analysis text."""
        improvements = []
        
        # Use LLM to extract structured improvements
        extraction_prompt = f"""
        From this analysis, extract SPECIFIC, ACTIONABLE improvements:
        
        {analysis_text}
        
        Return a JSON array of improvements, each with:
        {{
            "what": "Specific description of what to improve",
            "why": "Why this improvement is important",
            "how": "Concrete implementation steps",
            "priority": "critical|high|medium|low",
            "effort": "small|medium|large", 
            "impact": "low|medium|high|transformative",
            "files_affected": ["list", "of", "files"],
            "implementation_notes": "Specific technical details"
        }}
        
        Focus on the most impactful improvements. Return valid JSON only.
        """
        
        try:
            improvements_json = self.llm_provider.generate_text(extraction_prompt, temperature=0.2)
            
            # Clean up the JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', improvements_json, re.DOTALL)
            if json_match:
                improvements_data = json.loads(json_match.group())
                
                for imp in improvements_data:
                    if isinstance(imp, dict) and "what" in imp:
                        improvements.append(imp)
                        
        except Exception as e:
            self.logger.error(f"Failed to parse structured improvements: {e}")
            
            # Fallback: parse simple improvements from text
            lines = analysis_text.split('\n')
            current_improvement = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith(('*', '-', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    if current_improvement and "what" in current_improvement:
                        improvements.append(current_improvement)
                    
                    current_improvement = {
                        "what": re.sub(r'^[1-9*-]\.\s*', '', line),
                        "priority": "medium",
                        "effort": "medium",
                        "impact": "medium"
                    }
                elif "priority" in line.lower() and current_improvement:
                    if "critical" in line.lower():
                        current_improvement["priority"] = "critical"
                    elif "high" in line.lower():
                        current_improvement["priority"] = "high"
                    elif "low" in line.lower():
                        current_improvement["priority"] = "low"
            
            if current_improvement and "what" in current_improvement:
                improvements.append(current_improvement)
        
        # Ensure we have at least some improvements
        if not improvements:
            improvements = [{
                "what": "Enhance project based on comprehensive analysis",
                "why": "Project needs meaningful improvements to better fulfill its goals",
                "how": "Implement improvements based on detailed analysis findings",
                "priority": "high",
                "effort": "medium",
                "impact": "high",
                "files_affected": ["multiple"],
                "implementation_notes": "See full analysis for details"
            }]
        
        return improvements[:8]  # Limit to top 8 improvements
    
    def _should_continue_iteration(self, improvement_analysis: Dict, iteration_count: int, 
                                 max_iterations: Optional[int], workflow_type: str) -> bool:
        """
        Determine if another iteration should be run based on iteration limits.
        
        Args:
            improvement_analysis: Analysis of potential improvements
            iteration_count: Current iteration count
            max_iterations: Maximum iterations allowed (None for indefinite)
            workflow_type: Type of workflow (indefinite or iteration)
            
        Returns:
            bool: True if another iteration should be run
        """
        # Simple logic - continue if we haven't hit the max iterations limit
        if workflow_type == "iteration" and max_iterations is not None:
            return iteration_count < max_iterations
        
        # For indefinite workflows, always continue (user will stop manually)
        if workflow_type == "indefinite":
            return True
            
        # Default to continuing for reasonable number of iterations
        return iteration_count < 10
    
    def _create_evolved_goal(self, original_goal: str, project_state: Dict, improvement_analysis: Dict, iteration_count: int) -> str:
        """
        Create an evolved, more comprehensive goal for the next iteration.
        
        Args:
            original_goal: The original goal text
            project_state: Current project state analysis
            improvement_analysis: Analysis of potential improvements
            iteration_count: Current iteration number
            
        Returns:
            str: Evolved goal text for next iteration
        """
        self.logger.info(f"Creating evolved goal for iteration {iteration_count + 1}")
        
        target_technology = project_state.get('target_technology', 'unknown')
        
        # Gather context about what's been built
        current_features = self._analyze_implemented_features(project_state)
        missing_features = improvement_analysis.get("improvements", [])
        
        evolution_prompt = f"""
        COMPREHENSIVE {target_technology.upper()} TECHNICAL SPECIFICATION FOR ITERATION {iteration_count + 1}
        
        TARGET TECHNOLOGY: {target_technology}
        ORIGINAL PROJECT GOAL: {original_goal}
        
        CURRENT PROJECT STATE (Iteration {iteration_count}):
        - Files: {project_state.get('file_count', 0)} files
        - Structure: {project_state.get('structure', 'unknown')}
        - Implementation Status: {project_state.get('analysis', 'No analysis')}
        
        FEATURES SUCCESSFULLY IMPLEMENTED:
        {current_features}
        
        CREATIVE EXPANSION OPPORTUNITIES:
        {self._format_improvements_for_goal(missing_features)}
        
        Create a COMPREHENSIVE {target_technology.upper()} TECHNICAL SPECIFICATION for iteration {iteration_count + 1} structured as follows:
        
        **ITERATION {iteration_count + 1} {target_technology.upper()} TECHNICAL SPECIFICATIONS:**
        
        **PROJECT VISION:**
        [Brief description of what this {target_technology} project should become]
        
        **EXISTING {target_technology.upper()} CAPABILITIES (maintain and build upon):**
        - [Complete inventory of all current {target_technology} features and modules]
        - [List all working {target_technology} functionality from previous iterations]
        
        **NEW {target_technology.upper()} CAPABILITIES TO BUILD THIS ITERATION:**
        
        **Major {target_technology} Feature 1: [Feature Name]**
        - Purpose: [What user need does this address in {target_technology}]
        - Implementation: [Specific {target_technology} modules/files to create - be very detailed]
        - Acceptance Criteria: [How to know it's complete and working]
        - User Benefit: [Why users will find this transformative]
        - Technical Requirements: [{target_technology} APIs, libraries, functions needed]
        
        **Major {target_technology} Feature 2: [Feature Name]**
        - Purpose: [What problem does this solve in {target_technology}]
        - Implementation: [Technical specifications - {target_technology} modules, functions]
        - Integration: [How it connects to existing {target_technology} features]
        - Success Metrics: [Measurable outcomes]
        - Technical Requirements: [Specific {target_technology} implementation details]
        
        **TECHNICAL REQUIREMENTS FOR {target_technology.upper()}:**
        - Minimum 300+ lines of new functional {target_technology} code
        - 3-5 new {target_technology} modules or major components
        - Complete user workflows implemented in {target_technology}
        - Supporting {target_technology} utilities and configurations
        - Integration with existing {target_technology} architecture
        
        **{target_technology.upper()} QUALITY STANDARDS:**
        - [{target_technology} specific performance targets]
        - [{target_technology} user experience requirements]
        - [{target_technology} reliability and robustness standards]
        
        **EXPANSION PHILOSOPHY:**
        This iteration should make the {target_technology} project significantly more capable and valuable to users while maintaining all existing functionality and adding substantial new value.
        
        EVOLVED {target_technology.upper()} TECHNICAL SPECIFICATION FOR ITERATION {iteration_count + 1}:
        """
        
        try:
            evolved_goal_text = self.llm_provider.generate_text(evolution_prompt, temperature=0.3)
            
            # Save the evolved goal as an artifact and file
            self._save_evolved_goal(evolved_goal_text, iteration_count + 1)
            
            return evolved_goal_text
            
        except Exception as e:
            self.logger.error(f"Failed to create evolved goal: {e}")
            return original_goal  # Fallback to original goal
    
    def _analyze_implemented_features(self, project_state: Dict) -> str:
        """Analyze what features have been successfully implemented."""
        try:
            target_tech = project_state.get('target_technology', 'unknown')
            
            # Use LLM to analyze what's been implemented
            analysis_prompt = f"""
            Based on this {target_tech} project analysis, summarize what features have been successfully implemented:
            
            {project_state.get('analysis', 'No detailed analysis available')}
            
            Files: {project_state.get('files', [])}
            
            Provide a concise summary of working {target_tech} features and capabilities.
            """
            
            implemented_features = self.llm_provider.generate_text(analysis_prompt, temperature=0.2)
            return implemented_features
            
        except Exception as e:
            self.logger.error(f"Failed to analyze implemented features: {e}")
            return "Feature analysis unavailable"
    
    def _format_improvements_for_goal(self, improvements: List[Dict]) -> str:
        """Format improvement suggestions for inclusion in evolved goal."""
        if not improvements:
            return "No specific improvements identified"
        
        formatted = "Key opportunities for expansion:\n"
        for i, imp in enumerate(improvements[:8], 1):  # Limit to top 8
            what = imp.get("what", "Unknown improvement")
            why = imp.get("why", "No reason specified")
            formatted += f"{i}. {what} - {why}\n"
        
        return formatted
    
    def _save_evolved_goal(self, evolved_goal: str, iteration_number: int):
        """Save the evolved goal as both an artifact and a goal file."""
        try:
            import os
            
            # Save as agent artifact
            agent_work_dir = os.path.join(".", "agent_work")
            os.makedirs(agent_work_dir, exist_ok=True)
            
            artifact_file = os.path.join(agent_work_dir, f"evolved_goal_iteration_{iteration_number}.md")
            with open(artifact_file, 'w') as f:
                f.write(f"# Evolved Goal - Iteration {iteration_number}\n\n")
                f.write(f"**Created:** {datetime.now().isoformat()}\n\n")
                f.write(f"**Agent:** {self.agent_id}\n\n")
                f.write("## Evolved Goal Text\n\n")
                f.write(evolved_goal)
            
            # Also save as a goal file that can be used by other agents (in goals directory for cleaner organization)
            goals_dir = "goals"
            os.makedirs(goals_dir, exist_ok=True)
            goal_file = os.path.join(goals_dir, f"goal_iteration_{iteration_number}.txt")
            with open(goal_file, 'w') as f:
                f.write(evolved_goal)
            
            self.logger.info(f"Saved evolved goal to: {artifact_file} and {goal_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save evolved goal: {e}")
