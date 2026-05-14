"""
Simple Flask API for LLM Towns game.

Provides endpoints for:
- World overview (2D grid)
- Town-level details
- Character management
- Actions and interactions
"""

from flask import Flask, request, jsonify
from typing import Dict, List, Any
import json
import threading
import time

from llm.brain import LLMBrain, OpenAIChatClient
from llm.prompts import build_goal_prompt
from simulation.actions import Goal
from simulation.planner import Planner
from simulation.scheduler import SimulationScheduler
from simulation.villager import Position, Villager

app = Flask(__name__)

llm_brain = None
try:
    llm_client = OpenAIChatClient()
    llm_brain = LLMBrain(llm_client)
    planner = Planner(llm_brain=llm_brain)
except ValueError:
    planner = Planner()

scheduler = SimulationScheduler(planner=planner, llm_brain=llm_brain)

# Bootstrap a small default villager and goal.
def _create_default_world() -> None:
    villager = Villager(
        id="char_1",
        name="Alice",
        town="town_1",
        profession="Merchant",
        position=Position(x=5, y=5),
    )
    scheduler.add_villager(villager)
    scheduler.add_goal(Goal(actor_id=villager.id, description="Acquire food", priority=5, created_tick=0))

_create_default_world()

# Background simulation thread
def _simulation_loop() -> None:
    while True:
        scheduler.advance_tick(1)
        time.sleep(1)  # Advance one tick per second

simulation_thread = threading.Thread(target=_simulation_loop, daemon=True)
simulation_thread.start()

# Simple in-memory data structures
world_data = {
    "width": 10,
    "height": 10,
    "grid": [[1 if (i + j) % 2 == 0 else 0 for j in range(10)] for i in range(10)]
}

towns = {
    "town_1": {
        "name": "Riverford",
        "position": (2, 2),
        "width": 20,
        "height": 20,
        "grid": [[0 for _ in range(20)] for _ in range(20)]
    }
}

characters = {
    "char_1": {
        "id": "char_1",
        "name": "Alice",
        "town": "town_1",
        "position": (5, 5),
        "occupation": "Merchant",
        "wants": ["Gold", "Knowledge"],
        "relationships": {"char_2": "Friend"},
        "history": ["Arrived at town", "Met Bob"]
    },
    "char_2": {
        "id": "char_2",
        "name": "Bob",
        "town": "town_1",
        "position": (6, 6),
        "occupation": "Blacksmith",
        "wants": ["Ore", "Recognition"],
        "relationships": {"char_1": "Friend"},
        "history": ["Started at forge", "Met Alice"]
    }
}


# World endpoints
@app.route('/api/world', methods=['GET'])
def get_world():
    """Get the world overview (2D grid where towns occupy blocks)."""
    return jsonify({
        "status": "success",
        "data": world_data
    })


@app.route('/api/world/dimensions', methods=['GET'])
def get_world_dimensions():
    """Get world dimensions."""
    return jsonify({
        "status": "success",
        "width": world_data["width"],
        "height": world_data["height"]
    })


# Town endpoints
@app.route('/api/town/<town_id>', methods=['GET'])
def get_town(town_id: str):
    """Get town-level details including layout and objects."""
    if town_id not in towns:
        return jsonify({"status": "error", "message": "Town not found"}), 404
    
    town = towns[town_id]
    return jsonify({
        "status": "success",
        "data": town
    })


@app.route('/api/towns', methods=['GET'])
def list_towns():
    """List all towns."""
    return jsonify({
        "status": "success",
        "data": list(towns.values())
    })


# Character endpoints
@app.route('/api/character/<char_id>', methods=['GET'])
def get_character(char_id: str):
    """Get character details including wants, relationships, and history."""
    if char_id not in characters:
        return jsonify({"status": "error", "message": "Character not found"}), 404
    
    return jsonify({
        "status": "success",
        "data": characters[char_id]
    })


@app.route('/api/characters', methods=['GET'])
def list_characters():
    """List all characters."""
    town_id = request.args.get('town')
    
    if town_id:
        # Filter by town
        filtered = [c for c in characters.values() if c.get('town') == town_id]
        return jsonify({
            "status": "success",
            "data": filtered
        })
    
    return jsonify({
        "status": "success",
        "data": list(characters.values())
    })


@app.route('/api/character/<char_id>', methods=['PUT'])
def update_character(char_id: str):
    """Update character details."""
    if char_id not in characters:
        return jsonify({"status": "error", "message": "Character not found"}), 404
    
    data = request.get_json()
    characters[char_id].update(data)
    
    return jsonify({
        "status": "success",
        "data": characters[char_id]
    })


@app.route('/api/character/<char_id>/history', methods=['POST'])
def add_character_history(char_id: str):
    """Add an event to character history."""
    if char_id not in characters:
        return jsonify({"status": "error", "message": "Character not found"}), 404
    
    data = request.get_json()
    event = data.get('event')
    
    if not event:
        return jsonify({"status": "error", "message": "Event not provided"}), 400
    
    characters[char_id]['history'].append(event)
    
    return jsonify({
        "status": "success",
        "data": characters[char_id]
    })


# Simulation endpoints
@app.route('/api/sim/status', methods=['GET'])
def get_simulation_status():
    """Return the current simulation snapshot."""
    return jsonify({
        "status": "success",
        "data": scheduler.snapshot(),
        "running": True,  # Simulation runs autonomously
    })


# Removed /api/sim/tick as simulation now runs automatically


