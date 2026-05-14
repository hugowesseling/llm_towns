from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random

from llm.brain import LLMBrain


@dataclass
class TerrainFeature:
    id: str
    name: str
    type: str  # forest, mountain, river, field, etc.
    position: Tuple[int, int]
    size: Tuple[int, int]  # width, height
    description: str
    resources: Dict[str, int] = field(default_factory=dict)  # resource_name -> quantity
    walkable: bool = True


@dataclass
class Town:
    id: str
    name: str
    position: Tuple[int, int]
    width: int
    height: int
    description: str
    buildings: List[Dict[str, str]] = field(default_factory=list)  # [{"type": "market", "name": "Central Market"}]
    population: int = 0
    economy: str = "agricultural"  # agricultural, mercantile, industrial, etc.
    culture: str = "traditional"  # traditional, progressive, mystical, etc.


@dataclass
class World:
    width: int
    height: int
    grid: List[List[int]] = field(default_factory=list)  # 0=grass, 1=forest, 2=water, 3=mountain, etc.
    towns: Dict[str, Town] = field(default_factory=dict)
    terrain_features: Dict[str, TerrainFeature] = field(default_factory=dict)
    name: str = "Unknown World"
    description: str = ""
    climate: str = "temperate"  # temperate, tropical, desert, arctic, etc.
    era: str = "medieval"  # ancient, medieval, renaissance, industrial, etc.

    def __post_init__(self):
        if not self.grid:
            self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def get_tile_type(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return -1  # out of bounds

    def is_walkable(self, x: int, y: int) -> bool:
        tile_type = self.get_tile_type(x, y)
        if tile_type == -1:
            return False
        # Define walkable tiles: 0=grass, 1=forest (slow), 2=water (no), 3=mountain (no)
        return tile_type in [0, 1]

    def add_terrain_feature(self, feature: TerrainFeature) -> None:
        self.terrain_features[feature.id] = feature
        # Update grid with feature
        for dy in range(feature.size[1]):
            for dx in range(feature.size[0]):
                x, y = feature.position[0] + dx, feature.position[1] + dy
                if 0 <= x < self.width and 0 <= y < self.height:
                    # Map feature types to tile types
                    tile_mapping = {
                        "forest": 1,
                        "mountain": 3,
                        "river": 2,
                        "lake": 2,
                    }
                    self.grid[y][x] = tile_mapping.get(feature.type, 0)

    def add_town(self, town: Town) -> None:
        self.towns[town.id] = town


class WorldGenerator:
    def __init__(self, llm_brain: Optional[LLMBrain] = None):
        self.llm_brain = llm_brain

    def generate_world(self, width: int = 50, height: int = 50) -> World:
        """Generate a complete world using LLM or fallbacks."""
        world = World(width=width, height=height)

        if self.llm_brain:
            world_data = self._generate_world_with_llm(width, height)
            world.name = world_data.get("name", "Generated World")
            world.description = world_data.get("description", "")
            world.climate = world_data.get("climate", "temperate")
            world.era = world_data.get("era", "medieval")
        else:
            world.name = "Fallback World"
            world.description = "A simple generated world"
            world.climate = "temperate"
            world.era = "medieval"

        # Generate terrain features
        self._generate_terrain_features(world)

        # Generate towns
        self._generate_towns(world)

        return world

    def _generate_world_with_llm(self, width: int, height: int) -> Dict[str, str]:
        """Use LLM to generate world metadata."""
        system_prompt = (
            "You are a world-building assistant for a medieval village simulation. "
            "Generate a world description with name, description, climate, and era. "
            "Return only a JSON object with these keys. Keep descriptions concise."
        )

        user_prompt = (
            f"Generate a medieval world {width}x{height} tiles. "
            "Include a creative name, brief description, climate type, and historical era."
        )

        try:
            return self.llm_brain.chat_json(
                system=system_prompt,
                user=user_prompt,
                temperature=0.8,
                max_tokens=150,
            )
        except Exception:
            return {
                "name": "Mystwood Valley",
                "description": "A lush valley surrounded by ancient forests and rolling hills",
                "climate": "temperate",
                "era": "medieval",
            }

    def _generate_terrain_features(self, world: World) -> None:
        """Generate terrain features for the world."""
        num_features = random.randint(3, 8)

        feature_types = ["forest", "mountain", "river", "lake"]
        feature_names = {
            "forest": ["Darkwood Forest", "Eldergrove", "Whispering Woods", "Ironbark Grove"],
            "mountain": ["Stonepeak Mountains", "Dragonspine Range", "Crystal Hills", "Thunderpeaks"],
            "river": ["Silverbrook River", "Crystal Stream", "Meadowflow", "Deepwater"],
            "lake": ["Mirror Lake", "Tranquil Waters", "Moonpool", "Serene Lake"],
        }

        for i in range(num_features):
            feature_type = random.choice(feature_types)
            name = random.choice(feature_names[feature_type])

            # Find a valid position
            max_attempts = 50
            for _ in range(max_attempts):
                x = random.randint(0, world.width - 5)
                y = random.randint(0, world.height - 5)
                size = (random.randint(3, 8), random.randint(3, 8))

                # Check if area is clear
                clear = True
                for dy in range(size[1]):
                    for dx in range(size[0]):
                        if not world.is_walkable(x + dx, y + dy):
                            clear = False
                            break
                    if not clear:
                        break

                if clear:
                    feature = TerrainFeature(
                        id=f"feature_{i}",
                        name=name,
                        type=feature_type,
                        position=(x, y),
                        size=size,
                        description=f"A {feature_type} feature in the landscape",
                        walkable=feature_type in ["forest"],  # forests are walkable but slow
                    )

                    # Add some resources
                    if feature_type == "forest":
                        feature.resources = {"wood": random.randint(50, 200)}
                    elif feature_type == "mountain":
                        feature.resources = {"stone": random.randint(30, 100), "ore": random.randint(10, 50)}

                    world.add_terrain_feature(feature)
                    break

    def _generate_towns(self, world: World) -> None:
        """Generate towns for the world."""
        num_towns = random.randint(2, 5)

        town_names = [
            "Riverford", "Stonebrook", "Eldridge", "Meadowvale", "Oakwood",
            "Silverpeak", "Greenfield", "Blackwood", "Crystalbrook", "Ironforge"
        ]

        for i in range(num_towns):
            # Find a suitable location (prefer grasslands)
            max_attempts = 50
            for _ in range(max_attempts):
                x = random.randint(5, world.width - 15)
                y = random.randint(5, world.height - 15)

                # Check if area is mostly grass
                grass_count = 0
                total_count = 0
                for dy in range(10):
                    for dx in range(10):
                        if world.get_tile_type(x + dx, y + dy) == 0:
                            grass_count += 1
                        total_count += 1

                if grass_count / total_count > 0.7:  # 70% grass
                    town = Town(
                        id=f"town_{i}",
                        name=random.choice(town_names),
                        position=(x, y),
                        width=10,
                        height=10,
                        description=f"A {random.choice(['quaint', 'bustling', 'peaceful', 'prosperous'])} village",
                        population=random.randint(50, 200),
                        economy=random.choice(["agricultural", "mercantile", "crafts"]),
                        culture=random.choice(["traditional", "progressive", "spiritual"]),
                    )

                    # Add some buildings
                    buildings = [
                        {"type": "market", "name": "Central Market"},
                        {"type": "inn", "name": "Traveler's Rest"},
                        {"type": "blacksmith", "name": "Forge & Anvil"},
                        {"type": "temple", "name": "Sacred Grove"},
                    ]
                    town.buildings = random.sample(buildings, random.randint(2, 4))

                    world.add_town(town)
                    break

    def generate_villagers_for_town(self, town: Town, count: int = 5) -> List[Dict[str, any]]:
        """Generate villagers for a specific town."""
        villagers = []

        professions = ["Farmer", "Merchant", "Blacksmith", "Innkeeper", "Guard", "Priest", "Herbalist"]
        first_names = ["Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Helen"]
        last_names = ["Smith", "Johnson", "Brown", "Williams", "Jones", "Garcia", "Miller", "Davis"]

        for i in range(count):
            villager = {
                "id": f"{town.id}_villager_{i}",
                "name": f"{random.choice(first_names)} {random.choice(last_names)}",
                "town": town.id,
                "profession": random.choice(professions),
                "position": (
                    town.position[0] + random.randint(0, town.width - 1),
                    town.position[1] + random.randint(0, town.height - 1)
                ),
                "needs": {
                    "hunger": random.randint(30, 70),
                    "energy": random.randint(50, 90),
                    "social": random.randint(40, 80),
                },
                "inventory": {"gold": random.randint(5, 20)},
                "relationships": {},
                "description": f"A {random.choice(['friendly', 'hardworking', 'mysterious', 'ambitious'])} villager",
            }
            villagers.append(villager)

        return villagers