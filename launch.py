#!/usr/bin/env python3
"""
Helper script to manage the LLM Towns server and client.
Provides convenient shortcuts for running both components.
"""

import subprocess
import sys
import time
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SERVER_SCRIPT = PROJECT_ROOT / "app.py"
CLIENT_DIR = PROJECT_ROOT / "client"

def run_server():
    """Start the Flask server."""
    print("🚀 Starting LLM Towns Flask Server...")
    print(f"   Working directory: {PROJECT_ROOT}")
    os.chdir(PROJECT_ROOT)
    try:
        subprocess.run([sys.executable, str(SERVER_SCRIPT)])
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped.")

def run_client():
    """Start the visualization client."""
    print("🎮 Starting LLM Towns Visualization Client...")
    print(f"   Working directory: {CLIENT_DIR}")
    os.chdir(CLIENT_DIR)
    try:
        subprocess.run([sys.executable, "viewer.py"])
    except KeyboardInterrupt:
        print("\n⏹️  Client stopped.")

def test_connection():
    """Test server connectivity."""
    print("🔍 Testing server connection...")
    os.chdir(CLIENT_DIR)
    subprocess.run([sys.executable, "test_connection.py"])

def show_help():
    """Display help information."""
    print("""
LLM Towns - Server & Client Manager
====================================

Usage:
  python launch.py [command]

Commands:
  server          Start the Flask API server
  client          Start the visualization client
  test            Test server connectivity
  help            Show this help message

Quick Start:
  1. Terminal 1: python launch.py server
  2. Terminal 2: python launch.py test
  3. Terminal 2: python launch.py client

Manual Alternative:
  Terminal 1:
    cd /home/hugo/git/llm_towns.worktrees/agents-curly-marmot
    python app.py

  Terminal 2:
    cd /home/hugo/git/llm_towns.worktrees/agents-curly-marmot/client
    python viewer.py

Environment:
  - Server runs on: http://localhost:5000
  - Client resolution: 1200×800 (map + sidebar)
  - Update interval: 1.0 second
  - FPS: 30
""")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "server":
        run_server()
    elif command == "client":
        run_client()
    elif command == "test":
        test_connection()
    elif command in ("help", "-h", "--help"):
        show_help()
    else:
        print(f"Unknown command: {command}")
        print("Run 'python launch.py help' for usage.")
        sys.exit(1)
