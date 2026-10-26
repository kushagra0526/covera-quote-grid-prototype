import json

import numpy as np

from . import grid, model

YEARS = 8000
METHODS = ["cheapest premium", "premium + deductible", "grid, always pick", "grid, pick only when clear"]


def scenario(seed, held):
    rng = np.random.default_rng(seed)
    client = model.make_client(rng)
    hide, thin, sig = (0.25, 0.7, 0.6) if held else (0.18, 0.5, 0.3)
    quotes, truth, prem = model.make_quotes(client, rng, 4, hide, thin)
    rate = {p: float(rng.lognormal(0, sig)) for p in model.GENERIC}
    if held and rng.random() < 0.25:
        rate["water"] *= 4                                   # a risk the checker's generic profile does not know about
    ev = model.events(client, np.random.default_rng(seed + 99), YEARS, rate)
    cost = [p - model.payout(t, client, ev, YEARS) for t, p in zip(truth, prem)]
    return client, quotes, prem, cost


def score(seeds, held):
    acc = {m: {"best": 0, "regret": [], "abstain": 0} for m in METHODS}
    n = 0
    for s in seeds:
        client, quotes, prem, cost = scenario(s, held)
        best = int(np.argmin(cost))
        res = grid.compare(quotes, prem, client)
        picks = {"cheapest premium": int(np.argmin(prem)),
                 "premium + deductible": int(np.argmin([p + q["deductible"] for p, q in zip(prem, quotes)])),
                 "grid, always pick": res["leader"],
                 "grid, pick only when clear": res["leader"] if res["decision"] == "PICK" else None}
        n += 1
        for m, p in picks.items():
            if p is None:
                acc[m]["abstain"] += 1
                continue
            acc[m]["best"] += p == best
            acc[m]["regret"].append(cost[p] - cost[best])
    out = {}
    for m, d in acc.items():
        k = n - d["abstain"]
        out[m] = {"picked_true_best_pct": round(100 * d["best"] / max(k, 1)), "mean_regret_per_year": round(float(np.mean(d["regret"]))) if d["regret"] else None,
                  "wrong_confident_pct": round(100 * (k - d["best"]) / max(k, 1)), "abstained_pct": round(100 * d["abstain"] / n)}
    return out


def main():
    res = {"dev": score(range(0, 60), False), "held_out": score(range(1000, 1100), True)}
    json.dump(res, open("out/result.json", "w"), indent=1)
    for k, v in res.items():
        print(k)
        for m, d in v.items():
            print("  ", m, d)


if __name__ == "__main__":
    main()