@app.route('/api/villager/<villager_id>/goal', methods=['POST'])
def assign_villager_goal(villager_id: str):
    """Assign a new goal to a villager."""
    villager = scheduler.get_villager(villager_id)
    if villager is None:
        return jsonify({"status": "error", "message": "Villager not found"}), 404

    data = request.get_json() or {}
    description = data.get('description')
    priority = int(data.get('priority', 1))
    if not description:
        return jsonify({"status": "error", "message": "Goal description required"}), 400

    goal = Goal(actor_id=villager_id, description=description, priority=priority, created_tick=scheduler.current_tick)
    scheduler.add_goal(goal)
    return jsonify({"status": "success", "goal": {
        "id": goal.id,
        "description": goal.description,
        "priority": goal.priority,
        "actor_id": goal.actor_id,
    }})


@app.route('/api/villager/<villager_id>/summary', methods=['GET'])
def get_villager_summary(villager_id: str):
    """Get the current summary of a simulation villager."""
    villager = scheduler.get_villager(villager_id)
    if villager is None:
        return jsonify({"status": "error", "message": "Villager not found"}), 404

    return jsonify({"status": "success", "data": villager.summary()})


@app.route('/api/villager/<villager_id>/suggest-goal', methods=['POST'])
def suggest_villager_goal(villager_id: str):
    """Ask the LLM for a suggested goal for a villager."""
    villager = scheduler.get_villager(villager_id)
    if villager is None:
        return jsonify({"status": "error", "message": "Villager not found"}), 404

    if scheduler.planner.llm_brain is None:
        return jsonify({"status": "error", "message": "LLM not configured"}), 503

    data = request.get_json() or {}
    extra_context = data.get("context", {})
    if not isinstance(extra_context, dict):
        return jsonify({"status": "error", "message": "Context must be a JSON object"}), 400

    context = {
        "tick": scheduler.current_tick,
        "position": {"x": villager.position.x, "y": villager.position.y},
        "needs": {
            "hunger": villager.needs.hunger,
            "energy": villager.needs.energy,
            "social": villager.needs.social,
        },
        "inventory": villager.inventory.items,
        "relationships": villager.relationships,
        "current_goal_id": villager.current_goal_id,
        "current_plan_id": villager.current_plan_id,
        **extra_context,
    }

    messages = build_goal_prompt(villager.summary(), context)
    try:
        goal_data = scheduler.planner.llm_brain.create_chat_json(
            messages=messages,
            temperature=0.5,
            max_tokens=200,
        )
    except Exception as exc:
        return jsonify({"status": "error", "message": "LLM goal suggestion failed", "detail": str(exc)}), 502

    if not isinstance(goal_data, dict):
        return jsonify({"status": "error", "message": "LLM returned unexpected format"}), 502

    return jsonify({"status": "success", "data": goal_data})


# Actions endpoints
@app.route('/api/character/<char_id>/possible-actions', methods=['GET'])
def get_possible_actions(char_id: str):
    """Get possible actions for a character based on adjacent squares."""
    if char_id not in characters:
        return jsonify({"status": "error", "message": "Character not found"}), 404
    
    char = characters[char_id]
    x, y = char['position']
    town = towns[char['town']]
    
    # Find adjacent characters
    adjacent_chars = [
        c for cid, c in characters.items()
        if cid != char_id and c['town'] == char['town']
        and abs(c['position'][0] - x) <= 1 and abs(c['position'][1] - y) <= 1
    ]
    
    possible_actions = {
        "movement": ["north", "south", "east", "west"],
        "interactions": [
            {"type": "talk", "target": c['id'], "name": c['name']} 
            for c in adjacent_chars
        ],
        "objects": ["pick_up", "drop", "use"]
    }
    
    return jsonify({
        "status": "success",
        "data": possible_actions
    })


# Interactions endpoints
@app.route('/api/interact', methods=['POST'])
def interact():
    """Execute an interaction between two characters or with an object."""
    data = request.get_json()
    char_id = data.get('actor')
    target_id = data.get('target')
    action_type = data.get('type', 'talk')
    
    if char_id not in characters or target_id not in characters:
        return jsonify({"status": "error", "message": "Character not found"}), 404
    
    actor = characters[char_id]
    target = characters[target_id]
    
    # Simple interaction logic
    interaction_result = {
        "actor": char_id,
        "target": target_id,
        "type": action_type,
        "success": True,
        "message": f"{actor['name']} {action_type}s with {target['name']}"
    }
    
    # Update history
    actor['history'].append(f"{action_type.capitalize()} with {target['name']}")
    target['history'].append(f"{actor['name']} {action_type}s with you")
    
    return jsonify({
        "status": "success",
        "data": interaction_result
    })


@app.route('/api/character/<char_id>/move', methods=['POST'])
def move_character(char_id: str):
    """Move a character to a new position."""
    if char_id not in characters:
        return jsonify({"status": "error", "message": "Character not found"}), 404
    
    data = request.get_json()
    new_x = data.get('x')
    new_y = data.get('y')
    
    if new_x is None or new_y is None:
        return jsonify({"status": "error", "message": "Position not provided"}), 400
    
    char = characters[char_id]
    old_pos = char['position']
    char['position'] = (new_x, new_y)
    char['history'].append(f"Moved from {old_pos} to ({new_x}, {new_y})")
    
    return jsonify({
        "status": "success",
        "data": {
            "character_id": char_id,
            "old_position": old_pos,
            "new_position": (new_x, new_y)
        }
    })


# Health check
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
