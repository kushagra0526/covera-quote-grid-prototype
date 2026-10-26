"""Small-business package (BOP-like) quotes with known truth: a loss model, what each quote pays, and a quote generator.

All rates and sizes are invented for the simulation; nothing here is insurance advice or carrier data.
"""
import numpy as np

# field -> allowed values; None in a quote means "not stated in the document"
VAL = ("RC", "ACV")
EQ = ("included", "sublimit", "excluded")
LIQ = ("included", "sublimit", "excluded")
SUBLIMIT = {"water": 25_000, "eq": 25_000, "liq": 100_000}
GENERIC = {"fire": (0.012, 0.12, 1.2), "water": (0.04, 0.015, 1.0), "theft": (0.06, 0.003, 0.9),
           "eq": (0.08, 8_000, 0.8), "gl": (0.05, 25_000, 1.8), "liq": (0.015, 120_000, 1.5)}   # rate/yr, median (x value for property), sigma


def make_client(rng):
    value = float(rng.choice([400e3, 700e3, 1.2e6, 2e6]))
    return {"value": value, "daily_income": float(rng.uniform(900, 4000)), "alcohol": bool(rng.random() < 0.6),
            "fridge": bool(rng.random() < 0.9)}


def events(client, rng, years, rate_mult=None, sev_mult=None):
    """Loss events over `years` simulated years (expected payout = total payout / years; there are no aggregate limits)."""
    rate_mult, sev_mult = rate_mult or {}, sev_mult or {}
    out = {}
    for p, (lam, med, sig) in GENERIC.items():
        lam = lam * rate_mult.get(p, 1.0)
        if p == "eq" and not client["fridge"]:
            lam *= 0.2
        if p == "liq" and not client["alcohol"]:
            lam = 0.0
        n = rng.poisson(lam * years)
        base = med * client["value"] if p in ("fire", "water", "theft") else med
        sev = base * sev_mult.get(p, 1.0) * rng.lognormal(0, sig, n)
        if p in ("fire", "water", "theft"):
            sev = np.minimum(sev, client["value"])
        out[p] = sev
    return out


def payout(terms, client, ev, years, unknown="included"):
    """Expected annual payout of a quote. A term the quote does not state is read as `unknown` ('included' = generous, 'excluded' = thin)."""
    t = {k: (unknown_default(k, unknown) if v is None else v) for k, v in terms.items()}
    V = client["value"]
    limit = t["limit_pct"] * V
    factor = 1.0 if t["coins"] == 0 else min(1.0, limit / (t["coins"] * V))
    val = 1.0 if t["valuation"] == "RC" else 0.8
    ded = t["deductible"]
    total = 0.0
    for p in ("fire", "water", "theft"):
        loss = ev[p]
        cap = limit
        if p == "water":
            cap = min(limit, SUBLIMIT["water"] if t["water_sub"] == "sublimit" else (0 if t["water_sub"] == "excluded" else limit))
        pay = np.minimum(cap, np.maximum(0.0, loss * val * factor - ded))
        total += pay.sum()
        if p in ("fire", "water"):               # closure days after a big loss; waiting period comes off the front
            big = loss > 0.05 * V
            days = np.where(big, 20 + 120 * loss / V, 0.0)
            bi = np.maximum(0.0, days - t["bi_wait_days"]).clip(max=t["bi_max_days"]) * client["daily_income"]
            total += bi[pay > 0].sum()
    eq = ev["eq"]
    if t["eq"] == "included":
        total += np.maximum(0.0, eq - ded).sum()
    elif t["eq"] == "sublimit":
        total += np.minimum(SUBLIMIT["eq"], np.maximum(0.0, eq - ded)).sum()
    total += np.minimum(t["gl_limit"], ev["gl"]).sum()
    liq = ev["liq"]
    if t["liq"] == "included":
        total += np.minimum(t["gl_limit"], liq).sum()
    elif t["liq"] == "sublimit":
        total += np.minimum(SUBLIMIT["liq"], liq).sum()
    return total / years


def unknown_default(field, mode):
    good = {"eq": "included", "liq": "included", "water_sub": "included", "bi_wait_days": 0, "valuation": "RC"}
    bad = {"eq": "excluded", "liq": "excluded", "water_sub": "excluded", "bi_wait_days": 3, "valuation": "ACV"}
    return (good if mode == "included" else bad)[field]


STATABLE = ("eq", "liq", "water_sub", "bi_wait_days", "valuation")


def random_terms(rng, thin_bias=0.5):
    def pick(options, thin):
        return options[1 + int(rng.random() < 0.5)] if rng.random() < thin and len(options) > 2 else options[0]
    return {"limit_pct": float(rng.choice([0.8, 0.9, 1.0, 1.1])), "valuation": "ACV" if rng.random() < thin_bias * 0.7 else "RC",
            "coins": float(rng.choice([0.0, 0.8, 0.9, 1.0])), "deductible": float(rng.choice([1000, 2500, 5000, 10000])),
            "water_sub": pick(("included", "sublimit", "excluded"), thin_bias * 0.8), "eq": pick(EQ, thin_bias * 0.8),
            "liq": pick(LIQ, thin_bias * 0.8), "bi_wait_days": float(rng.choice([0, 1, 3])), "bi_max_days": float(rng.choice([180, 365])),
            "gl_limit": float(rng.choice([1e6, 1e6, 2e6]))}


def make_quotes(client, rng, n_quotes=4, hide=0.18, thin_bias=0.5):
    """Returns (stated quotes, true terms, premiums). Premium = what the quote pays under generic assumptions x carrier load."""
    ev = events(client, rng, 6000)
    quotes, truth, prem = [], [], []
    for _ in range(n_quotes):
        t = random_terms(rng, thin_bias)
        load = float(rng.lognormal(np.log(1.55), 0.12))
        prem.append(round(load * payout(t, client, ev, 6000) + 0.002 * client["value"] + 600))
        truth.append(t)
        stated = dict(t)
        for f in STATABLE:
            if rng.random() < hide:
                stated[f] = None
        quotes.append(stated)
    return quotes, truth, prem
