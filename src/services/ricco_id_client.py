"""
RICCO ID Client - Authentication integration
"""

import httpx
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime, timedelta
import jwt


class RiccoIDClient:
    """Client for RICCO ID service"""

    def __init__(self, base_url: str, shared_secret: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api"
        self.shared_secret = shared_secret
        self.timeout = timeout
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client

    def generate_service_token(self, service_name: str = "ricco-ai") -> str:
        """Generate service-to-service JWT"""
        if not self.shared_secret:
            raise ValueError("RICCO_SHARED_SECRET not configured")
        
        payload = {
            "sub": f"service:{service_name}",
            "iss": "ricco-ai",
            "aud": "ricco-id",
            "type": "service",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, self.shared_secret, algorithm="HS256")

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token with RICCO ID"""
        try:
            headers = {
                "Authorization": f"Bearer {self.generate_service_token()}",
                "Content-Type": "application/json"
            }
            response = await self.http_client.post(
                f"{self.api_url}/auth/verify",
                headers=headers,
                json={"token": token}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None

    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user info from RICCO ID"""
        try:
            headers = {"Authorization": f"Bearer {self.generate_service_token()}"}
            response = await self.http_client.get(
                f"{self.api_url}/users/{user_id}",
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    async def get_trust_score(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user trust score"""
        try:
            headers = {"Authorization": f"Bearer {self.generate_service_token()}"}
            response = await self.http_client.get(
                f"{self.api_url}/trust/score/{user_id}",
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to get trust score: {e}")
            return None

    async def get_kyc_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get KYC status"""
        try:
            headers = {"Authorization": f"Bearer {self.generate_service_token()}"}
            response = await self.http_client.get(
                f"{self.api_url}/kyc/status/{user_id}",
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to get KYC status: {e}")
            return None

    async def close(self):
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
