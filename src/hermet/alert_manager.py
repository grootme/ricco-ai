"""
Alert Manager for Hermet Agent

Manages alerts with deduplication, throttling, and multi-channel delivery.
"""

import asyncio
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid
from datetime import datetime


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status"""
    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"


@dataclass
class Alert:
    """Alert data structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    status: AlertStatus = AlertStatus.PENDING
    source: str = "hermet"
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    fired_at: Optional[float] = None
    resolved_at: Optional[float] = None
    fingerprint: str = ""  # For deduplication
    count: int = 1
    last_notification: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity.value,
            "status": self.status.value,
            "source": self.source,
            "message": self.message,
            "details": self.details,
            "labels": self.labels,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "fired_at": self.fired_at,
            "resolved_at": self.resolved_at,
            "fingerprint": self.fingerprint,
            "count": self.count,
            "last_notification": self.last_notification,
        }


@dataclass
class AlertRule:
    """Alert rule definition"""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity = AlertSeverity.WARNING
    message_template: str = "Alert: {name}"
    cooldown: float = 300.0  # seconds
    auto_resolve: bool = True
    resolve_after: float = 600.0  # seconds
    labels: Dict[str, str] = field(default_factory=dict)


class AlertManager:
    """
    Alert manager with deduplication and throttling
    
    Features:
    - Alert deduplication using fingerprints
    - Rate limiting and cooldown
    - Multi-channel notification
    - Alert aggregation
    - Auto-resolution
    """
    
    def __init__(
        self,
        cooldown: float = 300.0,
        max_per_minute: int = 10,
        retention_hours: int = 24,
    ):
        self.default_cooldown = cooldown
        self.max_per_minute = max_per_minute
        self.retention_hours = retention_hours
        
        self.logger = logging.getLogger("hermet.alert_manager")
        
        # Alert storage
        self._alerts: Dict[str, Alert] = {}
        self._pending: List[Alert] = []
        
        # Rate limiting
        self._alert_times: Dict[str, List[float]] = defaultdict(list)
        self._notification_times: Dict[str, float] = {}
        
        # Alert rules
        self._rules: Dict[str, AlertRule] = {}
        
        # Notification channels
        self._channels: List[Callable] = []
        
        # Statistics
        self._total_alerts = 0
        self._notifications_sent = 0
        self._alerts_suppressed = 0
        self._initialized = False
    
    async def initialize(self):
        """Initialize the alert manager"""
        self._initialized = True
        self.logger.info("Alert manager initialized")
    
    def register_rule(self, rule: AlertRule):
        """Register an alert rule"""
        self._rules[rule.name] = rule
        self.logger.info(f"Registered alert rule: {rule.name}")
    
    def add_notification_channel(self, channel: Callable):
        """Add a notification channel"""
        self._channels.append(channel)
        self.logger.info(f"Added notification channel: {channel.__name__ if hasattr(channel, '__name__') else 'anonymous'}")
    
    async def create_alert(
        self,
        name: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.WARNING,
        source: str = "hermet",
        details: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Alert:
        """Create a new alert"""
        if not self._initialized:
            await self.initialize()
        
        # Generate fingerprint for deduplication
        fingerprint = self._generate_fingerprint(name, source, labels)
        
        # Check for existing alert
        if fingerprint in self._alerts:
            existing = self._alerts[fingerprint]
            existing.count += 1
            existing.updated_at = time.time()
            
            # Check if we should notify (cooldown)
            if self._should_notify(fingerprint):
                self._pending.append(existing)
            
            return existing
        
        # Create new alert
        alert = Alert(
            name=name,
            severity=severity,
            source=source,
            message=message,
            details=details or {},
            labels=labels or {},
            fingerprint=fingerprint,
        )
        
        self._alerts[fingerprint] = alert
        self._total_alerts += 1
        
        # Add to pending queue
        if self._should_notify(fingerprint):
            self._pending.append(alert)
        
        return alert
    
    async def process_pending(self) -> List[Alert]:
        """Process pending alerts and send notifications"""
        if not self._pending:
            return []
        
        alerts_to_send = []
        now = time.time()
        
        for alert in self._pending:
            # Check rate limit
            if not self._check_rate_limit(alert.fingerprint):
                self._alerts_suppressed += 1
                continue
            
            # Mark as firing
            alert.status = AlertStatus.FIRING
            if alert.fired_at is None:
                alert.fired_at = now
            alert.last_notification = now
            
            alerts_to_send.append(alert)
            self._notification_times[alert.fingerprint] = now
            self._notifications_sent += 1
        
        # Send notifications
        for alert in alerts_to_send:
            await self._send_notifications(alert)
        
        # Clear pending queue
        self._pending.clear()
        
        return alerts_to_send
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications through all channels"""
        for channel in self._channels:
            try:
                if asyncio.iscoroutinefunction(channel):
                    await channel(alert)
                else:
                    channel(alert)
            except Exception as e:
                self.logger.error(f"Error in notification channel: {e}")
    
    async def resolve_alert(
        self,
        fingerprint: str,
        message: Optional[str] = None,
    ):
        """Resolve an alert"""
        if fingerprint not in self._alerts:
            return
        
        alert = self._alerts[fingerprint]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = time.time()
        alert.updated_at = time.time()
        
        if message:
            alert.details["resolution_message"] = message
        
        self.logger.info(f"Resolved alert: {alert.name}")
    
    async def check_rules(self, metrics: Dict[str, Any]):
        """Check all alert rules against metrics"""
        for name, rule in self._rules.items():
            try:
                if rule.condition(metrics):
                    await self.create_alert(
                        name=rule.name,
                        message=rule.message_template.format(name=rule.name),
                        severity=rule.severity,
                        labels=rule.labels,
                    )
                elif rule.auto_resolve:
                    # Check if alert should be auto-resolved
                    fingerprint = self._generate_fingerprint(rule.name, "hermet", rule.labels)
                    if fingerprint in self._alerts:
                        alert = self._alerts[fingerprint]
                        if alert.status == AlertStatus.FIRING:
                            if time.time() - alert.fired_at > rule.resolve_after:
                                await self.resolve_alert(fingerprint)
            
            except Exception as e:
                self.logger.error(f"Error checking rule {name}: {e}")
    
    def _generate_fingerprint(
        self,
        name: str,
        source: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> str:
        """Generate a fingerprint for alert deduplication"""
        label_str = ",".join(f"{k}={v}" for k, v in sorted((labels or {}).items()))
        return f"{source}:{name}:{label_str}"
    
    def _should_notify(self, fingerprint: str) -> bool:
        """Check if we should send notification (cooldown)"""
        if fingerprint not in self._notification_times:
            return True
        
        last_notification = self._notification_times[fingerprint]
        cooldown = self.default_cooldown
        
        # Check if rule has custom cooldown
        for rule in self._rules.values():
            rule_fingerprint = self._generate_fingerprint(rule.name, "hermet", rule.labels)
            if rule_fingerprint == fingerprint:
                cooldown = rule.cooldown
                break
        
        return time.time() - last_notification >= cooldown
    
    def _check_rate_limit(self, fingerprint: str) -> bool:
        """Check rate limit for alert fingerprint"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old entries
        self._alert_times[fingerprint] = [
            t for t in self._alert_times[fingerprint] if t > minute_ago
        ]
        
        # Check limit
        if len(self._alert_times[fingerprint]) >= self.max_per_minute:
            return False
        
        # Record this alert
        self._alert_times[fingerprint].append(now)
        return True
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (firing) alerts"""
        return [
            alert for alert in self._alerts.values()
            if alert.status == AlertStatus.FIRING
        ]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts by severity"""
        return [
            alert for alert in self._alerts.values()
            if alert.severity == severity
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alert manager statistics"""
        return {
            "total_alerts": self._total_alerts,
            "active_alerts": len(self.get_active_alerts()),
            "notifications_sent": self._notifications_sent,
            "alerts_suppressed": self._alerts_suppressed,
            "rules_count": len(self._rules),
            "channels_count": len(self._channels),
        }
    
    def cleanup_old_alerts(self):
        """Remove old resolved alerts"""
        now = time.time()
        retention_seconds = self.retention_hours * 3600
        
        to_remove = [
            fp for fp, alert in self._alerts.items()
            if alert.status == AlertStatus.RESOLVED
            and alert.resolved_at
            and now - alert.resolved_at > retention_seconds
        ]
        
        for fp in to_remove:
            del self._alerts[fp]
        
        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} old alerts")
