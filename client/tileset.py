"""
Tileset and graphics utilities for the map visualization.
Creates simple procedural tiles or uses pixel art representations.
"""

import pygame
from typing import Dict, Tuple
import colorsys

TILE_SIZE = 32  # pixels per tile

# Tile type IDs from world_generator.py
TILE_IDS = {
    0: "GRASS",
    1: "FOREST",
    2: "WATER",
    3: "MOUNTAIN",
    4: "SAND",
    5: "SNOW",
    6: "SWAMP",
    7: "ROAD",
    8: "BUILDING",
    9: "HOUSE",
    10: "TOWN_SQUARE",
}

# Color palette for tiles
TILE_COLORS = {
    0: (34, 139, 34),        # GRASS - forest green
    1: (0, 100, 0),          # FOREST - dark green
    2: (30, 144, 255),       # WATER - dodger blue
    3: (139, 69, 19),        # MOUNTAIN - saddle brown
    4: (238, 214, 175),      # SAND - bisque
    5: (255, 250, 250),      # SNOW - snow
    6: (85, 107, 47),        # SWAMP - dark khaki
    7: (200, 200, 200),      # ROAD - light gray
    8: (128, 0, 0),          # BUILDING - maroon
    9: (210, 105, 30),       # HOUSE - chocolate
    10: (255, 215, 0),       # TOWN_SQUARE - gold
}


def create_tile_surface(tile_id: int, size: int = TILE_SIZE) -> pygame.Surface:
    """Create a procedural tile surface for the given tile type."""
    surface = pygame.Surface((size, size))
    
    color = TILE_COLORS.get(tile_id, (128, 128, 128))
    
    if tile_id == 0:  # GRASS - add some variation
        surface.fill(color)
        # Add subtle grass texture
        for x in range(0, size, 4):
            for y in range(0, size, 4):
                if (x + y) % 8 == 0:
                    pygame.draw.circle(surface, (20, 120, 20), (x + 2, y + 2), 1)
    
    elif tile_id == 1:  # FOREST - add trees
        surface.fill((0, 80, 0))
        # Draw tree tops
        pygame.draw.polygon(surface, color, [
            (size // 2, 2),
            (size - 4, size - 8),
            (4, size - 8)
        ])
    
    elif tile_id == 2:  # WATER - add wave pattern
        surface.fill(color)
        lighter = (50, 160, 255)
        for x in range(0, size, 6):
            pygame.draw.line(surface, lighter, (x, 0), (x, size // 2), 1)
    
    elif tile_id == 3:  # MOUNTAIN - add peak
        surface.fill(color)
        pygame.draw.polygon(surface, (160, 82, 45), [
            (size // 2, 2),
            (size - 2, size - 2),
            (2, size - 2)
        ])
    
    elif tile_id == 4:  # SAND - add ripples
        surface.fill(color)
        for x in range(0, size, 5):
            pygame.draw.arc(surface, (200, 180, 140), (x, 0, size, size), 0, 3.14, 1)
    
    elif tile_id == 5:  # SNOW
        surface.fill(color)
        # Add snowflakes
        pygame.draw.circle(surface, (200, 200, 220), (size // 4, size // 4), 2)
        pygame.draw.circle(surface, (200, 200, 220), (3 * size // 4, 3 * size // 4), 2)
    
    elif tile_id == 6:  # SWAMP - murky water with vegetation
        surface.fill(color)
        pygame.draw.circle(surface, (60, 80, 20), (size // 3, size // 3), 4)
        pygame.draw.circle(surface, (60, 80, 20), (2 * size // 3, 2 * size // 3), 3)
    
    elif tile_id == 7:  # ROAD - add center line
        surface.fill(color)
        pygame.draw.line(surface, (100, 100, 100), (0, size // 2), (size, size // 2), 2)
    
    elif tile_id == 8:  # BUILDING - brick pattern
        surface.fill(color)
        for row in range(0, size, 8):
            for col in range(0, size, 8):
                pygame.draw.rect(surface, (100, 0, 0), (col, row, 6, 6), 1)
    
    elif tile_id == 9:  # HOUSE - simple roof
        surface.fill(color)
        pygame.draw.polygon(surface, (139, 69, 19), [
            (size // 2, 2),
            (size - 2, size // 2),
            (2, size // 2)
        ])
    
    elif tile_id == 10:  # TOWN_SQUARE - decorative pattern
        surface.fill(color)
        for x in range(0, size, 8):
            pygame.draw.line(surface, (200, 170, 0), (x, 0), (x, size), 1)
            pygame.draw.line(surface, (200, 170, 0), (0, x), (size, x), 1)
    
    else:
        surface.fill((128, 128, 128))
    
    return surface


class TilesetCache:
    """Caches rendered tile surfaces for performance."""
    
    def __init__(self, tile_size: int = TILE_SIZE):
        self.tile_size = tile_size
        self.cache: Dict[int, pygame.Surface] = {}
    
    def get_tile(self, tile_id: int) -> pygame.Surface:
        """Get a tile surface, creating it if necessary."""
        if tile_id not in self.cache:
            self.cache[tile_id] = create_tile_surface(tile_id, self.tile_size)
        return self.cache[tile_id]


def create_villager_sprite(size: int = TILE_SIZE) -> pygame.Surface:
    """Create a simple circular villager sprite."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surface, (255, 100, 100, 255), (size // 2, size // 2), size // 3)
    # Eyes
    pygame.draw.circle(surface, (0, 0, 0, 255), (size // 3, size // 2 - 2), 2)
    pygame.draw.circle(surface, (0, 0, 0, 255), (2 * size // 3, size // 2 - 2), 2)
    return surface


def create_selected_overlay(size: int = TILE_SIZE) -> pygame.Surface:
    """Create an overlay to indicate selected tile."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(surface, (255, 255, 0, 100), (0, 0, size, size), 2)
    return surface
