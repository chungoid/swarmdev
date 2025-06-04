"""
Specialized Agent implementations for the SwarmDev platform.
Clean, focused implementations using BaseAgent infrastructure.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """
    Research agent for gathering information and analyzing requirements.
    Uses MCP tools for documentation lookup and sequential thinking.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None):
        super().__init__(agent_id, agent_type, llm_provider, mcp_manager, config)
    
    def process_task(self, task: Dict) -> Dict:
        """Process research tasks using LLM and MCP tools."""
        try:
            self.status = "processing"
            goal = task.get("goal", "")
            context = task.get("context", {})
            
            self.logger.info(f"RESEARCH: Starting investigation of goal: {goal[:100]}...")
            
            # Use MCP sequential thinking for complex research planning
            research_plan = self._plan_research_approach(goal, context)
            
            # Conduct the research using the plan
            research_results = self._conduct_research(research_plan, goal, context)
            
            # Synthesize findings
            synthesis = self._synthesize_research_findings(research_results, goal)
            
            self.status = "completed"
            return {
                "status": "success",
                "agent_type": self.agent_type,
                "research_plan": research_plan,
                "findings": research_results,
                "synthesis": synthesis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"RESEARCH: Failed to process task: {e}")
            return self.handle_error(e, task)
        
    def _plan_research_approach(self, goal: str, context: Dict) -> Dict:
        """Plan research approach using enhanced task execution."""
        result = self.execute_enhanced_task(
            task_description="Plan a comprehensive research approach for gathering relevant information",
            context={"goal": goal, "context": context},
            fallback_method=self._basic_research_planning
        )
        
        # Extract plan from enhanced result for backward compatibility
        if result.get("status") == "success":
            plan_content = result.get("result", result)
            return {"plan": plan_content, "method": result.get("method", "enhanced")}
        else:
            return {"plan": "Research planning failed", "method": "error"}
    
    def _basic_research_planning(self, task_description: str, context: Dict) -> Dict:
        """Fallback research planning using LLM only."""
        goal = context.get("goal", "")
        research_context = context.get("context", {})
        
        if not self.llm_provider:
            return {
                "status": "error",
                "result": "Basic research planning requires LLM provider"
            }
        
        planning_prompt = f"""
        Plan a research approach for: {goal}
        
        Context: {research_context}
        
        Create a structured research plan including:
        1. Information gathering priorities
        2. Technology research needs
        3. Documentation sources to investigate
        4. Research methodology
        
        Return as structured plan.
        """
        
        try:
            plan_text = self.llm_provider.generate_text(planning_prompt, temperature=0.3)
            return {
                "status": "success",
                "method": "llm_only",
                "result": plan_text,
                "tools_used": []
            }
        except Exception as e:
            return {
                "status": "error",
                "result": f"Planning failed: {e}"
            }
    
    def _conduct_research(self, research_plan: Dict, goal: str, context: Dict) -> Dict:
        """Conduct comprehensive research using enhanced task execution."""
        result = self.execute_enhanced_task(
            task_description="Conduct comprehensive research based on the research plan",
            context={"goal": goal, "research_plan": research_plan, "context": context},
            fallback_method=self._basic_research_conduct
        )
        
        # Return results in expected format
        if result.get("status") == "success":
            return {
                "basic_research": result.get("result", "Research completed"),
                "method": result.get("method", "enhanced"),
                "tools_used": result.get("tools_used", [])
            }
        else:
            return {"basic_research": "Research failed", "method": "error"}
    
    def _basic_research_conduct(self, task_description: str, context: Dict) -> Dict:
        """Fallback research conduct using LLM only."""
        goal = context.get("goal", "")
        research_plan = context.get("research_plan", {})
        research_context = context.get("context", {})
        
        if not self.llm_provider:
            return {
                "status": "error",
                "result": "Basic research requires LLM provider"
            }
        
        research_prompt = f"""
        Conduct comprehensive research for this project:
        
        GOAL: {goal}
        RESEARCH PLAN: {json.dumps(research_plan, indent=2)}
        CONTEXT: {json.dumps(research_context, indent=2)}
        
        Provide detailed research findings covering:
        1. Technical requirements and considerations
        2. Best practices and patterns
        3. Implementation approaches
        4. Potential challenges and solutions
        5. Tools, libraries, and frameworks needed
        
        Be thorough and provide actionable insights for implementation.
        """
        
        try:
            research_result = self.llm_provider.generate_text(research_prompt, temperature=0.3)
            return {
                "status": "success",
                "method": "llm_only",
                "result": research_result,
                "tools_used": []
            }
        except Exception as e:
            return {
                "status": "error",
                "result": f"Research failed: {e}"
            }
    

     
    def _synthesize_research_findings(self, results: Dict, goal: str) -> str:
        """Synthesize research findings into actionable insights."""
        if not self.llm_provider:
            return "Research completed - manual synthesis required"
        
        synthesis_prompt = f"""
        Synthesize these research findings into a clear, actionable summary:
        
        ORIGINAL GOAL: {goal}
        
        RESEARCH RESULTS:
        - Technologies Found: {list(results.keys())}
        - Documentation Available: {list(results.keys())}
        - Analysis: {json.dumps(results, indent=2)}
        
        Create a concise synthesis that:
        1. Summarizes key findings
        2. Highlights critical insights
        3. Provides clear next steps
        4. Identifies any gaps or concerns
        
        Focus on actionable outcomes.
        """
        
        try:
            return self.llm_provider.generate_text(synthesis_prompt, temperature=0.3)
        except Exception as e:
            self.logger.error(f"Synthesis generation failed: {e}")
            return f"Research completed with findings: {len(results)} findings analyzed"


