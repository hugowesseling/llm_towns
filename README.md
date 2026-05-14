# Game arch basics
Backend and frontend to enable continuous operation.

Backend in some language with easy structures and good LLM connections: python

Backend provides provides requests that give local world overview.

Frontend: first, just simple blockview

# World structure
- 2d grid data
- 2 levels of detail:
- - World: Towns occupy just one block
- - Town level:
- - - A house is multiple squares
- - - Each square is obstruction or not
- - - A door is a square
- Interaction logic:
- - Information or object transfer
- - Interaction only on adjacent squares
- Characters:
- - Occupy a square
- - Have wants, relationships, occupations
- - Store history per character
- - LLM evaluation per character for internal thoughts
- - LLM evaluation for multi character for interactions
- Actions:
- - Before LLM call, possible actions determined:
- - - Possible characters that can be interacted with
- Use LLMs to expand world.
- Use image gens to generate new block-types

# Simulation action model

This repository now includes a small simulation module under `simulation/` that implements:
- `Action` and `ActionState` for hierarchical, time-bound tasks
- `Goal` and `Plan` as separate intent/plan layers
- `VillagerCognition` and decision layers for reactive, tactical, and reflective thinking

The pattern is:
- Goal (why)
- Plan (how)
- Actions / sub-actions (what executes)
- Atomic deterministic ticks (when)
