"""
Specialized Agent implementations for the SwarmDev platform.
Clean, focused implementations using BaseAgent infrastructure.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """
    Research agent for gathering information and analyzing requirements.
    Uses MCP tools for documentation lookup and sequential thinking.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None, memory_manager=None):
        super().__init__(agent_id, agent_type, llm_provider, mcp_manager, config, memory_manager)
    
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
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None, memory_manager=None):
        super().__init__(agent_id, agent_type, llm_provider, mcp_manager, config, memory_manager)
    
    def process_task(self, task: Dict) -> Dict:
        """Process planning tasks using sequential thinking and project analysis with enhanced workflow parameters."""
        try:
            self.status = "processing"
            goal = task.get("goal", "")
            context = task.get("context", {})
            project_dir = context.get("project_dir")
            
            # Extract planning parameters from task.data or task directly
            task_data = task.get("data", {})
            planning_type = task_data.get("planning_type", task.get("planning_type", "standard"))
            use_analysis_results = task_data.get("use_analysis_results", task.get("use_analysis_results", False))
            use_research_results = task_data.get("use_research_results", task.get("use_research_results", False))
            preserve_functionality = task_data.get("preserve_functionality", task.get("preserve_functionality", False))
            plan_incremental_steps = task_data.get("plan_incremental_steps", task.get("plan_incremental_steps", False))
            risk_assessment = task_data.get("risk_assessment", task.get("risk_assessment", False))
            
            target_version = task_data.get("target_version", task.get("target_version"))
            scope_to_current_version = task_data.get("scope_to_current_version", task.get("scope_to_current_version", False))
            plan_version_increment = task_data.get("plan_version_increment", task.get("plan_version_increment", False))
            define_completion_criteria = task_data.get("define_completion_criteria", task.get("define_completion_criteria", False))
            create_version_blueprint = task_data.get("create_version_blueprint", task.get("create_version_blueprint", False))
            plan_iteration_roadmap = task_data.get("plan_iteration_roadmap", task.get("plan_iteration_roadmap", False))
            estimate_effort_distribution = task_data.get("estimate_effort_distribution", task.get("estimate_effort_distribution", False))
            plan_completion_sequence = task_data.get("plan_completion_sequence", task.get("plan_completion_sequence", False))


            self.logger.info(f"PLANNING: Creating '{planning_type}' plan for goal: {goal[:100]}...")
            self.logger.info(f"Use analysis: {use_analysis_results}, Use research: {use_research_results}, Iteration Roadmap: {plan_iteration_roadmap}")

            current_iteration_count = 0 
            iteration_count_from_data = task_data.get("iteration_count")
            iteration_count_from_task_attr = task.get("iteration_count")
            execution_id_str = task.get("execution_id", "")

            if iteration_count_from_data is not None:
                try: current_iteration_count = int(iteration_count_from_data)
                except ValueError: self.logger.warning(f"Could not parse iteration_count '{iteration_count_from_data}' from task.data.")
            elif iteration_count_from_task_attr is not None:
                try: current_iteration_count = int(iteration_count_from_task_attr)
                except ValueError: self.logger.warning(f"Could not parse iteration_count '{iteration_count_from_task_attr}' from task attribute.")
            elif "_cycle_" in execution_id_str:
                try:
                    cycle_part = execution_id_str.split("_cycle_")[1]
                    current_iteration_count = int(cycle_part.split("_")[0])
                except (IndexError, ValueError) as e_parse:
                    self.logger.warning(f"Could not parse iteration_count from execution_id '{execution_id_str}': {e_parse}")
            
            retrieved_previous_iteration_insights: Optional[Dict] = None
            effective_goal = goal 

            if current_iteration_count > 0 and self.memory_manager:
                previous_iteration_count = current_iteration_count - 1
                self.logger.info(f"Retrieving context from previous iteration {previous_iteration_count} for planning.")
                retrieved_iteration_context = self.memory_manager.retrieve_iteration_context(previous_iteration_count)
                
                if retrieved_iteration_context and retrieved_iteration_context.get("analysis_insights"):
                    retrieved_previous_iteration_insights = retrieved_iteration_context.get("analysis_insights")
                    self.logger.debug(f"Retrieved insights from iter {previous_iteration_count}: {str(retrieved_previous_iteration_insights)[:200]}...")
                    evolved_goal_from_memory = retrieved_previous_iteration_insights.get("evolved_goal")
                    if evolved_goal_from_memory:
                        self.logger.info(f"Using evolved goal from previous iteration {previous_iteration_count}: '{evolved_goal_from_memory[:100]}...'")
                        effective_goal = evolved_goal_from_memory 
                    else:
                        self.logger.info(f"No evolved goal found in memory for iter {previous_iteration_count}. Using original goal for this cycle.")
                else:
                    self.logger.warning(f"Could not retrieve analysis insights from previous iteration {previous_iteration_count}.")
            
            project_context_analysis = self._investigate_project_context_enhanced(
                project_dir, preserve_functionality, planning_type
            ) if project_dir else {}
            
            analysis_results_context = {}
            if use_analysis_results:
                analysis_results_context = self._retrieve_analysis_results(context) 
            
            research_results_context = {}
            if use_research_results:
                research_results_context = self._retrieve_research_results(context)
            
            detailed_plan = self._create_detailed_plan_enhanced(
                effective_goal, 
                context, 
                project_context_analysis, 
                analysis_results_context, 
                research_results_context, 
                retrieved_previous_iteration_insights, 
                planning_type, 
                target_version, 
                preserve_functionality,
                current_iteration_count 
            )
            
            task_breakdown = self._break_down_tasks_enhanced(
                detailed_plan, effective_goal, planning_type, plan_incremental_steps
            )
            
            execution_strategy = self._plan_execution_strategy_enhanced(
                task_breakdown, risk_assessment, estimate_effort_distribution # ensure correct param passed
            )
            
            version_plan = {}
            if target_version and (plan_version_increment or create_version_blueprint):
                version_plan = self._create_version_plan(
                    detailed_plan, target_version, scope_to_current_version
                )
            
            completion_plan = {}
            if define_completion_criteria or plan_completion_sequence:
                completion_plan = self._create_completion_plan(
                    task_breakdown, execution_strategy, target_version
                )
            
            self.status = "completed"
            return {
                "status": "success", 
                "agent_type": self.agent_type,
                "detailed_plan": detailed_plan,
                "task_breakdown": task_breakdown,
                "execution_strategy": execution_strategy,
                "project_context": project_context_analysis,
                "timestamp": datetime.now().isoformat(),
                "planning_type": planning_type,
                "analysis_context": analysis_results_context,
                "research_context": research_results_context,
                "version_plan": version_plan,
                "completion_plan": completion_plan,
                "workflow_parameters": {
                    "preserve_functionality": preserve_functionality,
                    "plan_incremental_steps": plan_incremental_steps,
                    "risk_assessment": risk_assessment,
                    "target_version": target_version,
                    "current_iteration_count": current_iteration_count,
                    "retrieved_previous_insights": bool(retrieved_previous_iteration_insights)
                }
            }
            
        except Exception as e:
            self.logger.error(f"PLANNING: Failed to process task: {e}", exc_info=True)
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
    
    # NEW: Enhanced planning methods for iteration workflow
    
    def _investigate_project_context_enhanced(self, project_dir: str, preserve_functionality: bool, planning_type: str) -> Dict:
        """Enhanced project context investigation based on planning parameters."""
        try:
            project_path = self.investigate_project(project_dir)
            
            if self.llm_provider:
                # Build investigation prompt based on parameters
                investigation_focus = []
                if preserve_functionality:
                    investigation_focus.append("- Existing functionality that must be preserved")
                    investigation_focus.append("- Critical components and dependencies")
                    investigation_focus.append("- Integration points that could be affected")
                
                if planning_type == "strategic_iteration":
                    investigation_focus.append("- Architectural patterns and extensibility")
                    investigation_focus.append("- Refactoring opportunities and constraints")
                    investigation_focus.append("- Code organization and modularity")
                
                investigation_prompt = f"""
                Investigate this project directory for {planning_type} planning:
                
                PROJECT DIRECTORY: {project_path}
                PLANNING TYPE: {planning_type}
                PRESERVE FUNCTIONALITY: {preserve_functionality}
                
                Focus on:
                {chr(10).join(investigation_focus) if investigation_focus else "- General project structure"}
                
                Also analyze:
                1. Existing project structure and organization
                2. Technologies and frameworks in use
                3. Current development state
                4. Potential integration points
                5. Constraints or considerations for new development
                
                Provide a structured analysis tailored for {planning_type} planning.
                """
                
                context_analysis = self.llm_provider.generate_text(investigation_prompt, temperature=0.2)
                return {
                    "analysis": context_analysis, 
                    "project_dir": project_path,
                    "planning_type": planning_type,
                    "preserve_functionality": preserve_functionality
                }
                
        except Exception as e:
            self.logger.warning(f"Enhanced project investigation failed: {e}")
            
        return {
            "analysis": "Enhanced project context not available", 
            "project_dir": project_dir,
            "planning_type": planning_type
        }
    
    def _retrieve_analysis_results(self, context: Dict) -> Dict:
        """Retrieve and process analysis results from previous workflow phases."""
        # In a real implementation, this would look up analysis results from the orchestrator
        # For now, we'll extract what we can from the context
        analysis_results = context.get("analysis_results", {})
        
        if not analysis_results and self.llm_provider:
            self.logger.info("No analysis results found in context - planning without analysis input")
        
        return {
            "available": bool(analysis_results),
            "results": analysis_results,
            "project_state": analysis_results.get("project_state", {}),
            "improvements": analysis_results.get("improvements_suggested", [])
        }
    
    def _retrieve_research_results(self, context: Dict) -> Dict:
        """Retrieve and process research results from previous workflow phases."""
        # In a real implementation, this would look up research results from the orchestrator
        research_results = context.get("research_results", {})
        
        if not research_results and self.llm_provider:
            self.logger.info("No research results found in context - planning without research input")
        
        return {
            "available": bool(research_results),
            "results": research_results,
            "findings": research_results.get("findings", {}),
            "synthesis": research_results.get("synthesis", "")
        }
    
    def _create_detailed_plan_enhanced(self, goal: str, context: Dict, project_context: Dict, 
                                     analysis_context: Dict, research_context: Dict,
                                     retrieved_previous_iteration_insights: Optional[Dict], 
                                     planning_type: str, target_version: Optional[str], 
                                     preserve_functionality: bool,
                                     current_iteration_count: int) -> Dict:
        """Create enhanced detailed plan using all available context and workflow parameters."""
        enhanced_context = {
            "goal": goal,
            "context": context,
            "project_context": project_context,
            "analysis_context": analysis_context,
            "research_context": research_context,
            "planning_type": planning_type,
            "target_version": target_version,
            "preserve_functionality": preserve_functionality
        }
        
        result = self.execute_enhanced_task(
            task_description=f"Create a {planning_type} development plan with comprehensive context awareness",
            context=enhanced_context,
            fallback_method=self._basic_detailed_planning_enhanced
        )
        
        # Extract plan from enhanced result
        if result.get("status") == "success":
            plan_content = result.get("result", result)
            return {
                "plan": plan_content, 
                "method": result.get("method", "enhanced"),
                "planning_type": planning_type,
                "context_used": {
                    "analysis_available": analysis_context.get("available", False),
                    "research_available": research_context.get("available", False),
                    "project_context": bool(project_context.get("analysis")),
                    "target_version": target_version
                }
            }
        else:
            return {"plan": "Enhanced planning failed", "method": "error", "planning_type": planning_type}
    
    def _basic_detailed_planning_enhanced(self, task_description: str, context: Dict) -> Dict:
        """Enhanced fallback detailed planning with workflow awareness."""
        goal = context.get("goal", "")
        planning_context = context.get("context", {})
        project_context = context.get("project_context", {})
        analysis_context = context.get("analysis_context", {})
        research_context = context.get("research_context", {})
        planning_type = context.get("planning_type", "standard")
        target_version = context.get("target_version")
        preserve_functionality = context.get("preserve_functionality", False)
        
        if not self.llm_provider:
            return {
                "status": "error",
                "result": "Enhanced planning requires LLM provider"
            }
        
        # Build planning guidance based on type
        planning_guidance = {
            "strategic_iteration": "Focus on incremental improvements and strategic refactoring. Plan for existing codebase integration.",
            "standard": "Plan comprehensive implementation with clear phases and dependencies.",
            "incremental": "Plan small, manageable changes that can be implemented safely."
        }
        
        # Build context sections
        context_sections = []
        if analysis_context.get("available"):
            context_sections.append(f"ANALYSIS RESULTS: {analysis_context.get('improvements', [])}")
        if research_context.get("available"):
            context_sections.append(f"RESEARCH FINDINGS: {research_context.get('synthesis', '')}")
        
        planning_prompt = f"""
        Create a {planning_type} implementation plan:
        
        GOAL: {goal}
        PLANNING TYPE: {planning_type}
        GUIDANCE: {planning_guidance.get(planning_type, "Standard planning approach")}
        {f"TARGET VERSION: {target_version}" if target_version else ""}
        PRESERVE FUNCTIONALITY: {preserve_functionality}
        
        CONTEXT: {planning_context}
        PROJECT CONTEXT: {project_context.get('analysis', 'None')}
        
        {chr(10).join(context_sections) if context_sections else ""}
        
        Include:
        1. Architecture and design considerations {"(preserving existing functionality)" if preserve_functionality else ""}
        2. Implementation phases {"(incremental steps)" if planning_type == "strategic_iteration" else ""}
        3. Component requirements and integration approach
        4. {"Risk assessment and mitigation strategies" if preserve_functionality else "Risk considerations"}
        5. Testing and validation strategy
        {"6. Version-specific requirements and compatibility" if target_version else ""}
        
        Provide a structured, actionable plan optimized for {planning_type}.
        """
        
        try:
            plan = self.llm_provider.generate_text(planning_prompt, temperature=0.3)
            return {
                "status": "success",
                "method": "llm_enhanced",
                "result": plan,
                "tools_used": []
            }
        except Exception as e:
            return {
                "status": "error",
                "result": f"Enhanced planning failed: {e}"
            }
    
    def _break_down_tasks_enhanced(self, detailed_plan: Dict, goal: str, planning_type: str, plan_incremental_steps: bool) -> List[Dict]:
        """Enhanced task breakdown based on planning type and parameters."""
        if not self.llm_provider:
            return [{"task": "Implement solution", "type": "development", "priority": "high"}]
        
        # Build breakdown guidance based on planning type
        breakdown_guidance = {
            "strategic_iteration": "Break down into incremental, safe refactoring steps that preserve existing functionality.",
            "standard": "Create comprehensive development tasks covering all aspects of implementation.",
            "incremental": "Focus on small, manageable incremental changes."
        }
        
        breakdown_prompt = f"""
        Break down this {planning_type} plan into specific, actionable tasks:
        
        GOAL: {goal}
        PLANNING TYPE: {planning_type}
        GUIDANCE: {breakdown_guidance.get(planning_type, "Standard task breakdown")}
        DETAILED PLAN: {detailed_plan.get('plan', '')}
        INCREMENTAL STEPS: {plan_incremental_steps}
        
        Create tasks that are:
        1. Specific and actionable
        2. {"Incremental and safe for existing codebase" if planning_type == "strategic_iteration" else "Appropriately scoped"}
        3. Clearly defined with success criteria
        4. Categorized by type (analysis, design, development, testing, refactoring)
        5. Prioritized (critical, high, medium, low)
        {"6. Ordered for incremental implementation" if plan_incremental_steps else ""}
        
        For {planning_type} planning, focus on {"incremental improvements" if planning_type == "strategic_iteration" else "comprehensive implementation"}.
        
        Return as a JSON array of task objects with fields: task, description, type, priority, estimated_effort, dependencies.
        """
        
        try:
            response = self.llm_provider.generate_text(breakdown_prompt, temperature=0.2)
            
            # Try to parse JSON response
            try:
                tasks = json.loads(response.strip())
                if isinstance(tasks, list):
                    return tasks[:12]  # Limit to 12 tasks for manageability
            except:
                pass
            
            # Fallback: parse text response with enhanced categorization
            lines = response.strip().split('\n')
            tasks = []
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('```'):
                    task_type = "development"
                    if any(word in line.lower() for word in ["refactor", "restructure", "reorganize"]):
                        task_type = "refactoring"
                    elif any(word in line.lower() for word in ["analyze", "review", "assess"]):
                        task_type = "analysis"
                    elif any(word in line.lower() for word in ["test", "validate", "verify"]):
                        task_type = "testing"
                    
                    tasks.append({
                        "task": line.strip(),
                        "description": f"Task {i+1} from {planning_type} plan breakdown",
                        "type": task_type,
                        "priority": "high" if planning_type == "strategic_iteration" else "medium",
                        "estimated_effort": "TBD"
                    })
            
            return tasks[:12]  # Limit for manageability
            
        except Exception as e:
            self.logger.error(f"Enhanced task breakdown failed: {e}")
            return [{"task": f"Implement solution according to {planning_type} plan", "type": "development", "priority": "high"}]
    
    def _plan_execution_strategy_enhanced(self, task_breakdown: List[Dict], risk_assessment: bool, estimate_effort_distribution: bool) -> Dict:
        """Enhanced execution strategy planning with risk assessment and effort estimation."""
        if not self.llm_provider:
            return {"strategy": "Execute tasks in order", "risk_level": "unknown"}
        
        strategy_prompt = f"""
        Plan an enhanced execution strategy for these tasks:
        
        TASKS: {json.dumps(task_breakdown, indent=2)}
        RISK ASSESSMENT REQUIRED: {risk_assessment}
        EFFORT ESTIMATION REQUIRED: {estimate_effort_distribution}
        
        Consider:
        1. Task dependencies and sequencing
        2. Parallel execution opportunities
        3. {"Risk mitigation and safety measures" if risk_assessment else "Basic risk considerations"}
        4. Resource requirements and constraints
        5. {"Detailed effort distribution and timeline" if estimate_effort_distribution else "Timeline estimation"}
        6. Validation and testing integration
        
        {"Provide detailed risk analysis and mitigation strategies." if risk_assessment else ""}
        {"Include effort estimates and resource allocation planning." if estimate_effort_distribution else ""}
        
        Provide a comprehensive execution strategy.
        """
        
        try:
            strategy = self.llm_provider.generate_text(strategy_prompt, temperature=0.3)
            return {
                "strategy": strategy, 
                "total_tasks": len(task_breakdown),
                "risk_assessment_included": risk_assessment,
                "effort_estimation_included": estimate_effort_distribution
            }
        except Exception as e:
            self.logger.error(f"Enhanced execution strategy planning failed: {e}")
            return {"strategy": "Enhanced sequential execution with monitoring", "total_tasks": len(task_breakdown)}
    
    def _create_version_plan(self, detailed_plan: Dict, target_version: str, scope_to_current_version: bool) -> Dict:
        """Create version-specific planning for target version."""
        if not self.llm_provider:
            return {"target_version": target_version, "plan": "Version planning not available"}
        
        version_prompt = f"""
        Create a version-specific plan for reaching target version {target_version}:
        
        DETAILED PLAN: {detailed_plan.get('plan', '')}
        TARGET VERSION: {target_version}
        SCOPE TO CURRENT VERSION: {scope_to_current_version}
        
        Plan:
        1. Version increment strategy (major, minor, patch)
        2. Breaking changes assessment
        3. Backward compatibility considerations
        4. Version-specific requirements
        5. Release readiness criteria
        6. Migration path for existing users
        
        Provide a structured version roadmap.
        """
        
        try:
            version_plan = self.llm_provider.generate_text(version_prompt, temperature=0.2)
            return {
                "target_version": target_version,
                "plan": version_plan,
                "scope_limited": scope_to_current_version
            }
        except Exception as e:
            self.logger.error(f"Version planning failed: {e}")
            return {"target_version": target_version, "plan": "Version planning failed"}
    
    def _create_completion_plan(self, task_breakdown: List[Dict], execution_strategy: Dict, target_version: Optional[str]) -> Dict:
        """Create completion criteria and sequence planning."""
        if not self.llm_provider:
            return {"completion_criteria": "Standard completion", "sequence": "Sequential"}
        
        completion_prompt = f"""
        Create a completion plan based on the task breakdown and execution strategy:
        
        TASKS: {json.dumps(task_breakdown[:5], indent=2)}... (showing first 5 of {len(task_breakdown)})
        EXECUTION STRATEGY: {execution_strategy.get('strategy', '')[:500]}...
        {f"TARGET VERSION: {target_version}" if target_version else ""}
        
        Define:
        1. Completion criteria for each phase
        2. Success metrics and validation points
        3. Final acceptance criteria
        4. Completion sequence and dependencies
        5. {"Version release criteria" if target_version else "Project completion criteria"}
        
        Provide clear completion planning.
        """
        
        try:
            completion_plan = self.llm_provider.generate_text(completion_prompt, temperature=0.2)
            return {
                "completion_criteria": completion_plan,
                "total_tasks": len(task_breakdown),
                "target_version": target_version
            }
        except Exception as e:
            self.logger.error(f"Completion planning failed: {e}")
            return {"completion_criteria": "Standard sequential completion", "total_tasks": len(task_breakdown)}