class PlanningAgent(BaseAgent):
    """
    Planning agent for creating project plans and breaking down goals.
    Uses sequential thinking for complex planning tasks.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None):
        super().__init__(agent_id, agent_type, llm_provider, mcp_manager, config)
    
    def process_task(self, task: Dict) -> Dict:
        """Process planning tasks using sequential thinking and project analysis."""
        try:
            self.status = "processing"
            goal = task.get("goal", "")
            context = task.get("context", {})
            project_dir = context.get("project_dir")
            
            self.logger.info(f"PLANNING: Creating plan for goal: {goal[:100]}...")
            
            # Investigate project if directory provided
            project_context = self._investigate_project_context(project_dir) if project_dir else {}
            
            # Use sequential thinking for complex planning
            detailed_plan = self._create_detailed_plan(goal, context, project_context)
            
            # Break down into actionable tasks
            task_breakdown = self._break_down_tasks(detailed_plan, goal)
            
            # Identify dependencies and timeline
            execution_strategy = self._plan_execution_strategy(task_breakdown)
            
            self.status = "completed"
            return {
                "status": "success",
                "agent_type": self.agent_type,
                "detailed_plan": detailed_plan,
                "task_breakdown": task_breakdown,
                "execution_strategy": execution_strategy,
                "project_context": project_context,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"PLANNING: Failed to process task: {e}")
            return self.handle_error(e, task)
    
    def _investigate_project_context(self, project_dir: str) -> Dict:
        """Investigate project context using base agent method."""
        try:
            project_path = self.investigate_project(project_dir)
            
            if self.llm_provider:
                investigation_prompt = f"""
                Investigate this project directory to understand the current state and structure:
                
                PROJECT DIRECTORY: {project_path}
                
                Analyze:
                1. Existing project structure and organization
                2. Technologies and frameworks in use
                3. Current development state
                4. Potential integration points
                5. Constraints or considerations for new development
                
                                Provide a structured analysis of the project context.
                """
                
                context_analysis = self.llm_provider.generate_text(investigation_prompt, temperature=0.2)
                return {"analysis": context_analysis, "project_dir": project_path}
                
        except Exception as e:
            self.logger.warning(f"Project investigation failed: {e}")
            
        return {"analysis": "No project context available", "project_dir": project_dir}
    
    def _create_detailed_plan(self, goal: str, context: Dict, project_context: Dict) -> Dict:
        """Create detailed plan using enhanced task execution."""
        result = self.execute_enhanced_task(
            task_description="Create a comprehensive development plan",
            context={"goal": goal, "context": context, "project_context": project_context},
            fallback_method=self._basic_detailed_planning
        )
        
        # Extract plan from enhanced result for backward compatibility
        if result.get("status") == "success":
            plan_content = result.get("result", result)
            return {"plan": plan_content, "method": result.get("method", "enhanced")}
        else:
            return {"plan": "Planning failed", "method": "error"}
    
    def _basic_detailed_planning(self, task_description: str, context: Dict) -> Dict:
        """Fallback detailed planning using LLM only."""
        goal = context.get("goal", "")
        planning_context = context.get("context", {})
        project_context = context.get("project_context", {})
        
        if not self.llm_provider:
            return {
                "status": "error",
                "result": "Basic planning requires LLM provider"
            }
        
        planning_prompt = f"""
        Create a detailed implementation plan:
        
        GOAL: {goal}
        CONTEXT: {planning_context}
        PROJECT CONTEXT: {project_context.get('analysis', 'None')}
        
        Include:
        1. Architecture and design considerations
        2. Implementation phases
        3. Component requirements
        4. Integration approach
        5. Testing and validation strategy
        
        Provide a structured, actionable plan.
        """
        
        try:
            plan_text = self.llm_provider.generate_text(planning_prompt, temperature=0.3)
            return {
                "status": "success",
                "method": "llm_only",
                "result": plan_text,
                "tools_used": []
            }
        except Exception as e:
            return {
                "status": "error",
                "result": f"Planning failed: {e}"
            }
    
    def _break_down_tasks(self, detailed_plan: Dict, goal: str) -> List[Dict]:
        """Break down the plan into specific, actionable tasks."""
        if not self.llm_provider:
            return [{"task": "Implement solution", "type": "development", "priority": "high"}]
        
        breakdown_prompt = f"""
        Break down this plan into specific, actionable tasks:
        
        GOAL: {goal}
        DETAILED PLAN: {detailed_plan.get('plan', '')}
        
        Create tasks that are:
        1. Specific and actionable
        2. Appropriately scoped (not too large or small)
        3. Clearly defined with success criteria
        4. Categorized by type (research, planning, development, testing, etc.)
        5. Prioritized (high, medium, low)
        
        Return as a JSON array of task objects with fields: task, description, type, priority, estimated_effort.
        """
        
        try:
            response = self.llm_provider.generate_text(breakdown_prompt, temperature=0.2)
            
            # Try to parse JSON response
            try:
                tasks = json.loads(response.strip())
                if isinstance(tasks, list):
                    return tasks
            except:
                pass
            
            # Fallback: parse text response
            lines = response.strip().split('\n')
            tasks = []
            for i, line in enumerate(lines):
                if line.strip():
                    tasks.append({
                        "task": line.strip(),
                        "description": f"Task {i+1} from plan breakdown",
                        "type": "development",
                        "priority": "medium",
                        "estimated_effort": "TBD"
                    })
            
            # Intelligent task limiting - allow more tasks for complex goals, fewer for simple ones
            max_tasks = min(len(tasks), 15 if len(goal) > 200 else 8)
            return tasks[:max_tasks]
            
        except Exception as e:
            self.logger.error(f"Task breakdown failed: {e}")
            return [{"task": "Implement solution according to plan", "type": "development", "priority": "high"}]
    
    def _plan_execution_strategy(self, task_breakdown: List[Dict]) -> Dict:
        """Plan execution strategy including dependencies and timeline."""
        if not self.llm_provider:
            return {"strategy": "Execute tasks in order", "dependencies": [], "timeline": "TBD"}
        
        strategy_prompt = f"""
        Plan an execution strategy for these tasks:
        
        TASKS: {json.dumps(task_breakdown, indent=2)}
        
        Consider:
        1. Task dependencies and sequencing
        2. Parallel execution opportunities
        3. Risk mitigation
        4. Resource requirements
        5. Timeline estimation
        
        Provide a structured execution strategy.
        """
        
        try:
            strategy = self.llm_provider.generate_text(strategy_prompt, temperature=0.3)
            return {"strategy": strategy, "total_tasks": len(task_breakdown)}
        except Exception as e:
            self.logger.error(f"Execution strategy planning failed: {e}")
            return {"strategy": "Execute tasks sequentially", "total_tasks": len(task_breakdown)}


class DevelopmentAgent(BaseAgent):
    """
    Development agent for implementing code and creating files.
    Uses project investigation and LLM-driven development.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None):
        super().__init__(agent_id, agent_type, llm_provider, mcp_manager, config)
    
    def process_task(self, task: Dict) -> Dict:
        """Process development tasks using project investigation and intelligent implementation."""
        try:
            self.status = "processing"
            goal = task.get("goal", "")
            context = task.get("context", {})
            project_dir = context.get("project_dir")
            
            self.logger.info(f"DEVELOPMENT: Implementing goal: {goal[:100]}...")
            
            # Investigate project before implementation
            project_analysis = self._investigate_project_for_development(project_dir) if project_dir else {}
            
            # Plan implementation approach
            implementation_plan = self._plan_implementation(goal, context, project_analysis)
            
            # Generate code and files
            implementation_results = self._implement_solution(implementation_plan, project_dir)
            
            self.status = "completed"
            return {
                "status": "success",
                "agent_type": self.agent_type,
                "project_analysis": project_analysis,
                "implementation_plan": implementation_plan,
                "implementation_results": implementation_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"DEVELOPMENT: Failed to process task: {e}")
            return self.handle_error(e, task)
    
    def _investigate_project_for_development(self, project_dir: str) -> Dict:
        """Investigate project specifically for development context."""
        try:
            project_path = self.investigate_project(project_dir)
            
            if self.llm_provider:
                dev_investigation_prompt = f"""
                Investigate this project for development planning:
                
                PROJECT DIRECTORY: {project_path}
                
                Focus on:
                1. Existing code structure and patterns
                2. Technologies, frameworks, and dependencies
                3. File organization and naming conventions
                4. Integration points and architecture
                5. Development environment and tooling
                
                Provide insights relevant to implementing new functionality.
                """
                
                analysis = self.llm_provider.generate_text(dev_investigation_prompt, temperature=0.2)
                return {"analysis": analysis, "project_dir": project_path}
                
        except Exception as e:
            self.logger.warning(f"Development investigation failed: {e}")
            
        return {"analysis": "No project analysis available", "project_dir": project_dir}
    
    def _plan_implementation(self, goal: str, context: Dict, project_analysis: Dict) -> Dict:
        """Plan implementation approach using enhanced task execution."""
        result = self.execute_enhanced_task(
            task_description="Plan implementation approach and architecture for the development goal",
            context={"goal": goal, "context": context, "project_analysis": project_analysis},
            fallback_method=self._basic_implementation_planning
        )
        
        # Process result for backward compatibility
        if result.get("status") == "success":
            plan_content = result.get("result", "Implementation plan completed")
            
            # Extract file list from plan if needed
            files = self._extract_files_from_plan(plan_content, goal)
            
            return {
                "approach": plan_content, 
                "files": files,
                "method": result.get("method", "enhanced"),
                "tools_used": result.get("tools_used", [])
            }
        else:
            return {"approach": "Implementation planning failed", "files": ["main.py"]}
    
    def _basic_implementation_planning(self, task_description: str, context: Dict) -> Dict:
        """Fallback implementation planning using LLM only."""
        goal = context.get("goal", "")
        dev_context = context.get("context", {})
        project_analysis = context.get("project_analysis", {})
        
        if not self.llm_provider:
            return {
                "status": "error",
                "result": "Basic implementation planning requires LLM provider"
            }
        
        planning_prompt = f"""
        Plan the implementation for this development goal:
        
        GOAL: {goal}
        CONTEXT: {dev_context}
        PROJECT ANALYSIS: {project_analysis.get('analysis', 'None')}
        
        Plan:
        1. Implementation approach and architecture
        2. Files that need to be created or modified
        3. Integration with existing code
        4. Dependencies and requirements
        5. Testing considerations
        
        Focus on practical, implementable solutions that integrate well with the existing project.
        """
        
        try:
            plan = self.llm_provider.generate_text(planning_prompt, temperature=0.3)
            return {
                "status": "success",
                "method": "llm_only",
                "result": plan,
                "tools_used": []
            }
        except Exception as e:
            return {
                "status": "error",
                "result": f"Implementation planning failed: {e}"
            }
    
    def _extract_files_from_plan(self, plan: str, goal: str) -> List[str]:
        """Extract file list from implementation plan."""
        if not self.llm_provider:
            return ["main.py"]
        
        file_extraction_prompt = f"""
        From this implementation plan, extract the specific files that need to be created or modified:
        
        PLAN: {plan}
        
        Return a simple list of file paths (one per line), relative to project root.
        Include:
        1. Main implementation files (.py, .js, etc.)
        2. Configuration files (.json, .yaml, .env, etc.)
        3. Documentation files (README.md, requirements.txt, etc.)
        4. Package structure files (__init__.py for Python packages)
        5. Test files if mentioned
        
        For Python projects, include __init__.py files for any new packages/directories.
        Use proper file extensions and follow language conventions.
        """
        
        try:
            files_response = self.llm_provider.generate_text(file_extraction_prompt, temperature=0.1)
            files = []
            for line in files_response.split('\n'):
                line = line.strip()
                # Skip empty lines, comments, and markdown delimiters
                if line and not line.startswith('#') and not line.startswith('```') and line != '```':
                    # Remove any remaining markdown artifacts
                    if line.startswith('- '):
                        line = line[2:]  # Remove bullet points
                    
                    # Accept various file types
                    valid_extensions = ['.py', '.json', '.txt', '.md', '.yaml', '.yml', '.env', '.js', '.ts', '.html', '.css']
                    if any(line.endswith(ext) for ext in valid_extensions) or line == '__init__.py':
                        files.append(line)
            
            # Intelligent file limiting - allow more files for complex projects
            max_files = min(len(files), 15 if len(goal) > 300 else 10)
            return files[:max_files]
            
        except Exception as e:
            self.logger.error(f"File extraction failed: {e}")
            return ["main.py"]
    
    def _implement_solution(self, implementation_plan: Dict, project_dir: str) -> Dict:
        """Implement the solution by generating code for planned files."""
        if not self.llm_provider:
            return {"status": "error", "message": "No LLM provider for implementation"}
        
        results = {
            "files_created": [],
            "files_modified": [],
            "code_generated": {},
            "errors": []
        }
        
        planned_files = implementation_plan.get("files", [])
        approach = implementation_plan.get("approach", "")
        
        # Process all planned files (already filtered by intelligent limit above)
        for file_path in planned_files:
            try:
                # Handle special cases for certain file types
                if file_path == '__init__.py' or file_path.endswith('/__init__.py'):
                    # Generate simple __init__.py content
                    init_content = self._generate_init_file_content(file_path, approach)
                    results["code_generated"][file_path] = init_content
                    self._write_file_to_disk(file_path, init_content, project_dir, results)
                    continue
                
                # Determine file purpose and generate appropriate code
                code_generation_prompt = f"""
                Generate code for this file based on the implementation plan:
                
                FILE PATH: {file_path}
                IMPLEMENTATION APPROACH: {approach}
                PROJECT DIRECTORY: {project_dir}
                
                Generate complete, functional code that:
                1. Implements the planned functionality
                2. Follows best practices for the detected technology
                3. Integrates well with the existing project structure
                4. Includes appropriate imports, error handling, and documentation
                5. Is production-ready and well-structured
                
                IMPORTANT: Return ONLY the raw code content without any markdown formatting, explanations, or code block delimiters. No ```python or ``` tags.
                """
                
                generated_code = self.llm_provider.generate_text(code_generation_prompt, temperature=0.2)
                
                # Clean up any remaining markdown artifacts
                cleaned_code = self._clean_generated_code(generated_code)
                
                # Store the cleaned code
                results["code_generated"][file_path] = cleaned_code
                
                # Write file to disk
                self._write_file_to_disk(file_path, cleaned_code, project_dir, results)
                    
            except Exception as e:
                error_msg = f"Failed to generate code for {file_path}: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        results["status"] = "success" if results["code_generated"] else "partial"
        return results
    
    def _clean_generated_code(self, code: str) -> str:
        """Clean generated code of markdown artifacts and formatting issues."""
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Skip markdown code block delimiters
            if stripped in ['```', '```python', '```json', '```markdown', '```plaintext']:
                continue
            # Skip language tags at start of code blocks
            if stripped.startswith('```') and len(stripped) < 20:
                continue
            cleaned_lines.append(line)
        
        # Remove leading/trailing empty lines
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    
    def _generate_init_file_content(self, file_path: str, approach: str) -> str:
        """Generate appropriate __init__.py content."""
        if file_path == '__init__.py':
            # Root package __init__.py
            return '"""Main package initialization."""\n\n__version__ = "0.1.0"\n'
        
        # Sub-package __init__.py - extract package name from path
        parts = file_path.split('/')
        if len(parts) > 1:
            package_name = parts[-2]  # Get directory name
            return f'"""Package: {package_name}"""\n'
        
        return '"""Package initialization."""\n'
    
    def _write_file_to_disk(self, file_path: str, content: str, project_dir: str, results: Dict):
        """Write file content to disk and track the operation."""
        if not project_dir:
            self.logger.warning(f"No project directory specified, cannot write file: {file_path}")
            return
            
        full_file_path = os.path.join(project_dir, file_path)
        
        # Check if file exists to determine created vs modified
        file_exists = os.path.exists(full_file_path)
        
        # Create directory structure if needed
        dir_path = os.path.dirname(full_file_path)
        if dir_path:  # Only create if there's actually a directory
            os.makedirs(dir_path, exist_ok=True)
        
        # Write the content to the file
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Track what we did
        if file_exists:
            results["files_modified"].append(file_path)
            self.logger.info(f"Modified file: {file_path}")
        else:
            results["files_created"].append(file_path)
            self.logger.info(f"Created file: {file_path}")


