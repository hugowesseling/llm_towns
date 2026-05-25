"""
LLM Towns Visualization Client
A pygame-based map viewer for the LLM Towns simulation.
Displays the world grid, villagers, and simulation state with scrolling.
"""

import pygame
import sys
from typing import Dict, List, Tuple, Optional, Any
import threading
import time

from api_client import APIClient
from tileset import TilesetCache, create_villager_sprite, create_selected_overlay, TILE_SIZE

# UI Colors
COLOR_UI_BG = (40, 40, 40)
COLOR_UI_TEXT = (200, 200, 200)
COLOR_UI_BORDER = (100, 100, 100)
COLOR_SELECTED = (255, 255, 0)

# Window and map settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
MAP_VIEWPORT_WIDTH = WINDOW_WIDTH - 250  # Leave space for sidebar
MAP_VIEWPORT_HEIGHT = WINDOW_HEIGHT


class WorldViewport:
    """Manages the scrollable map viewport."""
    
    def __init__(self, width: int, height: int, world_width: int, world_height: int):
        self.width = width
        self.height = height
        self.world_width = world_width
        self.world_height = world_height
        self.scroll_x = 0
        self.scroll_y = 0
        self.selected_tile: Optional[Tuple[int, int]] = None
    
    def scroll(self, dx: int, dy: int):
        """Scroll the viewport."""
        max_scroll_x = max(0, (self.world_width * TILE_SIZE) - self.width)
        max_scroll_y = max(0, (self.world_height * TILE_SIZE) - self.height)
        
        self.scroll_x = max(0, min(self.scroll_x + dx, max_scroll_x))
        self.scroll_y = max(0, min(self.scroll_y + dy, max_scroll_y))
    
    def screen_to_world(self, screen_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Convert screen coordinates to world tile coordinates."""
        screen_x, screen_y = screen_pos
        world_x = (self.scroll_x + screen_x) // TILE_SIZE
        world_y = (self.scroll_y + screen_y) // TILE_SIZE
        return (world_x, world_y)
    
    def world_to_screen(self, world_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Convert world tile coordinates to screen coordinates."""
        world_x, world_y = world_pos
        screen_x = (world_x * TILE_SIZE) - self.scroll_x
        screen_y = (world_y * TILE_SIZE) - self.scroll_y
        return (screen_x, screen_y)
    
    def is_visible(self, world_x: int, world_y: int) -> bool:
        """Check if a world tile is visible in the viewport."""
        screen_x, screen_y = self.world_to_screen((world_x, world_y))
        return 0 <= screen_x < self.width and 0 <= screen_y < self.height


class SimulationClient:
    """Main client for the LLM Towns visualization."""
    
    def __init__(self, api_url: str = "http://localhost:5000"):
        pygame.init()
        
        self.api = APIClient(api_url)
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("LLM Towns - World Viewer")
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 20)
        self.font_large = pygame.font.Font(None, 24)
        
        # World data
        self.world_width = 50
        self.world_height = 50
        self.grid: List[List[int]] = []
        self.villagers: Dict[str, Dict[str, Any]] = {}
        self.towns: Dict[str, Dict[str, Any]] = {}
        
        # Viewport
        self.viewport = WorldViewport(MAP_VIEWPORT_WIDTH, MAP_VIEWPORT_HEIGHT, 50, 50)
        
        # Graphics
        self.tileset = TilesetCache()
        self.villager_sprite = create_villager_sprite()
        self.selected_overlay = create_selected_overlay()
        
        # Simulation state
        self.running = True
        self.paused = False
        self.selected_character: Optional[str] = None
        self.selected_town: Optional[str] = None
        self.update_thread_running = False
        self.last_update = 0
        self.update_interval = 1.0  # seconds
        
        # Load initial data
        self._connect_and_load()
    
    def _connect_and_load(self):
        """Connect to server and load initial world data."""
        print("Connecting to server...")
        if not self.api.health_check():
            print("ERROR: Cannot connect to server at", self.api.base_url)
            print("Make sure the Flask app is running!")
            raise RuntimeError("Server not reachable")
        
        print("Loading world data...")
        dims = self.api.get_world_dimensions()
        if dims:
            self.world_width = dims.get("width", 50)
            self.world_height = dims.get("height", 50)
            self.viewport = WorldViewport(MAP_VIEWPORT_WIDTH, MAP_VIEWPORT_HEIGHT, 
                                         self.world_width, self.world_height)
        
        self._refresh_world_data()
        print("Client ready!")
    
    def _refresh_world_data(self):
        """Fetch current world state from server."""
        # Get grid
        grid = self.api.get_world_grid()
        if grid:
            self.grid = grid
        
        # Get characters
        chars = self.api.get_characters()
        if chars:
            self.villagers = {c.get("id"): c for c in chars}
        
        # Get towns
        towns = self.api.get_towns()
        if towns:
            self.towns = {t.get("id"): t for t in towns}
    
    def _update_loop(self):
        """Background thread for updating world state."""
        while self.update_thread_running:
            try:
                self._refresh_world_data()
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"Update error: {e}")
                time.sleep(1)
    
    def start_background_updates(self):
        """Start background thread for fetching updated data."""
        self.update_thread_running = True
        thread = threading.Thread(target=self._update_loop, daemon=True)
        thread.start()
    
    def stop_background_updates(self):
        """Stop the background update thread."""
        self.update_thread_running = False
    
    def handle_events(self):
        """Handle keyboard and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                
                # Scroll with arrow keys
                elif event.key == pygame.K_UP:
                    self.viewport.scroll(0, -TILE_SIZE * 3)
                elif event.key == pygame.K_DOWN:
                    self.viewport.scroll(0, TILE_SIZE * 3)
                elif event.key == pygame.K_LEFT:
                    self.viewport.scroll(-TILE_SIZE * 3, 0)
                elif event.key == pygame.K_RIGHT:
                    self.viewport.scroll(TILE_SIZE * 3, 0)
                
                # Home key to center
                elif event.key == pygame.K_HOME:
                    self.viewport.scroll_x = 0
                    self.viewport.scroll_y = 0
                
                # Deselect with C
                elif event.key == pygame.K_c:
                    self.selected_character = None
                    self.selected_town = None
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = event.pos
                    # Only if clicking on map area
                    if mouse_pos[0] < MAP_VIEWPORT_WIDTH:
                        world_pos = self.viewport.screen_to_world(mouse_pos)
                        self.viewport.selected_tile = world_pos
                        self._select_at_position(world_pos)
            
            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[2]:  # Right-click drag to scroll
                    rel = pygame.mouse.get_rel()
                    self.viewport.scroll(-rel[0], -rel[1])
    
    def _select_at_position(self, world_pos: Tuple[int, int]):
        """Select character or town at given position."""
        world_x, world_y = world_pos
        
        # Check for villager at this position
        for char_id, char_data in self.villagers.items():
            if char_data.get("position") == [world_x, world_y]:
                self.selected_character = char_id
                self.selected_town = None
                return
        
        # Check for town center at this position
        for town_id, town_data in self.towns.items():
            town_pos = town_data.get("position", [])
            if town_pos == [world_x, world_y]:
                self.selected_town = town_id
                self.selected_character = None
                return
        
        # Nothing selected
        self.selected_character = None
        self.selected_town = None
    
    def draw(self):
        """Draw the complete scene."""
        self.screen.fill(COLOR_UI_BG)
        
        # Draw map area
        self._draw_map()
        
        # Draw sidebar
        self._draw_sidebar()
    
    def _draw_map(self):
        """Draw the scrollable map viewport."""
        # Create surface for map with scissor test would be nice but we'll just clip manually
        map_surface = pygame.Surface((MAP_VIEWPORT_WIDTH, MAP_VIEWPORT_HEIGHT))
        map_surface.fill((0, 0, 0))
        
        # Draw tiles
        start_tile_x = self.viewport.scroll_x // TILE_SIZE
        start_tile_y = self.viewport.scroll_y // TILE_SIZE
        end_tile_x = min(self.world_width, start_tile_x + (MAP_VIEWPORT_WIDTH // TILE_SIZE) + 1)
        end_tile_y = min(self.world_height, start_tile_y + (MAP_VIEWPORT_HEIGHT // TILE_SIZE) + 1)
        
        for y in range(max(0, start_tile_y), end_tile_y):
            for x in range(max(0, start_tile_x), end_tile_x):
                if y < len(self.grid) and x < len(self.grid[y]):
                    tile_id = self.grid[y][x]
                    tile_surface = self.tileset.get_tile(tile_id)
                    screen_x, screen_y = self.viewport.world_to_screen((x, y))
                    map_surface.blit(tile_surface, (screen_x, screen_y))
        
        # Draw villagers
        for char_id, char_data in self.villagers.items():
            pos = char_data.get("position")
            if pos:
                x, y = pos
                if self.viewport.is_visible(x, y):
                    screen_x, screen_y = self.viewport.world_to_screen((x, y))
                    map_surface.blit(self.villager_sprite, (screen_x, screen_y))
                    
                    # Draw name label if selected
                    if char_id == self.selected_character:
                        map_surface.blit(self.selected_overlay, (screen_x, screen_y))
        
        # Draw town centers
        for town_id, town_data in self.towns.items():
            pos = town_data.get("position")
            if pos:
                x, y = pos
                if self.viewport.is_visible(x, y):
                    screen_x, screen_y = self.viewport.world_to_screen((x, y))
                    # Draw a star for town center
                    center = (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2)
                    pygame.draw.circle(map_surface, (255, 215, 0), center, 5)
                    
                    if town_id == self.selected_town:
                        map_surface.blit(self.selected_overlay, (screen_x, screen_y))
        
        self.screen.blit(map_surface, (0, 0))
        
        # Draw map border
        pygame.draw.line(self.screen, COLOR_UI_BORDER, (MAP_VIEWPORT_WIDTH, 0), 
                        (MAP_VIEWPORT_WIDTH, WINDOW_HEIGHT), 2)
    
    def _draw_sidebar(self):
        """Draw the right sidebar with info and controls."""
        sidebar_x = MAP_VIEWPORT_WIDTH
        sidebar_width = WINDOW_WIDTH - MAP_VIEWPORT_WIDTH
        
        # Draw selected character/town info
        info_y = 10
        
        if self.selected_character and self.selected_character in self.villagers:
            char = self.villagers[self.selected_character]
            self._draw_text(f"Character: {self.selected_character}", sidebar_x + 10, info_y, 
                          self.font_large, (255, 200, 0))
            info_y += 30
            
            self._draw_text(f"Pos: {char.get('position')}", sidebar_x + 10, info_y)
            info_y += 25
            
            needs = char.get("needs", {})
            self._draw_text(f"Hunger: {needs.get('hunger', 0):.1f}", sidebar_x + 10, info_y)
            info_y += 20
            self._draw_text(f"Energy: {needs.get('energy', 0):.1f}", sidebar_x + 10, info_y)
            info_y += 20
            self._draw_text(f"Social: {needs.get('social', 0):.1f}", sidebar_x + 10, info_y)
            info_y += 25
            
            goal = char.get("current_goal")
            if goal:
                self._draw_text(f"Goal: {goal}", sidebar_x + 10, info_y, wrap_width=200)
                info_y += 50
        
        elif self.selected_town and self.selected_town in self.towns:
            town = self.towns[self.selected_town]
            self._draw_text(f"Town: {town.get('name', 'Unknown')}", sidebar_x + 10, info_y,
                          self.font_large, (0, 200, 255))
            info_y += 30
            
            self._draw_text(f"ID: {self.selected_town}", sidebar_x + 10, info_y)
            info_y += 25
            
            self._draw_text(f"Population: {town.get('population', 0)}", sidebar_x + 10, info_y)
            info_y += 20
            self._draw_text(f"Economy: {town.get('economy', '?')}", sidebar_x + 10, info_y)
            info_y += 20
            self._draw_text(f"Culture: {town.get('culture', '?')}", sidebar_x + 10, info_y)
            info_y += 25
            
            desc = town.get("description", "")
            if desc:
                self._draw_text(f"Desc: {desc}", sidebar_x + 10, info_y, wrap_width=200)
        
        # Draw controls at bottom
        controls_y = WINDOW_HEIGHT - 150
        self._draw_text("--- CONTROLS ---", sidebar_x + 10, controls_y, self.font_large)
        controls_y += 30
        
        controls = [
            "Arrows: Scroll",
            "Click: Select",
            "Right-drag: Pan",
            "Home: Center",
            "Space: Pause",
            "C: Deselect",
            "ESC: Quit"
        ]
        
        for control in controls:
            self._draw_text(control, sidebar_x + 10, controls_y, self.font_small)
            controls_y += 20
    
    def _draw_text(self, text: str, x: int, y: int, font: Optional[pygame.font.Font] = None,
                   color: Tuple[int, int, int] = COLOR_UI_TEXT, wrap_width: int = 0):
        """Draw text on screen with optional wrapping."""
        if font is None:
            font = self.font_small
        
        if wrap_width > 0:
            # Simple word wrap
            words = text.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if font.size(test_line)[0] > wrap_width:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                lines.append(current_line)
            
            for i, line in enumerate(lines):
                surface = font.render(line, True, color)
                self.screen.blit(surface, (x, y + i * 20))
        else:
            surface = font.render(text, True, color)
            self.screen.blit(surface, (x, y))
    
    def run(self):
        """Main loop."""
        self.start_background_updates()
        
        try:
            while self.running:
                self.handle_events()
                self.draw()
                pygame.display.flip()
                self.clock.tick(30)  # 30 FPS
        finally:
            self.stop_background_updates()
            pygame.quit()


def main():
    try:
        client = SimulationClient()
        client.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
