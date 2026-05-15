"""
Flask API for LLM Towns game.

Provides endpoints for:
- World overview (2D grid, biomes, POIs, roads, events)
- Town-level details with lore
- Character management
- Actions and interactions
- Dynamic world events (seasons, weather)
"""

from flask import Flask, request, jsonify
from typing import Dict, List, Any
import json
import math
import random
import threading
import time

from llm.brain import LLMBrain, OpenAIChatClient
from llm.prompts import build_goal_prompt
from simulation.actions import Goal
from simulation.market import Market
from simulation.planner import Planner
from simulation.scheduler import SimulationScheduler
from simulation.villager import Position, Villager
from world.world_generator import (
    World, WorldGenerator, Season, WeatherType, WorldEvent,
    PointOfInterest, Road,
)

app = Flask(__name__)

llm_brain = None
try:
    llm_client = OpenAIChatClient()
    llm_brain = LLMBrain(llm_client)
    planner = Planner(llm_brain=llm_brain)
except ValueError:
    planner = Planner()

# Generate world first, then scheduler
world_generator = WorldGenerator(llm_brain=llm_brain)
world = world_generator.generate_world(width=50, height=50, seed=42)
scheduler = SimulationScheduler(planner=planner, llm_brain=llm_brain, world=world)


def _create_world_entities() -> None:
    if not world.towns:
        return

    # Create villagers for each town
    for town_id, town in world.towns.items():
        villagers_data = world_generator.generate_villagers_for_town(world, town, count=3)
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

            goal = Goal(
                actor_id=villager.id,
                description="Explore the town",
                priority=3,
                created_tick=0,
            )
            scheduler.add_goal(goal)

    # Create a market in each town
    for town in world.towns.values():
        market = Market(
            id=f"market_{town.id}",
            position=(
                town.position[0] + town.width // 2,
                town.position[1] + town.height // 2,
            ),
            inventory={"food": 50, "wood": 30, "tools": 10},
            prices={"food": 2.0, "wood": 1.5, "tools": 5.0},
        )
        scheduler.add_market(market)


_create_world_entities()


def _simulation_loop() -> None:
    while True:
        scheduler.advance_tick(1)

        # Advance season every 720 ticks (~12 min)
        if scheduler.current_tick % 720 == 0 and scheduler.current_tick > 0:
            event = world_generator.advance_season(world)
            if event:
                scheduler.snapshot()["recent_events"].append(event.title)

        # Random events every 180 ticks (~3 min)
        if scheduler.current_tick % 180 == 0 and scheduler.current_tick > 0:
            event = world_generator.trigger_random_event(world)
            if event:
                scheduler.snapshot()["recent_events"].append(event.title)

        time.sleep(1)


simulation_thread = threading.Thread(target=_simulation_loop, daemon=True)
simulation_thread.start()


# ── World endpoints ─────────────────────────────────────────────────────

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
            "lore": world.lore,
            "world_history": world.world_history,
            "season": world.season.value,
            "weather": world.weather.value,
            "year": world.year,
            "world_age": world.world_age,
            "towns": list(world.towns.keys()),
            "terrain_features": list(world.terrain_features.keys()),
            "poi_count": len(world.poi_list),
            "road_count": len(world.roads),
            "active_event_count": len(world.active_events),
        },
    })


@app.route('/api/world/dimensions', methods=['GET'])
def get_world_dimensions():
    """Get world dimensions."""
    return jsonify({
        "status": "success",
        "width": world.width,
        "height": world.height,
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
            3: "mountain",
            4: "sand",
            5: "snow",
            6: "swamp",
            7: "road",
            8: "building",
            9: "house",
            10: "town_square",
        },
    })


@app.route('/api/world/biomes', methods=['GET'])
def get_world_biomes():
    """Get the world biome grid."""
    return jsonify({
        "status": "success",
        "grid": world.biome_grid,
    })


@app.route('/api/world/lore', methods=['GET'])
def get_world_lore():
    """Get the world's backstory and history."""
    return jsonify({
        "status": "success",
        "data": {
            "name": world.name,
            "description": world.description,
            "lore": world.lore,
            "history": world.world_history,
        },
    })