class AnalysisAgent(BaseAgent):
    """
    Analysis agent for analyzing project state and suggesting improvements.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None):
        super().__init__(agent_id, agent_type, llm_provider, mcp_manager, config)
    
    def process_task(self, task: Dict) -> Dict:
        """Process analysis tasks including project state analysis and improvement suggestions."""
        try:
            self.status = "processing"
            goal = task.get("goal", "")
            context = task.get("context", {})
            project_dir = context.get("project_dir")
            iteration_count = task.get("iteration_count", 0)
            max_iterations = task.get("max_iterations", None)
            workflow_type = task.get("workflow_type", "indefinite")
            
            self.logger.info(f"ANALYSIS: Analyzing project for goal: {goal[:100]}...")
            
            # Analyze current project state
            project_state = self._analyze_project_state(project_dir) if project_dir else {}
            
            # Analyze improvements needed
            improvement_analysis = self._analyze_improvements(goal, context, project_state)
            
            # Create evolved goal for next iteration if needed
            evolved_goal = None
            if iteration_count > 0 and iteration_count < (max_iterations or 10):
                evolved_goal = self._create_evolved_goal(goal, project_state, improvement_analysis, iteration_count)
            
            # Determine if another iteration is needed
            should_continue = self._should_continue_iteration(
                improvement_analysis, iteration_count, max_iterations, workflow_type
            )
            
            self.status = "completed"
            return {
                "status": "success",
                "agent_type": self.agent_type,
                "project_state": project_state,
                "improvement_analysis": improvement_analysis,
                "should_continue": should_continue,
                "iteration_count": iteration_count + 1,
                "improvements_suggested": improvement_analysis.get("improvements", []),
                "evolved_goal": evolved_goal,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"ANALYSIS: Failed to process task: {e}")
            return self.handle_error(e, task)
    
    def _analyze_project_state(self, project_dir: str) -> Dict:
        """Analyze current project state using LLM investigation."""
        try:
            project_path = self.investigate_project(project_dir)
            
            if self.llm_provider:
                state_prompt = f"""
                Analyze the current state of this project:
                
                PROJECT DIRECTORY: {project_path}
                
                Assess:
                1. Current functionality and features
                2. Code structure and organization
                3. Technologies and frameworks in use
                4. Completeness and gaps
                5. Quality and maintainability
                6. Integration points and architecture
                7. Areas for improvement or expansion within scope of the goal
                
                Provide a comprehensive project state analysis.
                """
                
                analysis = self.llm_provider.generate_text(state_prompt, temperature=0.2)
                return {"analysis": analysis, "project_dir": project_path}
                
        except Exception as e:
            self.logger.warning(f"Project state analysis failed: {e}")
            
        return {"analysis": "Project state analysis not available", "project_dir": project_dir}
    
    def _analyze_improvements(self, goal: str, context: Dict, project_state: Dict) -> Dict:
        """Analyze what improvements are needed using enhanced task execution."""
        result = self.execute_enhanced_task(
            task_description="Analyze what improvements are needed to achieve the goal",
            context={"goal": goal, "context": context, "project_state": project_state},
            fallback_method=self._basic_improvement_analysis
        )
        
        # Process result for backward compatibility
        if result.get("status") == "success":
            analysis_content = result.get("result", "Improvement analysis completed")
            
            # Extract improvements from analysis
            improvements = self._extract_improvements_from_analysis(analysis_content)
            
            return {
                "analysis": analysis_content,
                "improvements": improvements,
                "improvement_count": len(improvements),
                "method": result.get("method", "enhanced"),
                "tools_used": result.get("tools_used", [])
            }
        else:
            return {"improvements": ["Analysis failed - manual review needed"], "improvement_count": 1}
    
    def _basic_improvement_analysis(self, task_description: str, context: Dict) -> Dict:
        """Fallback improvement analysis using LLM only."""
        goal = context.get("goal", "")
        analysis_context = context.get("context", {})
        project_state = context.get("project_state", {})
        
        if not self.llm_provider:
            return {
                "status": "error",
                "result": "Basic improvement analysis requires LLM provider"
            }
        
        improvement_prompt = f"""
        Analyze what improvements are needed for this project:
        
        GOAL: {goal}
        CONTEXT: {analysis_context}
        PROJECT STATE: {project_state.get('analysis', 'None')}
        
        Identify:
        1. Gaps between current state and desired goal
        2. Missing functionality or features
        3. Code improvements needed
        4. Architectural enhancements within scope of the goal
        5. Integration requirements
        6. Reorganization of file or code structure
        7. Documentation needs
        8. Testing requirements
        
        Provide specific, actionable improvement suggestions.
        """
        
        try:
            analysis = self.llm_provider.generate_text(improvement_prompt, temperature=0.3)
            return {
                "status": "success",
                "method": "llm_only",
                "result": analysis,
                "tools_used": []
            }
        except Exception as e:
            return {
                "status": "error",
                "result": f"Improvement analysis failed: {e}"
            }
    
    def _extract_improvements_from_analysis(self, analysis: str) -> List[str]:
        """Extract specific improvements from analysis."""
        if not self.llm_provider:
            return ["Analysis completed - manual review needed"]
        
        improvements_prompt = f"""
        From this analysis, extract specific improvement actions:
        
        ANALYSIS: {analysis}
        
        Return a numbered list of specific, actionable improvements.
        """
        
        try:
            improvements_response = self.llm_provider.generate_text(improvements_prompt, temperature=0.2)
            improvements = [imp.strip() for imp in improvements_response.split('\n') if imp.strip()]
            return improvements
        except Exception as e:
            self.logger.error(f"Improvement extraction failed: {e}")
            return ["Analysis completed - manual review needed"]
    
    def _create_evolved_goal(self, original_goal: str, project_state: Dict, improvement_analysis: Dict, iteration_count: int) -> str:
        """Create an evolved goal for the next iteration based on current progress."""
        if not self.llm_provider:
            return original_goal
        
        evolution_prompt = f"""
        Create an evolved goal for the next iteration based on current progress:
        
        ORIGINAL GOAL: {original_goal}
        CURRENT ITERATION: {iteration_count}
        PROJECT STATE: {project_state.get('analysis', '')[:500]}...
        IMPROVEMENTS IDENTIFIED: {improvement_analysis.get('improvements', [])}
        
        Create a focused, evolved goal that:
        1. Builds on what has been accomplished
        2. Addresses the most important remaining gaps
        3. Is achievable in one iteration
        4. Maintains the overall project direction
        5. Is within scope of the original goal
        
        Return only the evolved goal text.
        """
        
        try:
            evolved_goal = self.llm_provider.generate_text(evolution_prompt, temperature=0.3)
            return evolved_goal.strip()
        except Exception as e:
            self.logger.error(f"Goal evolution failed: {e}")
            return original_goal
    
    def _should_continue_iteration(self, improvement_analysis: Dict, iteration_count: int, max_iterations: Optional[int], workflow_type: str) -> bool:
        """Determine if another iteration should be performed."""
        # For the new enhanced iteration workflow, use the smart continuation logic
        if workflow_type == "iteration" and "completion_strategy" in improvement_analysis:
            continuation_result = self._should_continue_iteration_enhanced(improvement_analysis, iteration_count)
            return continuation_result.get("should_continue", False)
        
        # Legacy logic for other workflows
        # Check max iterations limit
        if max_iterations is not None and iteration_count >= max_iterations:
            return False
        
        # For indefinite workflow, check if there are meaningful improvements
        if workflow_type == "indefinite":
            improvement_count = improvement_analysis.get("improvement_count", 0)
            return improvement_count > 0
        
        # For iteration workflow, respect max_iterations
        if workflow_type == "iteration":
            return max_iterations is None or iteration_count < max_iterations
        
        # Default: continue if improvements are available
        return improvement_analysis.get("improvement_count", 0) > 0

    def _should_continue_iteration_enhanced(self, improvement_analysis: Dict, iteration_count: int) -> Dict:
        """
        Enhanced iteration continuation logic for the new unified iteration workflow.
        Solves the "coat tails" problem with smart completion planning.
        """
        # Extract context from the improvement analysis
        context = improvement_analysis.get("context", {})
        initial_iterations = context.get("initial_iterations", 3)
        target_version = context.get("target_version")
        completion_strategy = context.get("completion_strategy", "smart")
        adaptive = context.get("adaptive_planning", True)
        
        self.logger.info(f"Enhanced continuation assessment: iteration {iteration_count}/{initial_iterations}, strategy: {completion_strategy}")
        
        # STRATEGY 1: Version-driven completion (from VersionedWorkflow)
        if target_version and completion_strategy == "version_driven":
            version_status = self._assess_version_completion(improvement_analysis, target_version)
            if version_status.get("target_reached", False):
                self.logger.info(f"Target version {target_version} reached - stopping iterations")
                return {
                    "should_continue": False,
                    "completion_reason": f"Target version {target_version} reached",
                    "completion_mode": "version_complete"
                }
        
        # STRATEGY 2: Smart completion assessment (NEW - solving "coat tails")
        if completion_strategy == "smart":
            completion_assessment = self._assess_smart_completion(
                improvement_analysis, iteration_count, initial_iterations, target_version
            )
            
            if completion_assessment.get("ready_for_completion", False):
                self.logger.info(f"Smart completion triggered: {completion_assessment.get('reason', 'ready')}")
                return {
                    "should_continue": completion_assessment.get("needs_final_iteration", False),
                    "completion_reason": completion_assessment.get("reason", "Project ready for completion"),
                    "completion_mode": "smart_completion",
                    "final_iteration_plan": completion_assessment.get("final_plan", {})
                }
        
        # STRATEGY 3: Adaptive iteration adjustment (from VersionedWorkflow pattern)
        if adaptive:
            iteration_assessment = self._assess_adaptive_iterations(
                improvement_analysis, iteration_count, initial_iterations
            )
            
            # Can extend beyond initial estimate if valuable work remains
            if iteration_assessment.get("should_extend", False):
                self.logger.info(f"Adaptive extension: {iteration_assessment.get('reason', 'valuable work remains')}")
                return {
                    "should_continue": True,
                    "completion_reason": f"Extending beyond initial estimate: {iteration_assessment.get('reason', 'valuable work remains')}",
                    "completion_mode": "adaptive_extension",
                    "estimated_remaining": iteration_assessment.get("estimated_remaining", 1)
                }
        
        # STRATEGY 4: Fixed iteration respect (fallback)
        if iteration_count >= initial_iterations:
            self.logger.info(f"Reached initial iteration limit ({initial_iterations}) - stopping")
            return {
                "should_continue": False,
                "completion_reason": f"Reached initial iteration limit ({initial_iterations})",
                "completion_mode": "fixed_limit"
            }
        
        # Default: continue if improvements available
        improvement_count = improvement_analysis.get("improvement_count", 0)
        should_continue = improvement_count > 0
        self.logger.info(f"Standard continuation: {should_continue} ({improvement_count} improvements available)")
        
        return {
            "should_continue": should_continue,
            "completion_reason": "Improvements available" if should_continue else "No improvements needed",
            "completion_mode": "standard_iteration"
        }

    def _assess_smart_completion(self, improvement_analysis: Dict, iteration_count: int, 
                               initial_iterations: int, target_version: Optional[str]) -> Dict:
        """
        NEW: Smart completion assessment to avoid "coat tails".
        Analyzes the current state to determine if the project is ready for completion.
        """
        improvements = improvement_analysis.get("improvements", [])
        
        # Categorize improvements by impact and effort
        critical_bugs = [imp for imp in improvements if any(word in imp.lower() for word in ["bug", "error", "critical", "broken", "fix"])]
        major_features = [imp for imp in improvements if any(word in imp.lower() for word in ["feature", "implement", "add", "create"])]
        polish_items = [imp for imp in improvements if any(word in imp.lower() for word in ["polish", "enhance", "optimize", "clean", "refactor", "improve"])]
        
        # Calculate remaining capacity
        remaining_iterations = initial_iterations - iteration_count
        
        self.logger.info(f"Smart completion analysis: {len(critical_bugs)} bugs, {len(major_features)} features, {len(polish_items)} polish items, {remaining_iterations} iterations remaining")
        
        # Smart completion logic
        if remaining_iterations <= 1:
            # Last iteration - focus on completion readiness
            if not critical_bugs and len(major_features) <= 1:
                return {
                    "ready_for_completion": True,
                    "needs_final_iteration": len(major_features) > 0 or len(polish_items) > 0,
                    "reason": "Project ready for completion with optional final polish",
                    "final_plan": {
                        "focus": "completion_and_polish",
                        "tasks": major_features + polish_items[:2]  # Limit polish scope
                    }
                }
            elif critical_bugs:
                return {
                    "ready_for_completion": False,
                    "needs_final_iteration": True,
                    "reason": f"Critical issues must be resolved: {len(critical_bugs)} bugs",
                    "final_plan": {
                        "focus": "critical_fixes",
                        "tasks": critical_bugs
                    }
                }
        
        elif remaining_iterations == 2:
            # Second-to-last iteration - prepare for completion
            total_remaining_work = len(critical_bugs) + len(major_features)
            if total_remaining_work <= 2:
                return {
                    "ready_for_completion": True,
                    "needs_final_iteration": True,
                    "reason": "Entering completion sequence - preparing final iteration",
                    "final_plan": {
                        "focus": "prepare_completion",
                        "tasks": critical_bugs + major_features[:1]
                    }
                }
        
        return {
            "ready_for_completion": False,
            "needs_final_iteration": False,
            "reason": "Substantial work remains - continue normal iteration"
        }

    def _assess_version_completion(self, improvement_analysis: Dict, target_version: str) -> Dict:
        """
        Assess if the target version has been reached (borrowed from VersionedWorkflow logic).
        """
        # This is a simplified version - in a real implementation, this would
        # analyze version files and semantic versioning
        project_state = improvement_analysis.get("project_state", {})
        analysis_text = project_state.get("analysis", "").lower()
        
        # Look for version indicators in the analysis
        version_reached = target_version.lower() in analysis_text or "target version" in analysis_text
        
        return {
            "target_reached": version_reached,
            "current_version": "auto-detected",  # Placeholder
            "progress_to_target": 0.8 if not version_reached else 1.0
        }

    def _assess_adaptive_iterations(self, improvement_analysis: Dict, iteration_count: int, 
                                  initial_iterations: int) -> Dict:
        """
        Assess if iterations should be extended beyond the initial estimate (borrowed from VersionedWorkflow).
        """
        improvements = improvement_analysis.get("improvements", [])
        improvement_count = len(improvements)
        
        # High-value work that justifies extension
        architectural_improvements = [imp for imp in improvements if any(word in imp.lower() for word in ["architecture", "design", "structure", "framework"])]
        security_improvements = [imp for imp in improvements if any(word in imp.lower() for word in ["security", "vulnerability", "safety"])]
        performance_improvements = [imp for imp in improvements if any(word in imp.lower() for word in ["performance", "speed", "optimization", "efficiency"])]
        
        high_value_work = len(architectural_improvements) + len(security_improvements) + len(performance_improvements)
        
        # Extension criteria
        should_extend = (
            iteration_count < initial_iterations * 2 and  # Don't extend beyond 2x original estimate
            high_value_work > 0 and  # Must have high-value work
            improvement_count >= 3  # Must have substantial work remaining
        )
        
        if should_extend:
            estimated_remaining = min(high_value_work, 2)  # Cap extension at 2 iterations
            reason = f"{high_value_work} high-value improvements available (architecture/security/performance)"
        else:
            estimated_remaining = 0
            reason = "No high-value work justifies extension"
        
        return {
            "should_extend": should_extend,
            "estimated_remaining": estimated_remaining,
            "reason": reason,
            "high_value_work_count": high_value_work
        }


class DocumentationAgent(BaseAgent):
    """
    Documentation agent for creating and maintaining project documentation.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None):
        super().__init__(agent_id, agent_type, llm_provider, mcp_manager, config)
    
    def process_task(self, task: Dict) -> Dict:
        """Process documentation tasks."""
        try:
            self.status = "processing"
            goal = task.get("goal", "")
            context = task.get("context", {})
            project_dir = context.get("project_dir")
            
            self.logger.info(f"DOCUMENTATION: Creating docs for goal: {goal[:100]}...")
            
            # Analyze project for documentation needs
            project_analysis = self._analyze_documentation_needs(project_dir) if project_dir else {}
            
            # Generate documentation content
            documentation_content = self._generate_documentation(goal, context, project_analysis)
            
            # Create documentation structure
            doc_structure = self._plan_documentation_structure(documentation_content)
            
            self.status = "completed"
            return {
                "status": "success",
                "agent_type": self.agent_type,
                "project_analysis": project_analysis,
                "documentation_content": documentation_content,
                "documentation_structure": doc_structure,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"DOCUMENTATION: Failed to process task: {e}")
            return self.handle_error(e, task)
    
    def _analyze_documentation_needs(self, project_dir: str) -> Dict:
        """Analyze project to understand documentation requirements."""
        try:
            project_path = self.investigate_project(project_dir)
            
            if self.llm_provider:
                doc_analysis_prompt = f"""
                Analyze this project to understand documentation needs:
                
                PROJECT DIRECTORY: {project_path}
                
                Assess:
                1. Existing documentation and gaps
                2. Code complexity requiring documentation
                3. API endpoints or interfaces needing docs
                4. Setup and installation requirements
                5. Usage examples and tutorials needed
                6. Architecture and design documentation gaps
                
                Identify specific documentation requirements.
                """
                
                analysis = self.llm_provider.generate_text(doc_analysis_prompt, temperature=0.2)
                return {"analysis": analysis, "project_dir": project_path}
                
        except Exception as e:
            self.logger.warning(f"Documentation analysis failed: {e}")
            
        return {"analysis": "Documentation analysis not available", "project_dir": project_dir}
    
    def _generate_documentation(self, goal: str, context: Dict, project_analysis: Dict) -> Dict:
        """Generate comprehensive documentation content using enhanced task execution."""
        result = self.execute_enhanced_task(
            task_description="Generate comprehensive project documentation",
            context={"goal": goal, "context": context, "project_analysis": project_analysis},
            fallback_method=self._basic_documentation_generation
        )
        
        # Process result for backward compatibility
        if result.get("status") == "success":
            doc_content = result.get("result", "Documentation generated")
            
            # Generate README from documentation
            readme_content = self._generate_readme_from_docs(doc_content, goal)
            
            return {
                "full_documentation": doc_content,
                "readme": readme_content,
                "generation_method": result.get("method", "enhanced"),
                "tools_used": result.get("tools_used", [])
            }
        else:
            return {"content": f"Documentation for: {goal}", "generation_method": "error"}
    
    def _basic_documentation_generation(self, task_description: str, context: Dict) -> Dict:
        """Fallback documentation generation using LLM only."""
        goal = context.get("goal", "")
        doc_context = context.get("context", {})
        project_analysis = context.get("project_analysis", {})
        
        if not self.llm_provider:
            return {
                "status": "error",
                "result": "Basic documentation generation requires LLM provider"
            }
        
        doc_generation_prompt = f"""
        Generate comprehensive documentation for this project goal:
        
        GOAL: {goal}
        CONTEXT: {doc_context}
        PROJECT ANALYSIS: {project_analysis.get('analysis', 'None')}
        
        Create documentation including:
        1. Project overview and purpose
        2. Installation and setup instructions
        3. Usage examples and tutorials
        4. API documentation (if applicable)
        5. Architecture and design notes
        6. Troubleshooting and FAQ
        
        Generate clear, comprehensive documentation.
        """
        
        try:
            content = self.llm_provider.generate_text(doc_generation_prompt, temperature=0.3)
            return {
                "status": "success",
                "method": "llm_only",
                "result": content,
                "tools_used": []
            }
        except Exception as e:
            return {
                "status": "error",
                "result": f"Documentation generation failed: {e}"
            }
    
    def _generate_readme_from_docs(self, doc_content: str, goal: str) -> str:
        """Generate README.md from comprehensive documentation."""
        if not self.llm_provider:
            return f"# {goal}\n\nProject documentation will be available soon."
        
        readme_prompt = f"""
        Create a professional README.md file for this project:
        
        GOAL: {goal}
        FULL DOCUMENTATION: {doc_content[:1000]}...
        
        Include:
        - Clear project title and description
        - Installation instructions
        - Quick start guide
        - Basic usage examples
        - Contributing guidelines
        - License information
        
        Format as proper Markdown.
        """
        
        try:
            readme_content = self.llm_provider.generate_text(readme_prompt, temperature=0.2)
            return readme_content
        except Exception as e:
            self.logger.error(f"README generation failed: {e}")
            return f"# {goal}\n\nProject documentation will be available soon."
    
    def _plan_documentation_structure(self, documentation_content: Dict) -> Dict:
        """Plan the organization and structure of documentation files."""
        if not self.llm_provider:
            return {"structure": "docs/README.md"}
        
        structure_prompt = f"""
        Plan the file structure for this documentation:
        
        DOCUMENTATION CONTENT: {str(documentation_content)[:500]}...
        
        Recommend:
        1. Documentation file organization
        2. Directory structure
        3. File naming conventions
        4. Cross-references and navigation
        
        Suggest a logical, maintainable documentation structure.
        """
        
        try:
            structure = self.llm_provider.generate_text(structure_prompt, temperature=0.2)
            
            # Extract file list
            files = ["README.md", "docs/installation.md", "docs/usage.md", "docs/api.md"]
            
            return {
                "structure_plan": structure,
                "recommended_files": files
            }
            
        except Exception as e:
            self.logger.error(f"Documentation structure planning failed: {e}")
            return {"structure_plan": "Standard docs structure", "recommended_files": ["README.md"]} 