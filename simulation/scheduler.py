from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import heapq

from .actions import ActionState, Goal, Plan
from .decision import DecisionLayer, should_run_layer
from .planner import Planner
from .villager import Villager
from llm.brain import LLMBrain
from llm.prompts import build_goal_prompt, build_town_context, build_plan_prompt
from world.world_generator import World, TerrainTile


@dataclass
class SimulationScheduler:
    planner: Planner = field(default_factory=Planner)
    villagers: Dict[str, Villager] = field(default_factory=dict)
    goals: Dict[str, Goal] = field(default_factory=dict)
    plans: Dict[str, Plan] = field(default_factory=dict)
    current_tick: int = 0
    event_log: List[Dict[str, object]] = field(default_factory=list)
    llm_brain: Optional[LLMBrain] = None
    markets: Dict[str, 'Market'] = field(default_factory=dict)
    world: Optional[World] = None

    def add_market(self, market: 'Market') -> None:
        self.markets[market.id] = market

    def add_villager(self, villager: Villager) -> None:
        self.villagers[villager.id] = villager

    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """A* pathfinding with road preference."""
        if not self.world:
            return []  # No world, no path

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        def tile_cost(x, y):
            if self.world and self.world.get_tile_type(x, y) == 7:  # ROAD
                return 0.4
            return 1.0

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, goal)}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if self.world.is_walkable(neighbor[0], neighbor[1]):
                    step_cost = tile_cost(neighbor[0], neighbor[1])
                    tentative_g = g_score[current] + step_cost
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        return []  # No path

    def is_position_free(self, pos: Tuple[int, int], exclude_villager_id: Optional[str] = None) -> bool:
        for vid, v in self.villagers.items():
            if vid != exclude_villager_id and (v.position.x, v.position.y) == pos:
                return False
        return True

    def _get_market_for_villager(self, villager: Villager) -> Optional['Market']:
        """Find the market in the villager's home town."""
        for mid, m in self.markets.items():
            if mid == f"market_{villager.town}":
                return m
        # Fallback: any market
        for m in self.markets.values():
            return m
        return None

    def execute_action(self, action: Action) -> None:
        villager = self.villagers.get(action.actor_id)
        if not villager:
            return

        if action.type == "walk":
            destination = action.metadata.get("destination")
            if isinstance(destination, str):
                if destination == "market":
                    market = self._get_market_for_villager(villager)
                    if market:
                        dest_pos = market.position
                    else:
                        dest_pos = (villager.position.x + 1, villager.position.y)
                elif destination == "home":
                    # Walk toward town center
                    if self.world and villager.town in self.world.towns:
                        t = self.world.towns[villager.town]
                        dest_pos = (t.position[0] + t.width // 2, t.position[1] + t.height // 2)
                    else:
                        dest_pos = (villager.position.x + 1, villager.position.y)
                elif destination == "square":
                    if self.world and villager.town in self.world.towns:
                        t = self.world.towns[villager.town]
                        dest_pos = (t.position[0] + t.width // 2, t.position[1] + t.height // 2)
                    else:
                        dest_pos = (villager.position.x + 1, villager.position.y)
                else:
                    dest_pos = (villager.position.x + 1, villager.position.y)
                path = self.find_path((villager.position.x, villager.position.y), dest_pos)
                if path and len(path) > 0:
                    next_pos = path[0]
                    if self.move_villager(villager, next_pos):
                        action.metadata["path"] = path[1:]
                    else:
                        action.state = ActionState.BLOCKED

        elif action.type == "travel":
            target_town_id = action.metadata.get("target") or action.metadata.get("destination")
            if target_town_id and self.world and target_town_id in self.world.towns:
                target_town = self.world.towns[target_town_id]
                # Pick the nearest entry point
                entry = target_town.entry_points.get("south")
                if entry is None:
                    entry = (target_town.position[0] + target_town.width // 2,
                             target_town.position[1] + target_town.height // 2)
                dest_pos = entry
                path = self.find_path((villager.position.x, villager.position.y), dest_pos)
                if path and len(path) > 0:
                    next_pos = path[0]
                    if self.move_villager(villager, next_pos):
                        action.metadata["path"] = path[1:]
                    else:
                        action.state = ActionState.BLOCKED
                else:
                    action.state = ActionState.FAILED
            else:
                action.state = ActionState.FAILED

        elif action.type == "trade":
            market = self._get_market_for_villager(villager)
            if market and villager.position.x == market.position[0] and villager.position.y == market.position[1]:
                if market.buy_item(villager, "food", 1):
                    self.event_log.append({
                        "tick": self.current_tick,
                        "event": "trade_completed",
                        "villager_id": villager.id,
                        "item": "food",
                        "quantity": 1,
                    })
                else:
                    action.state = ActionState.FAILED

    def move_villager(self, villager: Villager, target: Tuple[int, int]) -> bool:
        if not self.is_position_free(target, exclude_villager_id=villager.id):
            return False
        if self.world and not self.world.is_walkable(target[0], target[1]):
            return False
        villager.position.x, villager.position.y = target
        return True

    def get_villager(self, villager_id: str) -> Optional[Villager]:
        return self.villagers.get(villager_id)

    def add_goal(self, goal: Goal) -> None:
        self.goals[goal.id] = goal
        villager = self.get_villager(goal.actor_id)
        if villager:
            villager.assign_goal(goal)
            self.event_log.append({
                "tick": self.current_tick,
                "event": "goal_added",
                "villager_id": villager.id,
                "goal_id": goal.id,
                "description": goal.description,
            })

    def _ensure_plan(self, villager: Villager) -> None:
        if not villager.current_goal_id:
            return
        if villager.current_plan_id and self.plans.get(villager.current_plan_id):
            plan = self.plans[villager.current_plan_id]
            if not plan.is_complete():
                return

        goal = self.goals.get(villager.current_goal_id)
        if not goal:
            return

        plan = self.planner.create_plan(villager, goal, self.current_tick, self)
        self.plans[plan.id] = plan
        villager.current_plan_id = plan.id
        self.event_log.append({
            "tick": self.current_tick,
            "event": "plan_created",
            "villager_id": villager.id,
            "plan_id": plan.id,
            "goal_id": goal.id,
        })

    def advance_tick(self, count: int = 1) -> None:
        for _ in range(count):
            self.current_tick += 1
            self._tick_villagers()

    def _tick_villagers(self) -> None:
        for villager in self.villagers.values():
            self._ensure_plan(villager)
            if villager.current_plan_id is None:
                continue
            plan = self.plans.get(villager.current_plan_id)
            if plan is None:
                continue
            plan.advance(self.current_tick)
            if plan.is_complete():
                self.event_log.append({
                    "tick": self.current_tick,
                    "event": "plan_completed",
                    "villager_id": villager.id,
                    "plan_id": plan.id,
                })
                villager.current_plan_id = None
                villager.current_goal_id = None
            else:
                current_action = plan.get_current_action()
                if current_action and current_action.state == ActionState.RUNNING:
                    self.execute_action(current_action)

            # Check if villager needs a new goal
            if villager.is_idle() and should_run_layer(DecisionLayer.REFLECTIVE, self.current_tick, villager.cognition.last_reflective_tick):
                self._assign_new_goal(villager)
                villager.cognition.last_reflective_tick = self.current_tick

    def _assign_new_goal(self, villager: Villager) -> None:
        if self.llm_brain is None:
            goal = Goal(actor_id=villager.id, description="Idle and reflect", priority=1, created_tick=self.current_tick)
            self.add_goal(goal)
            return

        town_context = ""
        if self.world:
            town_context = build_town_context(villager.town, self.world.towns)

        context = {
            "tick": self.current_tick,
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
        }

        messages = build_goal_prompt(villager.summary(), context, town_context=town_context)
        try:
            goal_data = self.llm_brain.create_chat_json(
                messages=messages,
                temperature=0.5,
                max_tokens=200,
            )
            if isinstance(goal_data, dict) and "goal" in goal_data:
                goal = Goal(
                    actor_id=villager.id,
                    description=goal_data["goal"],
                    priority=goal_data.get("priority", 1),
                    created_tick=self.current_tick,
                )
                self.add_goal(goal)
                self.event_log.append({
                    "tick": self.current_tick,
                    "event": "goal_auto_assigned",
                    "villager_id": villager.id,
                    "goal_id": goal.id,
                    "description": goal.description,
                })
        except Exception:
            # If LLM fails, assign default goal
            goal = Goal(actor_id=villager.id, description="Idle and reflect", priority=1, created_tick=self.current_tick)
            self.add_goal(goal)

    def snapshot(self) -> Dict[str, object]:
        return {
            "tick": self.current_tick,
            "villagers": {vid: v.summary() for vid, v in self.villagers.items()},
            "plans": {pid: {
                "id": plan.id,
                "actor_id": plan.actor_id,
                "goal_id": plan.goal_id,
                "actions": [
                    {
                        "action_id": action.id,
                        "type": action.type,
                        "state": action.state.value,
                        "duration_ticks": action.duration_ticks,
                        "progress_ticks": action.progress_ticks,
                        "metadata": action.metadata,
                    }
                    for action in plan.actions
                ]
            } for pid, plan in self.plans.items()},
            "events": self.event_log[-20:],
        }
