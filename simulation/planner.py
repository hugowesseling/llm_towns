from __future__ import annotations

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .actions import Action, ActionState, Goal, Plan
from .villager import Villager
from llm.brain import LLMBrain
from llm.prompts import build_plan_prompt


@dataclass
class Planner:
    default_durations: Dict[str, int] = field(default_factory=lambda: {
        "walk": 10,
        "trade": 6,
        "gather": 8,
        "rest": 20,
        "idle": 3,
    })

    llm_brain: Optional[LLMBrain] = None

    def create_plan(self, villager: Villager, goal: Goal, current_tick: int, scheduler: Optional['SimulationScheduler'] = None) -> Plan:
        if self.llm_brain:
            try:
                return self._create_plan_from_llm(villager, goal, current_tick, scheduler)
            except Exception:
                # Fallback to deterministic plan generation if LLM fails.
                pass

        return self._create_fallback_plan(villager, goal, current_tick, scheduler)

    def _create_plan_from_llm(self, villager: Villager, goal: Goal, current_tick: int, scheduler: Optional['SimulationScheduler'] = None) -> Plan:
        villager_summary = villager.summary()
        context = {
            "tick": current_tick,
            "location": {"x": villager.position.x, "y": villager.position.y},
            "needs": {
                "hunger": villager.needs.hunger,
                "energy": villager.needs.energy,
                "social": villager.needs.social,
            },
            "inventory": villager.inventory.items,
            "relationships": villager.relationships,
        }

        messages = build_plan_prompt(goal.__dict__, villager_summary, context)
        plan_data = self.llm_brain.create_chat_json(
            messages=messages,
            temperature=0.5,
            max_tokens=400,
        )

        if not isinstance(plan_data, dict):
            raise ValueError("LLM plan output must be a JSON object")

        plan = Plan(actor_id=villager.id, goal_id=goal.id, created_tick=current_tick, last_reviewed_tick=current_tick)
        actions = plan_data.get("actions", [])
        for action_payload in actions:
            action = self._parse_action_payload(villager, action_payload, scheduler)
            if action is not None:
                plan.enqueue_action(action)

        if not plan.actions:
            raise ValueError("LLM returned no valid actions")

        plan.actions[0].state = ActionState.READY
        return plan

    def _create_fallback_plan(self, villager: Villager, goal: Goal, current_tick: int, scheduler: Optional['SimulationScheduler'] = None) -> Plan:
        plan = Plan(actor_id=villager.id, goal_id=goal.id, created_tick=current_tick, last_reviewed_tick=current_tick)
        description = goal.description.lower()

        if "food" in description or "hunger" in description:
            plan.enqueue_action(self._build_walk_action(villager, "market", scheduler))
            plan.enqueue_action(self._build_action(villager, "trade", duration=6, metadata={"purpose": "buy food"}))
            plan.enqueue_action(self._build_walk_action(villager, "home", scheduler))
        elif "social" in description or "talk" in description:
            plan.enqueue_action(self._build_walk_action(villager, "square", scheduler))
            plan.enqueue_action(self._build_action(villager, "chat", duration=5, metadata={"purpose": "socialize"}))
        else:
            plan.enqueue_action(self._build_action(villager, "idle", duration=3, metadata={"purpose": "stand by"}))

        if plan.actions:
            plan.actions[0].state = ActionState.READY
        return plan

    def _parse_action_payload(self, villager: Villager, payload: Dict[str, Any], scheduler: Optional['SimulationScheduler'] = None) -> Optional[Action]:
        if not isinstance(payload, dict):
            return None

        action_type = payload.get("type")
        duration_ticks = payload.get("duration_ticks")
        if not action_type or not isinstance(duration_ticks, int):
            return None

        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        target = payload.get("target")
        if target is not None:
            metadata = {**metadata, "target": target}

        return Action(
            actor_id=villager.id,
            type=action_type,
            duration_ticks=duration_ticks,
            metadata=metadata,
        )

    def _build_action(self, villager: Villager, action_type: str, duration: int, metadata: Dict[str, object] = None) -> Action:
        return Action(
            actor_id=villager.id,
            type=action_type,
            duration_ticks=duration,
            metadata=metadata or {},
        )

    def _build_walk_action(self, villager: Villager, destination: str, scheduler: Optional['SimulationScheduler'] = None) -> Action:
        return Action(
            actor_id=villager.id,
            type="walk",
            duration_ticks=self.default_durations.get("walk", 10),
            metadata={"destination": destination},
        )
