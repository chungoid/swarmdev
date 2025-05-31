"""
Log Analyzer utility for the SwarmDev platform.
This module provides tools to analyze and summarize agent logs for workflow understanding.
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TaskExecution:
    """Represents a single task execution."""
    task_id: str
    agent_type: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    status: str
    goal: str
    files_created: List[str]
    files_modified: List[str]
    decisions: List[Dict]
    llm_calls: List[Dict]
    errors: List[Dict]


class LogAnalyzer:
    """
    Analyzer for SwarmDev agent logs that provides insights into workflow execution.
    """
    
    def __init__(self, logs_dir: str = "logs"):
        """
        Initialize the log analyzer.
        
        Args:
            logs_dir: Directory containing log files
        """
        self.logs_dir = logs_dir
        self.log_files = self._discover_log_files()
    
    def _discover_log_files(self) -> Dict[str, str]:
        """Discover available log files."""
        log_files = {}
        
        if not os.path.exists(self.logs_dir):
            return log_files
        
        for file in os.listdir(self.logs_dir):
            if file.endswith('.log'):
                agent_type = file.replace('.log', '').replace('agent', '')
                log_files[agent_type] = os.path.join(self.logs_dir, file)
        
        return log_files
    
    def analyze_workflow_execution(self, workflow_id: Optional[str] = None) -> Dict:
        """
        Analyze a complete workflow execution across all agents.
        
        Args:
            workflow_id: Optional workflow ID to filter by
            
        Returns:
            Dict: Comprehensive workflow analysis
        """
        analysis = {
            "workflow_summary": {},
            "agent_executions": {},
            "timeline": [],
            "performance_metrics": {},
            "insights": [],
            "recommendations": []
        }
        
        # Analyze each agent's logs
        all_tasks = []
        for agent_type, log_file in self.log_files.items():
            agent_tasks = self._parse_agent_log(log_file, agent_type)
            all_tasks.extend(agent_tasks)
            analysis["agent_executions"][agent_type] = self._summarize_agent_execution(agent_tasks)
        
        # Filter by workflow if specified
        if workflow_id:
            all_tasks = [task for task in all_tasks if workflow_id in task.task_id]
        
        # Create timeline and summary
        analysis["timeline"] = self._create_execution_timeline(all_tasks)
        analysis["workflow_summary"] = self._create_workflow_summary(all_tasks)
        analysis["performance_metrics"] = self._calculate_performance_metrics(all_tasks)
        analysis["insights"] = self._generate_insights(all_tasks)
        analysis["recommendations"] = self._generate_recommendations(all_tasks)
        
        return analysis
    
    def _parse_agent_log(self, log_file: str, agent_type: str) -> List[TaskExecution]:
        """Parse a single agent log file and extract task executions."""
        tasks = []
        current_task = None
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                # Parse task start
                if "TASK STARTED:" in line:
                    task_id = self._extract_task_id(line)
                    if task_id:
                        current_task = TaskExecution(
                            task_id=task_id,
                            agent_type=agent_type,
                            start_time=self._extract_timestamp(line),
                            end_time=None,
                            duration=None,
                            status="running",
                            goal="",
                            files_created=[],
                            files_modified=[],
                            decisions=[],
                            llm_calls=[],
                            errors=[]
                        )
                
                # Parse task completion
                elif "TASK COMPLETED:" in line and current_task:
                    current_task.end_time = self._extract_timestamp(line)
                    current_task.status = "completed"
                
                # Parse duration
                elif "Duration:" in line and current_task:
                    duration_match = re.search(r'Duration: ([\d.]+) seconds', line)
                    if duration_match:
                        current_task.duration = float(duration_match.group(1))
                        tasks.append(current_task)
                        current_task = None
                
                # Parse goal
                elif "Goal:" in line and current_task:
                    goal_match = re.search(r'Goal: (.+)', line)
                    if goal_match:
                        current_task.goal = goal_match.group(1)
                
                # Parse file operations
                elif "FILE CREATED:" in line and current_task:
                    file_match = re.search(r'FILE CREATED: (.+)', line)
                    if file_match:
                        current_task.files_created.append(file_match.group(1))
                
                elif "FILE MODIFIED:" in line and current_task:
                    file_match = re.search(r'FILE MODIFIED: (.+)', line)
                    if file_match:
                        current_task.files_modified.append(file_match.group(1))
                
                # Parse decisions
                elif "DECISION:" in line and current_task:
                    decision_match = re.search(r'DECISION: (.+)', line)
                    if decision_match:
                        current_task.decisions.append({
                            "decision": decision_match.group(1),
                            "timestamp": self._extract_timestamp(line)
                        })
                
                # Parse LLM calls
                elif "LLM CALL:" in line and current_task:
                    llm_match = re.search(r'LLM CALL: (.+)', line)
                    if llm_match:
                        current_task.llm_calls.append({
                            "call_type": llm_match.group(1),
                            "timestamp": self._extract_timestamp(line)
                        })
                
                # Parse errors
                elif "ERROR OCCURRED:" in line and current_task:
                    error_match = re.search(r'ERROR OCCURRED: (.+)', line)
                    if error_match:
                        current_task.errors.append({
                            "error": error_match.group(1),
                            "timestamp": self._extract_timestamp(line)
                        })
                        current_task.status = "failed"
        
        except Exception as e:
            print(f"Error parsing log file {log_file}: {e}")
        
        return tasks
    
    def _extract_task_id(self, line: str) -> Optional[str]:
        """Extract task ID from log line."""
        match = re.search(r'TASK STARTED: (.+)', line)
        return match.group(1) if match else None
    
    def _extract_timestamp(self, line: str) -> datetime:
        """Extract timestamp from log line."""
        match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        if match:
            return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
        return datetime.now()
    
    def _summarize_agent_execution(self, tasks: List[TaskExecution]) -> Dict:
        """Summarize execution for a single agent."""
        if not tasks:
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "total_duration": 0,
                "avg_duration": 0,
                "files_created": 0,
                "files_modified": 0,
                "decisions_made": 0,
                "llm_calls": 0
            }
        
        completed_tasks = [t for t in tasks if t.status == "completed"]
        failed_tasks = [t for t in tasks if t.status == "failed"]
        total_duration = sum(t.duration for t in tasks if t.duration)
        
        return {
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "total_duration": total_duration,
            "avg_duration": total_duration / len(tasks) if tasks else 0,
            "files_created": sum(len(t.files_created) for t in tasks),
            "files_modified": sum(len(t.files_modified) for t in tasks),
            "decisions_made": sum(len(t.decisions) for t in tasks),
            "llm_calls": sum(len(t.llm_calls) for t in tasks)
        }
    
    def _create_execution_timeline(self, tasks: List[TaskExecution]) -> List[Dict]:
        """Create a timeline of task executions."""
        timeline = []
        
        for task in sorted(tasks, key=lambda t: t.start_time):
            timeline.append({
                "timestamp": task.start_time.isoformat(),
                "agent_type": task.agent_type,
                "task_id": task.task_id,
                "event": "task_started",
                "duration": task.duration
            })
            
            if task.end_time:
                timeline.append({
                    "timestamp": task.end_time.isoformat(),
                    "agent_type": task.agent_type,
                    "task_id": task.task_id,
                    "event": "task_completed",
                    "status": task.status
                })
        
        return timeline
    
    def _create_workflow_summary(self, tasks: List[TaskExecution]) -> Dict:
        """Create overall workflow summary."""
        if not tasks:
            return {}
        
        start_time = min(t.start_time for t in tasks)
        end_time = max(t.end_time for t in tasks if t.end_time)
        total_duration = (end_time - start_time).total_seconds() if end_time else 0
        
        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat() if end_time else None,
            "total_duration": total_duration,
            "total_tasks": len(tasks),
            "agents_involved": list(set(t.agent_type for t in tasks)),
            "success_rate": len([t for t in tasks if t.status == "completed"]) / len(tasks),
            "total_files_created": sum(len(t.files_created) for t in tasks),
            "total_files_modified": sum(len(t.files_modified) for t in tasks)
        }
    
    def _calculate_performance_metrics(self, tasks: List[TaskExecution]) -> Dict:
        """Calculate performance metrics."""
        if not tasks:
            return {}
        
        durations = [t.duration for t in tasks if t.duration]
        
        return {
            "avg_task_duration": sum(durations) / len(durations) if durations else 0,
            "max_task_duration": max(durations) if durations else 0,
            "min_task_duration": min(durations) if durations else 0,
            "total_llm_calls": sum(len(t.llm_calls) for t in tasks),
            "avg_llm_calls_per_task": sum(len(t.llm_calls) for t in tasks) / len(tasks),
            "error_rate": len([t for t in tasks if t.errors]) / len(tasks),
            "productivity_score": sum(len(t.files_created) + len(t.files_modified) for t in tasks) / len(tasks)
        }
    
    def _generate_insights(self, tasks: List[TaskExecution]) -> List[str]:
        """Generate insights from task execution data."""
        insights = []
        
        if not tasks:
            return ["No task execution data available for analysis."]
        
        # Performance insights
        durations = [t.duration for t in tasks if t.duration]
        if durations:
            avg_duration = sum(durations) / len(durations)
            if avg_duration > 300:  # 5 minutes
                insights.append(f"Tasks are taking longer than expected (avg: {avg_duration:.1f}s). Consider optimization.")
        
        # File creation insights
        total_files = sum(len(t.files_created) + len(t.files_modified) for t in tasks)
        if total_files == 0:
            insights.append("No files were created or modified. Check if agents are producing output.")
        elif total_files < len(tasks):
            insights.append("Low file output relative to task count. Agents may not be generating enough content.")
        
        # Error insights
        error_tasks = [t for t in tasks if t.errors]
        if error_tasks:
            insights.append(f"{len(error_tasks)} tasks encountered errors. Review error logs for debugging.")
        
        # Agent utilization insights
        agent_types = set(t.agent_type for t in tasks)
        if len(agent_types) == 1:
            insights.append("Only one agent type was used. Consider if multi-agent workflow would be beneficial.")
        
        return insights
    
    def _generate_recommendations(self, tasks: List[TaskExecution]) -> List[str]:
        """Generate recommendations for workflow improvement."""
        recommendations = []
        
        if not tasks:
            return ["Ensure agents are properly configured and tasks are being executed."]
        
        # Performance recommendations
        durations = [t.duration for t in tasks if t.duration]
        if durations and max(durations) > 600:  # 10 minutes
            recommendations.append("Consider breaking down long-running tasks into smaller chunks.")
        
        # LLM usage recommendations
        total_llm_calls = sum(len(t.llm_calls) for t in tasks)
        if total_llm_calls > len(tasks) * 5:
            recommendations.append("High LLM usage detected. Consider caching or batching LLM calls for efficiency.")
        
        # Output recommendations
        avg_files_per_task = sum(len(t.files_created) + len(t.files_modified) for t in tasks) / len(tasks)
        if avg_files_per_task < 1:
            recommendations.append("Increase file output per task to improve productivity.")
        
        return recommendations
    
    def generate_workflow_report(self, output_file: str = "workflow_analysis.md") -> str:
        """Generate a comprehensive workflow analysis report."""
        analysis = self.analyze_workflow_execution()
        
        report = f"""# SwarmDev Workflow Analysis Report

