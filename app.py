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
from simulation.market import Market
from simulation.planner import Planner
from simulation.scheduler import SimulationScheduler
from simulation.villager import Position, Villager
from world.world_generator import World, WorldGenerator

app = Flask(__name__)

llm_brain = None
try:
    llm_client = OpenAIChatClient()
    llm_brain = LLMBrain(llm_client)
    planner = Planner(llm_brain=llm_brain)
except ValueError:
    planner = Planner()

scheduler = SimulationScheduler(planner=planner, llm_brain=llm_brain, world=world)

# Generate world using LLM
world_generator = WorldGenerator(llm_brain=llm_brain)
world = world_generator.generate_world(width=50, height=50)

# Bootstrap villagers and markets from generated world
def _create_world_entities() -> None:
    # Create villagers for the first town
    if world.towns:
        first_town_id = list(world.towns.keys())[0]
        town = world.towns[first_town_id]
        villagers_data = world_generator.generate_villagers_for_town(town, count=3)

        for villager_data in villagers_data:
            villager = Villager(
                id=villager_data["id"],
                name=villager_data["name"],
                town=villager_data["town"],
                profession=villager_data["profession"],
                position=Position(x=villager_data["position"][0], y=villager_data["position"][1]),
            )
            villager.needs.hunger = villager_data["needs"]["hunger"]
            villager.needs.energy = villager_data["needs"]["energy"]
            villager.needs.social = villager_data["needs"]["social"]
            villager.inventory.add("gold", villager_data["inventory"]["gold"])
            scheduler.add_villager(villager)

            # Give each villager an initial goal
            goal = Goal(
                actor_id=villager.id,
                description="Explore the town",
                priority=3,
                created_tick=0
            )
            scheduler.add_goal(goal)

    # Create a market in the town center
    if world.towns:
        first_town = list(world.towns.values())[0]
        market = Market(
            id="market_1",
            position=(first_town.position[0] + first_town.width // 2,
                     first_town.position[1] + first_town.height // 2),
            inventory={"food": 50, "wood": 30, "tools": 10},
            prices={"food": 2.0, "wood": 1.5, "tools": 5.0}
        )
        scheduler.add_market(market)

_create_world_entities()
    scheduler.add_market(market)

_create_default_world()

# Background simulation thread
def _simulation_loop() -> None:
    while True:
        scheduler.advance_tick(1)
        time.sleep(1)  # Advance one tick per second

simulation_thread = threading.Thread(target=_simulation_loop, daemon=True)
simulation_thread.start()


# World endpoints
@app.route('/api/world', methods=['GET'])
def get_world():
    """Get the world overview."""
    return jsonify({
        "status": "success",
        "data": {
            "name": world.name,
            "description": world.description,
            "width": world.width,
            "height": world.height,
            "climate": world.climate,
            "era": world.era,
            "towns": list(world.towns.keys()),
            "terrain_features": list(world.terrain_features.keys()),
        }
    })


@app.route('/api/world/dimensions', methods=['GET'])
def get_world_dimensions():
    """Get world dimensions."""
    return jsonify({
        "status": "success",
        "width": world.width,
        "height": world.height
    })


@app.route('/api/world/grid', methods=['GET'])
def get_world_grid():
    """Get the world terrain grid."""
    return jsonify({
        "status": "success",
        "grid": world.grid,
        "legend": {
            0: "grass",
            1: "forest",
            2: "water",
            3: "mountain"
        }
    })


# Town endpoints
@app.route('/api/town/<town_id>', methods=['GET'])
def get_town(town_id: str):
    """Get town-level details."""
    if town_id not in world.towns:
        return jsonify({"status": "error", "message": "Town not found"}), 404
    
    town = world.towns[town_id]
    return jsonify({
        "status": "success",
        "data": {
            "id": town.id,
            "name": town.name,
            "position": town.position,
            "width": town.width,
            "height": town.height,
            "description": town.description,
            "buildings": town.buildings,
            "population": town.population,
            "economy": town.economy,
            "culture": town.culture,
        }
    })


@app.route('/api/towns', methods=['GET'])
def list_towns():
    """List all towns."""
    towns_data = []
    for town in world.towns.values():
        towns_data.append({
            "id": town.id,
            "name": town.name,
            "position": town.position,
            "description": town.description,
            "population": town.population,
        })
    
    return jsonify({
        "status": "success",
        "data": towns_data
    })


# Character endpoints
@app.route('/api/character/<char_id>', methods=['GET'])
def get_character(char_id: str):
    """Get character details."""
    villager = scheduler.get_villager(char_id)
    if villager is None:
        return jsonify({"status": "error", "message": "Character not found"}), 404
    
    return jsonify({
        "status": "success",
        "data": villager.summary()
    })


@app.route('/api/characters', methods=['GET'])
def list_characters():
    """List all characters."""
    town_id = request.args.get('town')
    
    characters_data = []
    for villager in scheduler.villagers.values():
        if town_id and villager.town != town_id:
            continue
        characters_data.append(villager.summary())
    
    return jsonify({
        "status": "success",
        "data": characters_data
    })


@app.route('/api/character/<char_id>', methods=['PUT'])
def update_character(char_id: str):
    """Update character details (limited support for generated villagers)."""
    villager = scheduler.get_villager(char_id)
    if villager is None:
        return jsonify({"status": "error", "message": "Character not found"}), 404
    
    data = request.get_json()
    # Only allow updating relationships for now
    if "relationships" in data:
        villager.relationships.update(data["relationships"])
    
    return jsonify({
        "status": "success",
        "data": villager.summary()
    })


@app.route('/api/character/<char_id>/history', methods=['POST'])
def add_character_history(char_id: str):
    """Add an event to character history (stored in villager memories)."""
    villager = scheduler.get_villager(char_id)
    if villager is None:
        return jsonify({"status": "error", "message": "Character not found"}), 404
    
    data = request.get_json() or {}
    event = data.get('event')
    
    if not event:
        return jsonify({"status": "error", "message": "Event not provided"}), 400
    
    villager.memories.append(event)
    
    return jsonify({
        "status": "success",
        "data": villager.summary()
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
    """Get possible actions for a character based on nearby entities."""
    villager = scheduler.get_villager(char_id)
    if villager is None:
        return jsonify({"status": "error", "message": "Character not found"}), 404
    
    x, y = villager.position.x, villager.position.y
    
    # Find adjacent villagers
    adjacent_villagers = []
    for vid, v in scheduler.villagers.items():
        if vid != char_id and abs(v.position.x - x) <= 1 and abs(v.position.y - y) <= 1:
            adjacent_villagers.append({"id": v.id, "name": v.name})
    
    # Find nearby markets
    nearby_markets = []
    for mid, market in scheduler.markets.items():
        if abs(market.position[0] - x) <= 2 and abs(market.position[1] - y) <= 2:
            nearby_markets.append({"id": mid, "name": f"Market at {market.position}"})
    
    possible_actions = {
        "movement": ["north", "south", "east", "west"],
        "interactions": [
            {"type": "talk", "target": v["id"], "name": v["name"]} 
            for v in adjacent_villagers
        ],
        "trading": [
            {"type": "trade", "target": m["id"], "name": m["name"]}
            for m in nearby_markets
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
    villager = scheduler.get_villager(char_id)
    if villager is None:
        return jsonify({"status": "error", "message": "Character not found"}), 404
    
    data = request.get_json()
    new_x = data.get('x')
    new_y = data.get('y')
    
    if new_x is None or new_y is None:
        return jsonify({"status": "error", "message": "Position not provided"}), 400
    
    old_pos = (villager.position.x, villager.position.y)
    villager.position.x = new_x
    villager.position.y = new_y
    villager.memories.append(f"Moved from {old_pos} to ({new_x}, {new_y})")
    
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