# ── Town endpoints ──────────────────────────────────────────────────────

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
            "lore": town.lore,
            "founded_year": town.founded_year,
            "buildings": town.buildings,
            "population": town.population,
            "economy": town.economy,
            "culture": town.culture,
            "relations": town.relations,
            "entry_points": town.entry_points,
        },
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
            "lore": town.lore,
            "population": town.population,
            "economy": town.economy,
            "culture": town.culture,
        })

    return jsonify({"status": "success", "data": towns_data})


# ── Point of Interest endpoints ─────────────────────────────────────────

@app.route('/api/world/points-of-interest', methods=['GET'])
def list_pois():
    """List all points of interest in the world."""
    pois = []
    for poi in world.poi_list:
        pois.append({
            "id": poi.id,
            "name": poi.name,
            "type": poi.type,
            "position": poi.position,
            "description": poi.description,
            "lore": poi.lore,
            "danger_level": poi.danger_level,
            "discovered": poi.discovered,
            "resources": poi.resources,
        })

    return jsonify({"status": "success", "data": pois})


@app.route('/api/world/points-of-interest/<poi_id>', methods=['GET'])
def get_poi(poi_id: str):
    """Get details of a specific point of interest."""
    poi = next((p for p in world.poi_list if p.id == poi_id), None)
    if poi is None:
        return jsonify({"status": "error", "message": "POI not found"}), 404

    return jsonify({
        "status": "success",
        "data": {
            "id": poi.id,
            "name": poi.name,
            "type": poi.type,
            "position": poi.position,
            "description": poi.description,
            "lore": poi.lore,
            "danger_level": poi.danger_level,
            "discovered": poi.discovered,
            "resources": poi.resources,
            "visited_by": poi.visited_by,
        },
    })


# ── Road endpoints ──────────────────────────────────────────────────────

@app.route('/api/world/roads', methods=['GET'])
def list_roads():
    """List all roads in the world."""
    roads = []
    for road in world.roads:
        roads.append({
            "id": road.id,
            "name": road.name,
            "start_town": road.start_town,
            "end_town": road.end_town,
            "path": road.path,
            "length": road.length,
            "condition": road.condition,
        })

    return jsonify({"status": "success", "data": roads})


# ── Character endpoints ─────────────────────────────────────────────────

@app.route('/api/character/<char_id>', methods=['GET'])
def get_character(char_id: str):
    """Get character details."""
    villager = scheduler.get_villager(char_id)
    if villager is None:
        return jsonify({"status": "error", "message": "Character not found"}), 404

    return jsonify({"status": "success", "data": villager.summary()})


@app.route('/api/characters', methods=['GET'])
def list_characters():
    """List all characters."""
    town_id = request.args.get('town')

    characters_data = []
    for villager in scheduler.villagers.values():
        if town_id and villager.town != town_id:
            continue
        characters_data.append(villager.summary())

    return jsonify({"status": "success", "data": characters_data})


@app.route('/api/character/<char_id>', methods=['PUT'])
def update_character(char_id: str):
    """Update character details (limited support for generated villagers)."""
    villager = scheduler.get_villager(char_id)
    if villager is None:
        return jsonify({"status": "error", "message": "Character not found"}), 404

    data = request.get_json()
    if "relationships" in data:
        villager.relationships.update(data["relationships"])

    return jsonify({"status": "success", "data": villager.summary()})


@app.route('/api/character/<char_id>/history', methods=['POST'])
def add_character_history(char_id: str):
    """Add an event to character history."""
    villager = scheduler.get_villager(char_id)
    if villager is None:
        return jsonify({"status": "error", "message": "Character not found"}), 404

    data = request.get_json() or {}
    event = data.get('event')

    if not event:
        return jsonify({"status": "error", "message": "Event not provided"}), 400

    villager.memories.append(event)

    return jsonify({"status": "success", "data": villager.summary()})


# ── Simulation endpoints ────────────────────────────────────────────────

@app.route('/api/sim/status', methods=['GET'])
def get_simulation_status():
    """Return the current simulation snapshot."""
    data = scheduler.snapshot()
    data["world"] = {
        "season": world.season.value,
        "weather": world.weather.value,
        "year": world.year,
        "world_age": world.world_age,
        "active_events": [e.title for e in world.active_events],
    }
    return jsonify({"status": "success", "data": data, "running": True})


@app.route('/api/sim/season/advance', methods=['POST'])
def advance_season():
    """Manually advance the season."""
    event = world_generator.advance_season(world)
    return jsonify({"status": "success", "event": {
        "type": event.type,
        "title": event.title,
        "description": event.description,
    }})


