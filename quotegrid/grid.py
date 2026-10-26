"""Coverage grid for several quotes on one risk: show where they differ, price the differences, and only name a winner when the gap beats what is unknown."""
import numpy as np

from .model import STATABLE, events, payout

FIELDS = ["limit_pct", "valuation", "coins", "deductible", "water_sub", "eq", "liq", "bi_wait_days", "bi_max_days", "gl_limit"]
GENERIC_YEARS = 8000


def generic_events(client, seed=7):
    return events(client, np.random.default_rng(seed), GENERIC_YEARS)


def compare(quotes, premiums, client, margin=0.0):
    ev = generic_events(client)
    grid = {f: [q[f] for q in quotes] for f in FIELDS}
    differs = [f for f in FIELDS if len({repr(v) for v in grid[f]}) > 1]
    missing = [(i, f) for i, q in enumerate(quotes) for f in STATABLE if q[f] is None]
    lo, hi = [], []                                      # annual cost = premium - expected payout; unknown terms read both ways
    for q, pr in zip(quotes, premiums):
        best = pr - payout(q, client, ev, GENERIC_YEARS, "included")
        worst = pr - payout(q, client, ev, GENERIC_YEARS, "excluded")
        lo.append(min(best, worst)), hi.append(max(best, worst))
    mid = [(a + b) / 2 for a, b in zip(lo, hi)]
    order = list(np.argsort(mid))
    top = order[0]
    clear = all(hi[top] + margin < lo[j] for j in range(len(quotes)) if j != top)
    # the questions that would settle it: unknown terms on quotes whose interval overlaps the leader's
    ask = [] if clear else [(i, f) for i, f in missing if i == top or lo[i] <= hi[top]]
    return {"grid": grid, "differs": differs, "missing": missing, "cost_lo": lo, "cost_hi": hi, "leader": int(top),
            "decision": "PICK" if clear else "ASK", "ask": ask}
