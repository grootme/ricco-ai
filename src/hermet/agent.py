"""
Hermet Agent - Main Agent Implementation

Hermet is an autonomous monitoring agent that uses skills, tools, and MCP proxy
to monitor system health, collect metrics, and react to events.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import logging

from .metrics_collector import MetricsCollector
from .event_handler import EventHandler
from .alert_manager import AlertManager
from .reactors import ReactorRegistry


class HermetState(str, Enum):
    """Hermet agent states"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class HermetConfig:
    """Configuration for Hermet Agent"""
    name: str = "hermet"
    version: str = "1.0.0"
    
    # Monitoring intervals
    metrics_interval: float = 15.0  # seconds
    health_check_interval: float = 30.0  # seconds
    alert_check_interval: float = 10.0  # seconds
    
    # Thresholds
    cpu_threshold: float = 80.0  # percentage
    memory_threshold: float = 85.0  # percentage
    error_rate_threshold: float = 5.0  # percentage
    latency_threshold: float = 2000.0  # milliseconds
    
    # Alert settings
    alert_cooldown: float = 300.0  # seconds between same alerts
    max_alerts_per_minute: int = 10
    
    # MCP settings
    mcp_proxy_enabled: bool = True
    mcp_servers: List[str] = field(default_factory=lambda: [
        "prometheus",
        "loki",
        "tempo",
        "grafana"
    ])
    
    # Skill settings
    skills_enabled: bool = True
    auto_react: bool = True
    
    # Logging
    log_level: str = "INFO"


