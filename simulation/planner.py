from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .actions import Action, ActionState, Goal, Plan
from .villager import Villager


@dataclass
class Planner:
    default_durations: Dict[str, int] = field(default_factory=lambda: {
        "walk": 10,
        "trade": 6,
        "gather": 8,
        "rest": 20,
        "idle": 3,
    })

    def create_plan(self, villager: Villager, goal: Goal, current_tick: int) -> Plan:
        plan = Plan(actor_id=villager.id, goal_id=goal.id, created_tick=current_tick, last_reviewed_tick=current_tick)
        description = goal.description.lower()

        if "food" in description or "hunger" in description:
            plan.enqueue_action(self._build_walk_action(villager, "market", current_tick))
            plan.enqueue_action(self._build_action(villager, "trade", duration=6, metadata={"purpose": "buy food"}))
            plan.enqueue_action(self._build_walk_action(villager, "home", current_tick))
        elif "social" in description or "talk" in description:
            plan.enqueue_action(self._build_walk_action(villager, "square", current_tick))
            plan.enqueue_action(self._build_action(villager, "chat", duration=5, metadata={"purpose": "socialize"}))
        else:
            plan.enqueue_action(self._build_action(villager, "idle", duration=3, metadata={"purpose": "stand by"}))

        if plan.actions:
            plan.actions[0].state = ActionState.READY
        return plan

    def _build_action(self, villager: Villager, action_type: str, duration: int, metadata: Dict[str, object] = None) -> Action:
        return Action(
            actor_id=villager.id,
            type=action_type,
            duration_ticks=duration,
            metadata=metadata or {},
        )

    def _build_walk_action(self, villager: Villager, destination: str, current_tick: int) -> Action:
        return Action(
            actor_id=villager.id,
            type="walk",
            duration_ticks=self.default_durations.get("walk", 10),
            metadata={"destination": destination},
        )
