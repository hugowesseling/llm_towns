#!/bin/bash
################################################################################
#
# LLM Towns - Start Both Server and Client
#
# Usage:
#   ./start.sh              # Starts both server and client with defaults
#   ./start.sh --help       # Show this help message
#
# This script:
#   1. Validates Python installation
#   2. Checks dependencies (pygame, requests)
#   3. Starts Flask server in background
#   4. Waits for server to be ready
#   5. Starts visualization client in foreground
#   6. Cleans up server on exit
#
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_SCRIPT="$PROJECT_DIR/app.py"
CLIENT_DIR="$PROJECT_DIR/client"
CLIENT_SCRIPT="$CLIENT_DIR/viewer.py"
SERVER_PORT=5000
SERVER_TIMEOUT=30
SERVER_PID=""

# Function: Print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function: Cleanup on exit
cleanup() {
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        print_info "Stopping server (PID $SERVER_PID)..."
        kill "$SERVER_PID" 2>/dev/null || true
        sleep 1
    fi
}

# Function: Show help
show_help() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════╗
║                 LLM TOWNS - START SERVER & CLIENT                       ║
╚══════════════════════════════════════════════════════════════════════════╝

Usage:
  ./start.sh              Start both server and client (default)
  ./start.sh --help       Show this help message
  ./start.sh --server     Start only the server
  ./start.sh --client     Start only the client (server must be running)

Environment Variables (optional):
  PROJECT_DIR             Override project directory (default: script location)
  SERVER_PORT             Change server port (default: 5000)
  SERVER_TIMEOUT          Wait time for server (default: 30 seconds)

Examples:
  # Normal usage - starts both in one command
  ./start.sh

  # Start server in background, client in another terminal
  ./start.sh --server &
  ./start.sh --client

  # Change server port
  SERVER_PORT=8000 ./start.sh

What happens:
  1. Validates Python 3.8+
  2. Checks for required packages (pygame, requests)
  3. Starts Flask server in background
  4. Waits for server to respond (default 30s)
  5. Starts visualization client in foreground
  6. Stops server when client closes

Keyboard shortcuts in client:
  ↑↓←→      Scroll map
  Click     Select entity
  Space     Pause/resume
  ESC       Exit

For more information, read:
  - QUICK_START.txt      (in project root)
  - CLIENT_GUIDE.md      (comprehensive guide)
  - CLIENT_SUMMARY.md    (technical details)

EOF
}

# Function: Check Python version
check_python() {
    print_info "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed!"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"
    
    # Check if version is 3.8+
    MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
        print_error "Python 3.8 or higher is required (found $PYTHON_VERSION)"
        exit 1
    fi
}

# Function: Check dependencies
check_dependencies() {
    print_info "Checking dependencies..."
    
    local missing=""
    
    if ! python3 -c "import pygame" 2>/dev/null; then
        missing="$missing pygame"
    fi
    
    if ! python3 -c "import requests" 2>/dev/null; then
        missing="$missing requests"
    fi
    
    if [ -n "$missing" ]; then
        print_warning "Missing packages:$missing"
        print_info "Installing dependencies..."
        python3 -m pip install --quiet pygame requests
    fi
    
    print_success "All dependencies available"
}

# Function: Wait for server to be ready
wait_for_server() {
    print_info "Waiting for server to respond on port $SERVER_PORT (timeout: ${SERVER_TIMEOUT}s)..."
    
    local elapsed=0
    local interval=1
    
    while [ $elapsed -lt $SERVER_TIMEOUT ]; do
        if curl -s "http://localhost:$SERVER_PORT/health" > /dev/null 2>&1; then
            print_success "Server is ready!"
            return 0
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
        echo -ne "${BLUE}  ${NC}Waiting... ${elapsed}s\r"
    done
    
    print_error "Server failed to start within ${SERVER_TIMEOUT} seconds"
    return 1
}

# Function: Start server
start_server() {
    print_info "Starting Flask server..."
    
    if [ ! -f "$SERVER_SCRIPT" ]; then
        print_error "Server script not found: $SERVER_SCRIPT"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    python3 "$SERVER_SCRIPT" > /tmp/llm_towns_server.log 2>&1 &
    SERVER_PID=$!
    
    print_success "Server started (PID: $SERVER_PID)"
    print_info "Server logs: /tmp/llm_towns_server.log"
    
    if ! wait_for_server; then
        print_error "Server failed to start. Check logs:"
        tail -20 /tmp/llm_towns_server.log
        exit 1
    fi
}

# Function: Start client
start_client() {
    print_info "Starting visualization client..."
    
    if [ ! -f "$CLIENT_SCRIPT" ]; then
        print_error "Client script not found: $CLIENT_SCRIPT"
        exit 1
    fi
    
    cd "$CLIENT_DIR"
    python3 "$CLIENT_SCRIPT"
}

# Function: Start both
start_both() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║              LLM TOWNS - STARTING SERVER & CLIENT                       ║"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"
    echo ""
    print_info "Project directory: $PROJECT_DIR"
    print_info "Server port: $SERVER_PORT"
    echo ""
    
    check_python
    check_dependencies
    
    echo ""
    start_server
    
    echo ""
    print_success "All systems ready! Launching client..."
    echo ""
    
    # Set trap to cleanup on exit
    trap cleanup EXIT INT TERM
    
    start_client
    
    print_info "Client closed. Shutting down server..."
}

# Main script logic
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --server)
        echo ""
        echo "╔══════════════════════════════════════════════════════════════════════════╗"
        echo "║                   LLM TOWNS - SERVER ONLY                               ║"
        echo "╚══════════════════════════════════════════════════════════════════════════╝"
        echo ""
        check_python
        check_dependencies
        echo ""
        cd "$PROJECT_DIR"
        exec python3 "$SERVER_SCRIPT"
        ;;
    --client)
        echo ""
        echo "╔══════════════════════════════════════════════════════════════════════════╗"
        echo "║                   LLM TOWNS - CLIENT ONLY                               ║"
        echo "╚══════════════════════════════════════════════════════════════════════════╝"
        echo ""
        check_python
        check_dependencies
        echo ""
        cd "$CLIENT_DIR"
        exec python3 "$CLIENT_SCRIPT"
        ;;
    "")
        # Default: start both
        start_both
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Run '$0 --help' for usage information"
        exit 1
        ;;
esac