Generated: {datetime.now().isoformat()}

## Workflow Summary

- **Start Time**: {analysis['workflow_summary'].get('start_time', 'N/A')}
- **End Time**: {analysis['workflow_summary'].get('end_time', 'N/A')}
- **Total Duration**: {analysis['workflow_summary'].get('total_duration', 0):.1f} seconds
- **Total Tasks**: {analysis['workflow_summary'].get('total_tasks', 0)}
- **Success Rate**: {analysis['workflow_summary'].get('success_rate', 0)*100:.1f}%
- **Files Created**: {analysis['workflow_summary'].get('total_files_created', 0)}
- **Files Modified**: {analysis['workflow_summary'].get('total_files_modified', 0)}

## Agent Performance

"""
        
        for agent_type, metrics in analysis['agent_executions'].items():
            report += f"""### {agent_type.title()}Agent

- **Tasks Executed**: {metrics['total_tasks']}
- **Success Rate**: {metrics['completed_tasks']}/{metrics['total_tasks']} ({metrics['completed_tasks']/max(metrics['total_tasks'], 1)*100:.1f}%)
- **Avg Duration**: {metrics['avg_duration']:.1f}s
- **Files Created**: {metrics['files_created']}
- **Files Modified**: {metrics['files_modified']}
- **Decisions Made**: {metrics['decisions_made']}
- **LLM Calls**: {metrics['llm_calls']}

"""
        
        report += f"""## Performance Metrics

- **Average Task Duration**: {analysis['performance_metrics'].get('avg_task_duration', 0):.1f}s
- **Total LLM Calls**: {analysis['performance_metrics'].get('total_llm_calls', 0)}
- **Productivity Score**: {analysis['performance_metrics'].get('productivity_score', 0):.2f}
- **Error Rate**: {analysis['performance_metrics'].get('error_rate', 0)*100:.1f}%

## Insights

"""
        
        for insight in analysis['insights']:
            report += f"- {insight}\n"
        
        report += "\n## Recommendations\n\n"
        
        for recommendation in analysis['recommendations']:
            report += f"- {recommendation}\n"
        
        # Save report
        with open(output_file, 'w') as f:
            f.write(report)
        
        return report


def analyze_logs(logs_dir: str = "logs") -> None:
    """Quick function to analyze logs and generate a report."""
    analyzer = LogAnalyzer(logs_dir)
    report = analyzer.generate_workflow_report()
    print(f"Workflow analysis complete! Report saved to workflow_analysis.md")
    print("\n" + "="*60)
    print(report[:1000] + "..." if len(report) > 1000 else report)


if __name__ == "__main__":
    analyze_logs() 