#!/usr/bin/env python3
"""
Quick test script to verify the client can connect to the API.
Run this to test before launching the full visualization.
"""

import sys
import time
from api_client import APIClient

def test_connection():
    """Test basic API connectivity."""
    print("LLM Towns Client - Connection Test")
    print("=" * 50)
    
    client = APIClient("http://localhost:5000")
    
    print("\n1. Checking health...")
    if not client.health_check():
        print("   ✗ Server not responding!")
        print("   Make sure the Flask app is running:")
        print("     cd /home/hugo/git/llm_towns.worktrees/agents-curly-marmot")
        print("     python app.py")
        return False
    print("   ✓ Server is alive")
    
    print("\n2. Fetching world dimensions...")
    dims = client.get_world_dimensions()
    if not dims:
        print("   ✗ Failed to get dimensions")
        return False
    print(f"   ✓ World: {dims['width']}×{dims['height']}")
    
    print("\n3. Fetching world grid...")
    grid = client.get_world_grid()
    if not grid:
        print("   ✗ Failed to get grid")
        return False
    print(f"   ✓ Grid loaded ({len(grid)} rows)")
    
    print("\n4. Fetching characters...")
    chars = client.get_characters()
    if chars is None:
        print("   ✗ Failed to get characters")
        return False
    print(f"   ✓ Found {len(chars)} villagers")
    if chars:
        print(f"     Sample: {chars[0].get('id')} at {chars[0].get('position')}")
    
    print("\n5. Fetching towns...")
    towns = client.get_towns()
    if towns is None:
        print("   ✗ Failed to get towns")
        return False
    print(f"   ✓ Found {len(towns)} towns")
    if towns:
        print(f"     Sample: {towns[0].get('name')} at {towns[0].get('position')}")
    
    print("\n6. Fetching sim status...")
    status = client.get_sim_status()
    if status is None:
        print("   ✗ Failed to get sim status")
        return False
    print(f"   ✓ Simulation is running")
    print(f"     Current tick: {status.get('current_tick', '?')}")
    print(f"     Season: {status.get('current_season', '?')}")
    
    print("\n" + "=" * 50)
    print("✓ All checks passed! Ready to launch viewer.")
    print("\nTo start the visualization, run:")
    print("  python viewer.py")
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
