"""
Comprehensive MCP Metrics and Logging System

This module provides detailed metrics collection, performance tracking,
and structured logging for MCP (Model Context Protocol) operations.
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from pathlib import Path

@dataclass
class MCPCallMetrics:
    """Detailed metrics for a single MCP call."""
    call_id: str
    tool_id: str
    method: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: str = "pending"  # pending, success, failure, timeout
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    response_size: Optional[int] = None
    retry_count: int = 0
    timeout_used: float = 0
    persistent_connection: bool = False
    agent_id: Optional[str] = None
    context: Optional[Dict] = None

@dataclass
class MCPToolHealth:
    """Health metrics for an individual MCP tool."""
    tool_id: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    timeout_calls: int = 0
    avg_response_time: float = 0.0
    last_success_time: Optional[str] = None
    last_failure_time: Optional[str] = None
    consecutive_failures: int = 0
    health_score: float = 1.0  # 0.0 to 1.0
    connection_status: str = "unknown"  # healthy, degraded, unhealthy, unknown

@dataclass
class MCPSystemMetrics:
    """Overall MCP system metrics."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    timeout_calls: int = 0
    avg_response_time: float = 0.0
    tools_healthy: int = 0
    tools_degraded: int = 0
    tools_unhealthy: int = 0
    uptime_start: str = ""
    last_reset_time: str = ""

