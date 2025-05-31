"""
Specialized agent implementations for the SwarmDev platform.
This module provides specialized agent classes for different tasks.
"""

import os
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

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
            
            # Read existing project files with better analysis
            existing_files = self._read_project_files(project_dir)
            self.logger.info(f"Read {len(existing_files)} existing files for analysis")
            
            # Get improvement suggestions from task context
            improvement_suggestions = getattr(self, '_improvement_suggestions', [])
            self.logger.info(f"Found {len(improvement_suggestions)} improvement suggestions")
            
            # Save development work plan for visibility
            work_plan = self._create_work_plan(goal, improvement_suggestions, existing_files)
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
    
    def _create_work_plan(self, goal: str, improvements: List[Dict], existing_files: Dict) -> str:
        """Create a detailed work plan showing what will be implemented."""
        plan = f"""# Development Agent Work Plan

**Goal:** {goal}
**Timestamp:** {datetime.now().isoformat()}
**Agent:** {self.agent_id}

## Current Project State
- **Files:** {len(existing_files)} files
- **Total Lines:** {sum(f.get('lines', 0) for f in existing_files.values())}
- **File Types:** {set(f.get('extension', '') for f in existing_files.values())}

## Existing Files Analysis
"""
        
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
        plan += "1. Analyze each improvement suggestion\n"
        plan += "2. Modify existing files where possible\n"
        plan += "3. Create new files only when necessary\n"
        plan += "4. Preserve existing functionality\n"
        plan += "5. Add comprehensive error handling\n"
        plan += "6. Improve user experience\n"
        
        return plan
    
    def _implement_specific_improvements(self, goal: str, improvements: List[Dict], 
                                       existing_files: Dict, project_dir: str) -> Dict:
        """Implement specific improvements suggested by analysis."""
        self.logger.info(f"Implementing {len(improvements)} specific improvements")
        
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
        BUILD NEW CAPABILITIES BASED ON CREATIVE EXPANSIONS:
        
        GOAL: {goal}
        
        CREATIVE EXPANSIONS TO BUILD INTO NEW FEATURES:
        {improvements_text}
        
        EXISTING PROJECT FILES:
        {self._format_files_for_implementation(existing_files)}
        
        Your task is to BUILD these creative expansions into substantial new capabilities:
        
        BUILDING REQUIREMENTS:
        - Create 300+ lines of new, working code this iteration
        - Build 2-3 entirely new modules implementing the suggested expansions
        - Implement complete, functional features (not stubs or placeholders)
        - Create supporting utilities and configurations
        - Focus on additive development that brings the expansions to life
        
        FORBIDDEN ACTIONS:
        - Making small modifications to existing files
        - Creating incomplete stub functions
        - Generic technical improvements (error handling, logging, documentation)
        - Refactoring existing code without adding new functionality
        
        SUBSTANTIAL BUILDING FOCUS:
        1. Focus on the CREATIVE EXPANSIONS listed above, not technical improvements
        2. Build entirely NEW capabilities that users can interact with
        3. Create complete workflows and user experiences
        4. Add substantial new functionality that expands project scope
        5. Implement features that transform what the project can do
        6. Build reusable components that enable future expansion
        
        For each new capability you build, return:
        
        === ACTION: CREATE ===
        === FILENAME: path/filename.ext ===
        === IMPROVEMENT: Description of new capability/expansion implemented ===
        [complete file content with substantial new functionality]
        === END FILE ===
        
        BUILD SUBSTANTIAL NEW FEATURES that implement the creative expansions!
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
            if line.startswith('=== ACTION:') and line.endswith('==='):
                current_action = line.replace('=== ACTION:', '').replace('===', '').strip()
            elif line.startswith('=== FILENAME:') and line.endswith('==='):
                # Save previous file
                if current_file and current_content and current_action:
                    self._save_implementation_file(
                        current_file, current_content, current_action, current_improvement,
                        project_dir, files_created, files_modified
                    )
                
                # Start new file
                current_file = line.replace('=== FILENAME:', '').replace('===', '').strip()
                current_content = []
                current_improvement = None
                
            elif line.startswith('=== IMPROVEMENT:') and line.endswith('==='):
                current_improvement = line.replace('=== IMPROVEMENT:', '').replace('===', '').strip()
            elif line.strip() == '=== END FILE ===':
                continue
            elif current_file:
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
            with open(full_path, 'w') as f:
                f.write(content)
            
            if action == "CREATE":
                files_created.append(file_path)
                self.logger.info(f"CREATED: {file_path} - {improvement}")
            elif action == "MODIFY":
                files_modified.append(file_path)
                self.logger.info(f"MODIFIED: {file_path} - {improvement}")
            
        except Exception as e:
            self.logger.error(f"Failed to save {file_path}: {e}")
    
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
            
            # Use LLM to analyze the project structure and functionality
            analysis_prompt = f"""
            Analyze this project structure and content:
            
            Files found: {list(project_files.keys())}
            
            File contents:
            {self._format_files_for_analysis(project_files)}
            
            Provide a comprehensive analysis including:
            1. Project type and technology stack
            2. Current functionality and features
            3. Code quality and structure assessment
            4. Potential issues or limitations
            5. Architecture overview
            
            Keep the analysis concise but thorough.
            """
            
            analysis_text = self.llm_provider.generate_text(analysis_prompt, temperature=0.3)
            
            return {
                "files": list(project_files.keys()),
                "file_count": len(project_files),
                "total_lines": sum(f["lines"] for f in project_files.values()),
                "analysis": analysis_text,
                "structure": self._identify_project_structure(project_files)
            }
            
        except Exception as e:
            return {
                "files": [],
                "file_count": 0,
                "total_lines": 0,
                "analysis": f"Error analyzing project: {e}",
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
    
    def _identify_project_structure(self, project_files: Dict) -> str:
        """Identify the project structure type."""
        files = list(project_files.keys())
        
        if "package.json" in files:
            return "nodejs"
        elif "requirements.txt" in files or "setup.py" in files or any(f.endswith(".py") for f in files):
            return "python"
        elif "Cargo.toml" in files:
            return "rust"
        elif "go.mod" in files or any(f.endswith(".go") for f in files):
            return "go"
        elif "pom.xml" in files or any(f.endswith(".java") for f in files):
            return "java"
        elif any(f.endswith(".html") for f in files):
            return "web"
        else:
            return "unknown"
    
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
        
        # Create creative expansion prompt that forces innovative thinking
        improvement_prompt = f"""
        CREATIVE PROJECT EXPANSION ANALYSIS (Iteration {iteration_count})
        
        ORIGINAL GOAL: {goal}
        
        CURRENT PROJECT STATE:
        - Files: {project_state.get('file_count', 0)} files, {project_state.get('total_lines', 0)} lines
        - Structure: {project_state.get('structure', 'unknown')}
        - Current Analysis: {project_state.get('analysis', 'No analysis available')}
        
        EXISTING FILES TO ANALYZE:
        {project_state.get('analysis', 'No file content available')}
        
        Your role is to identify opportunities for CREATIVE EXPANSION and substantial new capabilities.
        
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
        
        REQUIRED CREATIVE EXPANSION APPROACH:
        1. **Understand the Domain**: What problem space does this project operate in? Who are the users?
        2. **Identify User Needs**: What do users in this domain typically struggle with beyond the current scope?
        3. **Think Adjacent**: What related problems could this project solve if it expanded its capabilities?
        4. **Expand Scope**: What entirely NEW capabilities would make this project indispensable to users?
        5. **Consider Workflows**: What new user workflows or interaction methods are completely missing?
        6. **Integration Opportunities**: What external systems, APIs, or data sources could be leveraged?
        7. **Automation Potential**: What manual tasks in this domain could be automated for users?
        
        CREATIVITY REQUIREMENTS:
        - Suggest 5+ entirely NEW capabilities that don't currently exist
        - Each suggestion must add substantial user value and expand project scope
        - Focus on features that would differentiate this project from similar tools
        - Think about different user personas and their unmet needs
        - Consider what would make users say "I can't live without this feature"
        - Propose capabilities that would make this project a "must-have" tool in its field
        
        EXPANSION THINKING:
        - What could this project become if it reached its full potential?
        - What adjacent problem domains could it expand into?
        - How could it save users significant time or effort through new capabilities?
        - What integrations would create powerful new workflows?
        - What features would make competitors obsolete?
        
        PROVIDE SPECIFIC, CREATIVE EXPANSIONS:
        For each expansion, specify:
        - WHAT new capability to build (be very specific about the feature)
        - WHY users would find this transformative (real user value)
        - HOW to implement it (new modules, APIs, components needed)
        - PRIORITY (critical/high/medium/low)
        - EFFORT level (small/medium/large)
        - IMPACT level (low/medium/high/transformative)
        - USER_BENEFIT (how this changes users' lives/workflows)
        
        Focus on INNOVATIVE expansions that would make this project significantly more valuable and comprehensive!
        """
        
        self.logger.info("Sending analysis prompt to LLM...")
        analysis_text = self.llm_provider.generate_text(improvement_prompt, temperature=0.4)
        self.logger.info(f"Received analysis response: {len(analysis_text)} characters")
        
        # Save the full analysis as an artifact for visibility
        self._save_analysis_artifact(analysis_text, iteration_count)
        
        # Parse specific improvements from the analysis
        improvements = self._parse_specific_improvements(analysis_text)
        
        self.logger.info(f"Parsed {len(improvements)} specific improvements")
        for i, improvement in enumerate(improvements):
            self.logger.info(f"Improvement {i+1}: {improvement.get('what', 'Unknown')[:100]}...")
        
        return {
            "full_analysis": analysis_text,
            "improvements": improvements,
            "improvement_count": len(improvements),
            "has_significant_improvements": len(improvements) > 0,
            "analysis_depth": "comprehensive",
            "iteration": iteration_count
        }
    
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
        
        # Gather context about what's been built
        current_features = self._analyze_implemented_features(project_state)
        missing_features = improvement_analysis.get("improvements", [])
        
        evolution_prompt = f"""
        COMPREHENSIVE TECHNICAL SPECIFICATION FOR ITERATION {iteration_count + 1}
        
        ORIGINAL PROJECT GOAL:
        {original_goal}
        
        CURRENT PROJECT STATE (Iteration {iteration_count}):
        - Files: {project_state.get('file_count', 0)} files
        - Structure: {project_state.get('structure', 'unknown')}
        - Implementation Status: {project_state.get('analysis', 'No analysis')}
        
        FEATURES SUCCESSFULLY IMPLEMENTED:
        {current_features}
        
        CREATIVE EXPANSION OPPORTUNITIES:
        {self._format_improvements_for_goal(missing_features)}
        
        Create a COMPREHENSIVE TECHNICAL SPECIFICATION for iteration {iteration_count + 1} structured as follows:
        
        **ITERATION {iteration_count + 1} TECHNICAL SPECIFICATIONS:**
        
        **PROJECT VISION:**
        [Brief description of what this project should become]
        
        **EXISTING CAPABILITIES (maintain and build upon):**
        - [Complete inventory of all current features and modules]
        - [List all working functionality from previous iterations]
        
        **NEW CAPABILITIES TO BUILD THIS ITERATION:**
        
        **Major Feature 1: [Feature Name]**
        - Purpose: [What user need does this address]
        - Implementation: [Specific modules/files to create - be very detailed]
        - Acceptance Criteria: [How to know it's complete and working]
        - User Benefit: [Why users will find this transformative]
        - Technical Requirements: [APIs, libraries, data structures needed]
        
        **Major Feature 2: [Feature Name]**
        - Purpose: [What problem does this solve]
        - Implementation: [Technical specifications - modules, classes, functions]
        - Integration: [How it connects to existing features]
        - Success Metrics: [Measurable outcomes]
        - Technical Requirements: [Specific implementation details]
        
        **Major Feature 3: [Feature Name]**
        - [Same detailed structure for each new capability]
        
        **TECHNICAL REQUIREMENTS:**
        - Minimum 500+ lines of new functional code
        - 3-5 new modules or major components
        - Complete user workflows implemented
        - Supporting utilities and configurations
        - Integration with existing architecture
        
        **QUALITY STANDARDS:**
        - [Specific performance targets]
        - [User experience requirements]
        - [Reliability and robustness standards]
        
        **EXPANSION PHILOSOPHY:**
        This iteration should make the project significantly more capable and valuable to users while maintaining all existing functionality and adding substantial new value that transforms the user experience.
        
        EVOLVED TECHNICAL SPECIFICATION FOR ITERATION {iteration_count + 1}:
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
            files_summary = f"Project contains {project_state.get('file_count', 0)} files"
            structure_info = f"Architecture: {project_state.get('structure', 'unknown')}"
            
            # Use LLM to analyze what's been implemented
            analysis_prompt = f"""
            Based on this project analysis, summarize what features have been successfully implemented:
            
            {project_state.get('analysis', 'No detailed analysis available')}
            
            Files: {project_state.get('files', [])}
            
            Provide a concise summary of working features and capabilities.
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
