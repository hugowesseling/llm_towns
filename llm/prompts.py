from typing import Dict, List, Optional

SYSTEM_GOAL_PROMPT = (
    "You are a village simulation assistant. Provide a single short goal for the villager "
    "based on their current state, needs, and nearby context. Return only a JSON object "
    "with keys: goal, priority, and rationale. Do not include any markdown or explanatory text. "
    "Example output:\n" +
    '{"goal": "Acquire food", "priority": 5, "rationale": "The villager is hungry and has low food stores."}'
)

SYSTEM_PLAN_PROMPT = (
    "You are a village planning assistant. Create a deterministic plan for the given goal. "
    "Return only a JSON object with keys: goal, actions, and notes. Each action should include "
    "type, duration_ticks, target, and metadata. Do not include markdown or extra text. "
    "Supported action types: walk, travel, trade, gather, rest, idle, chat, explore. "
    "Use 'travel' to go to another town (target = town id). "
    "Use 'walk' to move within the current town (target = 'market', 'home', 'square', or a POI id). "
    "Example output:\n" +
    '{"goal": "Acquire food", "actions": [{"type": "walk", "duration_ticks": 10, "target": "market", "metadata": {"purpose": "travel"}}], "notes": "Simple market-run plan."}'
)


def build_town_context(villager_town_id: str, towns: Dict[str, object]) -> str:
    """Build a string describing nearby towns for a villager."""
    home_town = towns.get(villager_town_id)
    if not home_town:
        return ""

    lines = [f"Home town: {home_town.name} (id: {home_town.id})"]
    for tid, t in towns.items():
        if tid != villager_town_id:
            relation = home_town.relations.get(tid, "unknown")
            lines.append(f"  - {t.name} (id: {tid}) — relation: {relation}")
    return "\n".join(lines)


def build_goal_prompt(villager: Dict[str, object], context: Dict[str, object], town_context: Optional[str] = None) -> List[Dict[str, str]]:
    extra = f"\n\nTown context:\n{town_context}" if town_context else ""
    return [
        {"role": "system", "content": SYSTEM_GOAL_PROMPT},
        {"role": "user", "content": (
            f"Villager:\n{villager}\n\nContext:\n{context}{extra}\n\n"
            "Suggest the next goal for this villager in the current simulation state."
        )},
    ]


def build_plan_prompt(goal: Dict[str, object], villager: Dict[str, object], context: Dict[str, object], town_context: Optional[str] = None) -> List[Dict[str, str]]:
    extra = f"\n\nTown context:\n{town_context}" if town_context else ""
    return [
        {"role": "system", "content": SYSTEM_PLAN_PROMPT},
        {"role": "user", "content": (
            f"Goal:\n{goal}\n\nVillager:\n{villager}\n\nContext:\n{context}{extra}\n\n"
            "Produce a deterministic action plan that accomplishes the goal."
        )},
    ]
