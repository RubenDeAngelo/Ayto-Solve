# Are You The One? — Solver

Enumerates all feasible perfect-matching configurations for the German dating show *Are You The One?* given the clues revealed each episode, then visualises the results as a probability heatmap.

## How the show works

Each season pairs W women with M men. Every person has exactly one perfect match on the opposite side — except in seasons with a **double match**, where one person is the perfect match for *two* people (making the group sizes unequal, e.g. 11 women, 10 men).

Two types of clues are revealed during the season:

| Clue | What it tells you |
|---|---|
| **Matching night** | All participants pair up; the number of correct pairs is revealed, but not *which* ones |
| **Matchbox decision** | A specific pair enters the matchbox and are told definitively whether they are a perfect match |

The solver encodes all revealed clues as constraints and finds every assignment that satisfies all of them simultaneously. The probability that any given pair is a perfect match equals the fraction of valid solutions in which they appear together.

## Double match logic

When group sizes are unequal the solver iterates over a list of **candidate** double-match people (because the show hasn't revealed who it is yet):

- **More women than men** (`is_men_smaller`): one woman shares a man with another woman. The double-match woman has exactly one man; that man ends up with two women.
- **More men than women** (`is_women_smaller`): one man is the perfect match for two different women. Every woman has at least one man; one woman ends up with two men.

Once a regular pair is confirmed in the matchbox the double-match person is excluded from that same partner (a confirmed exclusive match cannot be part of a double).

## Project structure

```
.
├── main.py                  # CP-SAT solver (OR-Tools) — recommended, finds all solutions at once
├── ILP.py                   # ILP solver (PuLP / CBC) — iterative no-good cut approach
├── heatmap.py               # Probability heatmap visualisation
├── season_february25.json   # Season data — Feb 2025 (active)
├── are_you_the_one.json     # Season data — completed season
└── season_august24.json     # Season data — skeleton (no clues yet)
```

## Input format

Season data is stored in JSON with three sections:

```json
{
  "participants": {
    "women": ["Anna", "Camelia", "..."],
    "men":   ["Danish", "Dino", "..."],
    "double_match": ["Camelia", "Joanna", "Sophia"]
  },
  "matching_nights": [
    {
      "matches": { "Anna": "Enes", "Camelia": "Levin", "Nasti": "None", "..." : "..." },
      "correct_matches": 2
    }
  ],
  "matchbox_decisions": [
    { "woman": "Nadja", "man": "Danish", "is_match": true  },
    { "woman": "Anna",  "man": "Josh",   "is_match": false }
  ]
}
```

- `double_match` can be a **list** (multiple candidates) or a **single string** (identity already known).
- Set a participant's partner to `"None"` on a matching night when they sat out.

## Usage

Install dependencies:

```bash
pip install ortools pulp numpy matplotlib
```

Run the CP-SAT solver (faster, finds all solutions in one pass):

```bash
python main.py
```

Run the ILP solver (iterative, alternative approach):

```bash
python ILP.py
```

Both scripts print the number of feasible solutions and the runtime, then open an interactive heatmap window. Each cell shows the probability (%) that the row woman and column man are a perfect match across all valid solutions.

## Switching seasons

Change the filename at the top of `main.py` / `ILP.py`:

```python
data = load_data('are_you_the_one.json')
```

## Solvers at a glance

| | `main.py` (CP-SAT) | `ILP.py` (CBC) |
|---|---|---|
| Approach | Enumerates all solutions natively | Iterative no-good cuts |
| Speed | Fast | Slower for large solution spaces |
| Dependency | `ortools` | `pulp` |