class DevelopmentAgent(BaseAgent):
    """
    Development agent for implementing code and creating files.
    Uses planning results from PlanningAgent and implements using MCP filesystem tools.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None, memory_manager=None):
        super().__init__(agent_id, agent_type, llm_provider, mcp_manager, config, memory_manager)
    
    def process_task(self, task: Dict) -> Dict:
        """Process development tasks by implementing the planning results."""
        try:
            self.status = "processing"
            goal = task.get("goal", "")
            context = task.get("context", {})
            project_dir = context.get("project_dir", ".")
            
            self.logger.info(f"DEVELOPMENT: Implementing goal: {goal[:100]}...")
            
            # Determine iteration_count
            iteration_count = 0 # Default
            iteration_count_from_data = task.get("data", {}).get("iteration_count")
            iteration_count_from_task_attr = task.get("iteration_count")
            execution_id_str = task.get("execution_id", "")

            if iteration_count_from_data is not None:
                try:
                    iteration_count = int(iteration_count_from_data)
                except ValueError:
                    self.logger.warning(f"Could not parse iteration_count '{iteration_count_from_data}' from task.data.")
            elif iteration_count_from_task_attr is not None:
                try:
                    iteration_count = int(iteration_count_from_task_attr)
                except ValueError:
                    self.logger.warning(f"Could not parse iteration_count '{iteration_count_from_task_attr}' from task attribute.")
            elif "_cycle_" in execution_id_str:
                try:
                    cycle_part = execution_id_str.split("_cycle_")[1]
                    iteration_count = int(cycle_part.split("_")[0])
                except (IndexError, ValueError) as e_parse:
                    self.logger.warning(f"Could not parse iteration_count from execution_id '{execution_id_str}': {e_parse}")
            
            # Determine short_parent_task_id (e.g., "smart_implementation")
            full_task_id = task.get("task_id", "") # Orchestrator sets this to the full unique task ID
            task_execution_id_prefix = execution_id_str + "_"
            short_parent_task_id = full_task_id.replace(task_execution_id_prefix, "", 1) if full_task_id.startswith(task_execution_id_prefix) else full_task_id
            if short_parent_task_id == full_task_id and execution_id_str in full_task_id:
                parts = full_task_id.split(execution_id_str + "_")
                if len(parts) > 1:
                    short_parent_task_id = parts[1]

            self.logger.debug(f"Dev task context: iteration_count={iteration_count}, short_parent_task_id='{short_parent_task_id}'")

            planning_results = context.get("planning_results", {})
            research_results = context.get("research_results", {})
            
            task_breakdown = planning_results.get("task_breakdown", [])
            
            if not task_breakdown:
                # If no breakdown, attempt to generate a single implementation task based on the goal
                self.logger.critical("CRITICAL: No task breakdown from planning results. Development cannot proceed without a plan. Task will fail.")
                # This is a simplified fallback. Ideally, planning should always provide tasks.
                # Create a pseudo task for _determine_file_for_task
                # pseudo_task_for_file_gen = {
                # "task": goal, # Use the main goal as the task description
                # "type": "development"
                # }
                # file_info = self._determine_file_for_task(pseudo_task_for_file_gen, project_dir, goal, iteration_count)
                # if file_info:
                # implementation_results = self._implement_single_task(file_info, project_dir, goal, planning_results, iteration_count, short_parent_task_id, is_direct_info=True)
                # else:
                # raise Exception("No task breakdown from planning results and failed to generate direct file info.")
                raise Exception("No task breakdown from planning results. Development cannot proceed.")
            else:
                self.logger.info(f"Implementing {len(task_breakdown)} tasks from planning results")
                implementation_results = self._implement_planned_tasks(
                    task_breakdown, project_dir, goal, planning_results, research_results,
                    iteration_count, short_parent_task_id
                )
            
            self.status = "completed"
            return {
                "status": "success",
                "agent_type": self.agent_type,
                "files_created": implementation_results["files_created"],
                "files_modified": implementation_results["files_modified"],
                "implementation_summary": implementation_results["summary"],
                "tasks_completed": len(task_breakdown),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"DEVELOPMENT: Failed to process task: {e}")
            return self.handle_error(e, task)
    
    def _implement_planned_tasks(self, task_breakdown: List[Dict], project_dir: str, 
                               goal: str, planning_results: Dict, research_results: Dict,
                               iteration_count: int, short_parent_task_id: str) -> Dict:
        """Implement the planned tasks directly using MCP filesystem tools."""
        files_created = []
        files_modified = []
        implementation_summary = []
        
        self.logger.info(f"Starting implementation of {len(task_breakdown)} tasks")
        
        for i, task in enumerate(task_breakdown):
            task_name = task.get("task", f"Task {i+1}")
            task_type = task.get("type", "development")
            
            self.logger.info(f"Implementing task {i+1}/{len(task_breakdown)}: {task_name}")
            
            try:
                # Generate implementation for this specific task
                # _determine_file_for_task needs a task dict from task_breakdown
                file_info = self._determine_file_for_task(task, project_dir, goal, iteration_count)
                if not file_info:
                    self.logger.warning(f"Could not determine file for sub-task '{task_name}'. Skipping.")
                    implementation_summary.append({
                        "task": task_name,
                        "status": "skipped",
                        "reason": "Could not determine file information from LLM."
                    })
                    continue
                
                task_result = self._implement_single_task(file_info, project_dir, goal, planning_results, iteration_count, short_parent_task_id, is_direct_info=True)
                
                files_created.extend(task_result.get("files_created", []))
                files_modified.extend(task_result.get("files_modified", []))
                implementation_summary.append({
                    "task": task_name,
                    "status": "completed",
                    "files": task_result.get("files_created", []) + task_result.get("files_modified", [])
                })
                
            except Exception as e:
                self.logger.error(f"Failed to implement task '{task_name}': {e}")
                implementation_summary.append({
                    "task": task_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        self.logger.info(f"Implementation complete: {len(files_created)} files created, {len(files_modified)} files modified")
        
        return {
            "files_created": files_created,
            "files_modified": files_modified,
            "summary": implementation_summary
        }
    
    def _implement_single_task(self, file_info_or_sub_task_dict: Dict, project_dir: str, goal: str, planning_results: Dict, 
                               iteration_count: int, short_parent_task_id: str, is_direct_info: bool = False) -> Dict:
        """Implement a single task from the task breakdown or direct file_info."""
        
        if is_direct_info:
            file_info = file_info_or_sub_task_dict
        else:
            # This case might be deprecated if _determine_file_for_task is always called before
            sub_task_dict = file_info_or_sub_task_dict
            task_name = sub_task_dict.get("task", "Unknown sub-task")
            self.logger.debug(f"Determining file for sub-task: {task_name}")
            file_info = self._determine_file_for_task(sub_task_dict, project_dir, goal)

        if not file_info:
            self.logger.warning("No file information determined for task. Cannot implement.")
            return {"files_created": [], "files_modified": []}
        
        file_path = file_info["path"]
        file_content = file_info["content"]
        action = file_info["action"]  # "create" or "modify"
        
        # Convert to workspace path for MCP filesystem
        workspace_file_path = self._to_workspace_path(file_path)
        
        # Ensure directory exists (create recursively if needed)
        dir_path = os.path.dirname(workspace_file_path)
        if dir_path and dir_path != "." and dir_path != "/workspace":
            self._create_directory_recursive(dir_path, iteration_count, short_parent_task_id)
        
        # Write the file
        write_result = self.call_mcp_tool("filesystem", "write_file", {
            "path": workspace_file_path,
            "content": file_content
        })
        
        if not self._is_mcp_error(write_result):
            self.logger.info(f"Successfully {action}d file: {file_path}")
            
            # Log file operation to memory
            if self.memory_manager:
                content_summary = (file_content[:200] + '...') if len(file_content) > 200 else file_content
                self.memory_manager.store_file_operation(
                    iteration_count=iteration_count,
                    file_path=file_path, # Use the original, possibly relative path for logging consistency
                    operation=action,
                    task_id=short_parent_task_id, # Log against the parent dev task
                    content_summary=content_summary
                )
                self.logger.debug(f"Stored file op in memory: iter={iteration_count}, path={file_path}, op={action}, task_id={short_parent_task_id}")

            if action == "create":
                return {"files_created": [file_path], "files_modified": []}
            else:
                return {"files_created": [], "files_modified": [file_path]}
        else:
            error_msg = self._extract_mcp_error(write_result)
            raise Exception(f"Failed to write file {file_path}: {error_msg}")
    
    def _to_workspace_path(self, file_path: str) -> str:
        """Convert a relative or absolute path to a workspace path for MCP filesystem."""
        # If already a workspace path, return as-is
        if file_path.startswith("/workspace/"):
            return file_path
        
        # If absolute path, make it relative to workspace
        if os.path.isabs(file_path):
            # Convert absolute path to relative from current directory
            try:
                file_path = os.path.relpath(file_path, os.getcwd())
            except ValueError:
                # If paths are on different drives (Windows), use basename
                file_path = os.path.basename(file_path)
        
        # Remove leading ./ if present
        if file_path.startswith("./"):
            file_path = file_path[2:]
        
        # Prepend /workspace/
        return f"/workspace/{file_path}"
    
    def _is_mcp_error(self, mcp_result: Dict) -> bool:
        """Check if an MCP result indicates an error."""
        # Check for direct error key
        if mcp_result.get("error"):
            return True
        
        # Check for result.isError pattern
        result = mcp_result.get("result", {})
        if isinstance(result, dict) and result.get("isError", False):
            return True
        
        # If no result key at all, consider it an error
        if "result" not in mcp_result:
            return True
        
        return False
    
    def _extract_mcp_error(self, mcp_result: Dict) -> str:
        """Extract error message from MCP result."""
        # Check for direct error
        if mcp_result.get("error"):
            return str(mcp_result["error"])
        
        # Check for result.content error pattern
        result = mcp_result.get("result", {})
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                first_content = content[0]
                if isinstance(first_content, dict) and "text" in first_content:
                    return first_content["text"]
        
        # Fallback
        return "Unknown MCP error"
    
    def _determine_file_for_task(self, task: Dict, project_dir: str, goal: str, iteration_count: int) -> Optional[Dict]:
        """Determine what file to create/modify for a given task, handling potential conflicts using memory."""
        if not self.llm_provider:
            self.logger.warning("LLM provider not available, cannot determine file for task.")
            return None
        
        task_name = task.get("task", "")
        task_type = task.get("type", "development")

        context_summary_for_llm = "None available."
        if self.memory_manager and iteration_count > 0:
            try:
                self.logger.debug(f"Retrieving context from iteration {iteration_count - 1} for DevAgent task '{task_name}'.")
                # We want insights from the analysis phase of the *previous* iteration.
                previous_iteration_context = self.memory_manager.retrieve_iteration_context(iteration_count - 1)
                
                project_evolution_insights = previous_iteration_context.get("project_evolution", [])
                target_analysis_entity_name = f"analysis_{self.memory_manager.project_id}_{iteration_count - 1}"
                
                found_insights = []
                for analysis_entity_data in project_evolution_insights:
                    if analysis_entity_data.get("entity_name") == target_analysis_entity_name:
                        self.logger.debug(f"Found analysis entity for iteration {iteration_count - 1}: {target_analysis_entity_name}")
                        observations = analysis_entity_data.get("observations", [])
                        evolved_goal_obs = "Evolved Goal: Not found in observations."
                        improvement_obs = []
                        for obs_line in observations:
                            if obs_line.startswith("Evolved Goal:"):
                                evolved_goal_obs = obs_line
                            elif obs_line.startswith("Improvement"):
                                improvement_obs.append(obs_line)
                        
                        if evolved_goal_obs != "Evolved Goal: Not found in observations." or improvement_obs:
                            found_insights.append(f"Insights from previous analysis (iteration {iteration_count - 1}):")
                            found_insights.append(evolved_goal_obs)
                            found_insights.extend(improvement_obs[:3]) # Max 3 improvements in prompt
                        break 
                
                if found_insights:
                    context_summary_for_llm = "\n".join(found_insights)
                else:
                    self.logger.debug(f"No specific analysis insights found for iter {iteration_count - 1} in project_evolution data.")
            except Exception as e_mem_ctx:
                self.logger.warning(f"Error retrieving context from memory for DevAgent: {e_mem_ctx}", exc_info=True)
                context_summary_for_llm = "Error retrieving context from memory."
        
        initial_file_prompt = f"""
        Determine the file to create or modify for this development task:
        
        TASK: {task_name}
        TASK TYPE: {task_type}
        GOAL: {goal}
        PROJECT DIRECTORY (base for relative paths): {project_dir}

        ADDITIONAL CONTEXT FROM PREVIOUS ITERATION ANALYSIS:
        {context_summary_for_llm}
        
        Suggest a single file operation. Respond with EXACTLY this format:
        
        FILE_PATH: relative/path/to/file.py  (e.g., src/utils/helpers.py or README.md)
        ACTION: create OR modify
        CONTENT:
        [actual file content here - RAW CODE ONLY, NO MARKDOWN FORMATTING]
        
        Rules:
        - FILE_PATH should be relative to the PROJECT DIRECTORY.
        - Use appropriate file extensions.
        - Place files in logical directories (e.g. src/, tests/, docs/).
        - If modifying, assume you have the original content and provide the new COMPLETE content.
        - Generate complete, functional code with necessary imports and structure.
        - Make the code production-ready.
        - DO NOT use markdown code fences (```) in the file content.
        - Provide ONLY the raw file content after CONTENT:.
        
        Focus on implementing the specific task functionality.
        """
        
        try:
            raw_llm_response = self.llm_provider.generate_text(initial_file_prompt, temperature=0.2)
            parsed_info = self._parse_file_response(raw_llm_response, project_dir)

            if not parsed_info:
                self.logger.warning(f"Could not parse initial LLM response for task '{task_name}'. Response: {raw_llm_response[:200]}...")
                return None

            prospective_file_path_abs_or_rel = parsed_info["path"] 
            prospective_action = parsed_info["action"]
            prospective_content = parsed_info["content"]

            if self.memory_manager:
                path_for_memory_lookup: str
                abs_project_dir = os.path.abspath(project_dir)
                
                if os.path.isabs(prospective_file_path_abs_or_rel):
                    if prospective_file_path_abs_or_rel.startswith(abs_project_dir):
                        path_for_memory_lookup = os.path.relpath(prospective_file_path_abs_or_rel, abs_project_dir)
                    else:
                        self.logger.warning(f"Prospective path {prospective_file_path_abs_or_rel} is absolute but not in project dir {abs_project_dir}. Using basename for memory lookup.")
                        path_for_memory_lookup = os.path.basename(prospective_file_path_abs_or_rel)
                else:
                    path_for_memory_lookup = prospective_file_path_abs_or_rel
                
                path_for_memory_lookup = path_for_memory_lookup.replace(os.sep, '/')
                if path_for_memory_lookup.startswith("./"):
                    path_for_memory_lookup = path_for_memory_lookup[2:]

                self.logger.debug(f"Checking memory for file: '{path_for_memory_lookup}' (derived from: '{prospective_file_path_abs_or_rel}', project_dir: '{project_dir}')")
                file_history = self.memory_manager.get_file_conflict_context(path_for_memory_lookup)

                if file_history.get("exists"):
                    if prospective_action == "create":
                        self.logger.info(f"Conflict: Task '{task_name}' wants to CREATE '{path_for_memory_lookup}' which exists. History: {file_history}")
                        
                        conflict_resolution_prompt = f"""
                        You are an intelligent development agent. You planned to CREATE the file '{path_for_memory_lookup}' for the task '{task_name}'.
                        However, this file ALREADY EXISTS.
                        
                        File History from Memory:
                        - Path: {path_for_memory_lookup}
                        - Last Operation: {file_history.get('last_operation', 'N/A')}
                        - Last Modified Iteration: {file_history.get('last_iteration', 'N/A')}
                        - Previous Content Summary (if available): {file_history.get('content_summary', 'N/A')}
                        
                        Your original suggested content for CREATION was:
                        ---
                        {prospective_content}
                        ---
                        
                        How do you want to resolve this conflict? The project goal is: {goal}
                        Respond with EXACTLY this format (path relative to project root):
                        
                        FILE_PATH: relative/path/to/file.py
                        ACTION: overwrite OR modify OR rename_new OR skip
                        CONTENT:
                        [Your new content here. If skipping, write SKIP_CONTENT. If renaming, this is content for the NEW file.]
                        
                        Options:
                        - overwrite: Replace existing file with new content.
                        - modify: Provide NEW FULL content for '{path_for_memory_lookup}', considering its history.
                        - rename_new: Create a NEW file (e.g., '{os.path.splitext(path_for_memory_lookup)[0]}_new{os.path.splitext(path_for_memory_lookup)[1]}'). Provide its content.
                        - skip: Do not create or modify this file.
                        """
                        self.logger.debug(f"Sending conflict resolution prompt for {path_for_memory_lookup}")
                        conflict_llm_response = self.llm_provider.generate_text(conflict_resolution_prompt, temperature=0.3)
                        resolved_info = self._parse_file_response(conflict_llm_response, project_dir)

                        if not resolved_info or resolved_info.get("action") == "skip" or resolved_info.get("content","").strip().upper() == "SKIP_CONTENT":
                            self.logger.info(f"Skipping file operation for '{path_for_memory_lookup}' based on conflict resolution.")
                            return None 
                        
                        self.logger.info(f"Conflict for '{path_for_memory_lookup}' resolved. New action: '{resolved_info.get('action')}', New path (abs/rel from parse): '{resolved_info.get('path')}'")
                        return resolved_info 

                    elif prospective_action == "modify":
                        self.logger.info(f"Task '{task_name}' intends to MODIFY existing file '{path_for_memory_lookup}'. History available: {file_history}. Re-prompting LLM for context-aware modification.")
                        
                        modification_with_history_prompt = f"""
                        You are an intelligent development agent. Your task is '{task_name}' and you initially decided to MODIFY the file '{path_for_memory_lookup}'.
                        
                        File History from Memory:
                        - Path: {path_for_memory_lookup}
                        - Last Operation: {file_history.get('last_operation', 'N/A')}
                        - Last Modified Iteration: {file_history.get('last_iteration', 'N/A')}
                        - Previous Content Summary (if available): {file_history.get('content_summary', 'N/A')}
                        
                        Your initial suggested new content for the file was:
                        ---
                        {prospective_content}
                        ---
                        
                        Considering the file's history and your initial plan, provide the FINAL new and complete content for '{path_for_memory_lookup}'.
                        The project goal is: {goal}
                        
                        Respond with EXACTLY this format (path relative to project root):
                        
                        FILE_PATH: {path_for_memory_lookup}
                        ACTION: modify
                        CONTENT:
                        [Your final, complete new content here, taking history into account.]
                        
                        Ensure the content is complete and production-ready.
                        """
                        self.logger.debug(f"Sending modification-with-history prompt for {path_for_memory_lookup}")
                        modification_llm_response = self.llm_provider.generate_text(modification_with_history_prompt, temperature=0.25)
                        # Parse the response. The FILE_PATH and ACTION should ideally remain the same.
                        modified_info = self._parse_file_response(modification_llm_response, project_dir)

                        if not modified_info or modified_info.get("action") == "skip" or modified_info.get("content","").strip().upper() == "SKIP_CONTENT":
                            self.logger.warning(f"LLM decided to skip modification for '{path_for_memory_lookup}' after reviewing history, or response was invalid.")
                            return None
                        
                        # Ensure the action is still 'modify' and path hasn't unexpectedly changed
                        if modified_info.get("action") != "modify" or modified_info.get("path") != prospective_file_path_abs_or_rel:
                             self.logger.warning(f"LLM changed action/path unexpectedly during context-aware modify. Expected: modify '{prospective_file_path_abs_or_rel}', Got: {modified_info.get('action')} '{modified_info.get('path')}'. Proceeding with LLM's decision.")
                        
                        self.logger.info(f"Modification for '{path_for_memory_lookup}' refined with history. Action: '{modified_info.get('action')}', Path: '{modified_info.get('path')}'")
                        return modified_info # Return the content refined with history

            return parsed_info # No memory manager, or no conflict, or file didn't exist for modify intent

        except Exception as e:
            self.logger.error(f"Failed to determine file for task '{task_name}': {e}", exc_info=True)
            return None
    
    def _parse_file_response(self, response: str, project_dir: str) -> Optional[Dict]:
        """Parse the LLM response to extract file information."""
        lines = response.strip().split('\n')
        
        file_path = None
        action = "create"
        content_start = -1
        
        for i, line in enumerate(lines):
            if line.startswith("FILE_PATH:"):
                file_path = line.replace("FILE_PATH:", "").strip()
            elif line.startswith("ACTION:"):
                action = line.replace("ACTION:", "").strip()
            elif line.startswith("CONTENT:"):
                content_start = i + 1
                break
        
        if not file_path or content_start == -1:
            return None
        
        # Extract content
        content_lines = lines[content_start:]
        content = '\n'.join(content_lines).strip()
        
        # Clean up any markdown formatting that might have slipped through
        content = self._clean_file_content(content)
        
        # Make path absolute if relative
        if not os.path.isabs(file_path):
            if project_dir == "." or project_dir.startswith("./"):
                full_path = file_path
            else:
                full_path = os.path.join(project_dir, file_path)
        else:
            full_path = file_path
        
        return {
            "path": full_path,
            "content": content,
            "action": action
        }
    
    def _clean_file_content(self, content: str) -> str:
        """Clean file content by removing markdown formatting and other artifacts."""
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip markdown code fence lines
            if line.strip().startswith('```') and (
                line.strip() == '```' or 
                line.strip().startswith('```python') or
                line.strip().startswith('```javascript') or
                line.strip().startswith('```json') or
                line.strip().startswith('```yaml') or
                line.strip().startswith('```markdown') or
                line.strip().startswith('```bash') or
                line.strip().startswith('```sh')
            ):
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _create_directory_recursive(self, dir_path: str, iteration_count: int, task_id_for_memory: str) -> None:
        """Create directory recursively, ensuring all parent directories exist."""
        # Normalize the path
        dir_path = dir_path.rstrip('/')
        
        # Skip if it's the workspace root
        if dir_path == "/workspace" or dir_path == "":
            return
            
        # Check if directory already exists
        check_result = self.call_mcp_tool("filesystem", "list_files", {"path": dir_path})
        if not self._is_mcp_error(check_result):
            # Directory exists, we're done
            return
            
        # Get parent directory
        parent_dir = os.path.dirname(dir_path)
        
        # Recursively create parent if needed
        if parent_dir and parent_dir != "/workspace" and parent_dir != dir_path:
            self._create_directory_recursive(parent_dir, iteration_count, task_id_for_memory)
        
        # Now create this directory
        create_result = self.call_mcp_tool("filesystem", "create_directory", {"path": dir_path})
        if self._is_mcp_error(create_result):
            error_msg = self._extract_mcp_error(create_result)
            raise Exception(f"Failed to create directory {dir_path}: {error_msg}")
        
        self.logger.debug(f"Created directory: {dir_path}")

        if self.memory_manager:
            relative_dir_path = dir_path
            if relative_dir_path.startswith("/workspace/"):
                relative_dir_path = relative_dir_path[len("/workspace/"):]
            elif relative_dir_path.startswith("workspace/"):
                relative_dir_path = relative_dir_path[len("workspace/"):]
            relative_dir_path = relative_dir_path.strip('/')

            if relative_dir_path:
                self.memory_manager.store_directory_operation(
                    iteration_count=iteration_count,
                    dir_path=relative_dir_path,
                    operation="create",
                    task_id=task_id_for_memory
                )
                self.logger.debug(f"Stored directory creation in memory: iter={iteration_count}, path={relative_dir_path}, task_id={task_id_for_memory}")
            else:
                self.logger.warning(f"Skipping memory log for root-level directory creation: {dir_path}")