class MCPLogger:
    """Enhanced MCP logging with structured format and performance tracking."""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.logs_dir = self.project_dir / ".swarmdev" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = self._setup_logger()
        self.metrics_collector = MCPMetricsCollector()
        
    def _setup_logger(self) -> logging.Logger:
        """Set up structured MCP logger."""
        logger = logging.getLogger("mcp.enhanced")
        logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(
            self.logs_dir / "mcp_detailed.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Performance handler for metrics
        perf_handler = logging.FileHandler(
            self.logs_dir / "mcp_performance.log",
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        
        # Error handler for failures
        error_handler = logging.FileHandler(
            self.logs_dir / "mcp_errors.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.WARNING)
        
        # Custom formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
        )
        
        for handler in [file_handler, perf_handler, error_handler]:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def log_call_start(self, call_id: str, tool_id: str, method: str, 
                      params: Dict, timeout: float, agent_id: str = None,
                      context: Dict = None):
        """Log the start of an MCP call with full context."""
        call_data = {
            "event": "mcp_call_start",
            "call_id": call_id,
            "tool_id": tool_id,
            "method": method,
            "timeout": timeout,
            "agent_id": agent_id,
            "param_count": len(params) if params else 0,
            "has_context": context is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"MCP_CALL_START: {json.dumps(call_data)}")
        
        # Start metrics tracking
        metrics = MCPCallMetrics(
            call_id=call_id,
            tool_id=tool_id,
            method=method,
            start_time=time.time(),
            timeout_used=timeout,
            agent_id=agent_id,
            context=context
        )
        self.metrics_collector.start_call(metrics)
    
    def log_call_end(self, call_id: str, status: str, duration: float,
                    response: Dict = None, error: Exception = None):
        """Log the end of an MCP call with results."""
        call_data = {
            "event": "mcp_call_end",
            "call_id": call_id,
            "status": status,
            "duration": round(duration, 3),
            "response_size": len(str(response)) if response else 0,
            "has_error": error is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        if status == "success":
            self.logger.info(f"MCP_CALL_SUCCESS: {json.dumps(call_data)}")
        elif status == "timeout":
            self.logger.warning(f"MCP_CALL_TIMEOUT: {json.dumps(call_data)}")
        else:
            call_data["error_type"] = type(error).__name__ if error else "unknown"
            call_data["error_message"] = str(error) if error else "unspecified"
            self.logger.error(f"MCP_CALL_FAILURE: {json.dumps(call_data)}")
        
        # Complete metrics tracking
        self.metrics_collector.end_call(
            call_id, status, duration, response, error
        )
    
    def log_connection_event(self, tool_id: str, event: str, details: Dict = None):
        """Log MCP connection events (connect, disconnect, etc.)."""
        event_data = {
            "event": f"mcp_connection_{event}",
            "tool_id": tool_id,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            event_data.update(details)
        
        self.logger.info(f"MCP_CONNECTION: {json.dumps(event_data)}")
    
    def log_tool_health_check(self, tool_id: str, health: MCPToolHealth):
        """Log tool health assessment."""
        health_data = {
            "event": "mcp_tool_health",
            "tool_id": tool_id,
            "health_score": round(health.health_score, 3),
            "total_calls": health.total_calls,
            "success_rate": round(health.successful_calls / max(health.total_calls, 1), 3),
            "avg_response_time": round(health.avg_response_time, 3),
            "consecutive_failures": health.consecutive_failures,
            "connection_status": health.connection_status,
            "timestamp": datetime.now().isoformat()
        }
        
        if health.health_score < 0.5:
            self.logger.warning(f"MCP_TOOL_UNHEALTHY: {json.dumps(health_data)}")
        elif health.health_score < 0.8:
            self.logger.warning(f"MCP_TOOL_DEGRADED: {json.dumps(health_data)}")
        else:
            self.logger.info(f"MCP_TOOL_HEALTHY: {json.dumps(health_data)}")
    
    def log_system_metrics(self, metrics: MCPSystemMetrics):
        """Log overall system metrics."""
        system_data = {
            "event": "mcp_system_metrics",
            "total_calls": metrics.total_calls,
            "success_rate": round(metrics.successful_calls / max(metrics.total_calls, 1), 3),
            "avg_response_time": round(metrics.avg_response_time, 3),
            "tools_healthy": metrics.tools_healthy,
            "tools_degraded": metrics.tools_degraded,
            "tools_unhealthy": metrics.tools_unhealthy,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"MCP_SYSTEM_METRICS: {json.dumps(system_data)}")

class MCPMetricsCollector:
    """Collects and analyzes MCP metrics for performance insights."""
    
    def __init__(self, max_call_history: int = 1000):
        self.active_calls: Dict[str, MCPCallMetrics] = {}
        self.call_history: deque = deque(maxlen=max_call_history)
        self.tool_metrics: Dict[str, MCPToolHealth] = {}
        self.system_metrics = MCPSystemMetrics(
            uptime_start=datetime.now().isoformat()
        )
        self.lock = threading.Lock()
        
    def start_call(self, metrics: MCPCallMetrics):
        """Start tracking a new MCP call."""
        with self.lock:
            self.active_calls[metrics.call_id] = metrics
            
            # Initialize tool metrics if needed
            if metrics.tool_id not in self.tool_metrics:
                self.tool_metrics[metrics.tool_id] = MCPToolHealth(
                    tool_id=metrics.tool_id
                )
    
    def end_call(self, call_id: str, status: str, duration: float,
                response: Dict = None, error: Exception = None):
        """Complete tracking for an MCP call."""
        with self.lock:
            if call_id not in self.active_calls:
                return
            
            metrics = self.active_calls.pop(call_id)
            metrics.end_time = time.time()
            metrics.duration = duration
            metrics.status = status
            
            if error:
                metrics.error_type = type(error).__name__
                metrics.error_message = str(error)
            
            if response:
                metrics.response_size = len(str(response))
            
            # Update tool metrics
            tool_health = self.tool_metrics[metrics.tool_id]
            tool_health.total_calls += 1
            
            if status == "success":
                tool_health.successful_calls += 1
                tool_health.consecutive_failures = 0
                tool_health.last_success_time = datetime.now().isoformat()
            else:
                tool_health.failed_calls += 1
                tool_health.consecutive_failures += 1
                tool_health.last_failure_time = datetime.now().isoformat()
                
                if status == "timeout":
                    tool_health.timeout_calls += 1
            
            # Update response time average
            if tool_health.total_calls > 0:
                tool_health.avg_response_time = (
                    (tool_health.avg_response_time * (tool_health.total_calls - 1) + duration) 
                    / tool_health.total_calls
                )
            
            # Calculate health score
            success_rate = tool_health.successful_calls / tool_health.total_calls
            failure_penalty = min(tool_health.consecutive_failures * 0.1, 0.5)
            timeout_penalty = min(tool_health.timeout_calls / tool_health.total_calls * 0.3, 0.3)
            
            tool_health.health_score = max(0.0, success_rate - failure_penalty - timeout_penalty)
            
            # Determine connection status
            if tool_health.health_score >= 0.8:
                tool_health.connection_status = "healthy"
            elif tool_health.health_score >= 0.5:
                tool_health.connection_status = "degraded"
            else:
                tool_health.connection_status = "unhealthy"
            
            # Update system metrics
            self.system_metrics.total_calls += 1
            if status == "success":
                self.system_metrics.successful_calls += 1
            else:
                self.system_metrics.failed_calls += 1
                if status == "timeout":
                    self.system_metrics.timeout_calls += 1
            
            # Update system response time average
            if self.system_metrics.total_calls > 0:
                self.system_metrics.avg_response_time = (
                    (self.system_metrics.avg_response_time * (self.system_metrics.total_calls - 1) + duration)
                    / self.system_metrics.total_calls
                )
            
            # Add to history
            self.call_history.append(metrics)
    
    def get_tool_health(self, tool_id: str) -> Optional[MCPToolHealth]:
        """Get health metrics for a specific tool."""
        with self.lock:
            return self.tool_metrics.get(tool_id)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health report."""
        with self.lock:
            # Count tool health statuses
            healthy = sum(1 for h in self.tool_metrics.values() if h.connection_status == "healthy")
            degraded = sum(1 for h in self.tool_metrics.values() if h.connection_status == "degraded")
            unhealthy = sum(1 for h in self.tool_metrics.values() if h.connection_status == "unhealthy")
            
            self.system_metrics.tools_healthy = healthy
            self.system_metrics.tools_degraded = degraded
            self.system_metrics.tools_unhealthy = unhealthy
            
            return {
                "system_metrics": asdict(self.system_metrics),
                "tool_health": {tid: asdict(health) for tid, health in self.tool_metrics.items()},
                "active_calls": len(self.active_calls),
                "recent_performance": self._get_recent_performance()
            }
    
    def _get_recent_performance(self) -> Dict[str, Any]:
        """Analyze recent performance trends."""
        recent_calls = list(self.call_history)[-50:]  # Last 50 calls
        
        if not recent_calls:
            return {"calls": 0, "trends": "no_data"}
        
        success_count = sum(1 for call in recent_calls if call.status == "success")
        timeout_count = sum(1 for call in recent_calls if call.status == "timeout")
        avg_duration = sum(call.duration or 0 for call in recent_calls) / len(recent_calls)
        
        return {
            "calls": len(recent_calls),
            "success_rate": success_count / len(recent_calls),
            "timeout_rate": timeout_count / len(recent_calls),
            "avg_duration": avg_duration,
            "trend": "improving" if success_count > len(recent_calls) * 0.7 else "degrading"
        }
    
    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report."""
        health_data = self.get_system_health()
        
        report = ["=== MCP PERFORMANCE REPORT ==="]
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        # System overview
        system = health_data["system_metrics"]
        report.append("SYSTEM OVERVIEW:")
        report.append(f"  Total Calls: {system['total_calls']}")
        report.append(f"  Success Rate: {system['successful_calls'] / max(system['total_calls'], 1):.1%}")
        report.append(f"  Average Response Time: {system['avg_response_time']:.2f}s")
        report.append(f"  Tools Healthy/Degraded/Unhealthy: {system['tools_healthy']}/{system['tools_degraded']}/{system['tools_unhealthy']}")
        report.append("")
        
        # Tool breakdown
        report.append("TOOL PERFORMANCE:")
        for tool_id, health in health_data["tool_health"].items():
            status_emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(health["connection_status"], "❓")
            report.append(f"  {status_emoji} {tool_id}:")
            report.append(f"    Calls: {health['total_calls']} (Success: {health['successful_calls']}, Failed: {health['failed_calls']})")
            report.append(f"    Health Score: {health['health_score']:.2f}")
            report.append(f"    Avg Response: {health['avg_response_time']:.2f}s")
            report.append(f"    Consecutive Failures: {health['consecutive_failures']}")
        
        report.append("")
        
        # Recent trends
        recent = health_data["recent_performance"]
        if recent["calls"] > 0:
            report.append("RECENT TRENDS (Last 50 calls):")
            report.append(f"  Success Rate: {recent['success_rate']:.1%}")
            report.append(f"  Timeout Rate: {recent['timeout_rate']:.1%}")
            report.append(f"  Average Duration: {recent['avg_duration']:.2f}s")
            report.append(f"  Trend: {recent['trend'].title()}")
        
        return "\n".join(report)

# Global instances
_mcp_logger: Optional[MCPLogger] = None
_metrics_collector: Optional[MCPMetricsCollector] = None

def get_mcp_logger(project_dir: str = ".") -> MCPLogger:
    """Get or create the global MCP logger."""
    global _mcp_logger
    if _mcp_logger is None:
        _mcp_logger = MCPLogger(project_dir)
    return _mcp_logger

def get_metrics_collector() -> MCPMetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MCPMetricsCollector()
    return _metrics_collector 