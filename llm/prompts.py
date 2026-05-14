from typing import Dict, List

SYSTEM_GOAL_PROMPT = (
    "You are a village simulation assistant. Provide a single short goal for the villager "
    "based on their current state, needs, and nearby context. Return only a JSON object "
    "with keys: goal, priority, and rationale. Do not include any markdown or explanatory text. "
    "Example output:\n" +
    "{\"goal\": \"Acquire food\", \"priority\": 5, \"rationale\": \"The villager is hungry and has low food stores.\"}"
)

SYSTEM_PLAN_PROMPT = (
    "You are a village planning assistant. Create a deterministic plan for the given goal. "
    "Return only a JSON object with keys: goal, actions, and notes. Each action should include "
    "type, duration_ticks, target, and metadata. Do not include markdown or extra text. "
    "Example output:\n" +
    "{\"goal\": \"Acquire food\", \"actions\": [{\"type\": \"walk\", \"duration_ticks\": 10, \"target\": \"market\", \"metadata\": {\"purpose\": \"travel\"}}], \"notes\": \"Simple market-run plan.\"}"
)


def build_goal_prompt(villager: Dict[str, object], context: Dict[str, object]) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_GOAL_PROMPT},
        {"role": "user", "content": (
            f"Villager:\n{villager}\n\nContext:\n{context}\n\n"
            "Suggest the next goal for this villager in the current simulation state."
        )},
    ]


def build_plan_prompt(goal: Dict[str, object], villager: Dict[str, object], context: Dict[str, object]) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PLAN_PROMPT},
        {"role": "user", "content": (
            f"Goal:\n{goal}\n\nVillager:\n{villager}\n\nContext:\n{context}\n\n"
            "Produce a deterministic action plan that accomplishes the goal."
        )},
    ]
