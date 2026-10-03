"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {"name": "full three-tool run returns a fit card", "query": "vintage graphic tee under $30, size M", "wardrobe": "example", "criterion": 1},
    {"name": "empty search stops before styling", "query": "designer ballgown size XXS under $5", "wardrobe": "example", "criterion": 2},
    {"name": "actual item inputs match session state", "query": "vintage graphic tee under $30, size M", "wardrobe": "example", "criterion": 3, "mode": "state_probe"},
    {"name": "fit card contains accurate listing facts", "query": "vintage graphic tee under $30, size M", "wardrobe": "example", "criterion": 4},
    {"name": "empty wardrobe still receives styling advice", "query": "vintage graphic tee under $30, size M", "wardrobe": "empty", "criterion": 5},
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
