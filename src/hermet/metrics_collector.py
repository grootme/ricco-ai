"""
Metrics Collector for Hermet Agent

Collects metrics from multiple sources:
- Prometheus for metrics
- Loki for logs
- Tempo for traces
- Grafana for dashboards
- MCP servers via proxy
"""

import asyncio
import aiohttp
import time
from typing import Any, Dict, List, Optional
import logging
import json
from dataclasses import dataclass


@dataclass
class PrometheusConfig:
    """Prometheus configuration"""
    url: str = "http://localhost:9090"
    timeout: float = 10.0


@dataclass
class LokiConfig:
    """Loki configuration"""
    url: str = "http://localhost:3100"
    timeout: float = 10.0


@dataclass
class TempoConfig:
    """Tempo configuration"""
    url: str = "http://localhost:3200"
    timeout: float = 10.0


@dataclass
class GrafanaConfig:
    """Grafana configuration"""
    url: str = "http://localhost:3000"
    api_key: Optional[str] = None
    timeout: float = 10.0


class MetricsCollector:
    """
    Multi-source metrics collector for Hermet Agent
    
    Collects metrics from:
    - Prometheus (time-series metrics)
    - Loki (logs)
    - Tempo (distributed traces)
    - Grafana (dashboards)
    - MCP servers (via proxy)
    """
    
    def __init__(
        self,
        prometheus_config: Optional[PrometheusConfig] = None,
        loki_config: Optional[LokiConfig] = None,
        tempo_config: Optional[TempoConfig] = None,
        grafana_config: Optional[GrafanaConfig] = None,
    ):
        self.prometheus = prometheus_config or PrometheusConfig()
        self.loki = loki_config or LokiConfig()
        self.tempo = tempo_config or TempoConfig()
        self.grafana = grafana_config or GrafanaConfig()
        
        self.logger = logging.getLogger("hermet.metrics_collector")
        self._session: Optional[aiohttp.ClientSession] = None
        self._initialized = False
        
        # MCP proxy client
        self._mcp_clients: Dict[str, Any] = {}
    
    async def initialize(self):
        """Initialize the metrics collector"""
        if self._initialized:
            return
        
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100),
        )
        
        self._initialized = True
        self.logger.info("Metrics collector initialized")
    
    async def close(self):
        """Close the metrics collector"""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._initialized = False
        self.logger.info("Metrics collector closed")
    
    async def collect(self) -> Dict[str, Any]:
        """Collect metrics from all sources"""
        if not self._initialized:
            await self.initialize()
        
        metrics = {
            "timestamp": time.time(),
            "system": await self._collect_system_metrics(),
            "http": await self._collect_http_metrics(),
            "agents": await self._collect_agent_metrics(),
            "mcp": await self._collect_mcp_metrics(),
            "llm": await self._collect_llm_metrics(),
            "database": await self._collect_database_metrics(),
            "queue": await self._collect_queue_metrics(),
        }
        
        return metrics
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics from Prometheus"""
        metrics = {}
        
        try:
            # CPU usage
            cpu_query = '100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
            cpu_result = await self.query_prometheus(cpu_query)
            metrics["cpu_percent"] = self._extract_value(cpu_result, 0)
            
            # Memory usage
            mem_query = '100 * (1 - ((node_memory_MemAvailable_bytes) / (node_memory_MemTotal_bytes)))'
            mem_result = await self.query_prometheus(mem_query)
            metrics["memory_percent"] = self._extract_value(mem_result, 0)
            
            # Disk usage
            disk_query = '100 * (1 - ((node_filesystem_avail_bytes{mountpoint="/"}) / (node_filesystem_size_bytes{mountpoint="/"})))'
            disk_result = await self.query_prometheus(disk_query)
            metrics["disk_percent"] = self._extract_value(disk_result, 0)
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
        
        return metrics
    
    async def _collect_http_metrics(self) -> Dict[str, Any]:
        """Collect HTTP metrics from Prometheus"""
        metrics = {}
        
        try:
            # Request rate
            rate_query = 'sum(rate(ricco_http_requests_total[5m]))'
            rate_result = await self.query_prometheus(rate_query)
            metrics["request_rate"] = self._extract_value(rate_result, 0)
            
            # Error rate
            error_query = 'sum(rate(ricco_http_requests_total{status_code=~"5.."}[5m])) / sum(rate(ricco_http_requests_total[5m])) * 100'
            error_result = await self.query_prometheus(error_query)
            metrics["error_rate"] = self._extract_value(error_result, 0)
            
            # P99 latency
            latency_query = 'histogram_quantile(0.99, sum(rate(ricco_http_request_duration_seconds_bucket[5m])) by (le)) * 1000'
            latency_result = await self.query_prometheus(latency_query)
            metrics["p99_latency"] = self._extract_value(latency_result, 0)
            
            # Active requests
            active_query = 'sum(ricco_http_requests_in_progress)'
            active_result = await self.query_prometheus(active_query)
            metrics["active_requests"] = self._extract_value(active_result, 0)
            
        except Exception as e:
            self.logger.error(f"Error collecting HTTP metrics: {e}")
        
        return metrics
    
    async def _collect_agent_metrics(self) -> Dict[str, Any]:
        """Collect agent metrics from Prometheus"""
        metrics = {}
        
        try:
            # Active sessions
            sessions_query = 'sum(ricco_agent_active_sessions)'
            sessions_result = await self.query_prometheus(sessions_query)
            metrics["active_sessions"] = self._extract_value(sessions_result, 0)
            
            # Agent execution time (p95)
            exec_query = 'histogram_quantile(0.95, sum(rate(ricco_agent_execution_duration_seconds_bucket[5m])) by (le))'
            exec_result = await self.query_prometheus(exec_query)
            metrics["p95_execution_time"] = self._extract_value(exec_result, 0)
            
            # Agent errors
            error_query = 'sum(rate(ricco_agent_requests_total{status="error"}[5m]))'
            error_result = await self.query_prometheus(error_query)
            metrics["error_rate"] = self._extract_value(error_result, 0)
            
        except Exception as e:
            self.logger.error(f"Error collecting agent metrics: {e}")
        
        return metrics
    
    async def _collect_mcp_metrics(self) -> Dict[str, Any]:
        """Collect MCP metrics from Prometheus"""
        metrics = {}
        
        try:
            # Tool invocations
            invocations_query = 'sum(rate(ricco_mcp_tool_invocations_total[5m]))'
            invocations_result = await self.query_prometheus(invocations_query)
            metrics["tool_invocations_rate"] = self._extract_value(invocations_result, 0)
            
            # Active connections
            connections_query = 'sum(ricco_mcp_server_connections)'
            connections_result = await self.query_prometheus(connections_query)
            metrics["active_connections"] = self._extract_value(connections_result, 0)
            
            # Server health
            health_query = 'avg(ricco_mcp_server_health)'
            health_result = await self.query_prometheus(health_query)
            metrics["server_health_avg"] = self._extract_value(health_result, 1)
            
        except Exception as e:
            self.logger.error(f"Error collecting MCP metrics: {e}")
        
        return metrics
    
    async def _collect_llm_metrics(self) -> Dict[str, Any]:
        """Collect LLM/AI provider metrics from Prometheus"""
        metrics = {}
        
        try:
            # Request rate
            rate_query = 'sum(rate(ricco_llm_requests_total[5m]))'
            rate_result = await self.query_prometheus(rate_query)
            metrics["request_rate"] = self._extract_value(rate_result, 0)
            
            # Token usage
            tokens_query = 'sum(increase(ricco_llm_tokens_used_total[1h]))'
            tokens_result = await self.query_prometheus(tokens_query)
            metrics["tokens_hourly"] = self._extract_value(tokens_result, 0)
            
            # Cost
            cost_query = 'sum(ricco_llm_cost_total_dollars)'
            cost_result = await self.query_prometheus(cost_query)
            metrics["total_cost"] = self._extract_value(cost_result, 0)
            
            # Latency (p95)
            latency_query = 'histogram_quantile(0.95, sum(rate(ricco_llm_request_duration_seconds_bucket[5m])) by (le))'
            latency_result = await self.query_prometheus(latency_query)
            metrics["p95_latency"] = self._extract_value(latency_result, 0)
            
        except Exception as e:
            self.logger.error(f"Error collecting LLM metrics: {e}")
        
        return metrics
    
    async def _collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database metrics from Prometheus"""
        metrics = {}
        
        try:
            # Active connections
            conn_query = 'sum(ricco_db_connections_active)'
            conn_result = await self.query_prometheus(conn_query)
            metrics["active_connections"] = self._extract_value(conn_result, 0)
            
            # Query latency (p95)
            query_query = 'histogram_quantile(0.95, sum(rate(ricco_db_query_duration_seconds_bucket[5m])) by (le)) * 1000'
            query_result = await self.query_prometheus(query_query)
            metrics["p95_query_time_ms"] = self._extract_value(query_result, 0)
            
            # Errors
            error_query = 'sum(rate(ricco_db_errors_total[5m]))'
            error_result = await self.query_prometheus(error_query)
            metrics["error_rate"] = self._extract_value(error_result, 0)
            
        except Exception as e:
            self.logger.error(f"Error collecting database metrics: {e}")
        
        return metrics
    
    async def _collect_queue_metrics(self) -> Dict[str, Any]:
        """Collect queue/event metrics from Prometheus"""
        metrics = {}
        
        try:
            # Queue size
            size_query = 'sum(ricco_queue_size)'
            size_result = await self.query_prometheus(size_query)
            metrics["queue_size"] = self._extract_value(size_result, 0)
            
            # Processing rate
            rate_query = 'sum(rate(ricco_queue_messages_total{status="success"}[5m]))'
            rate_result = await self.query_prometheus(rate_query)
            metrics["processing_rate"] = self._extract_value(rate_result, 0)
            
            # Processing time
            time_query = 'histogram_quantile(0.95, sum(rate(ricco_queue_processing_time_seconds_bucket[5m])) by (le))'
            time_result = await self.query_prometheus(time_query)
            metrics["p95_processing_time"] = self._extract_value(time_result, 0)
            
        except Exception as e:
            self.logger.error(f"Error collecting queue metrics: {e}")
        
        return metrics
    
    def _extract_value(self, result: Dict[str, Any], default: float = 0) -> float:
        """Extract scalar value from Prometheus result"""
        try:
            data = result.get("data", {})
            result_list = data.get("result", [])
            if result_list:
                value = result_list[0].get("value", [None, default])
                return float(value[1]) if value[1] is not None else default
            return default
        except (KeyError, IndexError, TypeError, ValueError):
            return default
    
    async def query_prometheus(self, query: str) -> Dict[str, Any]:
        """Execute a Prometheus query"""
        if not self._session:
            await self.initialize()
        
        url = f"{self.prometheus.url}/api/v1/query"
        params = {"query": query}
        
        try:
            async with self._session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.prometheus.timeout),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"Prometheus query failed: {response.status}")
                    return {"data": {"result": []}}
        except Exception as e:
            self.logger.error(f"Prometheus query error: {e}")
            return {"data": {"result": []}}
    
    async def query_prometheus_range(
        self,
        query: str,
        start: float,
        end: float,
        step: str = "15s",
    ) -> Dict[str, Any]:
        """Execute a Prometheus range query"""
        if not self._session:
            await self.initialize()
        
        url = f"{self.prometheus.url}/api/v1/query_range"
        params = {
            "query": query,
            "start": start,
            "end": end,
            "step": step,
        }
        
        try:
            async with self._session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.prometheus.timeout),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"Prometheus range query failed: {response.status}")
                    return {"data": {"result": []}}
        except Exception as e:
            self.logger.error(f"Prometheus range query error: {e}")
            return {"data": {"result": []}}
    
    async def query_loki(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Query Loki logs"""
        if not self._session:
            await self.initialize()
        
        url = f"{self.loki.url}/loki/api/v1/query_range"
        params = {
            "query": query,
            "limit": limit,
            "start": int((time.time() - 3600) * 1e9),  # Last hour
            "end": int(time.time() * 1e9),
        }
        
        try:
            async with self._session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.loki.timeout),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_loki_results(data)
                else:
                    self.logger.error(f"Loki query failed: {response.status}")
                    return []
        except Exception as e:
            self.logger.error(f"Loki query error: {e}")
            return []
    
    def _parse_loki_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Loki query results"""
        results = []
        try:
            for stream in data.get("data", {}).get("result", []):
                labels = stream.get("stream", {})
                for value in stream.get("values", []):
                    timestamp_ns, log_line = value
                    results.append({
                        "timestamp": int(timestamp_ns) / 1e9,
                        "labels": labels,
                        "message": log_line,
                    })
        except Exception as e:
            self.logger.error(f"Error parsing Loki results: {e}")
        
        return results
    
    async def query_tempo(self, trace_id: str) -> Dict[str, Any]:
        """Query Tempo for a specific trace"""
        if not self._session:
            await self.initialize()
        
        url = f"{self.tempo.url}/api/traces/{trace_id}"
        
        try:
            async with self._session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=self.tempo.timeout),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"Tempo query failed: {response.status}")
                    return {}
        except Exception as e:
            self.logger.error(f"Tempo query error: {e}")
            return {}
    
    async def check_mcp_health(self) -> Dict[str, Any]:
        """Check health of all MCP servers"""
        health = {}
        
        try:
            # Query MCP server health metrics
            query = 'ricco_mcp_server_health'
            result = await self.query_prometheus(query)
            
            for item in result.get("data", {}).get("result", []):
                server_id = item.get("metric", {}).get("server_id", "unknown")
                value = item.get("value", [None, 0])
                health[server_id] = {
                    "healthy": float(value[1]) == 1.0 if value[1] else False,
                    "last_check": time.time(),
                }
        except Exception as e:
            self.logger.error(f"Error checking MCP health: {e}")
        
        return health
    
    async def check_agent_health(self) -> Dict[str, Any]:
        """Check health of all agents"""
        health = {}
        
        try:
            # Query agent error rates
            query = 'sum by (agent_type) (rate(ricco_agent_requests_total{status="error"}[5m]))'
            result = await self.query_prometheus(query)
            
            for item in result.get("data", {}).get("result", []):
                agent_type = item.get("metric", {}).get("agent_type", "unknown")
                value = item.get("value", [None, 0])
                error_rate = float(value[1]) if value[1] else 0
                health[agent_type] = {
                    "healthy": error_rate < 0.1,  # Less than 10% error rate
                    "error_rate": error_rate,
                    "last_check": time.time(),
                }
        except Exception as e:
            self.logger.error(f"Error checking agent health: {e}")
        
        return health
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check health of databases"""
        health = {}
        
        try:
            # Query database error rates
            query = 'sum by (database) (rate(ricco_db_errors_total[5m]))'
            result = await self.query_prometheus(query)
            
            for item in result.get("data", {}).get("result", []):
                database = item.get("metric", {}).get("database", "unknown")
                value = item.get("value", [None, 0])
                error_rate = float(value[1]) if value[1] else 0
                health[database] = {
                    "healthy": error_rate < 0.01,  # Less than 1% error rate
                    "error_rate": error_rate,
                    "last_check": time.time(),
                }
        except Exception as e:
            self.logger.error(f"Error checking database health: {e}")
        
        return health
    
    async def call_mcp_tool(
        self,
        server: str,
        tool: str,
        params: Dict[str, Any],
    ) -> Any:
        """Call an MCP tool through the proxy"""
        # This would integrate with the MCP proxy system
        self.logger.info(f"Calling MCP tool: {server}.{tool}")
        
        # Placeholder for MCP proxy integration
        # In production, this would route through the actual MCP proxy
        return {
            "server": server,
            "tool": tool,
            "params": params,
            "result": "mock_result",
        }
