from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from llm.brain import LLMBrain


# ── Noise (simple 2D value noise, stdlib-only) ──────────────────────────

class _NoiseGrid:
    """Permutation-based 2D value noise generator."""

    def __init__(self, seed: int | None = None):
        rng = random.Random(seed)
        perm = list(range(256))
        rng.shuffle(perm)
        self.perm = perm + perm  # double for overflow

    def _fade(self, t: float) -> float:
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    def _grad(self, h: int, x: float, y: float) -> float:
        h = h & 7
        ux = h & 4
        uy = h & 2
        if (h & 1) == 0:
            xh = ux
        else:
            xh = -ux
        if (h & 1) == 0:
            yh = uy
        else:
            yh = -uy
        return (xh * x + yh * y)

    def noise(self, x: float, y: float, octaves: int = 4, persistence: float = 0.5) -> float:
        total = 0.0
        frequency = 1.0
        amplitude = 1.0
        max_val = 0.0
        for _ in range(octaves):
            xi = int(math.floor(x * frequency)) & 255
            yi = int(math.floor(y * frequency)) & 255
            xf = x * frequency - math.floor(x * frequency)
            yf = y * frequency - math.floor(y * frequency)
            u = self._fade(xf)
            v = self._fade(yf)
            aa = self._grad(self.perm[self.perm[xi] + yi], xf, yf)
            ab = self._grad(self.perm[self.perm[xi] + yi + 1], xf, yf - 1)
            ba = self._grad(self.perm[self.perm[xi + 1] + yi], xf - 1, yf)
            bb = self._grad(self.perm[self.perm[xi + 1] + yi + 1], xf - 1, yf - 1)
            total += self._lerp(self._lerp(aa, ba, u), self._lerp(ab, bb, u), v) * amplitude
            max_val += amplitude
            amplitude *= persistence
            frequency *= 2
        return total / max_val


# ── Enums ────────────────────────────────────────────────────────────────

class BiomeType(str, Enum):
    GRASSLAND = "grassland"
    FOREST = "forest"
    DESERT = "desert"
    TUNDRA = "tundra"
    SWAMP = "swamp"
    PLAINS = "plains"
    HIGHLANDS = "highlands"


class TerrainTile(int, Enum):
    GRASS = 0
    FOREST = 1
    WATER = 2
    MOUNTAIN = 3
    SAND = 4
    SNOW = 5
    SWAMP_TERRAIN = 6
    ROAD = 7


class WeatherType(str, Enum):
    CLEAR = "clear"
    RAIN = "rain"
    SNOW = "snow"
    STORM = "storm"
    FOG = "fog"
    DUST_STORM = "dust_storm"