class DocumentationAgent(BaseAgent):
    """
    Documentation agent for creating and maintaining project documentation.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None, memory_manager=None):
        super().__init__(agent_id, agent_type, llm_provider, mcp_manager, config, memory_manager)
    
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


class AnalysisAgent(BaseAgent):
    """
    Analysis agent for project state analysis and improvement recommendations.
    Central to iteration workflows and continuous improvement processes.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None, memory_manager=None):
        super().__init__(agent_id, agent_type, llm_provider, mcp_manager, config, memory_manager)
    
    def process_task(self, task: Dict) -> Dict:
        """Process analysis tasks."""
        try:
            self.status = "processing"
            goal = task.get("goal", "")
            context = task.get("context", {})
            project_dir = context.get("project_dir")
            
            self.logger.info(f"ANALYSIS: Analyzing project for goal: {goal[:100]}...")
            
            task_data = task.get("data", {})
            analysis_depth = task_data.get("analysis_depth", "standard")
            workflow_type = task_data.get("workflow_type", task.get("context", {}).get("workflow_type", "unknown"))
            
            # Determine iteration_count (also check task.get("iteration_count") for direct pass-through from orchestrator)
            iteration_count = 0 # Default
            iteration_count_from_data = task_data.get("iteration_count")
            iteration_count_from_task_attr = task.get("iteration_count")
            execution_id_str = task.get("execution_id", "")

            if iteration_count_from_data is not None:
                try:
                    iteration_count = int(iteration_count_from_data)
                except ValueError:
                    self.logger.warning(f"Could not parse iteration_count '{iteration_count_from_data}' from task.data.")
            elif iteration_count_from_task_attr is not None:
                try:
                    iteration_count = int(iteration_count_from_task_attr)
                except ValueError:
                    self.logger.warning(f"Could not parse iteration_count '{iteration_count_from_task_attr}' from task attribute.")
            elif "_cycle_" in execution_id_str:
                try:
                    cycle_part = execution_id_str.split("_cycle_")[1]
                    iteration_count = int(cycle_part.split("_")[0])
                except (IndexError, ValueError) as e_parse:
                    self.logger.warning(f"Could not parse iteration_count from execution_id '{execution_id_str}': {e_parse}")
            
            # Max iterations might be in task.data or task.config or context.config
            max_iterations_from_data = task_data.get("max_iterations")
            max_iterations_from_task_config = task.get("config", {}).get("max_iterations")
            max_iterations_from_context_config = context.get("config", {}).get("max_iterations")
            max_iterations = max_iterations_from_data or max_iterations_from_task_config or max_iterations_from_context_config

            project_state = self._analyze_project_state_enhanced(project_dir, analysis_depth) if project_dir else {}
            duplicate_analysis = self.analyze_file_duplicates(project_dir) if project_dir else {}
            improvement_analysis = self._analyze_improvements(goal, context, project_state, duplicate_analysis)
            
            continuation_decision = self._determine_continuation(
                workflow_type, iteration_count, max_iterations, improvement_analysis, goal, context
            )
            
            evolved_goal = None
            if continuation_decision.get("should_continue", False):
                evolved_goal = self._evolve_goal(goal, improvement_analysis, iteration_count, context)
            
            # Store analysis insights in memory
            if self.memory_manager:
                project_state_analysis = project_state.get("analysis", {})
                comprehensive_analysis = "Not available"
                if isinstance(project_state_analysis, dict):
                    comprehensive_analysis = project_state_analysis.get("comprehensive_analysis", "Not available")
                elif isinstance(project_state_analysis, str):
                    comprehensive_analysis = project_state_analysis

                insights_payload = {
                    "project_id": context.get("project_id", "unknown_project"),
                    "iteration_count": iteration_count,
                    "project_state_analysis_summary": comprehensive_analysis[:500] + ("..." if len(comprehensive_analysis) > 500 else ""),
                    "duplicate_file_count": duplicate_analysis.get('potential_duplicates', 0),
                    "improvements_suggested": improvement_analysis.get("improvements", []),
                    "continuation_decision": continuation_decision,
                    "evolved_goal": evolved_goal,
                    "raw_improvement_analysis_text": improvement_analysis.get("analysis", "")[:1000] + ("..." if len(improvement_analysis.get("analysis", "")) > 1000 else "")
                }
                if self.memory_manager.store_analysis_insights(iteration_count, insights_payload):
                    self.logger.debug(f"Stored analysis insights in memory for iteration {iteration_count}")
                else:
                    self.logger.warning(f"Failed to store analysis insights in memory for iteration {iteration_count}")

            self.status = "completed"
            return {
                "status": "success",
                "agent_type": self.agent_type,
                "project_state": project_state,
                "duplicate_analysis": duplicate_analysis,
                "improvement_analysis": improvement_analysis,
                "improvements_suggested": improvement_analysis.get("improvements", []),
                "continuation_decision": continuation_decision,
                "evolved_goal": evolved_goal,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"ANALYSIS: Failed to process task: {e}")
            return self.handle_error(e, task)
    
    def _analyze_project_state_enhanced(self, project_dir: str, analysis_depth: str = "standard") -> Dict:
        """Perform enhanced project state analysis."""
        try:
            project_path = self.investigate_project(project_dir)
            
            # Use enhanced task execution for comprehensive analysis
            result = self.execute_enhanced_task(
                task_description=f"Analyze project state with {analysis_depth} depth",
                context={"project_dir": project_path, "analysis_depth": analysis_depth},
                fallback_method=self._basic_project_analysis
            )
            
            if result.get("status") == "success":
                analysis = result.get("result", {})
                
                # Ensure analysis is a dict, not a string
                if isinstance(analysis, str):
                    analysis = {"comprehensive_analysis": analysis}
                
                # Add file structure analysis
                analysis["file_analysis"] = self._analyze_file_structure(project_path)
                
                # Add technology stack analysis  
                analysis["tech_stack"] = self._analyze_technology_stack(project_path)
                
                return {
                    "analysis": analysis,
                    "analysis_method": result.get("method", "enhanced"),
                    "tools_used": result.get("tools_used", []),
                    "project_dir": project_path
                }
            else:
                return {"analysis": "Project analysis failed", "project_dir": project_path}
                
        except Exception as e:
            self.logger.error(f"Enhanced project analysis failed: {e}")
            return {"analysis": f"Analysis error: {e}", "project_dir": project_dir}
    
    def _basic_project_analysis(self, task_description: str, context: Dict) -> Dict:
        """Fallback basic project analysis using LLM only."""
        project_dir = context.get("project_dir", "")
        analysis_depth = context.get("analysis_depth", "standard")
        
        if not self.llm_provider:
            return {
                "status": "error",
                "result": "Basic project analysis requires LLM provider"
            }
        
        analysis_prompt = f"""
        Analyze this project directory for current state and improvement opportunities:
        
        PROJECT DIRECTORY: {project_dir}
        ANALYSIS DEPTH: {analysis_depth}
        
        Provide comprehensive analysis including:
        1. Project structure and organization
        2. Code quality and architecture assessment
        3. Technology stack and dependencies
        4. Current functionality and features
        5. Potential improvement areas
        6. Technical debt and maintenance needs
        7. Performance and scalability considerations
        
        Focus on providing actionable insights for project improvement.
        """
        
        try:
            analysis = self.llm_provider.generate_text(analysis_prompt, temperature=0.2)
            return {
                "status": "success",
                "method": "llm_only",
                "result": {"comprehensive_analysis": analysis},
                "tools_used": []
            }
        except Exception as e:
            return {
                "status": "error",
                "result": f"Analysis generation failed: {e}"
            }
    
    def _analyze_file_structure(self, project_dir: str) -> Dict:
        """Analyze project file structure and organization."""
        try:
            result = self.call_mcp_tool("filesystem", "list_files", {
                "path": project_dir,
                "recursive": True,
                "include_hidden": False
            })
            
            if not result.get("success"):
                return {"structure": "Unable to analyze file structure"}
            
            files = result.get("files", [])
            
            # Categorize files
            file_types = {}
            for file_path in files:
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in file_types:
                    file_types[ext] = 0
                file_types[ext] += 1
            
            return {
                "total_files": len(files),
                "file_types": file_types,
                "top_level_structure": [f for f in files if '/' not in f.strip('./')][:10]
            }
            
        except Exception as e:
            return {"structure": f"File structure analysis error: {e}"}
    
    def _analyze_technology_stack(self, project_dir: str) -> Dict:
        """Analyze technology stack and dependencies."""
        try:
            # Look for common dependency files
            stack_indicators = {
                "requirements.txt": "Python",
                "package.json": "Node.js/JavaScript",
                "pom.xml": "Java/Maven",
                "build.gradle": "Java/Gradle",
                "Cargo.toml": "Rust",
                "go.mod": "Go"
            }
            
            detected_stack = []
            
            for indicator_file, tech in stack_indicators.items():
                file_result = self.call_mcp_tool("filesystem", "read_file", {
                    "path": os.path.join(project_dir, indicator_file)
                })
                
                if file_result.get("success"):
                    detected_stack.append(tech)
            
            return {
                "detected_technologies": detected_stack,
                "analysis": f"Detected {len(detected_stack)} technology indicators"
            }
            
        except Exception as e:
            return {"detected_technologies": [], "analysis": f"Tech stack analysis error: {e}"}
    
    def _analyze_improvements(self, goal: str, context: Dict, project_state: Dict, duplicate_analysis: Dict) -> Dict:
        """Analyze potential improvements based on current project state."""
        if not self.llm_provider:
            return {"improvements": [], "analysis": "No LLM provider for improvement analysis"}
        
        improvement_prompt = f"""
        Based on the project analysis, identify specific improvements that could be made:
        
        GOAL: {goal}
        PROJECT STATE: {str(project_state)[:1000]}...
        DUPLICATE FILES: {duplicate_analysis.get('potential_duplicates', 0)} potential duplicates found
        
        Identify improvements in these categories:
        1. Code quality and structure enhancements
        2. File organization and cleanup opportunities
        3. Feature additions or enhancements
        4. Performance optimizations
        5. Architecture improvements
        6. Documentation improvements
        7. Testing enhancements
        
        For each improvement, provide:
        - What: Specific improvement description
        - Why: Benefit or rationale
        - Priority: high/medium/low
        - Effort: small/medium/large
        
        Focus on actionable, specific improvements.
        """
        
        try:
            analysis = self.llm_provider.generate_text(improvement_prompt, temperature=0.3)
            
            # Extract structured improvements
            improvements = self._extract_improvements_from_analysis(analysis)
            
            return {
                "analysis": analysis,
                "improvements": improvements,
                "total_improvements": len(improvements),
                "high_priority": len([i for i in improvements if i.get("priority") == "high"])
            }
            
        except Exception as e:
            self.logger.error(f"Improvement analysis failed: {e}")
            return {"improvements": [], "analysis": f"Analysis error: {e}"}
    
    def _extract_improvements_from_analysis(self, analysis: str) -> List[Dict]:
        """Extract structured improvements from analysis text."""
        improvements = []
        
        # Simple extraction - could be enhanced with better parsing
        lines = analysis.split('\n')
        current_improvement = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith(('What:', '- What:', '1.', '2.', '3.', '4.', '5.')):
                if current_improvement:
                    improvements.append(current_improvement)
                current_improvement = {"what": line.replace("What:", "").strip()}
            elif line.startswith(('Why:', '- Why:')):
                current_improvement["why"] = line.replace("Why:", "").strip()
            elif line.startswith(('Priority:', '- Priority:')):
                priority = line.replace("Priority:", "").strip().lower()
                current_improvement["priority"] = priority
            elif line.startswith(('Effort:', '- Effort:')):
                effort = line.replace("Effort:", "").strip().lower()
                current_improvement["effort"] = effort
        
        if current_improvement:
            improvements.append(current_improvement)
        
        return improvements[:10]  # Limit to avoid overwhelming
    
    def _determine_continuation(self, workflow_type: str, iteration_count: int, 
                              max_iterations: Optional[int], improvement_analysis: Dict,
                              goal: str, context: Dict) -> Dict:
        """Determine if workflow should continue based on analysis."""
        should_continue = False
        reason = ""
        completion_strategy = context.get("config", {}).get("completion_strategy", "smart")
        adaptive_enabled = context.get("config", {}).get("adaptive", True)
        target_version = context.get("config", {}).get("target_version")

        self.logger.info(f"Determining continuation: workflow='{workflow_type}', iter={iteration_count}, max_iter={max_iterations}, strategy='{completion_strategy}', adaptive={adaptive_enabled}")

        # Core improvement data
        improvements = improvement_analysis.get("improvements", [])
        high_priority_improvements = [imp for imp in improvements if imp.get("priority") == "high"]
        medium_priority_improvements = [imp for imp in improvements if imp.get("priority") == "medium"]

        # Smart Strategy (Default for iteration)
        if completion_strategy == "smart":
            significant_improvements_exist = len(high_priority_improvements) > 0 or len(medium_priority_improvements) >= 2
            if significant_improvements_exist:
                if max_iterations is not None and iteration_count >= max_iterations:
                    if adaptive_enabled:
                        should_continue = True
                        reason = f"Max iterations ({max_iterations}) reached, but adaptive mode enabled with significant improvements found ({len(high_priority_improvements)} high, {len(medium_priority_improvements)} medium)."
                    else:
                        should_continue = False
                        reason = f"Max iterations ({max_iterations}) reached, and adaptive mode disabled. Stopping despite improvements."
                else:
                    should_continue = True
                    reason = f"Significant improvements found ({len(high_priority_improvements)} high, {len(medium_priority_improvements)} medium). Continuing to iteration {iteration_count + 1}."
            else:
                should_continue = False
                reason = "No significant high or medium priority improvements identified for smart strategy."

        # Fixed Iteration Strategy
        elif completion_strategy == "fixed":
            if max_iterations is not None and iteration_count >= max_iterations:
                should_continue = False
                reason = f"Fixed strategy: Maximum iterations ({max_iterations}) reached."
            else:
                # Continue if improvements exist, otherwise stop early to avoid empty cycles
                if improvements:
                    should_continue = True
                    reason = f"Fixed strategy: Continuing to iteration {iteration_count + 1} of {max_iterations} (improvements found)."
                else:
                    should_continue = False
                    reason = f"Fixed strategy: No improvements found. Stopping early before iteration {iteration_count + 1} of {max_iterations}."
        
        # Version Driven Strategy
        elif completion_strategy == "version_driven" and target_version:
            # This strategy implies AnalysisAgent needs to assess if target_version is met.
            # For now, we'll assume it continues if improvements exist and max_iterations not hit.
            # A more sophisticated check would involve analyzing project_state against target_version requirements.
            self.logger.info(f"Version-driven strategy: Target is {target_version}. (Current check is placeholder)")
            if max_iterations is not None and iteration_count >= max_iterations:
                should_continue = False
                reason = f"Version-driven strategy: Max iterations ({max_iterations}) reached for target {target_version}."
            elif not improvements: # Stop if no improvements, even if version not met (to avoid empty cycles)
                should_continue = False
                reason = f"Version-driven strategy: No improvements identified to progress towards {target_version}."
            else:
                should_continue = True # Placeholder: Assume we continue if improvements and not at max_iter
                reason = f"Version-driven strategy: Continuing towards {target_version} (iteration {iteration_count + 1})."

        # Indefinite Workflow Type (overrides completion_strategy for this type)
        elif workflow_type == "indefinite":
            should_continue = len(improvements) > 0
            reason = f"Indefinite workflow: Found {len(improvements)} potential improvements." if should_continue else "Indefinite workflow: No improvements identified."
        
        # Fallback for other workflow types or misconfigurations
        else:
            if max_iterations is not None and iteration_count >= max_iterations:
                should_continue = False
                reason = f"Fallback: Max iterations ({max_iterations}) reached for workflow type '{workflow_type}'."
            elif not improvements:
                should_continue = False
                reason = f"Fallback: No improvements identified for workflow type '{workflow_type}'."
            else:
                should_continue = True
                reason = f"Fallback: Found {len(improvements)} improvements. Continuing for workflow '{workflow_type}'."

        self.logger.info(f"Continuation decision: {should_continue}. Reason: {reason}")
        
        return {
            "should_continue": should_continue,
            "reason": reason,
            "improvements_count": len(improvement_analysis.get("improvements", [])),
            "iteration_count": iteration_count,
            "max_iterations": max_iterations
        }
    
    def _evolve_goal(self, original_goal: str, improvement_analysis: Dict, iteration_count: int, context: Dict) -> str:
        """Evolve the goal based on improvement analysis for next iteration."""
        if not self.llm_provider:
            return original_goal
        
        improvements = improvement_analysis.get("improvements", [])
        if not improvements:
            return original_goal
        
        evolution_prompt = f"""
        Evolve this goal for the next iteration based on identified improvements:
        
        ORIGINAL GOAL: {original_goal}
        ITERATION: {iteration_count + 1}
        IDENTIFIED IMPROVEMENTS: {str(improvements[:5])}  # Top 5 improvements
        
        Create an evolved goal that:
        1. Builds upon the original goal
        2. Incorporates the most important improvements
        3. Is specific and actionable
        4. Maintains the overall project direction
        
        Return a clear, focused goal for the next iteration.
        """
        
        try:
            evolved_goal = self.llm_provider.generate_text(evolution_prompt, temperature=0.4)
            self.logger.info(f"Evolved goal for iteration {iteration_count + 1}")
            return evolved_goal.strip()
        except Exception as e:
            self.logger.error(f"Goal evolution failed: {e}")
            return original_goal 