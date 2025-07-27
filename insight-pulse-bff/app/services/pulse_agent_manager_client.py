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
        email: str,
        plan: str,
        linkedin_urls: List[str],
        digest_tone: str,
        post_tone: str,
        apify_token: Optional[str] = None,
        openai_token: Optional[str] = None
    ) -> Dict[str, Any]:
        
        payload = {
            "email": email,
            "plan": plan,
            "apifyToken": apify_token,
            "openaiToken": openai_token,
            "digestTone": digest_tone,
            "postTone": post_tone,
            "linkedinUrls": linkedin_urls,
        }

        payload = {k: v for k, v in payload.items() if v is not None}
        
        return await self._request("POST", "/agents/", json=payload)

    async def get_remote_agent(self, agent_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/agents/{agent_id}")

    async def update_remote_agent_status(self, agent_id: str, new_status: str) -> Dict[str, Any]:
        payload = {"status": new_status}
        return await self._request("PATCH", f"/agents/{agent_id}/status", json=payload)

    async def delete_remote_agent(self, agent_id: str):
        await self._request("DELETE", f"/agents/{agent_id}")

    async def update_remote_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a PATCH request to the external pulse-agent-manager to update an agent.
        Assumes pulse-agent-manager has a PATCH /agents/{id} endpoint.
        """
        # Ensure update_data keys match what pulse-agent-manager expects (e.g., camelCase aliases)
        # This is a generic update, so we'll pass the dict as is.
        # You might need to transform keys here if pulse-agent-manager has different aliases for PATCH.
        print(f"MOCKING: Attempted to PATCH agent {agent_id} in pulse-agent-manager with data: {update_data}")
        return {"status": "mock_success", "agent_id": agent_id, "updated_data": update_data}



pulse_agent_manager_client = PulseAgentManagerClient()