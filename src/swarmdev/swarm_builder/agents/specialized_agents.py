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
        """Process planning tasks using sequential thinking and project analysis with enhanced workflow parameters."""
        try:
            self.status = "processing"
            goal = task.get("goal", "")
            context = task.get("context", {})
            project_dir = context.get("project_dir")
            
            # NEW: Extract planning workflow parameters
            planning_type = task.get("planning_type", "standard")
            use_analysis_results = task.get("use_analysis_results", False)
            use_research_results = task.get("use_research_results", False)
            preserve_functionality = task.get("preserve_functionality", False)
            plan_incremental_steps = task.get("plan_incremental_steps", False)
            risk_assessment = task.get("risk_assessment", False)
            
            # Version-aware planning parameters
            target_version = task.get("target_version")
            scope_to_current_version = task.get("scope_to_current_version", False)
            plan_version_increment = task.get("plan_version_increment", False)
            define_completion_criteria = task.get("define_completion_criteria", False)
            create_version_blueprint = task.get("create_version_blueprint", False)
            
            # Adaptive iteration planning parameters
            plan_iteration_roadmap = task.get("plan_iteration_roadmap", False)
            estimate_effort_distribution = task.get("estimate_effort_distribution", False)
            plan_completion_sequence = task.get("plan_completion_sequence", False)
            
            self.logger.info(f"PLANNING: Creating plan for goal: {goal[:100]}...")
            self.logger.info(f"Planning type: {planning_type}, Use analysis: {use_analysis_results}, Use research: {use_research_results}")
            
            # Enhanced project investigation based on parameters
            project_context = self._investigate_project_context_enhanced(
                project_dir, preserve_functionality, planning_type
            ) if project_dir else {}
            
            # Retrieve analysis results if requested
            analysis_context = {}
            if use_analysis_results:
                analysis_context = self._retrieve_analysis_results(context)
            
            # Retrieve research results if requested  
            research_context = {}
            if use_research_results:
                research_context = self._retrieve_research_results(context)
            
            # Enhanced detailed planning with workflow parameters
            detailed_plan = self._create_detailed_plan_enhanced(
                goal, context, project_context, analysis_context, research_context,
                planning_type, target_version, preserve_functionality
            )
            
            # Enhanced task breakdown based on planning type
            task_breakdown = self._break_down_tasks_enhanced(
                detailed_plan, goal, planning_type, plan_incremental_steps
            )
            
            # Enhanced execution strategy with risk assessment
            execution_strategy = self._plan_execution_strategy_enhanced(
                task_breakdown, risk_assessment, estimate_effort_distribution
            )
            
            # Version planning if requested
            version_plan = {}
            if target_version and (plan_version_increment or create_version_blueprint):
                version_plan = self._create_version_plan(
                    detailed_plan, target_version, scope_to_current_version
                )
            
            # Completion planning if requested
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
                "project_context": project_context,
                "timestamp": datetime.now().isoformat(),
                
                # NEW: Enhanced planning results
                "planning_type": planning_type,
                "analysis_context": analysis_context,
                "research_context": research_context,
                "version_plan": version_plan,
                "completion_plan": completion_plan,
                "workflow_parameters": {
                    "preserve_functionality": preserve_functionality,
                    "plan_incremental_steps": plan_incremental_steps,
                    "risk_assessment": risk_assessment,
                    "target_version": target_version
                }
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
                                     planning_type: str, target_version: Optional[str], 
                                     preserve_functionality: bool) -> Dict:
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
            
            # NEW: Extract enhanced workflow parameters for file management
            implementation_style = task.get("implementation_style", "adaptive")
            use_planning_results = task.get("use_planning_results", False)
            maintain_compatibility = task.get("maintain_compatibility", True)
            optimize_for_maintainability = task.get("optimize_for_maintainability", True)
            prefer_modification_over_creation = task.get("prefer_modification_over_creation", True)
            cleanup_obsolete_files = task.get("cleanup_obsolete_files", False)
            
            self.logger.info(f"DEVELOPMENT: Implementing goal: {goal[:100]}...")
            self.logger.info(f"Implementation style: {implementation_style}, Prefer modification: {prefer_modification_over_creation}")
            
            # Analyze existing files to understand modification opportunities
            existing_files_analysis = {}
            if project_dir and prefer_modification_over_creation:
                existing_files_analysis = self._analyze_existing_files_for_modification(project_dir, goal)
            
            # Investigate project before implementation
            project_analysis = self._investigate_project_for_development(project_dir) if project_dir else {}
            
            # Enhanced planning with file management awareness
            implementation_plan = self._plan_implementation_enhanced(
                goal, context, project_analysis, existing_files_analysis,
                implementation_style, prefer_modification_over_creation
            )
            
            # Generate code and files with enhanced file management
            implementation_results = self._implement_solution_enhanced(
                implementation_plan, project_dir, prefer_modification_over_creation, cleanup_obsolete_files
            )
            
            self.status = "completed"
            return {
                "status": "success",
                "agent_type": self.agent_type,
                "project_analysis": project_analysis,
                "implementation_plan": implementation_plan,
                "implementation_results": implementation_results,
                "existing_files_analysis": existing_files_analysis,
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
    
    def _analyze_existing_files_for_modification(self, project_dir: str, goal: str) -> Dict:
        """Analyze existing files to understand modification opportunities instead of creating duplicates."""
        try:
            # Use filesystem MCP tool to get file list
            result = self.call_mcp_tool("filesystem", "list_files", {
                "path": project_dir,
                "recursive": True,
                "include_hidden": False
            })
            
            if not result.get("success"):
                return {"modifiable_files": [], "analysis": "Failed to analyze existing files"}
            
            files = result.get("files", [])
            
            # Filter for code files that might be relevant to the goal
            code_files = [f for f in files if f.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.h', '.go', '.rs'))]
            
            if not code_files or not self.llm_provider:
                return {"modifiable_files": [], "analysis": "No code files found or no LLM provider"}
            
            # Analyze files for modification potential
            analysis_prompt = f"""
            Analyze these existing files to understand which could be modified instead of creating new ones:
            
            GOAL: {goal}
            EXISTING FILES: {', '.join(code_files[:20])}  # Limit to avoid token overflow
            
            For each relevant file, assess:
            1. Whether it could be extended/modified to support the goal
            2. Risk level of modification (low/medium/high)
            3. What specific modifications would be needed
            4. Whether creating a new file would be better
            
            Focus on identifying files that could be safely enhanced rather than duplicated.
            Return analysis focusing on modification opportunities.
            """
            
            analysis = self.llm_provider.generate_text(analysis_prompt, temperature=0.2)
            
            # Extract modifiable files from analysis
            modifiable_files = self._extract_modifiable_files_from_analysis(analysis, code_files)
            
            return {
                "modifiable_files": modifiable_files,
                "total_files": len(code_files),
                "analysis": analysis
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing existing files: {e}")
            return {"modifiable_files": [], "analysis": f"Analysis error: {e}"}
    
    def _extract_modifiable_files_from_analysis(self, analysis: str, code_files: List[str]) -> List[Dict]:
        """Extract modifiable files information from LLM analysis."""
        modifiable = []
        
        # Simple extraction based on file mentions in analysis
        for file_path in code_files:
            filename = os.path.basename(file_path)
            if filename in analysis and ("modify" in analysis.lower() or "extend" in analysis.lower()):
                modifiable.append({
                    "file": file_path,
                    "confidence": "medium",  # Could be enhanced with better parsing
                    "reason": "Mentioned in modification analysis"
                })
        
        return modifiable[:5]  # Limit to avoid overwhelming the system
    
    def _plan_implementation_enhanced(self, goal: str, context: Dict, project_analysis: Dict, 
                                    existing_files_analysis: Dict, implementation_style: str,
                                    prefer_modification: bool) -> Dict:
        """Enhanced implementation planning with file management awareness."""
        enhanced_context = {
            "goal": goal,
            "context": context,
            "project_analysis": project_analysis,
            "existing_files_analysis": existing_files_analysis,
            "implementation_style": implementation_style,
            "prefer_modification": prefer_modification
        }
        
        result = self.execute_enhanced_task(
            task_description="Plan implementation approach with awareness of existing files and preference for modification over creation",
            context=enhanced_context,
            fallback_method=self._basic_implementation_planning_enhanced
        )
        
        # Process result for backward compatibility
        if result.get("status") == "success":
            plan_content = result.get("result", "Enhanced implementation plan completed")
            
            # Extract files with modification/creation decisions
            file_decisions = self._extract_file_decisions_from_plan(plan_content, existing_files_analysis)
            
            return {
                "approach": plan_content,
                "file_decisions": file_decisions,
                "method": result.get("method", "enhanced"),
                "tools_used": result.get("tools_used", []),
                "prefer_modification": prefer_modification
            }
        else:
            return {
                "approach": "Enhanced implementation planning failed", 
                "file_decisions": [],
                "prefer_modification": prefer_modification
            }
    
    def _basic_implementation_planning_enhanced(self, task_description: str, context: Dict) -> Dict:
        """Enhanced fallback planning with file management awareness."""
        goal = context.get("goal", "")
        dev_context = context.get("context", {})
        project_analysis = context.get("project_analysis", {})
        existing_files_analysis = context.get("existing_files_analysis", {})
        prefer_modification = context.get("prefer_modification", True)
        
        if not self.llm_provider:
            return {
                "status": "error",
                "result": "Enhanced implementation planning requires LLM provider"
            }
        
        modifiable_files = existing_files_analysis.get("modifiable_files", [])
        
        planning_prompt = f"""
        Plan the implementation for this development goal with file management awareness:
        
        GOAL: {goal}
        CONTEXT: {dev_context}
        PROJECT ANALYSIS: {project_analysis.get('analysis', 'None')}
        
        EXISTING FILES ANALYSIS:
        Modifiable files: {', '.join([f['file'] for f in modifiable_files])}
        Total existing files: {existing_files_analysis.get('total_files', 0)}
        
        FILE MANAGEMENT STRATEGY: {"Prefer modifying existing files over creating new ones" if prefer_modification else "Create new files as needed"}
        
        Plan with these priorities:
        1. MODIFICATION FIRST: Check if existing files can be enhanced instead of creating new ones
        2. AVOID DUPLICATION: Don't create files with similar names to existing ones (e.g., avoid base.py if base_agent.py exists)
        3. CONSOLIDATION: Consider consolidating functionality into existing files where appropriate
        4. CLEAN ARCHITECTURE: Ensure file organization makes sense
        
        For each file needed:
        - Specify whether to MODIFY existing file or CREATE new file
        - If creating new, explain why modification wasn't suitable
        - If modifying, specify what changes are needed
        - Avoid names that duplicate existing functionality
        
        Focus on practical, implementable solutions that minimize file duplication.
        """
        
        try:
            plan = self.llm_provider.generate_text(planning_prompt, temperature=0.3)
            return {
                "status": "success",
                "method": "enhanced_llm",
                "result": plan,
                "tools_used": []
            }
        except Exception as e:
            return {
                "status": "error",
                "result": f"Enhanced implementation planning failed: {e}"
            }
    
    def _extract_file_decisions_from_plan(self, plan: str, existing_files_analysis: Dict) -> List[Dict]:
        """Extract file modification/creation decisions from the enhanced plan."""
        if not self.llm_provider:
            return []
        
        extraction_prompt = f"""
        From this implementation plan, extract the file decisions in JSON format:
        
        PLAN: {plan[:1500]}...
        
        Return a JSON array of objects with this structure:
        [
            {
                "file": "path/to/file.py",
                "action": "modify" or "create",
                "reason": "brief explanation",
                "priority": "high/medium/low"
            }
        ]
        
        Only return valid JSON. Focus on files explicitly mentioned in the plan.
        """
        
        try:
            response = self.llm_provider.generate_text(extraction_prompt, temperature=0.1)
            # Try to parse JSON from response
            import json
            
            # Clean response in case there are markdown artifacts
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            file_decisions = json.loads(cleaned_response.strip())
            return file_decisions if isinstance(file_decisions, list) else []
            
        except Exception as e:
            self.logger.warning(f"Could not extract file decisions: {e}")
            return []
    
    def _implement_solution_enhanced(self, implementation_plan: Dict, project_dir: str, 
                                   prefer_modification: bool, cleanup_obsolete: bool) -> Dict:
        """Enhanced solution implementation with file management capabilities."""
        if not self.llm_provider:
            return {"status": "error", "message": "No LLM provider for implementation"}
        
        results = {
            "files_created": [],
            "files_modified": [],
            "files_removed": [],
            "code_generated": {},
            "errors": [],
            "cleanup_performed": cleanup_obsolete
        }
        
        file_decisions = implementation_plan.get("file_decisions", [])
        approach = implementation_plan.get("approach", "")
        
        # Process file decisions with modification preferences
        for decision in file_decisions:
            file_path = decision.get("file", "")
            action = decision.get("action", "create")
            reason = decision.get("reason", "")
            
            try:
                if action == "modify" and prefer_modification:
                    self._modify_existing_file(file_path, approach, reason, project_dir, results)
                else:
                    self._create_new_file(file_path, approach, reason, project_dir, results)
                    
            except Exception as e:
                error_msg = f"Failed to {action} {file_path}: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Cleanup obsolete files if requested
        if cleanup_obsolete and project_dir:
            cleanup_results = self._cleanup_obsolete_files(project_dir, results)
            results["files_removed"].extend(cleanup_results.get("removed", []))
            results["errors"].extend(cleanup_results.get("errors", []))
        
        results["status"] = "success" if (results["files_created"] or results["files_modified"]) else "partial"
        return results
    
    def _modify_existing_file(self, file_path: str, approach: str, reason: str, project_dir: str, results: Dict):
        """Modify an existing file instead of creating a new one."""
        if not project_dir:
            raise Exception("No project directory specified")
        
        full_file_path = os.path.join(project_dir, file_path)
        
        if not os.path.exists(full_file_path):
            # File doesn't exist, fall back to creation
            self._create_new_file(file_path, approach, reason, project_dir, results)
            return
        
        # Read existing file content
        with open(full_file_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Generate modifications using LLM
        modification_prompt = f"""
        Modify this existing file to support the implementation approach:
        
        FILE PATH: {file_path}
        EXISTING CONTENT:
        {existing_content}
        
        IMPLEMENTATION APPROACH: {approach}
        MODIFICATION REASON: {reason}
        
        Generate the complete modified file content that:
        1. Preserves existing functionality where possible
        2. Adds new functionality as needed
        3. Maintains code style and structure
        4. Includes proper imports and error handling
        5. Is production-ready and well-structured
        
        IMPORTANT: Return ONLY the complete modified file content without any markdown formatting or explanations.
        """
        
        modified_content = self.llm_provider.generate_text(modification_prompt, temperature=0.2)
        
        # Clean up any markdown artifacts
        cleaned_content = self._clean_generated_code(modified_content)
        
        # Write modified content
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        results["code_generated"][file_path] = cleaned_content
        results["files_modified"].append(file_path)
        self.logger.info(f"Modified existing file: {file_path}")
    
    def _create_new_file(self, file_path: str, approach: str, reason: str, project_dir: str, results: Dict):
        """Create a new file (fallback from modification or explicit creation)."""
        # Use existing implementation
        self._write_file_to_disk(file_path, self._generate_file_content(file_path, approach, reason), project_dir, results)
    
    def _generate_file_content(self, file_path: str, approach: str, reason: str) -> str:
        """Generate content for a new file."""
        if file_path == '__init__.py' or file_path.endswith('/__init__.py'):
            return self._generate_init_file_content(file_path, approach)
        
        content_prompt = f"""
        Generate code for this new file:
        
        FILE PATH: {file_path}
        IMPLEMENTATION APPROACH: {approach}
        CREATION REASON: {reason}
        
        Generate complete, functional code that:
        1. Implements the planned functionality
        2. Follows best practices for the detected technology
        3. Integrates well with the existing project structure
        4. Includes appropriate imports, error handling, and documentation
        5. Is production-ready and well-structured
        
        IMPORTANT: Return ONLY the raw code content without any markdown formatting or explanations.
        """
        
        generated_code = self.llm_provider.generate_text(content_prompt, temperature=0.2)
        return self._clean_generated_code(generated_code)
    
    def _cleanup_obsolete_files(self, project_dir: str, current_results: Dict) -> Dict:
        """Clean up files that may have been made obsolete by the current implementation."""
        cleanup_results = {"removed": [], "errors": []}
        
        try:
            self.logger.error(f"Goal evolution failed: {e}")
            return original_goal


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