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
    Uses planning results from PlanningAgent and implements using MCP filesystem tools.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None):
        super().__init__(agent_id, agent_type, llm_provider, mcp_manager, config)
    
    def process_task(self, task: Dict) -> Dict:
        """Process development tasks by implementing the planning results."""
        try:
            self.status = "processing"
            goal = task.get("goal", "")
            context = task.get("context", {})
            project_dir = context.get("project_dir", ".")
            
            self.logger.info(f"DEVELOPMENT: Implementing goal: {goal[:100]}...")
            
            # Get results from previous agents in the workflow
            planning_results = context.get("planning_results", {})
            research_results = context.get("research_results", {})
            analysis_results = context.get("analysis_results", {})
            
            # Extract task breakdown from planning results
            task_breakdown = planning_results.get("task_breakdown", [])
            execution_strategy = planning_results.get("execution_strategy", {})
            
            if not task_breakdown:
                raise Exception("No task breakdown from planning results - DevelopmentAgent requires planning from PlanningAgent")
            
            self.logger.info(f"Implementing {len(task_breakdown)} tasks from planning results")
            
            # Implement the planned tasks directly using MCP tools
            implementation_results = self._implement_planned_tasks(
                task_breakdown, project_dir, goal, planning_results, research_results
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
                               goal: str, planning_results: Dict, research_results: Dict) -> Dict:
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
                task_result = self._implement_single_task(task, project_dir, goal, planning_results)
                
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
    
    def _implement_single_task(self, task: Dict, project_dir: str, goal: str, planning_results: Dict) -> Dict:
        """Implement a single task from the task breakdown."""
        task_name = task.get("task", "")
        task_type = task.get("type", "development")
        
        # Determine file path and content based on task
        file_info = self._determine_file_for_task(task, project_dir, goal)
        
        if not file_info:
            return {"files_created": [], "files_modified": []}
        
        file_path = file_info["path"]
        file_content = file_info["content"]
        action = file_info["action"]  # "create" or "modify"
        
        # Convert to workspace path for MCP filesystem
        workspace_file_path = self._to_workspace_path(file_path)
        
        # Ensure directory exists (create recursively if needed)
        dir_path = os.path.dirname(workspace_file_path)
        if dir_path and dir_path != "." and dir_path != "/workspace":
            self._create_directory_recursive(dir_path)
        
        # Write the file
        write_result = self.call_mcp_tool("filesystem", "write_file", {
            "path": workspace_file_path,
            "content": file_content
        })
        
        if not self._is_mcp_error(write_result):
            self.logger.info(f"Successfully {action}d file: {file_path}")
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
    
    def _determine_file_for_task(self, task: Dict, project_dir: str, goal: str) -> Optional[Dict]:
        """Determine what file to create/modify for a given task."""
        if not self.llm_provider:
            return None
        
        task_name = task.get("task", "")
        task_type = task.get("type", "development")
        
        # Generate file content and path
        file_prompt = f"""
        Determine the file to create for this development task:
        
        TASK: {task_name}
        TASK TYPE: {task_type}
        GOAL: {goal}
        PROJECT DIRECTORY: {project_dir}
        
        Create a single file for this task. Respond with EXACTLY this format:
        
        FILE_PATH: relative/path/to/file.py
        ACTION: create
        CONTENT:
        [actual file content here - RAW CODE ONLY, NO MARKDOWN FORMATTING]
        
        Rules:
        - Use appropriate file extensions (.py, .js, .md, etc.)
        - Place files in logical directories (src/, tests/, docs/, etc.)
        - Generate complete, functional code
        - Include necessary imports and proper structure
        - Make the code production-ready
        - DO NOT use markdown code fences (```) in the file content
        - DO NOT include language identifiers like ```python
        - Provide ONLY the raw file content after CONTENT:
        
        Focus on implementing the specific task functionality.
        """
        
        try:
            response = self.llm_provider.generate_text(file_prompt, temperature=0.2)
            return self._parse_file_response(response, project_dir)
        except Exception as e:
            self.logger.error(f"Failed to determine file for task '{task_name}': {e}")
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
    
    def _create_directory_recursive(self, dir_path: str) -> None:
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
            self._create_directory_recursive(parent_dir)
        
        # Now create this directory
        create_result = self.call_mcp_tool("filesystem", "create_directory", {"path": dir_path})
        if self._is_mcp_error(create_result):
            error_msg = self._extract_mcp_error(create_result)
            raise Exception(f"Failed to create directory {dir_path}: {error_msg}")
        
        self.logger.debug(f"Created directory: {dir_path}")

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


