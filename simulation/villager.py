from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .actions import Goal
from .decision import VillagerCognition


@dataclass
class Position:
    x: int = 0
    y: int = 0


@dataclass
class Inventory:
    items: Dict[str, int] = field(default_factory=dict)

    def add(self, item: str, amount: int = 1) -> None:
        self.items[item] = self.items.get(item, 0) + amount

    def remove(self, item: str, amount: int = 1) -> bool:
        current = self.items.get(item, 0)
        if current < amount:
            return False
        if current == amount:
            self.items.pop(item, None)
        else:
            self.items[item] = current - amount
        return True


@dataclass
class Needs:
    hunger: int = 50
    energy: int = 80
    social: int = 50


@dataclass
class Villager:
    id: str
    name: str
    town: str
    profession: str = "Villager"
    position: Position = field(default_factory=Position)
    inventory: Inventory = field(default_factory=Inventory)
    needs: Needs = field(default_factory=Needs)
    relationships: Dict[str, str] = field(default_factory=dict)
    memories: List[str] = field(default_factory=list)
    current_goal_id: Optional[str] = None
    current_plan_id: Optional[str] = None
    cognition: VillagerCognition = field(default_factory=lambda: VillagerCognition(actor_id=""))

    def __post_init__(self) -> None:
        if not self.cognition.actor_id:
            self.cognition.actor_id = self.id

    def is_idle(self) -> bool:
        return self.current_plan_id is None

    def assign_goal(self, goal: Goal) -> None:
        self.current_goal_id = goal.id
        self.current_plan_id = None

    def summary(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "town": self.town,
            "profession": self.profession,
            "position": {"x": self.position.x, "y": self.position.y},
            "needs": {
                "hunger": self.needs.hunger,
                "energy": self.needs.energy,
                "social": self.needs.social,
            },
            "inventory": self.inventory.items,
            "current_goal_id": self.current_goal_id,
            "current_plan_id": self.current_plan_id,
            "relationships": self.relationships,
        }