class Season(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


class POIType(str, Enum):
    RUINS = "ruins"
    DUNGEON = "dungeon"
    LANDMARK = "landmark"
    SHRINE = "shrine"
    TREASURE = "treasure"
    CAMPFIRE = "campfire"
    WRECKAGE = "wreckage"
    FORTRESS = "fortress"


class WorldEventType(str, Enum):
    SEASON_CHANGE = "season_change"
    WEATHER_CHANGE = "weather_change"
    MIGRATION = "migration"
    DISASTER = "disaster"
    TRADE_ARRIVAL = "trade_arrival"
    MONSTER_SIGHTING = "monster_sighting"
    FESTIVAL = "festival"
    BANDIT_RAID = "bandit_raid"


# ── Data classes ─────────────────────────────────────────────────────────

@dataclass
class TerrainFeature:
    id: str
    name: str
    type: str
    position: Tuple[int, int]
    size: Tuple[int, int]
    description: str
    resources: Dict[str, int] = field(default_factory=dict)
    walkable: bool = True


@dataclass
class Town:
    id: str
    name: str
    position: Tuple[int, int]
    width: int
    height: int
    description: str
    buildings: List[Dict[str, str]] = field(default_factory=list)
    population: int = 0
    economy: str = "agricultural"
    culture: str = "traditional"
    lore: str = ""
    founded_year: int = 0
    relations: Dict[str, str] = field(default_factory=dict)  # town_id -> relationship


@dataclass
class World:
    width: int
    height: int
    grid: List[List[int]] = field(default_factory=list)
    towns: Dict[str, Town] = field(default_factory=dict)
    terrain_features: Dict[str, TerrainFeature] = field(default_factory=dict)
    name: str = "Unknown World"
    description: str = ""
    climate: str = "temperate"
    era: str = "medieval"
    lore: str = ""
    world_history: List[Dict[str, str]] = field(default_factory=list)
    biome_grid: List[List[str]] = field(default_factory=list)
    poi_list: List[PointOfInterest] = field(default_factory=list)
    roads: List[Road] = field(default_factory=list)
    season: Season = Season.SPRING
    weather: WeatherType = WeatherType.CLEAR
    world_age: int = 0  # in years
    year: int = 1
    events: List[WorldEvent] = field(default_factory=list)
    active_events: List[WorldEvent] = field(default_factory=list)

    def __post_init__(self):
        if not self.grid:
            self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        if not self.biome_grid:
            self.biome_grid = [["grassland" for _ in range(self.width)] for _ in range(self.height)]

    def get_tile_type(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return -1

    def get_biome(self, x: int, y: int) -> str:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.biome_grid[y][x]
        return "unknown"

    def is_walkable(self, x: int, y: int) -> bool:
        tile_type = self.get_tile_type(x, y)
        if tile_type == -1:
            return False
        return tile_type in [0, 1, 4, 5, 6, 7]

    def add_terrain_feature(self, feature: TerrainFeature) -> None:
        self.terrain_features[feature.id] = feature
        for dy in range(feature.size[1]):
            for dx in range(feature.size[0]):
                fx, fy = feature.position[0] + dx, feature.position[1] + dy
                if 0 <= fx < self.width and 0 <= fy < self.height:
                    tile_mapping = {
                        "forest": 1,
                        "mountain": 3,
                        "river": 2,
                        "lake": 2,
                    }
                    self.grid[fy][fx] = tile_mapping.get(feature.type, 0)

    def add_town(self, town: Town) -> None:
        self.towns[town.id] = town


@dataclass
class PointOfInterest:
    id: str
    name: str
    type: str
    position: Tuple[int, int]
    description: str
    lore: str = ""
    resources: Dict[str, int] = field(default_factory=dict)
    danger_level: int = 1  # 1-10
    discovered: bool = False
    visited_by: List[str] = field(default_factory=list)  # villager_ids


@dataclass
class Road:
    id: str
    name: str
    start_town: str
    end_town: str
    path: List[Tuple[int, int]] = field(default_factory=list)
    length: int = 0
    condition: str = "good"  # good, fair, broken


@dataclass
class WorldEvent:
    id: str
    type: str
    title: str
    description: str
    affected_towns: List[str] = field(default_factory=list)
    affected_positions: List[Tuple[int, int]] = field(default_factory=list)
    tick_start: int = 0
    duration_ticks: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False


# ── Generator ────────────────────────────────────────────────────────────

class WorldGenerator:
    def __init__(self, llm_brain: Optional[LLMBrain] = None):
        self.llm_brain = llm_brain

    def generate_world(self, width: int = 50, height: int = 50, seed: int | None = None) -> World:
        """Generate a complete world with biomes, terrain, towns, POIs, roads, and lore."""
        random.seed(seed)
        noise = _NoiseGrid(seed)

        world = World(width=width, height=height)

        # Step 1: LLM-generated world metadata
        if self.llm_brain:
            meta = self._generate_world_metadata(width, height, seed)
            world.name = meta.get("name", "Generated World")
            world.description = meta.get("description", "")
            world.climate = meta.get("climate", "temperate")
            world.era = meta.get("era", "medieval")
            world.lore = meta.get("lore", "")
            world.world_history = meta.get("history", [])
        else:
            world.name = "Fallback World"
            world.description = "A simple generated world"
            world.climate = "temperate"
            world.era = "medieval"

        # Step 2: Biome grid generation
        self._generate_biomes(world, noise)

        # Step 3: Terrain grid generation from biomes
        self._generate_terrain_from_biomes(world, noise)

        # Step 4: Town generation
        self._generate_towns(world, noise)

        # Step 5: LLM lore for towns
        if self.llm_brain:
            self._generate_town_lore(world)

        # Step 6: Terrain features
        self._generate_terrain_features(world, noise)

        # Step 7: Points of interest
        self._generate_pois(world, noise)

        # Step 8: Roads between towns
        self._generate_roads(world)

        return world

    # ── World metadata (LLM) ────────────────────────────────────────────

    def _generate_world_metadata(self, width: int, height: int, seed: int | None) -> Dict[str, Any]:
        system_prompt = (
            "You are a world-building assistant for a medieval village simulation. "
            "Create a rich, immersive world. Return only a JSON object with:\n"
            '"name" (string), "description" (2-3 sentences), "climate" (temperate/tropical/desert/arctic), '
            '"era" (ancient/medieval/renaissance/industrial), "lore" (3-4 sentences of world origin), '
            '"history" (array of 3-5 objects with "year" and "event" keys describing key moments in world history).'
        )
        user_prompt = (
            f"Generate a world of {width}x{height} tiles. "
            "Make it evocative and unique. Vary the year numbers in history to show passage of time."
        )

        try:
            return self.llm_brain.chat_json(
                system=system_prompt,
                user=user_prompt,
                temperature=0.85,
                max_tokens=400,
            )
        except Exception:
            return {
                "name": "Aethelgard",
                "description": "A land of rolling hills and ancient forests, where small villages scrape a living between the wilds and the remnants of a forgotten empire.",
                "climate": "temperate",
                "era": "medieval",
                "lore": "Aethelgard was shaped in the Age of Ash, when the dragons fell and their blood cooled into the black stone that now powers the furnaces of the north. The surviving kingdoms built upon the ashes, forging a new age of trade and exploration.",
                "history": [
                    {"year": 1, "event": "The Age of Ash begins as the great dragons fall."},
                    {"year": 47, "event": "The first settlements arise in the fertile valleys."},
                    {"year": 112, "event": "The Kingdom of Eldenmarsh establishes trade routes across the continent."},
                    {"year": 203, "event": "The Great Plague wipes out a third of the population."},
                    {"year": 315, "event": "The current age of recovery and rebuilding begins."},
                ],
            }

    # ── Biome generation ────────────────────────────────────────────────

    def _generate_biomes(self, world: World, noise: _NoiseGrid) -> None:
        """Generate a biome grid using layered noise."""
        moisture = [[0.0] * world.width for _ in range(world.height)]
        temperature = [[0.0] * world.width for _ in range(world.height)]
        elevation = [[0.0] * world.width for _ in range(world.height)]

        for y in range(world.height):
            for x in range(world.width):
                moisture[y][x] = (noise.noise(x * 0.03, y * 0.03, 4) + 1) / 2
                temperature[y][x] = (noise.noise(x * 0.02 + 100, y * 0.02 + 100, 3) + 1) / 2
                elevation[y][x] = (noise.noise(x * 0.04 + 200, y * 0.04 + 200, 5) + 1) / 2

        for y in range(world.height):
            for x in range(world.width):
                m = moisture[y][x]
                t = temperature[y][x]
                e = elevation[y][x]

                if e > 0.75:
                    if t > 0.55:
                        biome = BiomeType.HIGHLANDS.value
                    else:
                        biome = BiomeType.TUNDRA.value
                elif t > 0.65 and m < 0.35:
                    biome = BiomeType.DESERT.value
                elif m > 0.65 and t < 0.45:
                    biome = BiomeType.SWAMP.value
                elif e > 0.55 and t > 0.5:
                    biome = BiomeType.FOREST.value
                elif m > 0.55 and e < 0.5:
                    biome = BiomeType.FOREST.value
                elif t > 0.6 and e < 0.4:
                    biome = BiomeType.PLAINS.value
                else:
                    biome = BiomeType.GRASSLAND.value

                world.biome_grid[y][x] = biome

    # ── Terrain grid from biomes ────────────────────────────────────────

    def _generate_terrain_from_biomes(self, world: World, noise: _NoiseGrid) -> None:
        """Convert biome grid to terrain tile grid."""
        biome_to_tile = {
            "grassland": 0,
            "plains": 0,
            "forest": 1,
            "highlands": 3,
            "tundra": 5,
            "desert": 4,
            "swamp": 6,
        }

        for y in range(world.height):
            for x in range(world.width):
                biome = world.biome_grid[y][x]
                tile = biome_to_tile.get(biome, 0)
                world.grid[y][x] = tile

        # Scatter water bodies in low-elevation, high-moisture areas
        for y in range(2, world.height - 2):
            for x in range(2, world.width - 2):
                if world.get_biome(x, y) in ("grassland", "plains"):
                    local_noise = noise.noise(x * 0.08, y * 0.08, 2)
                    if local_noise > 0.75 and random.random() < 0.15:
                        world.grid[y][x] = 2  # water

        # Smooth lakes into slightly larger bodies
        for y in range(2, world.height - 2):
            for x in range(2, world.width - 2):
                if world.get_tile_type(x, y) == 2:
                    neighbors_water = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            if world.get_tile_type(x + dx, y + dy) == 2:
                                neighbors_water += 1
                    if neighbors_water >= 4:
                        world.grid[y][x] = 2

    # ── Town generation ─────────────────────────────────────────────────

    def _generate_towns(self, world: World, noise: _NoiseGrid) -> None:
        """Place towns in suitable biome locations, well separated."""
        num_towns = random.randint(3, 6)
        candidate_biomes = {"grassland", "plains", "forest"}

        # Gather candidate positions (tiles that are walkable grass)
        candidates = []
        for y in range(5, world.height - 10):
            for x in range(5, world.width - 10):
                if world.get_tile_type(x, y) == 0:
                    cx, cy = world.width / 2, world.height / 2
                    dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                    score = 1.0 / (1.0 + dist / (world.width / 2))
                    candidates.append((score, x, y))

        candidates.sort(reverse=True)

        # Greedy selection with minimum spacing
        town_positions = []  # list of (x, y)
        MIN_SPACING = 14  # minimum distance between towns

        for score, x, y in candidates:
            if len(town_positions) >= num_towns:
                break
            # Check distance to already-selected towns
            too_close = any(
                math.sqrt((x - tx) ** 2 + (y - ty) ** 2) < MIN_SPACING
                for tx, ty in town_positions
            )
            if too_close:
                continue

            # Verify there's a cluster of grass around this point
            grass_count = 0
            for ty in range(10):
                for tx in range(10):
                    nx, ny = x + tx, y + ty
                    if 0 <= nx < world.width and 0 <= ny < world.height:
                        if world.get_tile_type(nx, ny) == 0:
                            grass_count += 1
            if grass_count < 35:
                continue

            town_positions.append((x, y))

        # Place towns at selected positions
        used_names = set()
        town_names_pool = [
            "Riverford", "Stonebrook", "Eldridge", "Meadowvale", "Oakwood",
            "Silverpeak", "Greenfield", "Blackwood", "Crystalbrook", "Ironforge",
            "Holloway", "Thornwick", "Ashenmere", "Dunbrook", "Falkenholm",
            "Wyrmbane", "Crow's Rest", "Winterhold", "Misthollow", "Emberstead",
        ]

        for i, (tx, ty) in enumerate(town_positions):
            grass_count = 0
            for ty2 in range(10):
                for tx2 in range(10):
                    nx, ny = tx + tx2, ty + ty2
                    if 0 <= nx < world.width and 0 <= ny < world.height:
                        if world.get_tile_type(nx, ny) == 0:
                            grass_count += 1

            name = random.choice([n for n in town_names_pool if n not in used_names])
            used_names.add(name)

            town = Town(
                id=f"town_{i}",
                name=name,
                position=(tx, ty),
                width=random.randint(8, 12),
                height=random.randint(8, 12),
                description=f"A {'quaint' if grass_count < 50 else 'prosperous' if grass_count > 60 else 'peaceful'} settlement",
                population=random.randint(80, 500),
                economy=random.choice(["agricultural", "mercantile", "crafts", "fishing", "mining"]),
                culture=random.choice(["traditional", "progressive", "spiritual", "militant", "scholarly"]),
            )
            buildings_pool = [
                {"type": "market", "name": "Central Market"},
                {"type": "inn", "name": "The Traveler's Rest"},
                {"type": "blacksmith", "name": "Forge & Anvil"},
                {"type": "temple", "name": "Sacred Grove"},
                {"type": "tavern", "name": "The Drunken Badger"},
                {"type": "library", "name": "Town Archives"},
                {"type": "guild", "name": "Merchants' Guild"},
                {"type": "bakery", "name": "Golden Crust Bakery"},
            ]
            town.buildings = random.sample(buildings_pool, random.randint(3, 6))
            world.add_town(town)

    # ── Town lore (LLM) ─────────────────────────────────────────────────

    def _generate_town_lore(self, world: World) -> None:
        """Generate backstory and relations for each town using LLM."""
        if len(world.towns) < 2:
            return

        town_summaries = "\n".join(
            f"- {t.name} (pop: {t.population}, economy: {t.economy}, culture: {t.culture})"
            for t in world.towns.values()
        )
        system_prompt = (
            "You are a world-building assistant. For each town listed, generate a short 1-2 sentence lore description "
            "and a founded year (a positive integer between 50 and 300). Also define relations between town pairs: "
            "'allied', 'neutral', 'rival', 'trade_partner'. Return a JSON object with keys as town ids and values as:\n"
            '{"lore": string, "founded_year": int, "relations": {town_id: relation_string}}'
        )
        user_prompt = (
            f"World: {world.name}. Towns:\n{town_summaries}\n"
            "Generate rich, differentiated lore for each town."
        )

        try:
            data = self.llm_brain.chat_json(
                system=system_prompt,
                user=user_prompt,
                temperature=0.8,
                max_tokens=600,
            )
            for town_id, info in data.items():
                if town_id in world.towns:
                    world.towns[town_id].lore = info.get("lore", "")
                    world.towns[town_id].founded_year = info.get("founded_year", 100)
                    world.towns[town_id].relations = info.get("relations", {})
        except Exception:
            for town in world.towns.values():
                town.founded_year = random.randint(50, 300)

    # ── Terrain features ────────────────────────────────────────────────

    def _generate_terrain_features(self, world: World, noise: _NoiseGrid) -> None:
        """Place terrain features aligned with biome types."""
        feature_templates = {
            "forest": {
                "names": ["Darkwood Forest", "Eldergrove", "Whispering Woods", "Ironbark Grove", "Shadowfen Thicket"],
                "resource": "wood",
                "min_qty": 50,
                "max_qty": 200,
                "biomes": {"forest", "grassland", "plains"},
            },
            "mountain": {
                "names": ["Stonepeak Mountains", "Dragonspine Range", "Crystal Hills", "Thunderpeaks", "Ironcrest"],
                "resources": {"stone": (30, 100), "ore": (10, 50)},
                "biomes": {"highlands", "plains"},
            },
            "lake": {
                "names": ["Mirror Lake", "Tranquil Waters", "Moonpool", "Serene Lake", "Silvermere"],
                "biomes": {"grassland", "plains", "forest", "swamp"},
            },
            "ruins": {
                "names": ["Ancient Ruins", "Fallen Keep", "Old Crypt", "Lost Temple", "Shattered Tower"],
                "biomes": {"grassland", "plains", "desert", "tundra"},
            },
        }

        feature_count = random.randint(4, 10)
        for i in range(feature_count):
            feat_type = random.choice(list(feature_templates.keys()))
            template = feature_templates[feat_type]

            valid_positions = []
            for y in range(3, world.height - 3):
                for x in range(3, world.width - 3):
                    if world.get_biome(x, y) in template["biomes"]:
                        valid_positions.append((x, y))

            if not valid_positions:
                continue

            fx, fy = random.choice(valid_positions)
            fw = random.randint(3, 6)
            fh = random.randint(3, 6)

            # Check clear
            clear = True
            for dy in range(fh):
                for dx in range(fw):
                    if not world.is_walkable(fx + dx, fy + dy):
                        clear = False
                        break
                if not clear:
                    break
            if not clear:
                continue

            name = random.choice(template["names"])
            walkable = feat_type == "forest"

            resources = {}
            if feat_type == "forest":
                resources = {template["resource"]: random.randint(template["min_qty"], template["max_qty"])}
            elif feat_type == "mountain":
                for res, (lo, hi) in template["resources"].items():
                    resources[res] = random.randint(lo, hi)

            feature = TerrainFeature(
                id=f"feature_{i}",
                name=name,
                type=feat_type,
                position=(fx, fy),
                size=(fw, fh),
                description=f"A {feat_type} feature in the {world.get_biome(fx, fy)} biome",
                resources=resources,
                walkable=walkable,
            )
            world.add_terrain_feature(feature)

    # ── Points of interest ──────────────────────────────────────────────

    def _generate_pois(self, world: World, noise: _NoiseGrid) -> None:
        """Place interesting landmarks across the world."""
        num_pois = random.randint(6, 12)
        poi_templates = [
            (POIType.RUINS, "Ancient Ruins", "The crumbling remains of a forgotten civilization.", "Legends say treasure lies buried beneath the broken stones."),
            (POIType.DUNGEON, "Dark Dungeon", "A cavern system stretching deep beneath the earth.", "Brave adventurers speak of treasures and dangers in equal measure."),
            (POIType.LANDMARK, "Eagle's Perch", "A towering cliff overlooking the valley.", "Birds nest on its sheer face; the view from the top can be seen for miles."),
            (POIType.SHRINE, "Old Shrine", "A weathered shrine to an unknown deity.", "Pilgrims occasionally leave offerings at its weathered altar."),
            (POIType.TREASURE, "Buried Cache", "A hidden cache marked by strange carvings.", "Some say a merchant of old hid their wealth here."),
            (POIType.CAMPFIRE, "Wanderer's Camp", "The smoldering remains of a traveler's camp.", "Scattered maps and torn supplies hint at a hasty departure."),
            (POIType.WRECKAGE, "Wagon Wreckage", "The shattered remains of a merchant wagon.", "Wildlife has claimed the scattered cargo."),
            (POIType.FORTRESS, "Abandoned Fortress", "A massive stone fortress, long since emptied.", "Its walls are thick enough to withstand any siege."),
        ]

        selected_templates = random.choices(poi_templates, k=num_pois)

        for i, (poi_type, base_name, base_desc, lore) in enumerate(selected_templates):
            # Find valid position (not on water/mountain, not too close to towns)
            valid = False
            for _ in range(100):
                px = random.randint(2, world.width - 3)
                py = random.randint(2, world.height - 3)
                if world.get_tile_type(px, py) == 2 or world.get_tile_type(px, py) == 3:
                    continue

                # Not too close to towns
                too_close = False
                for town in world.towns.values():
                    dist = math.sqrt((px - town.position[0]) ** 2 + (py - town.position[1]) ** 2)
                    if dist < 10:
                        too_close = True
                        break
                if too_close:
                    continue

                # Not on existing terrain feature
                on_feature = False
                for feat in world.terrain_features.values():
                    fx, fy = feat.position
                    fw, fh = feat.size
                    if fx <= px < fx + fw and fy <= py < fy + fh:
                        on_feature = True
                        break
                if on_feature:
                    continue

                valid = True
                break

            if not valid:
                continue

            # Name with biome flavor
            biome = world.get_biome(px, py)
            name_prefixes = {
                "forest": ["Shaded", "Deep", "Verdant", "Shadowed"],
                "desert": ["Burning", "Dusty", "Sun-scorched", "Silent"],
                "tundra": ["Frozen", "Icy", "Bleak", "Hoarfrost"],
                "swamp": ["Murky", "Fogbound", "Misty", "Mire"],
                "highlands": ["Wind-swept", "Craggy", "High", "Sky"],
                "grassland": ["Open", "Rolling", "Sunlit", "Wide"],
                "plains": ["Endless", "Vast", "Flat", "Golden"],
            }
            prefix = random.choice(name_prefixes.get(biome, ["Mysterious"]))
            name = f"{prefix} {base_name}"

            poi = PointOfInterest(
                id=f"poi_{i}",
                name=name,
                type=poi_type.value,
                position=(px, py),
                description=base_desc,
                lore=lore,
                danger_level=random.randint(1, 8),
                resources=random.choice([
                    {"gold": random.randint(5, 50), "gems": random.randint(1, 10)},
                    {"herbs": random.randint(10, 30)},
                    {"antiques": random.randint(1, 5)},
                    {},
                ]),
            )
            world.poi_list.append(poi)

    # ── Roads ───────────────────────────────────────────────────────────

    def _generate_roads(self, world: World) -> None:
        """Generate roads connecting towns using a nearest-neighbor approach."""
        town_ids = list(world.towns.keys())
        if len(town_ids) < 2:
            return

        visited = {town_ids[0]}
        unvisited = set(town_ids[1:])
        road_id_counter = 0

        while unvisited:
            current = min(
                visited,
                key=lambda c: min(
                    math.sqrt(
                        (world.towns[c].position[0] - world.towns[t].position[0]) ** 2 +
                        (world.towns[c].position[1] - world.towns[t].position[1]) ** 2
                    )
                    for t in unvisited
                )
            )
            nearest = min(
                unvisited,
                key=lambda t: math.sqrt(
                    (world.towns[current].position[0] - world.towns[t].position[0]) ** 2 +
                    (world.towns[current].position[1] - world.towns[t].position[1]) ** 2
                )
            )

            path = self._trace_road(world, world.towns[current].position, world.towns[nearest].position)
            road = Road(
                id=f"road_{road_id_counter}",
                name=f"{world.towns[current].name} - {world.towns[nearest].name} Road",
                start_town=current,
                end_town=nearest,
                path=path,
                length=len(path),
                condition=random.choice(["good", "good", "fair"]),
            )
            world.roads.append(road)

            # Mark road tiles on grid
            for rx, ry in path:
                if world.get_tile_type(rx, ry) != 2 and world.get_tile_type(rx, ry) != 3:
                    world.grid[ry][rx] = TerrainTile.ROAD.value

            visited.add(nearest)
            unvisited.remove(nearest)
            road_id_counter += 1

    @staticmethod
    def _trace_road(world: World, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Trace a rough road between two points, favoring walkable tiles."""
        path = []
        cx, cy = start
        ex, ey = end

        while (cx, cy) != (ex, ey):
            path.append((cx, cy))

            if abs(cx - ex) > abs(cy - ey):
                cx += 1 if cx < ex else -1
            elif abs(cy - ey) > abs(cx - ex):
                cy += 1 if cy < ey else -1
            else:
                dx = 1 if cx < ex else -1
                dy = 1 if cy < ey else -1
                if random.random() < 0.5:
                    cx += dx
                else:
                    cy += dy

            # Avoid impassable terrain
            if 0 <= cx < world.width and 0 <= cy < world.height:
                if world.get_tile_type(cx, cy) == 2:  # water
                    # Try to go around
                    if world.get_tile_type(cx, cy - 1) != 2:
                        cy -= 1
                    elif world.get_tile_type(cx, cy + 1) != 2:
                        cy += 1
                    elif world.get_tile_type(cx - 1, cy) != 2:
                        cx -= 1
                    elif world.get_tile_type(cx + 1, cy) != 2:
                        cx += 1

        path.append(end)
        return path

    # ── Villagers ───────────────────────────────────────────────────────

    def generate_villagers_for_town(self, town: Town, count: int = 5) -> List[Dict[str, Any]]:
        """Generate villagers for a specific town."""
        villagers = []
        professions_by_economy = {
            "agricultural": ["Farmer", "Herder", "Miller", "Vintner", "Shepherd"],
            "mercantile": ["Merchant", "Apprentice", "Cartographer", "Broker", "Innkeeper"],
            "crafts": ["Blacksmith", "Carpenter", "Tanner", "Potter", "Weaver"],
            "fishing": ["Fisherman", "Net-maker", "Boat-builder", "Salt-packer"],
            "mining": ["Miner", "Quarryman", "Smelter", "Gem-cutter"],
        }
        professions = professions_by_economy.get(town.economy, ["Villager"])
        first_names = [
            "Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Helen",
            "Isaac", "Julia", "Karl", "Luna", "Marcus", "Nora", "Oscar", "Petra",
            "Quinn", "Rosa", "Soren", "Talia", "Ulric", "Vera", "Wren", "Xander",
            "Yara", "Zane", "Elara", "Cedric", "Mira", "Torin",
        ]
        last_names = [
            "Smith", "Johnson", "Brown", "Williams", "Jones", "Garcia", "Miller", "Davis",
            "Ashford", "Blackwood", "Crimson", "Dawnbreaker", "Emberly", "Frost",
            "Grayson", "Holloway", "Ironside", "Jasper", "Knightley", "Locke",
            "March", "Nightingale", "Oakenshield", "Pemberley", "Quested", "Ravencrest",
        ]

        for i in range(count):
            villager = {
                "id": f"{town.id}_villager_{i}",
                "name": f"{random.choice(first_names)} {random.choice(last_names)}",
                "town": town.id,
                "profession": random.choice(professions),
                "position": (
                    town.position[0] + random.randint(0, max(town.width - 1, 1)),
                    town.position[1] + random.randint(0, max(town.height - 1, 1)),
                ),
                "needs": {
                    "hunger": random.randint(30, 70),
                    "energy": random.randint(50, 90),
                    "social": random.randint(40, 80),
                },
                "inventory": {"gold": random.randint(5, 20)},
                "relationships": {},
                "description": f"A {'friendly' if random.random() > 0.5 else 'hardworking'} villager of {town.name}",
            }
            villagers.append(villager)

        return villagers

    # ── World events ────────────────────────────────────────────────────

    def advance_season(self, world: World) -> WorldEvent:
        """Advance the season and return the season change event."""
        season_order = [Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER]
        current_idx = season_order.index(world.season)
        next_season = season_order[(current_idx + 1) % 4]
        old_season = world.season

        if next_season == Season.SPRING:
            world.year += 1

        event = WorldEvent(
            id=f"event_season_{world.world_age}",
            type=WorldEventType.SEASON_CHANGE.value,
            title=f"The season changes from {old_season.value} to {next_season.value}",
            description=self._season_description(old_season, next_season),
            tick_start=world.world_age,
            duration_ticks=720,  # ~12 minutes per season (720 ticks at 1/sec)
        )
        world.season = next_season
        world.events.append(event)
        world.active_events.append(event)
        return event

    def _season_description(self, from_s: Season, to_s: Season) -> str:
        descriptions = {
            ("spring", "summer"): "The days grow longer and warmer. Crops begin to flourish across the land.",
            ("summer", "autumn"): "The air cools and leaves begin to turn. Harvest season arrives with bounty.",
            ("autumn", "winter"): "The first frost creeps across the fields. Villagers prepare for the cold months ahead.",
            ("winter", "spring"): "The snow melts and rivers swell. Life stirs once more beneath the thawing earth.",
        }
        return descriptions.get((from_s.value, to_s.value), "The seasons turn as they always have.")

    def trigger_random_event(self, world: World) -> Optional[WorldEvent]:
        """Trigger a random world event."""
        if not world.towns:
            return None

        town_ids = list(world.towns.keys())
        event_roll = random.random()

        if event_roll < 0.3:
            # Weather event
            weather = random.choice(list(WeatherType))
            event = WorldEvent(
                id=f"event_weather_{world.world_age}",
                type=WorldEventType.WEATHER_CHANGE.value,
                title=f"Weather shifts to {weather.value}",
                description=self._weather_description(weather),
                affected_towns=[random.choice(town_ids)],
                tick_start=world.world_age,
                duration_ticks=random.randint(60, 300),
                metadata={"weather": weather.value},
            )
            world.weather = weather
            world.events.append(event)
            world.active_events.append(event)
            return event

        elif event_roll < 0.5:
            # Bandit raid
            target = random.choice(town_ids)
            event = WorldEvent(
                id=f"event_bandit_{world.world_age}",
                type=WorldEventType.BANDIT_RAID.value,
                title="Bandits raid the settlement!",
                description=f"Bandits have been spotted raiding {world.towns[target].name}. The townsfolk must defend themselves.",
                affected_towns=[target],
                tick_start=world.world_age,
                duration_ticks=120,
            )
            world.events.append(event)
            world.active_events.append(event)
            return event

        elif event_roll < 0.65:
            # Trade arrival
            target = random.choice(town_ids)
            event = WorldEvent(
                id=f"event_trade_{world.world_age}",
                type=WorldEventType.TRADE_ARRIVAL.value,
                title="A merchant caravan arrives!",
                description=f"A merchant caravan from a distant land has arrived in {world.towns[target].name}, bringing exotic wares.",
                affected_towns=[target],
                tick_start=world.world_age,
                duration_ticks=240,
            )
            world.events.append(event)
            world.active_events.append(event)
            return event

        elif event_roll < 0.75:
            # Monster sighting
            pos = (random.randint(0, world.width - 1), random.randint(0, world.height - 1))
            event = WorldEvent(
                id=f"event_monster_{world.world_age}",
                type=WorldEventType.MONSTER_SIGHTING.value,
                title="A creature sighted in the wild!",
                description=f"Wanderers report a dangerous creature sighted near ({pos[0]}, {pos[1]}). Travelers are advised to be wary.",
                affected_positions=[pos],
                tick_start=world.world_age,
                duration_ticks=360,
            )
            world.events.append(event)
            world.active_events.append(event)
            return event

        elif event_roll < 0.85:
            # Migration
            from_town = random.choice(town_ids)
            event = WorldEvent(
                id=f"event_migration_{world.world_age}",
                type=WorldEventType.MIGRATION.value,
                title="A wave of migration begins",
                description=f"Rumors of better lands have sparked migration. Families from {world.towns[from_town].name} pack their belongings.",
                affected_towns=[from_town],
                tick_start=world.world_age,
                duration_ticks=600,
            )
            world.events.append(event)
            world.active_events.append(event)
            return event

        elif event_roll < 0.92:
            # Festival
            target = random.choice(town_ids)
            event = WorldEvent(
                id=f"event_festival_{world.world_age}",
                type=WorldEventType.FESTIVAL.value,
                title="A grand festival!",
                description=f"The people of {world.towns[target].name} are celebrating a festival! Music, food, and merriment fill the air.",
                affected_towns=[target],
                tick_start=world.world_age,
                duration_ticks=180,
            )
            world.events.append(event)
            world.active_events.append(event)
            return event

        elif event_roll < 0.97:
            # Disaster
            disaster_type = random.choice(["flood", "fire", "plague"])
            target = random.choice(town_ids)
            event = WorldEvent(
                id=f"event_disaster_{world.world_age}",
                type=WorldEventType.DISASTER.value,
                title=f"A {disaster_type} strikes!",
                description=f"A terrible {disaster_type} has befallen {world.towns[target].name}. The people suffer greatly.",
                affected_towns=[target],
                tick_start=world.world_age,
                duration_ticks=480,
            )
            world.events.append(event)
            world.active_events.append(event)
            return event

        return None

    def _weather_description(self, weather: WeatherType) -> str:
        descriptions = {
            WeatherType.CLEAR: "The sky clears and sunshine bathes the land.",
            WeatherType.RAIN: "Dark clouds gather and rain falls steadily.",
            WeatherType.SNOW: "Snow begins to fall, blanketing the countryside in white.",
            WeatherType.STORM: "Thunder crashes and lightning splits the sky. A fierce storm rages.",
            WeatherType.FOG: "A thick fog rolls in, reducing visibility to barely a few steps.",
            WeatherType.DUST_STORM: "A wall of dust rises on the horizon, swallowing the landscape.",
        }
        return descriptions.get(weather, "The weather changes.")