@app.route('/api/sim/event/random', methods=['POST'])
def trigger_random_event():
    """Manually trigger a random world event."""
    event = world_generator.trigger_random_event(world)
    if event is None:
        return jsonify({"status": "error", "message": "No event triggered"}), 400
    return jsonify({"status": "success", "event": {
        "type": event.type,
        "title": event.title,
        "description": event.description,
    }})


@app.route('/api/sim/events', methods=['GET'])
def get_events():
    """List recent world events."""
    limit = int(request.args.get('limit', 20))
    recent = world.events[-limit:]
    return jsonify({
        "status": "success",
        "data": [
            {
                "id": e.id,
                "type": e.type,
                "title": e.title,
                "description": e.description,
                "tick_start": e.tick_start,
                "resolved": e.resolved,
            }
            for e in recent
        ],
    })


# ── Villager goal endpoints ─────────────────────────────────────────────

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

    goal = Goal(
        actor_id=villager_id,
        description=description,
        priority=priority,
        created_tick=scheduler.current_tick,
    )
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
        "world_season": world.season.value,
        "world_weather": world.weather.value,
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


# ── Actions endpoints ───────────────────────────────────────────────────

@app.route('/api/character/<char_id>/possible-actions', methods=['GET'])
def get_possible_actions(char_id: str):
    """Get possible actions for a character based on nearby entities."""
    villager = scheduler.get_villager(char_id)
    if villager is None:
        return jsonify({"status": "error", "message": "Character not found"}), 404

    x, y = villager.position.x, villager.position.y

    adjacent_villagers = []
    for vid, v in scheduler.villagers.items():
        if vid != char_id and abs(v.position.x - x) <= 1 and abs(v.position.y - y) <= 1:
            adjacent_villagers.append({"id": v.id, "name": v.name})

    nearby_markets = []
    for mid, market in scheduler.markets.items():
        if abs(market.position[0] - x) <= 2 and abs(market.position[1] - y) <= 2:
            nearby_markets.append({"id": mid, "name": f"Market at {market.position}"})

    # Find nearby POIs
    nearby_pois = []
    for poi in world.poi_list:
        if not poi.discovered:
            continue
        dist = math.sqrt((poi.position[0] - x) ** 2 + (poi.position[1] - y) ** 2)
        if dist <= 5:
            nearby_pois.append({
                "id": poi.id,
                "name": poi.name,
                "type": poi.type,
                "danger_level": poi.danger_level,
            })

    # Travel options to other towns
    travel_options = []
    for town_id, town in world.towns.items():
        if town_id != villager.town:
            road_conn = any(
                r for r in world.roads
                if (r.start_town == villager.town and r.end_town == town_id) or
                   (r.end_town == villager.town and r.start_town == town_id)
            )
            if road_conn:
                travel_options.append({
                    "type": "travel",
                    "target": town_id,
                    "name": town.name,
                })

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
        "explore": [
            {"type": "explore", "target": p["id"], "name": p["name"], "danger": p["danger_level"]}
            for p in nearby_pois
        ],
        "travel": travel_options,
        "objects": ["pick_up", "drop", "use"],
    }

    return jsonify({"status": "success", "data": possible_actions})


# ── Interactions endpoints ──────────────────────────────────────────────

@app.route('/api/interact', methods=['POST'])
def interact():
    """Execute an interaction between two characters or with an object."""
    data = request.get_json()
    char_id = data.get('actor')
    target_id = data.get('target')
    action_type = data.get('type', 'talk')

    actor = scheduler.get_villager(char_id)
    target = scheduler.get_villager(target_id)

    if actor is None or target is None:
        return jsonify({"status": "error", "message": "Character not found"}), 404

    actor_town_name = world.towns[actor.town].name if actor.town in world.towns else "the wilderness"
    target_town_name = world.towns[target.town].name if target.town in world.towns else "the wilderness"

    interaction_result = {
        "actor": char_id,
        "target": target_id,
        "type": action_type,
        "success": True,
        "message": f"{actor.name} {action_type}s with {target.name}",
    }

    actor.memories.append(f"{action_type.capitalize()} with {target.name} from {target_town_name}")
    target.memories.append(f"{actor.name} from {actor_town_name} {action_type}s with you")

    return jsonify({"status": "success", "data": interaction_result})


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
            "new_position": (new_x, new_y),
        },
    })


# ── Health check ────────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