class AnalysisAgent(BaseAgent):
    """
    Analysis agent for project state analysis and improvement recommendations.
    Central to iteration workflows and continuous improvement processes.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None):
        super().__init__(agent_id, agent_type, llm_provider, mcp_manager, config)
    
    def process_task(self, task: Dict) -> Dict:
        """Process analysis tasks."""
        try:
            self.status = "processing"
            goal = task.get("goal", "")
            context = task.get("context", {})
            project_dir = context.get("project_dir")
            
            self.logger.info(f"ANALYSIS: Analyzing project for goal: {goal[:100]}...")
            
            # Get task-specific parameters
            task_data = task.get("data", {})
            analysis_depth = task_data.get("analysis_depth", "standard")
            workflow_type = task_data.get("workflow_type", "unknown")
            
            # Check both locations for iteration_count (orchestrator puts it directly on task, workflow puts it in data)
            iteration_count = task.get("iteration_count", task_data.get("iteration_count", 0))
            max_iterations = task.get("initial_iterations", task_data.get("max_iterations"))
            
            # Perform comprehensive project analysis
            project_state = self._analyze_project_state_enhanced(project_dir, analysis_depth) if project_dir else {}
            
            # Analyze file duplicates as part of project health
            duplicate_analysis = self.analyze_file_duplicates(project_dir) if project_dir else {}
            
            # Generate improvement analysis
            improvement_analysis = self._analyze_improvements(goal, context, project_state, duplicate_analysis)
            
            # Determine if workflow should continue (for iteration workflows)
            continuation_decision = self._determine_continuation(
                workflow_type, iteration_count, max_iterations, improvement_analysis
            )
            
            # Generate evolved goal if continuing
            evolved_goal = None
            if continuation_decision.get("should_continue", False):
                evolved_goal = self._evolve_goal(goal, improvement_analysis, iteration_count)
            
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
                              max_iterations: Optional[int], improvement_analysis: Dict) -> Dict:
        """Determine if workflow should continue based on analysis."""
        should_continue = False
        reason = ""
        
        self.logger.info(f"Determining continuation: workflow_type={workflow_type}, iteration_count={iteration_count}, max_iterations={max_iterations}")
        
        # Check max iterations limit
        if max_iterations is not None and iteration_count >= max_iterations:
            reason = f"Maximum iterations ({max_iterations}) reached"
            self.logger.info(f"Stopping: {reason}")
        else:
            # Check if there are meaningful improvements to make
            improvements = improvement_analysis.get("improvements", [])
            high_priority = improvement_analysis.get("high_priority", 0)
            
            self.logger.info(f"Found {len(improvements)} improvements, {high_priority} high-priority")
            
            if workflow_type == "indefinite":
                should_continue = len(improvements) > 0
                reason = f"Found {len(improvements)} potential improvements" if should_continue else "No improvements identified"
            elif workflow_type == "iteration":
                should_continue = high_priority > 0 or len(improvements) > 2
                reason = f"Found {high_priority} high-priority and {len(improvements)} total improvements" if should_continue else "Insufficient improvements to continue"
            else:
                should_continue = len(improvements) > 0
                reason = f"Found {len(improvements)} improvements for {workflow_type} workflow"
            
            self.logger.info(f"Continuation decision: should_continue={should_continue}, reason={reason}")
        
        return {
            "should_continue": should_continue,
            "reason": reason,
            "improvements_count": len(improvement_analysis.get("improvements", [])),
            "iteration_count": iteration_count,
            "max_iterations": max_iterations
        }
    
    def _evolve_goal(self, original_goal: str, improvement_analysis: Dict, iteration_count: int) -> str:
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