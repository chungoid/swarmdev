"""
Enhanced Interactive Agent implementation for the SwarmDev platform.
This module provides an advanced interactive agent with configuration assistance,
build orchestration, and external tool integration capabilities.
"""

import json
import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from ..utils.llm_provider import LLMProviderInterface
from .llm_agent import LLMEnabledInteractiveAgent


class EnhancedInteractiveAgent(LLMEnabledInteractiveAgent):
    """
    Enhanced Interactive Agent with configuration assistance and build orchestration.
    
    This agent extends the basic goal refinement capabilities with:
    - Configuration guidance and setup
    - Workflow recommendation
    - Build orchestration
    - External tool integration assistance
    - Environment setup help
    """
    
    def __init__(self, llm_provider: LLMProviderInterface, config: Optional[Dict] = None):
        """
        Initialize the Enhanced Interactive Agent.
        
        Args:
            llm_provider: LLM provider instance
            config: Optional configuration dictionary
        """
        super().__init__(llm_provider, config)
        self.mode = "goal_refinement"  # Current conversation mode
        self.build_config = {}  # Build configuration being assembled
        self.available_workflows = [
            "standard_project", "research_only", "development_only", 
            "indefinite", "iteration"
            # "refactor" and "versioned" are deprecated - use enhanced "iteration" instead
        ]
        self.recommended_config = {}
    
    def start_assistant_mode(self) -> str:
        """
        Start the enhanced assistant mode for full project setup.
        
        Returns:
            str: Initial assistant greeting
        """
        self.mode = "assistant"
        self.conversation_history = []
        self.current_goal = None
        self.build_config = {}
        
        greeting = (
            "Hello! I'm your SwarmDev assistant. I'll help you define your project, "
            "configure the optimal settings, and get your build started.\n\n"
            "Let's begin with your project idea. What would you like to build?"
        )
        
        self.conversation_history.append({"role": "agent", "content": greeting})
        return greeting
    
    def process_assistant_message(self, message: str) -> str:
        """
        Process a message in assistant mode with enhanced capabilities.
        
        Args:
            message: User message content
            
        Returns:
            str: Agent response with configuration assistance
        """
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Check if user wants to move to configuration from goal refinement
        if (not self.build_config and 
            message.lower() in ["configure", "configuration", "config", "move to config", "next phase", "continue to config"]):
            response = self._generate_configuration_recommendations()
            self.conversation_history.append({"role": "agent", "content": response})
            return response
        
        # Determine conversation stage and generate appropriate response
        if self.current_goal is None:
            # Goal definition stage
            return self._handle_goal_definition(message)
        elif not self.build_config:
            # Goal refinement stage (until user chooses to configure)
            return self._handle_goal_refinement(message)
        elif not self._is_configuration_complete():
            # Configuration stage
            return self._handle_configuration_setup(message)
        else:
            # Build execution stage
            return self._handle_build_execution(message)
    
    def _handle_goal_definition(self, message: str) -> str:
        """Handle initial goal definition and start refinement."""
        self.current_goal = message
        
        # Generate response using LLM for goal refinement
        prompt = self._create_goal_refinement_prompt()
        response = self._generate_response(prompt)
        
        # Extract refined goal if present
        refined_goal = self._extract_refined_goal(response)
        if refined_goal:
            self.current_goal = refined_goal
        
        self.conversation_history.append({"role": "agent", "content": response})
        return response
    
    def _handle_goal_refinement(self, message: str) -> str:
        """Handle goal refinement with user feedback."""
        # Update goal with new information
        self.current_goal = self._refine_goal(self.current_goal, message)
        
        # Count exchanges to determine if we should offer transition
        user_exchanges = len([msg for msg in self.conversation_history if msg['role'] == 'user'])
        
        # After 3+ exchanges, start offering the option to move to configuration
        if user_exchanges >= 3:
            # Check if this refinement cycle feels complete
            if self._should_offer_configuration_transition():
                prompt = self._create_transition_prompt()
                response = self._generate_response(prompt)
            else:
                # Continue refinement but hint at transition option
                prompt = self._create_goal_refinement_prompt()
                response = self._generate_response(prompt)
                # Add transition hint
                response += "\n\n(Tip: When you're ready to configure your build settings, just say 'configure' or 'next phase')"
        else:
            # Continue normal refinement
            prompt = self._create_goal_refinement_prompt()
            response = self._generate_response(prompt)
        
        self.conversation_history.append({"role": "agent", "content": response})
        return response
    
    def _handle_configuration_setup(self, message: str) -> str:
        """Handle configuration setup based on user preferences."""
        # Check if user wants to go back to goal refinement
        if message.lower() in ["refine more", "keep refining", "back to goal", "refine goal", "go back"]:
            self.build_config = {}  # Reset configuration
            response = "Sure! Let's continue refining your goal. What would you like to add or clarify?"
            self.conversation_history.append({"role": "agent", "content": response})
            return response
        
        # Parse user's configuration preferences
        config_updates = self._parse_configuration_input(message)
        self.build_config.update(config_updates)
        
        # Check if we have all necessary configuration
        if self._is_configuration_complete():
            response = self._generate_build_confirmation()
        else:
            response = self._request_missing_configuration()
        
        self.conversation_history.append({"role": "agent", "content": response})
        return response
    
    def _handle_build_execution(self, message: str) -> str:
        """Handle build execution and monitoring setup."""
        if message.lower() in ["yes", "y", "start", "begin"]:
            return self._start_build_process()
        elif message.lower() in ["no", "n", "cancel"]:
            response = "Build cancelled. You can restart the assistant anytime with 'swarmdev assistant'."
        else:
            response = "Please respond with 'yes' to start the build or 'no' to cancel."
        
        self.conversation_history.append({"role": "agent", "content": response})
        return response
    
    def _should_offer_configuration_transition(self) -> bool:
        """Determine if we should offer transition to configuration phase."""
        # Use LLM to assess if the goal has enough detail for configuration
        assessment_prompt = (
            f"Evaluate if this project goal has sufficient detail to proceed to configuration:\n\n"
            f"Goal: {self.current_goal}\n\n"
            f"A goal is ready for configuration if it includes:\n"
            f"- Clear problem definition and target users\n"
            f"- Core features and functionality\n"
            f"- Basic technical requirements\n"
            f"- Success criteria\n\n"
            f"Respond with 'READY' if the goal has enough detail to configure build settings, "
            f"or 'NEEDS_MORE' if significant clarification is still needed."
        )
        
        try:
            response = self._generate_response(assessment_prompt)
            return "READY" in response.upper()
        except Exception:
            # Fall back to exchange count if LLM fails
            user_exchanges = len([msg for msg in self.conversation_history if msg['role'] == 'user'])
            return user_exchanges >= 4
    
    def _create_transition_prompt(self) -> str:
        """Create a prompt that offers transition to configuration phase."""
        conversation_context = "\n\n".join([
            f"{'User' if msg['role'] == 'user' else 'Agent'}: {msg['content']}"
            for msg in self.conversation_history[-6:]  # Last 3 exchanges
        ])
        
        prompt = (
            "You are a SwarmDev assistant. Based on the conversation, the user's project goal "
            "appears to have sufficient detail for configuration. Create a response that:\n\n"
            f"Recent conversation:\n{conversation_context}\n\n"
            "1. Acknowledges the current goal refinement\n"
            "2. Suggests the goal is well-defined enough to proceed\n"
            "3. Offers to move to configuration phase OR continue refining\n"
            "4. Ask the user what they prefer\n\n"
            "Include the current refined goal in your response and give the user clear options: "
            "'configure' to move to build configuration, or 'refine more' to continue goal refinement."
        )
        
        return prompt
    
    def _create_goal_refinement_prompt(self) -> str:
        """Create an enhanced prompt for goal refinement."""
        conversation_context = "\n\n".join([
            f"{'User' if msg['role'] == 'user' else 'Agent'}: {msg['content']}"
            for msg in self.conversation_history
        ])
        
        prompt = (
            "You are an expert SwarmDev assistant helping a user define and refine their project goal. "
            "Your job is to ask clarifying questions that will help create a complete project specification.\n\n"
            f"Current conversation:\n{conversation_context}\n\n"
            "Based on this conversation, provide a helpful response that:\n"
            "1. Asks specific, targeted questions about unclear aspects\n"
            "2. Focuses on technical requirements, user needs, and success criteria\n"
            "3. Considers implementation complexity and feasibility\n\n"
            "If you have enough information for a complete project specification, include a section "
            "with 'REFINED GOAL:' followed by a detailed, actionable project description.\n\n"
            "Key areas to clarify if not already covered:\n"
            "- Problem being solved and target users\n"
            "- Core features and functionality\n"
            "- Technical requirements and constraints\n"
            "- Success criteria and deliverables\n"
            "- Preferred technologies or approaches"
        )
        
        return prompt
    
    def _generate_configuration_recommendations(self) -> str:
        """Generate configuration recommendations based on the refined goal."""

        
        # Analyze the goal to recommend configuration
        analysis_prompt = (
            f"Based on this project goal, recommend optimal SwarmDev configuration settings:\n\n"
            f"Goal: {self.current_goal}\n\n"
            f"Available workflows:\n"
            f"- standard_project: Research -> Planning -> Development -> Documentation\n"
            f"- research_only: Comprehensive research phase only\n"
            f"- development_only: Development -> Documentation (skip research/planning)\n"
            f"- indefinite: Continuous improvement cycles\n"
            f"- iteration: Fixed number of improvement cycles\n\n"
            f"Provide recommendations for:\n"
            f"1. Best workflow type and why\n"
            f"2. Estimated runtime and whether background mode is recommended\n"
            f"3. Suggested project directory structure\n"
            f"4. Any special configuration considerations\n\n"
            f"Format your response with clear sections and rationale."
        )
        
        recommendations = self._generate_response(analysis_prompt)
        
        # Extract structured recommendations
        self.recommended_config = self._parse_recommendations(recommendations)
        # Initialize build_config with a marker to indicate we're in config phase
        self.build_config = {"_in_config_phase": True}
        
        response = (
            f"Perfect! I've refined your goal:\n\n"
            f"{self.current_goal}\n\n"
            f"Based on your project, here are my configuration recommendations:\n\n"
            f"{recommendations}\n\n"
            f"Would you like to use these recommended settings, or would you prefer to customize them? "
            f"(Type 'use recommended', 'customize', or ask questions about any settings)"
        )
        
        return response
    
    def _parse_configuration_input(self, message: str) -> Dict[str, Any]:
        """Parse user input for configuration preferences."""
        config_updates = {}
        
        message_lower = message.lower()
        
        if "use recommended" in message_lower or "recommended" in message_lower:
            # Ensure we have recommended config and set defaults if needed
            if not self.recommended_config:
                self.recommended_config = {"workflow": "development_only", "project_dir": "./project"}
            config_updates.update(self.recommended_config)

        elif "customize" in message_lower:
            # Start customization process
            config_updates["customizing"] = True
        else:
            # Parse specific configuration mentions
            if "background" in message_lower:
                config_updates["background"] = "yes" in message_lower or "true" in message_lower
            
            if "workflow" in message_lower:
                for workflow in self.available_workflows:
                    if workflow in message_lower:
                        config_updates["workflow"] = workflow
                        break
            
            # Parse project directory
            if "project" in message_lower and "directory" in message_lower:
                # Extract directory path if mentioned
                words = message.split()
                for i, word in enumerate(words):
                    if word in ["directory", "dir", "folder"] and i + 1 < len(words):
                        config_updates["project_dir"] = words[i + 1]
                        break
        
        return config_updates
    
    def _parse_recommendations(self, recommendations: str) -> Dict[str, Any]:
        """Parse LLM recommendations into structured configuration."""
        config = {}
        
        # Simple parsing - in a real implementation, this would be more sophisticated
        if "development_only" in recommendations:
            config["workflow"] = "development_only"
        elif "standard_project" in recommendations:
            config["workflow"] = "standard_project"
        elif "research_only" in recommendations:
            config["workflow"] = "research_only"
        elif "indefinite" in recommendations:
            config["workflow"] = "indefinite"
        elif "iteration" in recommendations:
            config["workflow"] = "iteration"
        
        if "background" in recommendations.lower():
            config["background"] = True
        
        # Default project directory based on goal
        config["project_dir"] = "./project"
        
        return config
    
    def _is_configuration_complete(self) -> bool:
        """Check if we have all necessary configuration."""
        required_fields = ["workflow"]
        # Filter out internal markers
        config_fields = {k: v for k, v in self.build_config.items() if not k.startswith("_")}
        return all(field in config_fields for field in required_fields)
    
    def _request_missing_configuration(self) -> str:
        """Request missing configuration information."""
        missing = []
        
        if "workflow" not in self.build_config:
            missing.append("workflow type")
        
        return (
            f"I need a bit more configuration information. Please specify:\n"
            f"- {', '.join(missing)}\n\n"
            f"You can say something like 'use development_only workflow' or ask me "
            f"questions about any of these options."
        )
    
    def _generate_build_confirmation(self) -> str:
        """Generate build confirmation with final settings."""
        config_summary = []
        
        workflow = self.build_config.get("workflow", "standard_project")
        config_summary.append(f"Workflow: {workflow}")
        
        project_dir = self.build_config.get("project_dir", "./project")
        config_summary.append(f"Project Directory: {project_dir}")
        
        if self.build_config.get("background", False):
            config_summary.append("Background Mode: Enabled")
        
        if workflow == "iteration":
            max_iterations = self.build_config.get("max_iterations", 3)
            config_summary.append(f"Max Iterations: {max_iterations}")
        
        return (
            f"Perfect! Here's your final configuration:\n\n"
            f"Goal: {self.current_goal}\n\n"
            f"Settings:\n" + "\n".join(f"- {item}" for item in config_summary) + "\n\n"
            f"Ready to start your build? This will create your project and begin development.\n"
            f"Type 'yes' to start or 'no' to cancel."
        )
    
    def _start_build_process(self) -> str:
        """Start the actual build process with configured settings."""
        try:
            # Create goal file
            goal_file = "assistant_goal.txt"
            with open(goal_file, 'w') as f:
                f.write(self.current_goal)
            
            # Build the swarmdev command
            cmd = ["swarmdev", "build", "--goal", goal_file]
            
            # Add configuration options
            if "project_dir" in self.build_config:
                cmd.extend(["--project-dir", self.build_config["project_dir"]])
            
            if "workflow" in self.build_config:
                cmd.extend(["--workflow", self.build_config["workflow"]])
            
            if self.build_config.get("background", False):
                cmd.append("--background")
            
            if "max_iterations" in self.build_config:
                cmd.extend(["--max-iterations", str(self.build_config["max_iterations"])])
            
            if "target_version" in self.build_config:
                cmd.extend(["--target-version", self.build_config["target_version"]])
            
            if "current_version" in self.build_config:
                cmd.extend(["--current-version", self.build_config["current_version"]])
            
            # Start the build process
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Extract project ID from output
                output_lines = result.stdout.strip().split('\n')
                project_id_line = [line for line in output_lines if "project ID:" in line]
                
                if project_id_line:
                    project_id = project_id_line[0].split("project ID:")[-1].strip()
                    
                    response = (
                        f"Build started successfully!\n\n"
                        f"Project ID: {project_id}\n"
                        f"Project Directory: {self.build_config.get('project_dir', './project')}\n\n"
                        f"Monitor your build with:\n"
                        f"  swarmdev status --project-id {project_id} --watch\n\n"
                        f"The swarm is now working on your project!"
                    )
                else:
                    response = (
                        f"Build started successfully!\n\n"
                        f"Check the output above for your project ID and monitoring instructions."
                    )
            else:
                response = (
                    f"There was an error starting the build:\n{result.stderr}\n\n"
                    f"Please check your configuration and try again."
                )
            
            return response
            
        except Exception as e:
            return f"Error starting build process: {e}\n\nPlease try running the build manually."
    
    def get_configuration_help(self, topic: str) -> str:
        """Get help information about configuration topics."""
        help_topics = {
            "workflows": (
                "SwarmDev Workflow Types:\n\n"
                "1. standard_project: Complete development process with research, planning, development, and documentation\n"
                "2. research_only: Focus only on research and technology analysis\n"
                "3. development_only: Skip research and planning, go straight to implementation\n"
                "4. indefinite: Continuous improvement cycles that run until stopped\n"
                "5. iteration: Fixed number of improvement cycles\n\n"
                "Choose based on your project needs and timeline."
            ),
            "background": (
                "Background Mode:\n\n"
                "- Enabled: Build runs in the background, you can monitor with status commands\n"
                "- Disabled: Build runs in foreground with live progress updates\n\n"
                "Recommended for longer projects or when you want to do other work while building."
            ),
            "llm": (
                "LLM Provider Options:\n\n"
                "- auto: Automatically detect and use available providers\n"
                "- openai: Use OpenAI models (requires OPENAI_API_KEY)\n"
                "- anthropic: Use Anthropic models (requires ANTHROPIC_API_KEY)\n\n"
                "Set your API keys in environment variables or .env file."
            )
        }
        
        return help_topics.get(topic.lower(), f"No help available for topic: {topic}") 