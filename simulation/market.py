from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .villager import Villager


@dataclass
class Market:
    id: str
    position: tuple[int, int]
    inventory: Dict[str, int] = field(default_factory=dict)
    prices: Dict[str, float] = field(default_factory=dict)  # Buy/sell prices

    def buy_item(self, villager: Villager, item: str, quantity: int = 1) -> bool:
        if item not in self.inventory or self.inventory[item] < quantity:
            return False
        cost = self.prices.get(item, 1.0) * quantity
        if villager.inventory.items.get("gold", 0) < cost:
            return False
        # Transfer
        villager.inventory.remove("gold", int(cost))
        villager.inventory.add(item, quantity)
        self.inventory[item] -= quantity
        return True

    def sell_item(self, villager: Villager, item: str, quantity: int = 1) -> bool:
        if villager.inventory.items.get(item, 0) < quantity:
            return False
        payment = self.prices.get(item, 1.0) * quantity
        # Transfer
        villager.inventory.remove(item, quantity)
        villager.inventory.add("gold", int(payment))
        self.inventory[item] = self.inventory.get(item, 0) + quantity
        return True

    def trade_between_villagers(self, seller: Villager, buyer: Villager, item: str, quantity: int = 1, price: float = 1.0) -> bool:
        if seller.inventory.items.get(item, 0) < quantity or buyer.inventory.items.get("gold", 0) < price * quantity:
            return False
        # Transfer
        seller.inventory.remove(item, quantity)
        buyer.inventory.add(item, quantity)
        buyer.inventory.remove("gold", int(price * quantity))
        seller.inventory.add("gold", int(price * quantity))
        return True
