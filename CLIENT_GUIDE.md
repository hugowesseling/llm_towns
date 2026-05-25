# LLM Towns Visualization Client - Setup & Usage Guide

## Overview

The LLM Towns Visualization Client is a Python-based pygame application that displays the simulation world as a scrollable 2D map. It connects to the Flask API server and shows:

- **Terrain tiles** (grass, forest, water, mountains, sand, snow, swamp, roads, buildings, houses, town squares)
- **Villagers** as red circles, positioned in real-time
- **Towns** as gold stars at their center
- **Character details** (position, hunger, energy, social needs, current goal)
- **Town information** (population, economy, culture, description)

## Quick Start

### Option 1: Using the Launch Helper (Recommended)

**Terminal 1 - Start the Server:**
```bash
cd /home/hugo/git/llm_towns.worktrees/agents-curly-marmot
python launch.py server
```

**Terminal 2 - Start the Client:**
```bash
cd /home/hugo/git/llm_towns.worktrees/agents-curly-marmot
python launch.py client
```

### Option 2: Manual Launch

**Terminal 1 - Start the Server:**
```bash
cd /home/hugo/git/llm_towns.worktrees/agents-curly-marmot
python app.py
```

**Terminal 2 - Test Connection (Optional):**
```bash
cd /home/hugo/git/llm_towns.worktrees/agents-curly-marmot/client
python test_connection.py
```

**Terminal 2 - Start the Client:**
```bash
cd /home/hugo/git/llm_towns.worktrees/agents-curly-marmot/client
python viewer.py
```

## Client Controls

| Input | Action |
|-------|--------|
| **Arrow Keys ↑↓←→** | Scroll the map |
| **Left Click** | Select a villager or town |
| **Right-click + Drag** | Pan the map (smooth scrolling) |
| **Home Key** | Center map at top-left corner |
| **Space** | Pause/resume display updates |
| **C** | Deselect current character/town |
| **ESC** | Exit the application |

## UI Layout

The 1200×800 window is divided into two areas:

### Left Side (950px wide) - Map Viewport
- Scrollable 2D world map
- Terrain tiles with procedural textures
- Red circles = villagers
- Gold stars = town centers
- Yellow border = selected entity

### Right Side (250px wide) - Information Sidebar
- **Character Details** (when selected):
  - Position coordinates
  - Hunger, Energy, Social needs (0-100 scale)
  - Current goal description
- **Town Details** (when selected):
  - Town name and ID
  - Population count
  - Economy type (farming, mining, fishing, etc.)
  - Culture type (spiritual, martial, mercantile, etc.)
  - Description text
- **Control Reference** at bottom

## Tile Types Reference

| ID | Tile | Color | Pattern |
|----|------|-------|---------|
| 0 | GRASS | Forest Green | Sparse dots (grass tufts) |
| 1 | FOREST | Dark Green | Triangle peak (trees) |
| 2 | WATER | Dodger Blue | Horizontal lines (waves) |
| 3 | MOUNTAIN | Saddle Brown | Triangle peak (mountains) |
| 4 | SAND | Bisque | Arc pattern (ripples) |
| 5 | SNOW | White | Snowflake dots |
| 6 | SWAMP | Dark Khaki | Circle vegetation spots |
| 7 | ROAD | Light Gray | Center line |
| 8 | BUILDING | Maroon | Brick grid pattern |
| 9 | HOUSE | Chocolate | Roof triangle |
| 10 | TOWN_SQUARE | Gold | Cross grid pattern |

## Features Explained

### Real-Time Updates
The client runs a background thread that fetches updated world state every 1 second. This allows you to watch villagers move and interact without pausing.

**Pause with Space** to freeze updates if you want to examine something without it moving.

### Selection & Details
- **Click on a villager** (red circle) to see their stats and current goal
- **Click on a town center** (gold star) to see population, economy, and culture
- **Press C** to deselect and clear the info panel

### Scrolling
- **Arrow keys** scroll in 3-tile increments (96px)
- **Right-click drag** pans smoothly with your mouse
- **Home key** returns to the top-left corner of the map

## Troubleshooting

### "Cannot connect to server"
- Make sure the Flask server is running: `python app.py`
- Check that it's listening on `http://localhost:5000`
- Run `test_connection.py` to diagnose connectivity

### Visualization appears empty
- Verify the world was generated with towns and villagers
- Check the Flask server output for errors
- Try scrolling around (map might be off-screen)

### Performance is slow
- The client renders at 30 FPS, which is reasonable for this visualization
- If choppy, try reducing your screen resolution or moving the window to another display
- Background updates run every 1 second (not real-time, so slight lag is normal)

### Some villagers don't appear
- Villagers might be on other parts of the map
- Use **Home key** to reset the view and then arrow-key through the world

## Architecture

### Files
- **`viewer.py`** - Main visualization app (pygame UI, map rendering, event handling)
- **`api_client.py`** - HTTP client library (connects to Flask API)
- **`tileset.py`** - Graphics engine (procedural tile rendering, sprite creation)
- **`test_connection.py`** - Connection validation script
- **`__init__.py`** - Python package marker

### Key Classes
- `SimulationClient` - Main application, manages UI and simulation loop
- `WorldViewport` - Viewport manager, handles scrolling and coordinate conversion
- `APIClient` - REST API client, fetches world data
- `TilesetCache` - Graphics cache, pre-renders tiles for performance

## Extending the Client

### Add More Information Panels
Edit `_draw_sidebar()` in `viewer.py` to display:
- Character inventory
- Relationships and memories
- Current goals and plans
- Town relations

### Customize Tile Appearance
Edit `create_tile_surface()` in `tileset.py`:
```python
elif tile_id == 0:  # GRASS
    # Modify here to change grass appearance
    surface.fill(color)
    # Add more patterns, details, etc.
```

### Fetch Additional Data
Use `APIClient` methods in `viewer.py`:
```python
possible_actions = self.api.get_character(char_id + "/possible-actions")
town_relations = self.api.get_town(town_id)  # includes relations dict
sim_events = self.api.get_sim_status()  # includes recent events
```

### Change Colors
Edit `TILE_COLORS` dict in `tileset.py`:
```python
TILE_COLORS = {
    0: (34, 139, 34),  # GRASS - change these RGB values
    1: (0, 100, 0),    # FOREST
    # ...
}
```

## Performance Metrics

- **Frame Rate**: 30 FPS
- **Map Size**: 50×50 tiles (1600×1600 pixels at 32px per tile)
- **Viewport Size**: 950×800 pixels (allows viewing ~30×25 tiles at once)
- **Update Interval**: 1 second (background thread)
- **Memory**: ~50-100 MB typical

## Known Limitations

1. **No zoom** - Fixed 32px tile size (could add with scroll wheel)
2. **No layer toggling** - Can't hide tiles, villagers, or towns
3. **No time control** - Can't speed up/slow down simulation
4. **No direct actions** - Can't tell villagers what to do (view-only)
5. **Fixed window size** - 1200×800, not resizable

These could be added in future versions!

## Keyboard Shortcuts Quick Reference

```
NAVIGATION:
  ↑↓←→  Scroll map
  Home  Center map
  Right-drag  Pan smoothly

SELECTION:
  Click  Select entity
  C     Deselect

CONTROL:
  Space  Pause/resume updates
  ESC   Quit
```

## Development Notes

- Client uses **pygame 2.5.2** (cross-platform game library)
- **Threading** for background updates (non-blocking API calls)
- **Procedural graphics** (no external sprite sheets needed)
- **Responsive UI** with real-time hover and click detection

---

Enjoy exploring the LLM Towns world! 🏘️🎮
