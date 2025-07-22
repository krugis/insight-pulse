import httpx
from typing import Dict, Any, List, Optional

from app.core.config import settings

class PulseAgentManagerClient:
    def __init__(self):
        self.base_url = settings.PULSE_AGENT_MANAGER_BASE_URL
        self.client = httpx.AsyncClient()

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"An error occurred while requesting {e.request.url!r}: {e}")
            raise

    async def create_remote_agent(
        self,
        user_id: int,
        agent_name: str,
        config_data: Dict[str, Any],
        apify_token: Optional[str] = None,
        openai_token: Optional[str] = None
    ) -> Dict[str, Any]:
        # This is a hypothetical payload for the pulse-agent-manager
        # You'll need to adjust it based on your actual pulse-agent-manager's API spec
        payload = {
            "user_id": user_id,
            "agent_name": agent_name,
            "config": config_data,
            "apify_token": apify_token,
            "openai_token": openai_token,
            "type": "Insight Pulse Agent"
        }
        return await self._request("POST", "/agents", json=payload)

    async def get_remote_agent(self, agent_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/agents/{agent_id}")

    async def update_remote_agent_status(self, agent_id: str, new_status: str) -> Dict[str, Any]:
        payload = {"status": new_status}
        return await self._request("PATCH", f"/agents/{agent_id}/status", json=payload)

    async def delete_remote_agent(self, agent_id: str):
        await self._request("DELETE", f"/agents/{agent_id}")

pulse_agent_manager_client = PulseAgentManagerClient()