class HermetAgent:
    """
    Hermet Agent - Autonomous Monitoring Agent
    
    Uses skills, tools, and MCP proxy to:
    - Collect and analyze metrics from Prometheus
    - Monitor logs through Loki
    - Trace requests via Tempo
    - Visualize in Grafana
    - React to events automatically
    """
    
    def __init__(self, config: Optional[HermetConfig] = None):
        self.config = config or HermetConfig()
        self.state = HermetState.INITIALIZING
        self.logger = logging.getLogger(f"hermet.{self.config.name}")
        
        # Core components
        self.metrics_collector = MetricsCollector()
        self.event_handler = EventHandler()
        self.alert_manager = AlertManager(
            cooldown=self.config.alert_cooldown,
            max_per_minute=self.config.max_alerts_per_minute
        )
        self.reactor_registry = ReactorRegistry()
        
        # Runtime state
        self._tasks: List[asyncio.Task] = []
        self._running = False
        self._start_time: Optional[float] = None
        self._last_metrics: Dict[str, Any] = {}
        self._event_count = 0
        self._alert_count = 0
        
        # Registered callbacks
        self._on_metric_callbacks: List[Callable] = []
        self._on_alert_callbacks: List[Callable] = []
        self._on_event_callbacks: List[Callable] = []
        
    @property
    def uptime(self) -> float:
        """Get agent uptime in seconds"""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time
    
    @property
    def status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "name": self.config.name,
            "version": self.config.version,
            "state": self.state.value,
            "uptime": self.uptime,
            "events_processed": self._event_count,
            "alerts_sent": self._alert_count,
            "last_metrics": self._last_metrics,
            "tasks_running": len([t for t in self._tasks if not t.done()]),
        }
    
    async def initialize(self):
        """Initialize Hermet agent"""
        self.logger.info(f"Initializing Hermet Agent v{self.config.version}")
        self.state = HermetState.INITIALIZING
        
        # Initialize components
        await self.metrics_collector.initialize()
        await self.event_handler.initialize()
        await self.alert_manager.initialize()
        
        # Register default reactors
        self._register_default_reactors()
        
        self.logger.info("Hermet Agent initialized successfully")
    
    def _register_default_reactors(self):
        """Register default reactor implementations"""
        from .reactors import (
            HighCPUReactor,
            HighMemoryReactor,
            HighErrorRateReactor,
            HighLatencyReactor,
            MCPHealthReactor,
            AgentHealthReactor,
        )
        
        self.reactor_registry.register("high_cpu", HighCPUReactor())
        self.reactor_registry.register("high_memory", HighMemoryReactor())
        self.reactor_registry.register("high_error_rate", HighErrorRateReactor())
        self.reactor_registry.register("high_latency", HighLatencyReactor())
        self.reactor_registry.register("mcp_health", MCPHealthReactor())
        self.reactor_registry.register("agent_health", AgentHealthReactor())
    
    async def start(self):
        """Start Hermet agent monitoring"""
        if self._running:
            self.logger.warning("Hermet Agent is already running")
            return
        
        self._running = True
        self._start_time = time.time()
        self.state = HermetState.RUNNING
        
        self.logger.info("Starting Hermet Agent monitoring loops")
        
        # Start monitoring tasks
        self._tasks = [
            asyncio.create_task(self._metrics_loop()),
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._alert_check_loop()),
            asyncio.create_task(self._event_processing_loop()),
        ]
        
        # Wait for all tasks
        try:
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            self.logger.info("Hermet Agent tasks cancelled")
        except Exception as e:
            self.logger.error(f"Error in Hermet Agent: {e}")
            self.state = HermetState.ERROR
    
    async def stop(self):
        """Stop Hermet agent"""
        self.logger.info("Stopping Hermet Agent")
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self.state = HermetState.STOPPED
        self.logger.info("Hermet Agent stopped")
    
    async def pause(self):
        """Pause Hermet agent monitoring"""
        self.state = HermetState.PAUSED
        self.logger.info("Hermet Agent paused")
    
    async def resume(self):
        """Resume Hermet agent monitoring"""
        if self.state == HermetState.PAUSED:
            self.state = HermetState.RUNNING
            self.logger.info("Hermet Agent resumed")
    
    async def _metrics_loop(self):
        """Main metrics collection loop"""
        while self._running:
            try:
                if self.state == HermetState.RUNNING:
                    # Collect metrics from all sources
                    metrics = await self.metrics_collector.collect()
                    self._last_metrics = metrics
                    
                    # Notify callbacks
                    for callback in self._on_metric_callbacks:
                        try:
                            await callback(metrics)
                        except Exception as e:
                            self.logger.error(f"Error in metric callback: {e}")
                    
                    # Check thresholds and trigger reactors
                    if self.config.auto_react:
                        await self._check_thresholds(metrics)
                
                await asyncio.sleep(self.config.metrics_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in metrics loop: {e}")
                await asyncio.sleep(5)  # Back off on error
    
    async def _health_check_loop(self):
        """Health check loop for all components"""
        while self._running:
            try:
                if self.state == HermetState.RUNNING:
                    # Check MCP servers health
                    mcp_health = await self.metrics_collector.check_mcp_health()
                    
                    # Check agent health
                    agent_health = await self.metrics_collector.check_agent_health()
                    
                    # Check database health
                    db_health = await self.metrics_collector.check_database_health()
                    
                    # Emit health event
                    await self.event_handler.emit({
                        "type": "health_check",
                        "timestamp": time.time(),
                        "mcp": mcp_health,
                        "agents": agent_health,
                        "databases": db_health,
                    })
                
                await asyncio.sleep(self.config.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(10)
    
    async def _alert_check_loop(self):
        """Alert processing loop"""
        while self._running:
            try:
                if self.state == HermetState.RUNNING:
                    # Process pending alerts
                    alerts = await self.alert_manager.process_pending()
                    
                    for alert in alerts:
                        self._alert_count += 1
                        
                        # Notify callbacks
                        for callback in self._on_alert_callbacks:
                            try:
                                await callback(alert)
                            except Exception as e:
                                self.logger.error(f"Error in alert callback: {e}")
                
                await asyncio.sleep(self.config.alert_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in alert check loop: {e}")
                await asyncio.sleep(5)
    
    async def _event_processing_loop(self):
        """Event processing loop"""
        while self._running:
            try:
                if self.state == HermetState.RUNNING:
                    # Process events from queue
                    events = await self.event_handler.process_batch()
                    
                    for event in events:
                        self._event_count += 1
                        
                        # Notify callbacks
                        for callback in self._on_event_callbacks:
                            try:
                                await callback(event)
                            except Exception as e:
                                self.logger.error(f"Error in event callback: {e}")
                        
                        # Trigger reactors for event
                        if self.config.auto_react:
                            await self._trigger_reactors(event)
                
                await asyncio.sleep(1)  # Process events every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(5)
    
    async def _check_thresholds(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and trigger reactors"""
        # CPU check
        cpu_usage = metrics.get("system", {}).get("cpu_percent", 0)
        if cpu_usage > self.config.cpu_threshold:
            await self._trigger_reactor("high_cpu", {
                "value": cpu_usage,
                "threshold": self.config.cpu_threshold,
            })
        
        # Memory check
        memory_usage = metrics.get("system", {}).get("memory_percent", 0)
        if memory_usage > self.config.memory_threshold:
            await self._trigger_reactor("high_memory", {
                "value": memory_usage,
                "threshold": self.config.memory_threshold,
            })
        
        # Error rate check
        error_rate = metrics.get("http", {}).get("error_rate", 0)
        if error_rate > self.config.error_rate_threshold:
            await self._trigger_reactor("high_error_rate", {
                "value": error_rate,
                "threshold": self.config.error_rate_threshold,
            })
        
        # Latency check
        latency = metrics.get("http", {}).get("p99_latency", 0)
        if latency > self.config.latency_threshold:
            await self._trigger_reactor("high_latency", {
                "value": latency,
                "threshold": self.config.latency_threshold,
            })
    
    async def _trigger_reactor(self, reactor_name: str, data: Dict[str, Any]):
        """Trigger a specific reactor"""
        reactor = self.reactor_registry.get(reactor_name)
        if reactor:
            try:
                result = await reactor.execute(data)
                self.logger.info(f"Reactor {reactor_name} executed: {result}")
            except Exception as e:
                self.logger.error(f"Reactor {reactor_name} failed: {e}")
    
    async def _trigger_reactors(self, event: Dict[str, Any]):
        """Trigger reactors based on event type"""
        event_type = event.get("type", "")
        
        # Map event types to reactors
        reactor_mapping = {
            "mcp_server_down": "mcp_health",
            "agent_error": "agent_health",
            "high_cpu": "high_cpu",
            "high_memory": "high_memory",
            "high_error_rate": "high_error_rate",
            "high_latency": "high_latency",
        }
        
        reactor_name = reactor_mapping.get(event_type)
        if reactor_name:
            await self._trigger_reactor(reactor_name, event)
    
    # Registration methods
    
    def on_metric(self, callback: Callable):
        """Register callback for metric updates"""
        self._on_metric_callbacks.append(callback)
    
    def on_alert(self, callback: Callable):
        """Register callback for alerts"""
        self._on_alert_callbacks.append(callback)
    
    def on_event(self, callback: Callable):
        """Register callback for events"""
        self._on_event_callbacks.append(callback)
    
    def register_reactor(self, name: str, reactor: Any):
        """Register a custom reactor"""
        self.reactor_registry.register(name, reactor)
    
    # MCP Proxy Integration
    
    async def call_mcp_tool(self, server: str, tool: str, params: Dict[str, Any]) -> Any:
        """Call an MCP tool through the proxy"""
        if not self.config.mcp_proxy_enabled:
            raise RuntimeError("MCP proxy is disabled")
        
        return await self.metrics_collector.call_mcp_tool(server, tool, params)
    
    async def query_prometheus(self, query: str) -> Dict[str, Any]:
        """Query Prometheus metrics"""
        return await self.metrics_collector.query_prometheus(query)
    
    async def query_loki(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Query Loki logs"""
        return await self.metrics_collector.query_loki(query, limit)
    
    async def query_tempo(self, trace_id: str) -> Dict[str, Any]:
        """Query Tempo traces"""
        return await self.metrics_collector.query_tempo(trace_id)
    
    # Skill Integration
    
    async def execute_skill(self, skill_name: str, params: Dict[str, Any]) -> Any:
        """Execute a skill"""
        if not self.config.skills_enabled:
            raise RuntimeError("Skills are disabled")
        
        # Skills can be implemented as reactors
        reactor = self.reactor_registry.get(skill_name)
        if reactor:
            return await reactor.execute(params)
        
        raise ValueError(f"Unknown skill: {skill_name}")
