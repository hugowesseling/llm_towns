from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .actions import ActionState, Goal, Plan
from .decision import DecisionLayer, should_run_layer
from .planner import Planner
from .villager import Villager
from llm.brain import LLMBrain
from llm.prompts import build_goal_prompt


@dataclass
class SimulationScheduler:
    planner: Planner = field(default_factory=Planner)
    villagers: Dict[str, Villager] = field(default_factory=dict)
    goals: Dict[str, Goal] = field(default_factory=dict)
    plans: Dict[str, Plan] = field(default_factory=dict)
    current_tick: int = 0
    event_log: List[Dict[str, object]] = field(default_factory=list)
    llm_brain: Optional[LLMBrain] = None

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

            # Check if villager needs a new goal
            if villager.is_idle() and should_run_layer(DecisionLayer.REFLECTIVE, self.current_tick, villager.cognition.last_reflective_tick):
                self._assign_new_goal(villager)
                villager.cognition.last_reflective_tick = self.current_tick

    def _assign_new_goal(self, villager: Villager) -> None:
        if self.llm_brain is None:
            # Fallback: assign a default goal
            goal = Goal(actor_id=villager.id, description="Idle and reflect", priority=1, created_tick=self.current_tick)
            self.add_goal(goal)
            return

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

        messages = build_goal_prompt(villager.summary(), context)
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
