from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ActionState(Enum):
    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Action:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    actor_id: str = ""
    type: str = ""
    target_ids: List[str] = field(default_factory=list)
    state: ActionState = ActionState.PLANNED
    parent_id: Optional[str] = None
    subactions: List[Action] = field(default_factory=list)

    started_tick: Optional[int] = None
    duration_ticks: int = 1
    progress_ticks: int = 0

    interruptible: bool = True
    interrupt_priority: int = 0

    preconditions: List[Dict[str, Any]] = field(default_factory=list)
    effects: List[Dict[str, Any]] = field(default_factory=list)
    reservations: List[Dict[str, Any]] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def expected_end_tick(self) -> Optional[int]:
        if self.started_tick is None:
            return None
        return self.started_tick + self.duration_ticks

    def is_active(self) -> bool:
        return self.state in {ActionState.READY, ActionState.RUNNING, ActionState.BLOCKED}

    def is_completed(self) -> bool:
        return self.state is ActionState.COMPLETED

    def can_interrupt(self, incoming_priority: int) -> bool:
        if not self.interruptible:
            return False
        return incoming_priority >= self.interrupt_priority

    def start(self, tick: int) -> None:
        if self.state not in {ActionState.PLANNED, ActionState.READY}:
            return
        self.started_tick = tick
        self.progress_ticks = 0
        self.state = ActionState.RUNNING

    def tick(self, current_tick: int) -> None:
        if self.state is not ActionState.RUNNING:
            return

        if self.started_tick is None:
            self.started_tick = current_tick

        self.progress_ticks = current_tick - self.started_tick
        if self.progress_ticks >= self.duration_ticks:
            self.complete()

    def block(self) -> None:
        if self.state is ActionState.RUNNING:
            self.state = ActionState.BLOCKED

    def resume(self) -> None:
        if self.state is ActionState.BLOCKED:
            self.state = ActionState.RUNNING

    def complete(self) -> None:
        self.state = ActionState.COMPLETED

    def fail(self) -> None:
        self.state = ActionState.FAILED

    def cancel(self) -> None:
        self.state = ActionState.CANCELLED

    def add_subaction(self, subaction: Action) -> None:
        subaction.parent_id = self.id
        self.subactions.append(subaction)


@dataclass
class Goal:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    actor_id: str = ""
    description: str = ""
    priority: int = 0
    created_tick: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    actor_id: str = ""
    goal_id: Optional[str] = None
    actions: List[Action] = field(default_factory=list)
    created_tick: int = 0
    last_reviewed_tick: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_current_action(self) -> Optional[Action]:
        for action in self.actions:
            if action.is_active():
                return action
        return None

    def enqueue_action(self, action: Action) -> None:
        self.actions.append(action)

    def is_complete(self) -> bool:
        return all(action.is_completed() for action in self.actions)

    def advance(self, current_tick: int) -> None:
        current_action = self.get_current_action()
        if current_action is None:
            return

        if current_action.state is ActionState.READY:
            current_action.start(current_tick)

        if current_action.state is ActionState.RUNNING:
            current_action.tick(current_tick)

        if current_action.state is ActionState.COMPLETED and current_action.subactions:
            next_subaction = next((sa for sa in current_action.subactions if sa.state is ActionState.PLANNED), None)
            if next_subaction:
                next_subaction.state = ActionState.READY

    def interrupt(self, incoming_priority: int) -> bool:
        current_action = self.get_current_action()
        if current_action and current_action.can_interrupt(incoming_priority):
            current_action.block()
            return True
        return False
