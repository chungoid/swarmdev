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
            
            # NEW: Extract iteration workflow parameters
            analysis_depth = task.get("analysis_depth", "standard")
            focus_on_existing = task.get("focus_on_existing", False)
            analyze_architecture = task.get("analyze_architecture", False)
            identify_pain_points = task.get("identify_pain_points", False)
            detect_project_type = task.get("detect_project_type", False)
            
            # Version-aware parameters
            target_version = task.get("target_version")
            detect_current_version = task.get("detect_current_version", False)
            plan_version_roadmap = task.get("plan_version_roadmap", False)
            assess_version_completion = task.get("assess_version_completion", False)
            
            # Smart completion parameters
            completion_strategy = task.get("completion_strategy", "smart")
            adaptive_planning = task.get("adaptive_planning", True)
            initial_iterations = task.get("initial_iterations", max_iterations or 3)
            estimate_iteration_needs = task.get("estimate_iteration_needs", False)
            assess_completion_scope = task.get("assess_completion_scope", False)
            plan_completion_strategy = task.get("plan_completion_strategy", False)
            
            # Evaluation parameters
            evaluate_improvements = task.get("evaluate_improvements", False)
            assess_goal_completion = task.get("assess_goal_completion", False)
            check_version_complete = task.get("check_version_complete", False)
            check_target_reached = task.get("check_target_reached", False)
            plan_next_version = task.get("plan_next_version", False)
            evaluate_stopping_criteria = task.get("evaluate_stopping_criteria", False)
            assess_completion_readiness = task.get("assess_completion_readiness", False)
            calculate_remaining_effort = task.get("calculate_remaining_effort", False)
            determine_completion_mode = task.get("determine_completion_mode", False)
            plan_final_iteration = task.get("plan_final_iteration", False)
            
            self.logger.info(f"ANALYSIS: Analyzing project for goal: {goal[:100]}...")
            self.logger.info(f"Analysis depth: {analysis_depth}, Focus existing: {focus_on_existing}, Strategy: {completion_strategy}")
            
            # Analyze current project state with enhanced parameters
            project_state = self._analyze_project_state_enhanced(
                project_dir, analysis_depth, focus_on_existing, 
                analyze_architecture, detect_project_type, target_version
            ) if project_dir else {}
            
            # Enhanced improvement analysis based on workflow parameters
            improvement_analysis = self._analyze_improvements_enhanced(
                goal, context, project_state, iteration_count, 
                completion_strategy, target_version, evaluate_improvements
            )
            
            # Version analysis if requested
            version_analysis = {}
            if target_version and (detect_current_version or assess_version_completion):
                version_analysis = self._analyze_version_status(project_state, target_version)
            
            # Smart completion assessment if requested
            completion_assessment = {}
            if assess_completion_readiness or estimate_iteration_needs:
                completion_assessment = self._assess_project_completion(
                    improvement_analysis, iteration_count, initial_iterations, 
                    target_version, completion_strategy
                )
            
            # Create evolved goal for next iteration if needed
            evolved_goal = None
            if iteration_count > 0 and iteration_count < initial_iterations:
                evolved_goal = self._create_evolved_goal(goal, project_state, improvement_analysis, iteration_count)
            
            # Enhanced iteration continuation logic
            continuation_result = self._should_continue_iteration_enhanced_wrapper(
                improvement_analysis, iteration_count, initial_iterations, 
                completion_strategy, adaptive_planning, target_version
            )
            
            self.status = "completed"
            
            # Enhanced result with all new analysis data
            result = {
                "status": "success",
                "agent_type": self.agent_type,
                "project_state": project_state,
                "improvement_analysis": improvement_analysis,
                "should_continue": continuation_result.get("should_continue", False),
                "iteration_count": iteration_count + 1,
                "improvements_suggested": improvement_analysis.get("improvements", []),
                "evolved_goal": evolved_goal,
                "timestamp": datetime.now().isoformat(),
                
                # NEW: Enhanced analysis results
                "analysis_depth": analysis_depth,
                "completion_strategy": completion_strategy,
                "version_analysis": version_analysis,
                "completion_assessment": completion_assessment,
                "continuation_result": continuation_result,
                
                # Context for other agents to use
                "context": {
                    "initial_iterations": initial_iterations,
                    "target_version": target_version,
                    "completion_strategy": completion_strategy,
                    "adaptive_planning": adaptive_planning,
                    "workflow_type": workflow_type
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"ANALYSIS: Failed to process task: {e}")
            return self.handle_error(e, task)
    
    def _analyze_project_state_enhanced(self, project_dir: str, analysis_depth: str, focus_on_existing: bool, 
                                       analyze_architecture: bool, detect_project_type: bool, target_version: Optional[str]) -> Dict:
        """Analyze current project state using LLM investigation with enhanced parameters."""
        try:
            project_path = self.investigate_project(project_dir)
            
            if self.llm_provider:
                # Build analysis prompt based on parameters
                analysis_focus = []
                if focus_on_existing:
                    analysis_focus.append("- Existing codebase structure and organization")
                    analysis_focus.append("- Current functionality and implementation patterns")
                    analysis_focus.append("- Code quality and maintainability of existing code")
                
                if analyze_architecture:
                    analysis_focus.append("- Architectural patterns and design decisions")
                    analysis_focus.append("- Component interactions and dependencies")
                    analysis_focus.append("- Scalability and extensibility considerations")
                
                if detect_project_type:
                    analysis_focus.append("- Project type classification (web app, CLI tool, library, etc.)")
                    analysis_focus.append("- Technology stack identification")
                    analysis_focus.append("- Development environment and tooling")
                
                if target_version:
                    analysis_focus.append(f"- Version-related files and current version indicators")
                    analysis_focus.append(f"- Compatibility considerations for target version {target_version}")
                
                # Set analysis depth
                depth_instructions = {
                    "comprehensive": "Provide extremely detailed analysis covering all aspects",
                    "focused": "Focus on the most critical aspects for iteration planning", 
                    "completion_focused": "Focus specifically on completion readiness and remaining gaps",
                    "standard": "Provide balanced analysis of key aspects"
                }
                
                state_prompt = f"""
                Analyze the current state of this project with {analysis_depth} depth:
                
                PROJECT DIRECTORY: {project_path}
                
                {depth_instructions.get(analysis_depth, "Provide balanced analysis of key aspects")}
                
                Focus Areas:
                {chr(10).join(analysis_focus) if analysis_focus else "- General project assessment"}
                
                Also assess:
                1. Current functionality and features
                2. Technologies and frameworks in use
                3. Completeness and gaps
                4. Integration points and architecture
                5. Areas for improvement or expansion
                
                Provide a structured analysis that will inform planning and development decisions.
                """
                
                analysis = self.llm_provider.generate_text(state_prompt, temperature=0.2)
                
                # Extract additional metadata if requested
                metadata = {}
                if detect_project_type:
                    metadata.update(self._detect_project_metadata(project_path, analysis))
                
                return {
                    "analysis": analysis, 
                    "project_dir": project_path,
                    "analysis_depth": analysis_depth,
                    "focus_areas": analysis_focus,
                    "metadata": metadata
                }
                
        except Exception as e:
            self.logger.warning(f"Enhanced project state analysis failed: {e}")
            
        return {
            "analysis": "Enhanced project state analysis not available", 
            "project_dir": project_dir,
            "analysis_depth": analysis_depth
        }
    
    def _analyze_improvements_enhanced(self, goal: str, context: Dict, project_state: Dict, iteration_count: int, 
                                       completion_strategy: str, target_version: Optional[str], evaluate_improvements: bool) -> Dict:
        """Analyze what improvements are needed using enhanced task execution with workflow-aware parameters."""
        enhanced_context = {
            "goal": goal, 
            "context": context, 
            "project_state": project_state,
            "iteration_count": iteration_count,
            "completion_strategy": completion_strategy,
            "target_version": target_version,
            "evaluate_improvements": evaluate_improvements
        }
        
        result = self.execute_enhanced_task(
            task_description="Analyze what improvements are needed to achieve the goal with workflow-aware assessment",
            context=enhanced_context,
            fallback_method=self._basic_improvement_analysis_enhanced
        )
        
        # Process result for backward compatibility
        if result.get("status") == "success":
            analysis_content = result.get("result", "Improvement analysis completed")
            
            # Extract improvements from analysis with enhanced categorization
            improvements = self._extract_improvements_from_analysis_enhanced(
                analysis_content, completion_strategy, target_version
            )
            
            return {
                "analysis": analysis_content,
                "improvements": improvements,
                "improvement_count": len(improvements),
                "method": result.get("method", "enhanced"),
                "tools_used": result.get("tools_used", []),
                "completion_strategy": completion_strategy,
                "target_version": target_version,
                "context": enhanced_context  # Pass context for continuation logic
            }
        else:
            return {
                "improvements": ["Enhanced analysis failed - manual review needed"], 
                "improvement_count": 1,
                "completion_strategy": completion_strategy,
                "context": enhanced_context
            }
    
    def _basic_improvement_analysis_enhanced(self, task_description: str, context: Dict) -> Dict:
        """Enhanced fallback improvement analysis using LLM with workflow awareness."""
        goal = context.get("goal", "")
        analysis_context = context.get("context", {})
        project_state = context.get("project_state", {})
        iteration_count = context.get("iteration_count", 0)
        completion_strategy = context.get("completion_strategy", "smart")
        target_version = context.get("target_version")
        evaluate_improvements = context.get("evaluate_improvements", False)
        
        if not self.llm_provider:
            return {
                "status": "error",
                "result": "Enhanced improvement analysis requires LLM provider"
            }
        
        # Build workflow-aware prompt
        strategy_guidance = {
            "smart": "Focus on improvements that bring the project closer to completion. Prioritize by impact and effort.",
            "version_driven": f"Focus on improvements needed to reach version {target_version}. Consider semantic versioning implications.",
            "fixed": "Focus on the most critical improvements within the iteration scope."
        }
        
        improvement_prompt = f"""
        Analyze what improvements are needed for this project (Iteration {iteration_count + 1}):
        
        GOAL: {goal}
        CONTEXT: {analysis_context}
        PROJECT STATE: {project_state.get('analysis', 'None')}
        COMPLETION STRATEGY: {completion_strategy}
        {f"TARGET VERSION: {target_version}" if target_version else ""}
        
        STRATEGY GUIDANCE: {strategy_guidance.get(completion_strategy, "Focus on critical improvements")}
        
        Identify and categorize improvements:
        
        1. CRITICAL BUGS/ISSUES:
        - Blocking issues that prevent basic functionality
        - Security vulnerabilities
        - Breaking errors
        
        2. MAJOR FEATURES/FUNCTIONALITY:
        - Core features missing from the goal
        - Key functionality gaps
        - Integration requirements
        
        3. ARCHITECTURAL IMPROVEMENTS:
        - Code structure and organization
        - Design pattern implementations
        - Scalability considerations
        
        4. POLISH/OPTIMIZATION:
        - Code quality improvements
        - Performance optimizations
        - User experience enhancements
        - Documentation improvements
        
        {"5. VERSION-SPECIFIC REQUIREMENTS:" if target_version else ""}
        {"- Changes needed for version " + target_version if target_version else ""}
        {"- Compatibility considerations" if target_version else ""}
        {"- Breaking changes if needed" if target_version else ""}
        
        Provide specific, actionable improvement suggestions with clear categorization.
        """
        
        try:
            analysis = self.llm_provider.generate_text(improvement_prompt, temperature=0.3)
            return {
                "status": "success",
                "method": "llm_enhanced",
                "result": analysis,
                "tools_used": []
            }
        except Exception as e:
            return {
                "status": "error",
                "result": f"Enhanced improvement analysis failed: {e}"
            }
    
    def _extract_improvements_from_analysis_enhanced(self, analysis: str, completion_strategy: str, target_version: Optional[str]) -> List[str]:
        """Extract specific improvements from analysis with enhanced categorization."""
        if not self.llm_provider:
            return ["Enhanced analysis completed - manual review needed"]
        
        improvements_prompt = f"""
        From this analysis, extract specific improvement actions organized by priority:
        
        ANALYSIS: {analysis}
        COMPLETION STRATEGY: {completion_strategy}
        {f"TARGET VERSION: {target_version}" if target_version else ""}
        
        Extract improvements as a prioritized list, marking each with category:
        [CRITICAL] - Critical bugs/issues that must be fixed
        [MAJOR] - Major features/functionality needed
        [ARCH] - Architectural improvements
        [POLISH] - Polish/optimization items
        {f"[VERSION] - Version-specific requirements for {target_version}" if target_version else ""}
        
        Return only the numbered list with category tags.
        """
        
        try:
            improvements_response = self.llm_provider.generate_text(improvements_prompt, temperature=0.2)
            improvements = [imp.strip() for imp in improvements_response.split('\n') if imp.strip() and not imp.strip().startswith('#')]
            return improvements[:15]  # Limit to 15 most important improvements
        except Exception as e:
            self.logger.error(f"Enhanced improvement extraction failed: {e}")
            return ["Enhanced analysis completed - manual review needed"]
    
    def _detect_project_metadata(self, project_path: str, analysis: str) -> Dict:
        """Detect project metadata from analysis for enhanced project understanding."""
        if not self.llm_provider:
            return {}
        
        metadata_prompt = f"""
        Extract project metadata from this analysis:
        
        PROJECT PATH: {project_path}
        ANALYSIS: {analysis[:1000]}...
        
        Identify and return as JSON:
        {
            "project_type": "web_app|cli_tool|library|api|desktop_app|other",
            "primary_language": "python|javascript|java|go|rust|other",
            "framework": "detected framework or 'none'",
            "existing_codebase": true/false,
            "complexity_level": "simple|moderate|complex",
            "estimated_files": "number estimate"
        }
        
        Return only valid JSON.
        """
        
        try:
            metadata_response = self.llm_provider.generate_text(metadata_prompt, temperature=0.1)
            import json
            return json.loads(metadata_response.strip())
        except Exception as e:
            self.logger.warning(f"Project metadata detection failed: {e}")
            return {"project_type": "unknown", "existing_codebase": True}
    
    def _analyze_version_status(self, project_state: Dict, target_version: str) -> Dict:
        """Analyze version-related status and requirements."""
        if not self.llm_provider:
            return {"current_version": "unknown", "target_version": target_version}
        
        version_prompt = f"""
        Analyze version status for this project:
        
        PROJECT STATE: {project_state.get('analysis', '')[:1000]}...
        TARGET VERSION: {target_version}
        
        Determine:
        1. Current version (if detectable from files like package.json, setup.py, etc.)
        2. Version gap analysis (what's needed to reach target)
        3. Breaking changes required (if any)
        4. Compatibility considerations
        5. Version completion estimate (percentage)
        
        Provide structured version analysis.
        """
        
        try:
            version_analysis = self.llm_provider.generate_text(version_prompt, temperature=0.2)
            return {
                "analysis": version_analysis,
                "target_version": target_version,
                "current_version": "auto-detected",  # Could be enhanced with file parsing
                "completion_estimate": 0.5  # Placeholder - could be calculated
            }
        except Exception as e:
            self.logger.error(f"Version analysis failed: {e}")
            return {"current_version": "unknown", "target_version": target_version}
    
    def _assess_project_completion(self, improvement_analysis: Dict, iteration_count: int, 
                                 initial_iterations: int, target_version: Optional[str], 
                                 completion_strategy: str) -> Dict:
        """Assess project completion readiness and iteration needs."""
        improvements = improvement_analysis.get("improvements", [])
        
        # Categorize improvements by type
        critical_bugs = [imp for imp in improvements if "[CRITICAL]" in imp.upper()]
        major_features = [imp for imp in improvements if "[MAJOR]" in imp.upper()]
        architectural = [imp for imp in improvements if "[ARCH]" in imp.upper()]
        polish_items = [imp for imp in improvements if "[POLISH]" in imp.upper()]
        version_specific = [imp for imp in improvements if "[VERSION]" in imp.upper()]
        
        # Calculate completion metrics
        total_work = len(improvements)
        high_priority_work = len(critical_bugs) + len(major_features)
        remaining_iterations = max(0, initial_iterations - iteration_count)
        
        # Completion assessment based on strategy
        if completion_strategy == "version_driven" and target_version:
            completion_readiness = len(version_specific) == 0 and len(critical_bugs) == 0
            estimated_remaining = len(version_specific) + len(critical_bugs)
        else:
            completion_readiness = high_priority_work <= remaining_iterations and len(critical_bugs) == 0
            estimated_remaining = high_priority_work
        
        return {
            "total_improvements": total_work,
            "critical_bugs": len(critical_bugs),
            "major_features": len(major_features),
            "architectural_items": len(architectural),
            "polish_items": len(polish_items),
            "version_specific_items": len(version_specific),
            "completion_readiness": completion_readiness,
            "estimated_remaining_iterations": min(estimated_remaining, 3),  # Cap at 3
            "remaining_iterations_available": remaining_iterations,
            "completion_strategy": completion_strategy
        }
    
    def _should_continue_iteration_enhanced_wrapper(self, improvement_analysis: Dict, iteration_count: int, 
                                                   initial_iterations: int, completion_strategy: str, 
                                                   adaptive_planning: bool, target_version: Optional[str]) -> Dict:
        """
        Enhanced iteration continuation logic for the new unified iteration workflow.
        Solves the "coat tails" problem with smart completion planning.
        """
        # Add the context information to improvement_analysis for the enhanced method
        enhanced_analysis = improvement_analysis.copy()
        enhanced_analysis["context"] = {
            "initial_iterations": initial_iterations,
            "target_version": target_version,
            "completion_strategy": completion_strategy,
            "adaptive_planning": adaptive_planning
        }
        
        # Use the existing enhanced continuation logic
        return self._should_continue_iteration_enhanced(enhanced_analysis, iteration_count)
    
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