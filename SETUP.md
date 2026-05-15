## LLM Towns Flask API

A Flask backend API for the LLM Towns simulation. Towns are built from tiles (buildings, houses, town square) on a single 2D world grid with entry/exit points and inter-town travel.

### Features

The API implements endpoints for:
- **World Overview**: 2D grid with terrain tiles (0–10) including building/house/square types
- **Towns**: Town-level details including internal layout and 4 entry/exit points
- **Characters**: Villager data with needs, inventory, relationships, memories, town affiliation
- **Travel**: Road-connected towns exposed as travel targets in possible actions
- **Actions**: Determine possible actions based on adjacent characters, markets, POIs, and towns
- **Interactions**: Character-to-character interactions with town name propagation in memories

### Setup & Running

#### 1. Create Virtual Environment

```bash
cd /home/hugo/git/llm_towns
python3 -m venv venv
source venv/bin/activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Run the Flask App

```bash
python app.py
```

The app will start on `http://localhost:5000`

### Testing the API

In a new terminal (with venv activated):

```bash
source venv/bin/activate
python test_api.py
```

Or test individual endpoints with curl (character IDs follow `{town_id}_villager_{n}` format):

```bash
# Health check
curl http://localhost:5000/health

# Get world overview
curl http://localhost:5000/api/world

# Get world grid (with tile legend including 8=building, 9=house, 10=town_square)
curl http://localhost:5000/api/world/grid

# List all towns
curl http://localhost:5000/api/towns

# Get town details (includes entry_points)
curl http://localhost:5000/api/town/town_0

# List all characters
curl http://localhost:5000/api/characters

# List characters in a specific town
curl "http://localhost:5000/api/characters?town=town_0"

# Get character details
curl http://localhost:5000/api/character/town_0_villager_0

# Get possible actions (includes travel to road-connected towns)
curl http://localhost:5000/api/character/town_0_villager_0/possible-actions

# Move a character
curl -X POST http://localhost:5000/api/character/town_0_villager_0/move \
  -H "Content-Type: application/json" \
  -d '{"x": 7, "y": 7}'

# Interact between characters (memories include town names)
curl -X POST http://localhost:5000/api/interact \
  -H "Content-Type: application/json" \
  -d '{"actor": "town_0_villager_0", "target": "town_0_villager_1", "type": "talk"}'

# Add history event
curl -X POST http://localhost:5000/api/character/town_0_villager_0/history \
  -H "Content-Type: application/json" \
  -d '{"event": "Discovered a secret"}'
```

### API Endpoints

#### World
- `GET /api/world` - Get world overview (towns, POIs, seasons, weather)
- `GET /api/world/dimensions` - Get world width/height
- `GET /api/world/grid` - Get 2D terrain grid (legend: 0=grass … 7=road, 8=building, 9=house, 10=town_square)
- `GET /api/world/biomes` - Get biome grid
- `GET /api/world/lore` - Get world backstory and history
- `GET /api/world/points-of-interest` - List POIs
- `GET /api/world/points-of-interest/<poi_id>` - Get POI details
- `GET /api/world/roads` - List roads between towns

#### Towns
- `GET /api/town/<town_id>` - Get town details (includes `entry_points`, `buildings`, `relations`)
- `GET /api/towns` - List all towns

#### Characters
- `GET /api/character/<char_id>` - Get villager details (needs, inventory, relationships, goals)
- `GET /api/characters` - List all villagers (filter by `?town=town_id`)
- `PUT /api/character/<char_id>` - Update relationships
- `POST /api/character/<char_id>/history` - Add memory event
- `GET /api/character/<char_id>/possible-actions` - Get possible actions (movement, talk, trade, explore, **travel**)

#### Interactions
- `POST /api/interact` - Execute interaction (adds town-named memories like "Talked with Elara from Stonebrook")
- `POST /api/character/<char_id>/move` - Move character

#### Simulation
- `GET /api/sim/status` - Current simulation snapshot
- `POST /api/sim/season/advance` - Manually advance season
- `POST /api/sim/event/random` - Trigger random event
- `GET /api/sim/events` - List recent world events

#### Villager Goals
- `POST /api/villager/<villager_id>/goal` - Assign a goal
- `GET /api/villager/<villager_id>/summary` - Get villager summary
- `POST /api/villager/<villager_id>/suggest-goal` - LLM-suggested goal

#### Health
- `GET /health` - Health check

### Example Response (Town)

```json
{
  "status": "success",
  "data": {
    "id": "town_1",
    "name": "Misthollow",
    "position": [25, 39],
    "width": 8,
    "height": 11,
    "description": "A prosperous settlement",
    "lore": "",
    "founded_year": 0,
    "buildings": [
      {"type": "temple", "name": "Sacred Grove"},
      {"type": "library", "name": "Town Archives"},
      {"type": "market", "name": "Central Market"}
    ],
    "population": 120,
    "economy": "mining",
    "culture": "spiritual",
    "relations": {},
    "entry_points": {
      "east": [32, 44],
      "north": [29, 39],
      "south": [29, 49],
      "west": [25, 44]
    }
  }
}
```

### Example Response (Possible Actions with Travel)

```json
{
  "status": "success",
  "data": {
    "movement": ["north", "south", "east", "west"],
    "interactions": [],
    "trading": [{"type": "trade", "target": "market_town_0", "name": "Market at (30, 30)"}],
    "explore": [],
    "travel": [
      {"type": "travel", "target": "town_1", "name": "Misthollow"},
      {"type": "travel", "target": "town_2", "name": "Holloway"}
    ],
    "objects": ["pick_up", "drop", "use"]
  }
}
```
