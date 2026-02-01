"""
Test script for LLM Towns Flask API.

Run the Flask app first: python app.py
Then run this script to test the API endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def print_response(title: str, response):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(json.dumps(response.json(), indent=2))
    print(f"Status: {response.status_code}\n")


def test_api():
    """Test all API endpoints."""
    
    # Test health check
    print_response("Health Check", requests.get(f"{BASE_URL}/health"))
    
    # Test world endpoints
    print_response("Get World Overview", requests.get(f"{BASE_URL}/api/world"))
    print_response("Get World Dimensions", requests.get(f"{BASE_URL}/api/world/dimensions"))
    
    # Test town endpoints
    print_response("Get Town (town_1)", requests.get(f"{BASE_URL}/api/town/town_1"))
    print_response("List All Towns", requests.get(f"{BASE_URL}/api/towns"))
    
    # Test character endpoints
    print_response("Get Character (char_1)", requests.get(f"{BASE_URL}/api/character/char_1"))
    print_response("List All Characters", requests.get(f"{BASE_URL}/api/characters"))
    print_response("List Characters in town_1", 
                  requests.get(f"{BASE_URL}/api/characters?town=town_1"))
    
    # Test get possible actions
    print_response("Get Possible Actions for char_1", 
                  requests.get(f"{BASE_URL}/api/character/char_1/possible-actions"))
    
    # Test character movement
    print_response("Move char_1 to (7, 7)", 
                  requests.post(f"{BASE_URL}/api/character/char_1/move",
                               json={"x": 7, "y": 7}))
    
    # Test interaction
    print_response("char_1 talks to char_2", 
                  requests.post(f"{BASE_URL}/api/interact",
                               json={
                                   "actor": "char_1",
                                   "target": "char_2",
                                   "type": "talk"
                               }))
    
    # Test adding history
    print_response("Add history event to char_1", 
                  requests.post(f"{BASE_URL}/api/character/char_1/history",
                               json={"event": "Discovered a secret"}))
    
    # Test character update
    print_response("Update char_1 occupation", 
                  requests.put(f"{BASE_URL}/api/character/char_1",
                              json={"occupation": "Adventurer"}))
    
    # Test error handling
    print_response("Get Non-existent Character", 
                  requests.get(f"{BASE_URL}/api/character/char_999"))


if __name__ == "__main__":
    try:
        test_api()
        print("\n✓ All tests completed!")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Flask app at localhost:5000")
        print("Make sure to run: python app.py")
    except Exception as e:
        print(f"Error: {e}")
