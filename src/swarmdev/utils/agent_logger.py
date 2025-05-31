"""
Agent Logger utility for the SwarmDev platform.
This module provides specialized logging for agent classes with individual log files.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Dict, Optional
import json


class AgentLogger:
    """
    Specialized logger for SwarmDev agents that creates individual log files
    for each agent class with comprehensive formatting.
    """
    
    _loggers: Dict[str, logging.Logger] = {}
    _log_dir = ".swarmdev/logs"  # Use .swarmdev directory for internal logs
    
    @classmethod
    def get_logger(cls, agent_class: str, agent_id: str) -> logging.Logger:
        """
        Get or create a logger for a specific agent class.
        
        Args:
            agent_class: Name of the agent class (e.g., 'DevelopmentAgent')
            agent_id: Unique identifier for the agent instance
            
        Returns:
            logging.Logger: Configured logger instance
        """
        logger_name = f"{agent_class}.{agent_id}"
        
        if logger_name not in cls._loggers:
            cls._loggers[logger_name] = cls._create_logger(agent_class, agent_id)
        
        return cls._loggers[logger_name]
    
    @classmethod
    def _create_logger(cls, agent_class: str, agent_id: str) -> logging.Logger:
        """Create and configure a new logger for an agent."""
        # Ensure log directory exists
        os.makedirs(cls._log_dir, exist_ok=True)
        
        # Create logger
        logger_name = f"{agent_class}.{agent_id}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers if logger already exists
        if logger.handlers:
            return logger
        
        # Create file handler with rotation
        log_file = os.path.join(cls._log_dir, f"{agent_class.lower()}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create comprehensive formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Log initial creation
        logger.info(f"=== LOGGER INITIALIZED FOR {agent_class} ({agent_id}) ===")
        
        return logger
    
    @classmethod
    def log_task_start(cls, logger: logging.Logger, task: Dict):
        """Log the start of a task with comprehensive details."""
        logger.info("=" * 80)
        logger.info(f"TASK STARTED: {task.get('task_id', 'unknown')}")
        logger.info(f"Task Type: {task.get('agent_type', 'unknown')}")
        logger.info(f"Goal: {task.get('goal', 'No goal specified')[:100]}...")
        logger.info(f"Project Dir: {task.get('project_dir', 'unknown')}")
        logger.info(f"Iteration: {task.get('iteration_count', 'unknown')}")
        logger.info(f"Context Keys: {list(task.get('context', {}).keys())}")
        logger.debug(f"Full Task: {json.dumps(task, indent=2, default=str)}")
        logger.info("=" * 80)
    
    @classmethod
    def log_task_complete(cls, logger: logging.Logger, task: Dict, result: Dict, duration: float):
        """Log the completion of a task with results."""
        logger.info("=" * 80)
        logger.info(f"TASK COMPLETED: {task.get('task_id', 'unknown')}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Status: {result.get('status', 'unknown')}")
        logger.info(f"Result Keys: {list(result.keys())}")
        
        # Log specific metrics based on agent type
        if 'files_created' in result:
            logger.info(f"Files Created: {len(result['files_created'])}")
            for file in result['files_created']:
                logger.info(f"  → {file}")
        
        if 'files_modified' in result:
            logger.info(f"Files Modified: {len(result['files_modified'])}")
            for file in result['files_modified']:
                logger.info(f"  ↻ {file}")
        
        if 'improvements' in result:
            logger.info(f"Improvements Suggested: {len(result['improvements'])}")
        
        logger.debug(f"Full Result: {json.dumps(result, indent=2, default=str)}")
        logger.info("=" * 80)
    
    @classmethod
    def log_decision(cls, logger: logging.Logger, decision: str, reasoning: str, context: Optional[Dict] = None):
        """Log an important decision made by the agent."""
        logger.info(f"DECISION: {decision}")
        logger.info(f"REASONING: {reasoning}")
        if context:
            logger.debug(f"CONTEXT: {json.dumps(context, indent=2, default=str)}")
    
    @classmethod
    def log_llm_call(cls, logger: logging.Logger, prompt_type: str, prompt_length: int, response_length: int, temperature: float):
        """Log LLM API calls for debugging and monitoring."""
        logger.debug(f"LLM CALL: {prompt_type}")
        logger.debug(f"  Prompt Length: {prompt_length} chars")
        logger.debug(f"  Response Length: {response_length} chars") 
        logger.debug(f"  Temperature: {temperature}")
    
    @classmethod
    def log_file_operation(cls, logger: logging.Logger, operation: str, file_path: str, details: Optional[str] = None):
        """Log file operations performed by agents."""
        logger.info(f"FILE {operation.upper()}: {file_path}")
        if details:
            logger.info(f"  Details: {details}")
    
    @classmethod
    def log_analysis_metrics(cls, logger: logging.Logger, metrics: Dict):
        """Log analysis metrics and statistics."""
        logger.info("ANALYSIS METRICS:")
        for key, value in metrics.items():
            logger.info(f"  {key}: {value}")
    
    @classmethod
    def log_error_with_context(cls, logger: logging.Logger, error: Exception, context: Dict):
        """Log errors with comprehensive context."""
        logger.error("=" * 80)
        logger.error(f"ERROR OCCURRED: {type(error).__name__}")
        logger.error(f"Error Message: {str(error)}")
        logger.error(f"Context: {json.dumps(context, indent=2, default=str)}")
        logger.error("=" * 80, exc_info=True) 