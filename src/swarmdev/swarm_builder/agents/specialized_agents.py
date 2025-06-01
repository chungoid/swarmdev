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
        """Plan research approach, using reasoning tools if available."""
        planning_problem = f"""
        Plan a comprehensive research approach for this goal:
        
        GOAL: {goal}
        CONTEXT: {context}
        
        Consider:
        1. What information needs to be gathered
        2. What technologies/libraries should be researched
        3. What documentation sources would be valuable
        4. How to structure the research for maximum effectiveness
        
        Develop a systematic research plan.
        """
        
        # Try reasoning tool if available
        if "sequential-thinking" in self.get_available_mcp_tools():
            reasoning_result = self.call_mcp_tool(
                "sequential-thinking",
                "tools/call",
                {
                    "name": "sequential_thinking",
                    "arguments": {
                        "thought": planning_problem,
                        "nextThoughtNeeded": True,
                        "thoughtNumber": 1,
                        "totalThoughts": 3
                    }
                },
                timeout=20,
                justification="Planning comprehensive research approach"
            )
            
            if reasoning_result and not reasoning_result.get("error"):
                return {"plan": reasoning_result, "method": "mcp_reasoning"}
        
        # LLM planning fallback
        if self.llm_provider:
            planning_prompt = f"""
            Plan a research approach for: {goal}
            
            Context: {context}
            
            Create a structured research plan including:
            1. Information gathering priorities
            2. Technology research needs
            3. Documentation sources to investigate
            4. Research methodology
            
            Return as structured plan.
            """
            
            plan_text = self.llm_provider.generate_text(planning_prompt, temperature=0.3)
            return {"plan": plan_text, "method": "llm_planning"}
        
        return {"plan": "Basic research plan: investigate goal and gather relevant information", "method": "basic"}
    
    def _conduct_research(self, research_plan: Dict, goal: str, context: Dict) -> Dict:
        """
        Conduct comprehensive research based on the research plan using all available tools.
        """
        results = {}
        
        # Get LLM to do basic research  
        research_prompt = f"""
        Conduct comprehensive research for this project:
        
        GOAL: {goal}
        RESEARCH PLAN: {json.dumps(research_plan, indent=2)}
        CONTEXT: {json.dumps(context, indent=2)}
        
        Provide detailed research findings covering:
        1. Technical requirements and considerations
        2. Best practices and patterns
        3. Implementation approaches
        4. Potential challenges and solutions
        5. Tools, libraries, and frameworks needed
        
        Be thorough and provide actionable insights for implementation.
        """
        
        basic_research = self.llm_provider.generate_text(research_prompt, temperature=0.3)
        results["basic_research"] = basic_research
        
        # Use available MCP tools naturally if they would help
        available_tools = self.get_available_mcp_tools()
        if available_tools:
            self.logger.info(f"Enhancing research with available MCP tools: {available_tools}")
            
            # Try documentation tools for frameworks mentioned
            if "context7" in available_tools:
                doc_result = self._try_documentation_lookup(goal, basic_research)
                if doc_result:
                    results["documentation_enhanced"] = doc_result
            
            # Try reasoning tools for complex problems
            if "sequential-thinking" in available_tools:
                reasoning_result = self._try_reasoning_enhancement(goal, research_plan)
                if reasoning_result:
                    results["reasoning_enhanced"] = reasoning_result
            
            # Try web research for latest information  
            if "fetch" in available_tools:
                web_result = self._try_web_research(goal, context)
                if web_result:
                    results["web_enhanced"] = web_result
        
        return results
    
    def _try_documentation_lookup(self, goal: str, basic_research: str) -> Optional[str]:
        """Try to get documentation for technologies mentioned."""
        try:
            # Let LLM identify what docs would be helpful
            doc_prompt = f"""
            Based on this goal and research, what specific technologies, frameworks, or libraries 
            would benefit from up-to-date documentation lookup?
            
            GOAL: {goal}
            RESEARCH: {basic_research[:500]}...
            
            List up to 3 specific technology names that would benefit from current documentation.
            Return only the names, one per line. Examples:
            FastAPI
            React
            SQLAlchemy
            """
            
            tech_response = self.llm_provider.generate_text(doc_prompt, temperature=0.1)
            technologies = [tech.strip() for tech in tech_response.split('\n') if tech.strip()]
            
            # Try to get docs for identified technologies
            doc_results = []
            for tech in technologies[:3]:  # Limit to 3
                if len(tech) > 2 and len(tech) < 50:  # Basic validation
                    result = self.call_mcp_tool(
                        "context7", 
                        "tools/call",
                        {
                            "name": "resolve-library-id",
                            "arguments": {"libraryName": tech}
                        },
                        timeout=15,
                        justification=f"Getting documentation for {tech}"
                    )
                    
                    if result and not result.get("error"):
                        doc_results.append(f"Documentation found for {tech}")
                    
            return f"Documentation lookup for: {', '.join(technologies)}" if doc_results else None
            
        except Exception as e:
            self.logger.warning(f"Documentation lookup failed: {e}")
            return None
    
    def _try_reasoning_enhancement(self, goal: str, research_plan: Dict) -> Optional[str]:
        """Try structured reasoning if it would help."""
        try:
            reasoning_prompt = f"""
            Analyze this research goal systematically:
            
            GOAL: {goal}
            RESEARCH PLAN: {json.dumps(research_plan, indent=2)}
            
            Break down the problem and identify key technical decisions needed.
            """
            
            result = self.call_mcp_tool(
                "sequential-thinking",
                "tools/call", 
                {
                    "name": "sequential_thinking",
                    "arguments": {
                        "thought": reasoning_prompt,
                        "nextThoughtNeeded": True,
                        "thoughtNumber": 1,
                        "totalThoughts": 3
                    }
                },
                timeout=20,
                justification="Using structured reasoning for research analysis"
            )
            
            if result and not result.get("error"):
                return "Structured reasoning analysis completed"
            
        except Exception as e:
            self.logger.warning(f"Reasoning enhancement failed: {e}")
            return None
    
    def _try_web_research(self, goal: str, context: Dict) -> Optional[str]:
        """Try web research if helpful."""
        try:
            result = self.call_mcp_tool(
                "fetch",
                "tools/call",
                {
                    "name": "fetch", 
                    "arguments": {
                        "url": "https://docs.python.org/3/",
                        "method": "GET"
                    }
                },
                timeout=10,
                justification="Testing web research capability"
            )
            
            if result and not result.get("error"):
                return "Web research capability verified"
                
        except Exception as e:
            self.logger.warning(f"Web research failed: {e}")
            return None
    

    
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
        """Create detailed plan using dynamic MCP reasoning tools."""
        planning_problem = f"""
        Create a comprehensive plan for this development goal:
        
        GOAL: {goal}
        CONTEXT: {context}
        PROJECT CONTEXT: {project_context.get('analysis', 'None')}
        
        Think through:
        1. Understanding the requirements and scope
        2. Analyzing the current project state
        3. Identifying necessary components and architecture
        4. Planning the implementation approach
        5. Considering integration and testing strategies
        
        Develop a detailed, actionable plan.
        """
        
        # Use dynamic reasoning capability discovery
        reasoning_result = self.discover_and_use_capability(
            "reasoning",
            planning_problem,
            {"goal": goal, "context": context, "project_context": project_context}
        )
        
        if not reasoning_result.get("error"):
            return {"plan": reasoning_result, "method": "mcp_reasoning"}
        
        # Fallback to LLM planning
        if self.llm_provider:
            planning_prompt = f"""
            Create a detailed implementation plan:
            
            GOAL: {goal}
            CONTEXT: {context}
            PROJECT CONTEXT: {project_context.get('analysis', 'None')}
            
            Include:
            1. Architecture and design considerations
            2. Implementation phases
            3. Component requirements
            4. Integration approach
            5. Testing and validation strategy
            
            Provide a structured, actionable plan.
            """
            
            plan_text = self.llm_provider.generate_text(planning_prompt, temperature=0.3)
            return {"plan": plan_text, "method": "llm_fallback"}
        
        return {"plan": "Basic implementation plan required", "method": "basic"}
    
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
        """Plan implementation approach using LLM analysis."""
        if not self.llm_provider:
            return {"approach": "Basic implementation required", "files": []}
        
        planning_prompt = f"""
        Plan the implementation for this development goal:
        
        GOAL: {goal}
        CONTEXT: {context}
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
            
            # Extract file list from plan
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
            return {"approach": plan, "files": files[:max_files]}
            
        except Exception as e:
            self.logger.error(f"Implementation planning failed: {e}")
            return {"approach": "Direct implementation", "files": ["main.py"]}
    
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
                7. Areas for improvement or expansion
                
                Provide a comprehensive project state analysis.
                """
                
                analysis = self.llm_provider.generate_text(state_prompt, temperature=0.2)
                return {"analysis": analysis, "project_dir": project_path}
                
        except Exception as e:
            self.logger.warning(f"Project state analysis failed: {e}")
            
        return {"analysis": "Project state analysis not available", "project_dir": project_dir}
    
    def _analyze_improvements(self, goal: str, context: Dict, project_state: Dict) -> Dict:
        """Analyze what improvements are needed based on the goal and current state."""
        if not self.llm_provider:
            return {"improvements": ["Basic analysis not available"], "improvement_count": 1}
        
        improvement_prompt = f"""
        Analyze what improvements are needed for this project:
        
        GOAL: {goal}
        CONTEXT: {context}
        PROJECT STATE: {project_state.get('analysis', 'None')}
        
        Identify:
        1. Gaps between current state and desired goal
        2. Missing functionality or features
        3. Code improvements needed
        4. Architectural enhancements
        5. Integration requirements
        6. Documentation needs
        7. Testing requirements
        
        Provide specific, actionable improvement suggestions.
        """
        
        try:
            analysis = self.llm_provider.generate_text(improvement_prompt, temperature=0.3)
            
            # Extract specific improvements
            improvements_prompt = f"""
            From this analysis, extract specific improvement actions:
            
            ANALYSIS: {analysis}
            
            Return a numbered list of specific, actionable improvements.
            """
            
            improvements_response = self.llm_provider.generate_text(improvements_prompt, temperature=0.2)
            improvements = [imp.strip() for imp in improvements_response.split('\n') if imp.strip()]
            
            return {
                "analysis": analysis,
                "improvements": improvements,
                "improvement_count": len(improvements)
            }
        except Exception as e:
            self.logger.error(f"Improvement analysis failed: {e}")
            return {"improvements": ["Analysis failed - manual review needed"], "improvement_count": 1}
    
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
        """Generate comprehensive documentation content."""
        if not self.llm_provider:
            return {"content": "Documentation generation requires LLM provider"}
        
        doc_generation_prompt = f"""
        Generate comprehensive documentation for this project goal:
        
        GOAL: {goal}
        CONTEXT: {context}
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
            
            # Generate specific README content
            readme_prompt = f"""
            Create a professional README.md file for this project:
            
            GOAL: {goal}
            FULL DOCUMENTATION: {content[:1000]}...
            
            Include:
            - Clear project title and description
            - Installation instructions
            - Quick start guide
            - Basic usage examples
            - Contributing guidelines
            - License information
            
            Format as proper Markdown.
            """
            
            readme_content = self.llm_provider.generate_text(readme_prompt, temperature=0.2)
            
            return {
                "full_documentation": content,
                "readme": readme_content,
                "generation_method": "llm"
            }
            
        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            return {"content": f"Documentation for: {goal}", "generation_method": "basic"}
    
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