from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DecisionLayer(Enum):
    REACTIVE = "reactive"
    TACTICAL = "tactical"
    REFLECTIVE = "reflective"


LAYER_INTERVALS = {
    DecisionLayer.REACTIVE: 1,
    DecisionLayer.TACTICAL: 30,
    DecisionLayer.REFLECTIVE: 300,
}


@dataclass
class VillagerCognition:
    actor_id: str
    last_reactive_tick: int = 0
    last_tactical_tick: int = 0
    last_reflective_tick: int = 0
    current_goal_id: Optional[str] = None
    current_plan_id: Optional[str] = None
    last_thought_tick: int = 0


def should_run_layer(layer: DecisionLayer, current_tick: int, last_tick: int) -> bool:
    interval = LAYER_INTERVALS[layer]
    return current_tick - last_tick >= interval
