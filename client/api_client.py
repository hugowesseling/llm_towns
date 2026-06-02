"""
API client for fetching world and character data from the Flask server.
"""

import requests
from typing import Dict, List, Any, Optional

class APIClient:
    """Communicates with the Flask LLM Towns API."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.timeout = 5
    
    def health_check(self) -> bool:
        """Check if the server is running."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            return resp.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def get_world(self) -> Optional[Dict[str, Any]]:
        """Get world overview."""
        try:
            resp = requests.get(f"{self.base_url}/api/world", timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("data")
        except Exception as e:
            print(f"Failed to get world: {e}")
            return None
    
    def get_world_grid(self) -> Optional[List[List[int]]]:
        """Get 2D terrain grid."""
        try:
            resp = requests.get(f"{self.base_url}/api/world/grid", timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            # API returns grid directly, not wrapped in "data" key
            return data.get("grid")
        except Exception as e:
            print(f"Failed to get world grid: {e}")
            return None
    
    def get_world_dimensions(self) -> Optional[Dict[str, int]]:
        """Get world width and height."""
        try:
            resp = requests.get(f"{self.base_url}/api/world/dimensions", timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            # API returns dimensions directly, not wrapped in "data" key
            return {"width": data.get("width"), "height": data.get("height")}
        except Exception as e:
            print(f"Failed to get world dimensions: {e}")
            return None
    
    def get_characters(self, town: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get list of characters (optional filter by town)."""
        try:
            params = {"town": town} if town else {}
            resp = requests.get(f"{self.base_url}/api/characters", params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("data")
        except Exception as e:
            print(f"Failed to get characters: {e}")
            return None
    
    def get_character(self, char_id: str) -> Optional[Dict[str, Any]]:
        """Get character details including position."""
        try:
            resp = requests.get(f"{self.base_url}/api/character/{char_id}", timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("data")
        except Exception as e:
            print(f"Failed to get character {char_id}: {e}")
            return None
    
    def get_towns(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of all towns."""
        try:
            resp = requests.get(f"{self.base_url}/api/towns", timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("data")
        except Exception as e:
            print(f"Failed to get towns: {e}")
            return None
    
    def get_town(self, town_id: str) -> Optional[Dict[str, Any]]:
        """Get town details."""
        try:
            resp = requests.get(f"{self.base_url}/api/town/{town_id}", timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("data")
        except Exception as e:
            print(f"Failed to get town {town_id}: {e}")
            return None
    
    def get_sim_status(self) -> Optional[Dict[str, Any]]:
        """Get current simulation status."""
        try:
            resp = requests.get(f"{self.base_url}/api/sim/status", timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("data")
        except Exception as e:
            print(f"Failed to get sim status: {e}")
            return None
    
    def get_villager_detail(self, villager_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed villager info including goal, plan, memories."""
        try:
            resp = requests.get(f"{self.base_url}/api/villager/{villager_id}/summary", timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("data")
        except Exception as e:
            print(f"Failed to get villager detail for {villager_id}: {e}")
            return None
