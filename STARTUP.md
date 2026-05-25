# LLM Towns - Startup Scripts

Simple one-command startup for the LLM Towns server and visualization client.

## Overview

Two startup scripts are provided:
- **`start.sh`** — For macOS and Linux
- **`start.bat`** — For Windows

Both scripts:
- ✅ Run with **no arguments required** (sensible defaults)
- ✅ Validate Python installation and version
- ✅ Auto-install missing dependencies (pygame, requests)
- ✅ Start Flask server in background
- ✅ Wait for server to be ready
- ✅ Launch the visualization client
- ✅ Clean up on exit

## macOS / Linux

### Quick Start

```bash
cd /home/hugo/git/llm_towns.worktrees/agents-curly-marmot
./start.sh
```

That's it! The server starts automatically, then the client launches.

### Help

```bash
./start.sh --help
```

### Options

| Command | Effect |
|---------|--------|
| `./start.sh` | Start both server and client (default) |
| `./start.sh --help` | Show help message |
| `./start.sh --server` | Start only the server |
| `./start.sh --client` | Start only the client (server must be running) |

### Environment Variables (Optional)

```bash
# Change server port from default 5000
SERVER_PORT=8000 ./start.sh

# Increase timeout if server is slow
SERVER_TIMEOUT=60 ./start.sh

# Override project directory (if not in default location)
PROJECT_DIR=/path/to/project ./start.sh
```

### Examples

```bash
# Start both (simplest)
./start.sh

# Start server in background, client in separate terminal
./start.sh --server &
# In another terminal:
./start.sh --client

# Custom port
SERVER_PORT=8080 ./start.sh
```

## Windows

### Quick Start

```bash
cd C:\path\to\llm_towns
start.bat
```

That's it! Server starts in new window, client launches in current window.

### Help

```bash
start.bat --help
```

### Options

| Command | Effect |
|---------|--------|
| `start.bat` | Start both server and client (default) |
| `start.bat --help` | Show help message |
| `start.bat --server` | Start only the server (new window) |
| `start.bat --client` | Start only the client |

### Environment Variables (Optional)

```batch
REM Change server port from default 5000
set SERVER_PORT=8000
start.bat

REM Increase timeout if server is slow
set SERVER_TIMEOUT=60
start.bat
```

### Examples

```batch
REM Start both (simplest)
start.bat

REM Start server only
start.bat --server

REM Start client only (server must be running)
start.bat --client
```

## What Happens When You Run It

### Default Flow (`./start.sh` or `start.bat`)

1. **Validate Python** — Check Python 3.8+ is installed
2. **Check Dependencies** — Verify pygame and requests
3. **Auto-install Missing** — Run pip if needed
4. **Start Server** — Launch Flask in background (Linux/macOS) or new window (Windows)
5. **Wait for Server** — Poll `/health` endpoint (default timeout: 30 seconds)
6. **Launch Client** — Open pygame visualization window
7. **Auto-cleanup** — Stop server when client closes

### Logs

**Linux/macOS**: Server logs saved to `/tmp/llm_towns_server.log`

**Windows**: Server runs in separate window (view directly)

## Connection Issues

### "Server failed to start"

1. Check if port 5000 is available: `lsof -i :5000` (macOS/Linux)
2. Try different port: `SERVER_PORT=8000 ./start.sh`
3. View server logs: `tail -50 /tmp/llm_towns_server.log`

### "Client cannot connect"

1. Make sure server window is still open (Windows)
2. Check that server is actually listening: `curl http://localhost:5000/health`
3. Increase timeout: `SERVER_TIMEOUT=60 ./start.sh`

### Missing Python modules

The scripts auto-install missing packages. If that fails:

```bash
pip install pygame requests
```

## Keyboard Shortcuts in Client

Once the client is running:

| Key | Action |
|-----|--------|
| ↑↓←→ | Scroll map |
| Right-click + Drag | Pan smoothly |
| Home | Center map |
| Left-click | Select entity |
| C | Deselect |
| Space | Pause/resume |
| ESC | Exit |

## Advanced Usage

### Running on Different Machine

If running server on one machine and client on another:

**On server machine:**
```bash
./start.sh --server
```
This runs indefinitely. Make note of the IP address.

**On client machine:**
Edit `client/viewer.py` and change:
```python
client = SimulationClient("http://server_ip:5000")
```

Then run:
```bash
./start.sh --client
```

### Docker (Future)

These scripts can easily be containerized:

```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
CMD ["./start.sh"]
```

### CI/CD Integration

Use `./start.sh --server` in CI pipelines to start server for testing:

```yaml
- name: Start server
  run: |
    ./start.sh --server &
    sleep 5  # Wait for startup
    # Run tests...
```

## Troubleshooting

### Script Not Executing (macOS/Linux)

```bash
# Make executable
chmod +x start.sh

# Then run
./start.sh
```

### Permission Denied (Windows)

If you get "cannot be loaded because running scripts is disabled":

```powershell
# Run PowerShell as Administrator, then:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try again
start.bat
```

### Port Already in Use

```bash
# Find and kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Then use different port
SERVER_PORT=8000 ./start.sh
```

### Python Not in PATH

**Linux/macOS:**
```bash
/usr/bin/python3 /path/to/start.sh
```

**Windows:**
```batch
C:\Python311\python.exe start.bat
```

## File Sizes

- `start.sh` — 8.8 KB (bash script)
- `start.bat` — 8.0 KB (batch script)

## See Also

- `QUICK_START.txt` — 2-minute reference
- `CLIENT_GUIDE.md` — Full user guide
- `CLIENT_SUMMARY.md` — Technical details
- `launch.py` — Python launcher alternative

---

**That's it!** Run `./start.sh` (or `start.bat` on Windows) and you're ready to explore LLM Towns! 🎮
