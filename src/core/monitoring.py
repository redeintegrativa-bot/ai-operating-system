from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import psutil
import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import argparse
from collections import defaultdict


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class Metric:
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]


@dataclass
class HealthCheck:
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime


@dataclass
class Alert:
    level: str
    message: str
    timestamp: datetime
    context: Optional[Dict] = None


class Monitor:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.metrics: List[Metric] = []
        self.health_checks: List[HealthCheck] = []
        self.alerts: List[Alert] = []
        self.start_time = time.time()
        
        self._setup_logger()
        self._setup_directories()
    
    def _setup_logger(self):
        log_dir = os.path.join(self.project_root, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        self.logger = logging.getLogger("monitor")
        self.logger.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "monitor.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        json_handler = RotatingFileHandler(
            os.path.join(log_dir, "monitor.json"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        json_handler.setLevel(logging.DEBUG)
        json_formatter = logging.Formatter("%(message)s")
        json_handler.setFormatter(json_formatter)
        self.json_handler = json_handler
    
    def _setup_directories(self):
        os.makedirs(os.path.join(self.project_root, "logs"), exist_ok=True)
        os.makedirs(os.path.join(self.project_root, "metrics"), exist_ok=True)
    
    def log(self, level: LogLevel, message: str, context: Optional[Dict] = None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "message": message,
            "context": context or {}
        }
        
        log_level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        
        self.logger.log(log_level_map[level], message)
        
        if hasattr(self, 'json_handler'):
            self.json_handler.emit(
                logging.LogRecord(
                    name="monitor",
                    level=log_level_map[level],
                    pathname="",
                    lineno=0,
                    msg=json.dumps(log_entry),
                    args=(),
                    exc_info=None
                )
            )
        
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self._trigger_alert(level.value, message, context)
    
    def _trigger_alert(self, level: str, message: str, context: Optional[Dict] = None):
        alert = Alert(
            level=level,
            message=message,
            timestamp=datetime.now(),
            context=context
        )
        self.alerts.append(alert)
        
        self.log(LogLevel.INFO, f"Alert triggered: {level} - {message}", {"alert": True})
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict] = None):
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {}
        )
        self.metrics.append(metric)
        
        self.log(LogLevel.DEBUG, f"Metric recorded: {name}={value}", {"labels": labels})
    
    def get_metrics(self, name: Optional[str] = None) -> List[Metric]:
        if name:
            return [m for m in self.metrics if m.name == name]
        return self.metrics
    
    def health_check(self) -> HealthStatus:
        checks = []
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            cpu_status = HealthStatus.HEALTHY
            if cpu_percent > 90:
                cpu_status = HealthStatus.UNHEALTHY
            elif cpu_percent > 70:
                cpu_status = HealthStatus.DEGRADED
            
            memory_status = HealthStatus.HEALTHY
            if memory.percent > 90:
                memory_status = HealthStatus.UNHEALTHY
            elif memory.percent > 70:
                memory_status = HealthStatus.DEGRADED
            
            checks.append(HealthCheck(
                component="cpu",
                status=cpu_status,
                message=f"CPU usage: {cpu_percent}%",
                timestamp=datetime.now()
            ))
            
            checks.append(HealthCheck(
                component="memory",
                status=memory_status,
                message=f"Memory usage: {memory.percent}%",
                timestamp=datetime.now()
            ))
            
            log_dir = os.path.join(self.project_root, "logs")
            log_accessible = os.path.exists(log_dir) and os.access(log_dir, os.W_OK)
            
            log_status = HealthStatus.HEALTHY if log_accessible else HealthStatus.UNHEALTHY
            checks.append(HealthCheck(
                component="logs",
                status=log_status,
                message="Log directory accessible" if log_accessible else "Log directory not accessible",
                timestamp=datetime.now()
            ))
            
        except Exception as e:
            checks.append(HealthCheck(
                component="system",
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.now()
            ))
        
        self.health_checks.extend(checks)
        
        statuses = [c.status for c in checks]
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY
    
    def get_system_metrics(self) -> Dict:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            uptime = time.time() - self.start_time
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024 ** 3),
                "memory_total_gb": memory.total / (1024 ** 3),
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / (1024 ** 3),
                "disk_total_gb": disk.total / (1024 ** 3),
                "uptime_seconds": uptime,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def get_task_metrics(self) -> Dict:
        task_metrics = [m for m in self.metrics if m.name.startswith("task.")]
        
        created = len([m for m in task_metrics if m.name == "task.created"])
        completed = len([m for m in task_metrics if m.name == "task.completed"])
        failed = len([m for m in task_metrics if m.name == "task.failed"])
        
        completion_times = [m.value for m in task_metrics if m.name == "task.completion_time"]
        avg_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        return {
            "created": created,
            "completed": completed,
            "failed": failed,
            "success_rate": (completed / created * 100) if created > 0 else 0,
            "avg_completion_time": avg_time,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_agent_metrics(self) -> Dict:
        agent_tasks = defaultdict(lambda: {"total": 0, "completed": 0, "failed": 0})
        
        for metric in self.metrics:
            if metric.name.startswith("task.") and "agent_id" in metric.labels:
                agent_id = metric.labels["agent_id"]
                agent_tasks[agent_id]["total"] += 1
                
                if metric.name == "task.completed":
                    agent_tasks[agent_id]["completed"] += 1
                elif metric.name == "task.failed":
                    agent_tasks[agent_id]["failed"] += 1
        
        agent_summary = {}
        for agent_id, stats in agent_tasks.items():
            success_rate = (stats["completed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            agent_summary[agent_id] = {
                "total_tasks": stats["total"],
                "completed": stats["completed"],
                "failed": stats["failed"],
                "success_rate": success_rate
            }
        
        return {
            "agents": agent_summary,
            "total_agents": len(agent_summary),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_custom_metrics(self, prefix: Optional[str] = None) -> List[Dict]:
        if prefix:
            metrics = [m for m in self.metrics if m.name.startswith(prefix)]
        else:
            metrics = self.metrics
        
        return [asdict(m) for m in metrics]
    
    def generate_report(self) -> Dict:
        system_metrics = self.get_system_metrics()
        task_metrics = self.get_task_metrics()
        agent_metrics = self.get_agent_metrics()
        health_status = self.health_check()
        
        recent_alerts = [asdict(a) for a in self.alerts[-10:]]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": system_metrics,
            "tasks": task_metrics,
            "agents": agent_metrics,
            "health_status": health_status.value,
            "recent_alerts": recent_alerts,
            "total_metrics_recorded": len(self.metrics),
            "uptime_seconds": time.time() - self.start_time
        }
    
    def save_metrics(self):
        metrics_file = os.path.join(self.project_root, "metrics", "metrics.json")
        metrics_data = [asdict(m) for m in self.metrics]
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2, default=str)
        
        self.log(LogLevel.DEBUG, f"Saved {len(metrics_data)} metrics to {metrics_file}")
    
    def load_metrics(self):
        metrics_file = os.path.join(self.project_root, "metrics", "metrics.json")
        
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
            
            self.metrics = [Metric(**m) for m in metrics_data]
            self.log(LogLevel.INFO, f"Loaded {len(self.metrics)} metrics from {metrics_file}")


def main():
    parser = argparse.ArgumentParser(description="AI Operating System Monitor")
    parser.add_argument("--project-root", default="/root/ai-operating-system",
                       help="Project root directory")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    log_parser = subparsers.add_parser("log", help="Log a message")
    log_parser.add_argument("level", choices=["debug", "info", "warning", "error", "critical"],
                           help="Log level")
    log_parser.add_argument("message", help="Message to log")
    
    metric_parser = subparsers.add_parser("metric", help="Record a metric")
    metric_parser.add_argument("name", help="Metric name")
    metric_parser.add_argument("value", type=float, help="Metric value")
    metric_parser.add_argument("--labels", type=json.loads, default={},
                              help="Labels as JSON string")
    
    subparsers.add_parser("health", help="Perform health check")
    subparsers.add_parser("report", help="Generate full report")
    subparsers.add_parser("system", help="Show system metrics")
    subparsers.add_parser("tasks", help="Show task metrics")
    subparsers.add_parser("agents", help="Show agent metrics")
    subparsers.add_parser("alerts", help="Show recent alerts")
    
    args = parser.parse_args()
    
    monitor = Monitor(args.project_root)
    
    if args.command == "log":
        level = LogLevel(args.level)
        monitor.log(level, args.message)
        print(f"Logged [{args.level}]: {args.message}")
    
    elif args.command == "metric":
        monitor.record_metric(args.name, args.value, args.labels)
        print(f"Recorded metric: {args.name}={args.value}")
    
    elif args.command == "health":
        status = monitor.health_check()
        print(f"Health Status: {status.value}")
        for check in monitor.health_checks[-3:]:
            print(f"  {check.component}: {check.status.value} - {check.message}")
    
    elif args.command == "report":
        report = monitor.generate_report()
        print(json.dumps(report, indent=2, default=str))
    
    elif args.command == "system":
        metrics = monitor.get_system_metrics()
        print(json.dumps(metrics, indent=2, default=str))
    
    elif args.command == "tasks":
        metrics = monitor.get_task_metrics()
        print(json.dumps(metrics, indent=2, default=str))
    
    elif args.command == "agents":
        metrics = monitor.get_agent_metrics()
        print(json.dumps(metrics, indent=2, default=str))
    
    elif args.command == "alerts":
        alerts = [asdict(a) for a in monitor.alerts[-10:]]
        print(json.dumps(alerts, indent=2, default=str))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
