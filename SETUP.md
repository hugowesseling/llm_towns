## LLM Towns Flask API

A simple Flask backend API for the LLM Towns game concept based on the project README.

### Features

The API implements endpoints for:
- **World Overview**: 2D grid where towns occupy blocks
- **Towns**: Town-level details including layout
- **Characters**: Character data with wants, relationships, and history
- **Actions**: Determine possible actions based on adjacent characters
- **Interactions**: Character-to-character interactions and movement

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

Or test individual endpoints with curl:

```bash
# Health check
curl http://localhost:5000/health

# Get world overview
curl http://localhost:5000/api/world

# List all characters
curl http://localhost:5000/api/characters

# Get character details
curl http://localhost:5000/api/character/char_1

# Get possible actions for a character
curl http://localhost:5000/api/character/char_1/possible-actions

# Move a character
curl -X POST http://localhost:5000/api/character/char_1/move \
  -H "Content-Type: application/json" \
  -d '{"x": 7, "y": 7}'

# Interact between characters
curl -X POST http://localhost:5000/api/interact \
  -H "Content-Type: application/json" \
  -d '{"actor": "char_1", "target": "char_2", "type": "talk"}'

# Add history event
curl -X POST http://localhost:5000/api/character/char_1/history \
  -H "Content-Type: application/json" \
  -d '{"event": "Discovered a secret"}'
```

### API Endpoints

#### World
- `GET /api/world` - Get world grid overview
- `GET /api/world/dimensions` - Get world dimensions

#### Towns
- `GET /api/town/<town_id>` - Get town details
- `GET /api/towns` - List all towns

#### Characters
- `GET /api/character/<char_id>` - Get character details
- `GET /api/characters` - List all characters (optionally filter by `?town=town_id`)
- `PUT /api/character/<char_id>` - Update character
- `POST /api/character/<char_id>/history` - Add event to history
- `GET /api/character/<char_id>/possible-actions` - Get possible actions

#### Interactions
- `POST /api/interact` - Execute character interaction
- `POST /api/character/<char_id>/move` - Move character

#### Health
- `GET /health` - Health check

### Example Response

```json
{
  "status": "success",
  "data": {
    "id": "char_1",
    "name": "Alice",
    "town": "town_1",
    "position": [5, 5],
    "occupation": "Merchant",
    "wants": ["Gold", "Knowledge"],
    "relationships": {"char_2": "Friend"},
    "history": ["Arrived at town", "Met Bob"]
  }
}
```
