"""Added after the held-out run: score every method on the SAME comparisons, the ones where the grid names a winner."""
import numpy as np

from . import grid
from .run import scenario


def main(seeds=range(1000, 1100), held=True):
    rows = {"cheapest premium": [], "premium + deductible": [], "grid": []}
    asked = {"cheapest premium": [], "premium + deductible": []}
    for s in seeds:
        client, quotes, prem, cost = scenario(s, held)
        best = min(cost)
        res = grid.compare(quotes, prem, client)
        pick = {"cheapest premium": int(np.argmin(prem)), "premium + deductible": int(np.argmin([p + q["deductible"] for p, q in zip(prem, quotes)]))}
        if res["decision"] == "PICK":
            rows["grid"].append(cost[res["leader"]] - best)
            for m, p in pick.items():
                rows[m].append(cost[p] - best)
        else:
            for m, p in pick.items():
                asked[m].append(cost[p] - best)
    n = len(rows["grid"])
    print(f"comparisons where the grid names a winner: {n} of {len(list(seeds))}")
    for m, r in rows.items():
        print(f"  {m}: mean regret {np.mean(r):.0f}/yr, wrong {100 * np.mean([x > 1 for x in r]):.0f}%")
    for m, r in asked.items():
        print(f"  on the {len(r)} comparisons the grid asks about, {m}: mean regret {np.mean(r):.0f}/yr, wrong {100 * np.mean([x > 1 for x in r]):.0f}%")


if __name__ == "__main__":
    main()
