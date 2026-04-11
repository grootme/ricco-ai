"""
Context Engineering Layer - Multi-dimensional context fusion
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger
import json


class ContextType(str, Enum):
    PERSONAL = "personal"
    SPATIAL = "spatial"
    TEMPORAL = "temporal"
    DEVICE = "device"
    SOLUTION = "solution"
    SKILLS = "skills"
    SESSION = "session"


@dataclass
class ContextBundle:
    context_type: ContextType
    data: Dict[str, Any]
    priority: int = 5
    ttl: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_type": self.context_type.value,
            "data": self.data,
            "priority": self.priority,
            "created_at": self.created_at.isoformat()
        }


class ContextEngine:
    """Context Engineering Engine for personalized AI"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", max_tokens: int = 8000):
        self.redis_url = redis_url
        self.max_tokens = max_tokens
        self._redis = None
        self._cache: Dict[str, Dict] = {}

    async def initialize(self):
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self.redis_url)
            logger.info("Context Engine initialized with Redis")
        except Exception as e:
            logger.warning(f"Using in-memory context cache: {e}")

    async def collect_temporal_context(self) -> ContextBundle:
        now = datetime.utcnow()
        return ContextBundle(
            context_type=ContextType.TEMPORAL,
            data={
                "timestamp": now.isoformat(),
                "hour": now.hour,
                "day_of_week": now.strftime("%A"),
                "date": now.strftime("%Y-%m-%d"),
                "is_weekend": now.weekday() >= 5,
                "period": self._get_period(now.hour)
            },
            priority=6,
            ttl=3600
        )

    def _get_period(self, hour: int) -> str:
        if 5 <= hour < 12: return "morning"
        elif 12 <= hour < 17: return "afternoon"
        elif 17 <= hour < 21: return "evening"
        return "night"

    async def collect_solution_context(self, solution_id: str) -> ContextBundle:
        from src.config.settings import RICCO_SOLUTIONS
        config = RICCO_SOLUTIONS.get(solution_id, {})
        return ContextBundle(
            context_type=ContextType.SOLUTION,
            data={
                "solution_id": solution_id,
                "solution_name": config.get("name", "Unknown"),
                "domain": config.get("domain", ""),
                "available_agents": config.get("agents", []),
                "available_mcps": config.get("mcps", [])
            },
            priority=7
        )

    async def collect_skills_context(
        self,
        user_id: str,
        ricco_id_client: Optional[Any] = None
    ) -> ContextBundle:
        data = {"user_id": user_id, "trust_score": 0, "kyc_verified": False}
        
        if ricco_id_client:
            try:
                trust = await ricco_id_client.get_trust_score(user_id)
                if trust:
                    data["trust_score"] = trust.get("score", 0)
                kyc = await ricco_id_client.get_kyc_status(user_id)
                if kyc:
                    data["kyc_verified"] = kyc.get("verified", False)
            except Exception as e:
                logger.warning(f"Failed to get skills context: {e}")

        return ContextBundle(
            context_type=ContextType.SKILLS,
            data=data,
            priority=9,
            ttl=300
        )

    async def fuse_contexts(
        self,
        user_id: str,
        session_id: str,
        solution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fuse all contexts into unified bundle"""
        fused = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "contexts": {}
        }

        temporal = await self.collect_temporal_context()
        fused["contexts"]["temporal"] = temporal.to_dict()

        if solution_id:
            solution = await self.collect_solution_context(solution_id)
            fused["contexts"]["solution"] = solution.to_dict()

        return fused

    def generate_prompt(self, fused: Dict[str, Any]) -> str:
        """Generate context prompt for AI"""
        parts = ["## Context", ""]
        
        if "temporal" in fused.get("contexts", {}):
            t = fused["contexts"]["temporal"]["data"]
            parts.append(f"- Time: {t.get('time', '')} ({t.get('period', '')})")
            parts.append(f"- Date: {t.get('date', '')} ({t.get('day_of_week', '')})")

        if "solution" in fused.get("contexts", {}):
            s = fused["contexts"]["solution"]["data"]
            parts.append(f"- Solution: {s.get('solution_name', '')}")

        parts.extend(["", "---", ""])
        return "\n".join(parts)

    async def store_session(self, session_id: str, context: Dict):
        if self._redis:
            await self._redis.setex(f"ctx:{session_id}", 3600, json.dumps(context))
        else:
            self._cache[session_id] = context

    async def get_session(self, session_id: str) -> Optional[Dict]:
        if self._redis:
            data = await self._redis.get(f"ctx:{session_id}")
            return json.loads(data) if data else None
        return self._cache.get(session_id)

    async def close(self):
        if self._redis:
            await self._redis.close()


_context_engine: Optional[ContextEngine] = None


def get_context_engine() -> ContextEngine:
    global _context_engine
    if _context_engine is None:
        from src.config.settings import settings
        _context_engine = ContextEngine(
            redis_url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            max_tokens=settings.CONTEXT_MAX_TOKENS
        )
    return _context_engine
