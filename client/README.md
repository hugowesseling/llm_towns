# LLM Towns Client

A pygame-based visualization client for the LLM Towns simulation. Displays the world as a scrollable 2D map with terrains, towns, and villagers.

## Features

- **Scrollable Map**: Navigate the world with arrow keys or mouse dragging
- **Tile Visualization**: Different colored and patterned tiles for terrain types (grass, forest, water, mountains, sand, snow, swamp, roads, buildings, houses, town squares)
- **Villager Display**: See villagers as red circles on the map in real-time
- **Town Markers**: Towns marked with gold stars at their center
- **Character Details**: Click on villagers to see their stats (hunger, energy, social needs) and current goals
- **Town Info**: Click on towns to see population, economy, culture, and description
- **Real-time Updates**: Background thread fetches updated world state periodically

## Running the Client

### Prerequisites

1. Make sure the Flask server is running:
```bash
cd /path/to/llm_towns
python app.py
```

2. The client uses pygame (usually already installed):
```bash
pip install pygame requests
```

### Start the Viewer

```bash
cd client
python viewer.py
```

The window will open at 1200×800 pixels. The left side shows the map (950px wide), and the right sidebar (250px) shows character/town info and controls.

## Controls

| Key/Action | Effect |
|-----------|--------|
| **Arrow Keys** | Scroll the map |
| **Left Click** | Select a character or town |
| **Right-click Drag** | Pan the map |
| **Home** | Center map at top-left |
| **Space** | Pause/resume (pauses display updates) |
| **C** | Deselect current character/town |
| **ESC** | Exit |

## Tile Types

The map uses these tile types (IDs 0-10):

| ID | Tile | Color | Description |
|----|------|-------|-------------|
| 0 | GRASS | Forest Green | Default terrain |
| 1 | FOREST | Dark Green | Wooded areas |
| 2 | WATER | Dodger Blue | Rivers, lakes |
| 3 | MOUNTAIN | Saddle Brown | Impassable peaks |
| 4 | SAND | Bisque | Desert biome |
| 5 | SNOW | White | Tundra/snow |
| 6 | SWAMP | Dark Khaki | Murky wetlands |
| 7 | ROAD | Light Gray | World roads & streets |
| 8 | BUILDING | Maroon | Shops, temples (perimeter) |
| 9 | HOUSE | Chocolate | Residential buildings |
| 10 | TOWN_SQUARE | Gold | Central plaza (3×3) |

## Architecture

### `api_client.py`
HTTP client for fetching world state from the Flask API. Handles connection, data retrieval, and error handling.

### `tileset.py`
Graphics rendering module that creates procedural tile surfaces. Each tile type has distinct visual patterns and colors. Includes a `TilesetCache` for performance.

### `viewer.py`
Main visualization app. Contains:
- `WorldViewport`: Manages scrollable map viewport and coordinate conversion
- `SimulationClient`: Main app, handles rendering, events, and UI

## Extending

### Add New Tile Styles
Edit `tileset.py` and modify `create_tile_surface()` to add more detail to specific tile types.

### Customize Colors
Edit the `TILE_COLORS` dict in `tileset.py` to change terrain appearance.

### Add More UI Panels
Modify `_draw_sidebar()` in `viewer.py` to show additional information (inventory, relationships, events, etc.).

### Fetch Additional Data
Use `APIClient` methods in `viewer.py` to pull data (possible actions, town relations, events, etc.) and display it.
