from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .actions import ActionState, Goal, Plan
from .planner import Planner
from .villager import Villager


@dataclass
class SimulationScheduler:
    planner: Planner = field(default_factory=Planner)
    villagers: Dict[str, Villager] = field(default_factory=dict)
    goals: Dict[str, Goal] = field(default_factory=dict)
    plans: Dict[str, Plan] = field(default_factory=dict)
    current_tick: int = 0
    event_log: List[Dict[str, object]] = field(default_factory=list)

    def add_villager(self, villager: Villager) -> None:
        self.villagers[villager.id] = villager

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

        plan = self.planner.create_plan(villager, goal, self.current_tick)
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
