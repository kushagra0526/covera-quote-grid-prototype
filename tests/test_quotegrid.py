import numpy as np

from quotegrid import grid, model

CLIENT = {"value": 1e6, "daily_income": 2000.0, "alcohol": True, "fridge": True}
BASE = {"limit_pct": 1.0, "valuation": "RC", "coins": 0.0, "deductible": 1000.0, "water_sub": "included", "eq": "included",
        "liq": "included", "bi_wait_days": 0.0, "bi_max_days": 365.0, "gl_limit": 1e6}


def pay(**kw):
    ev = model.events(CLIENT, np.random.default_rng(3), 4000)
    return model.payout({**BASE, **kw}, CLIENT, ev, 4000)


def test_thinner_terms_pay_less():
    full = pay()
    assert pay(valuation="ACV") < full
    assert pay(liq="excluded") < full
    assert pay(deductible=10000.0) < full
    assert pay(limit_pct=0.8, coins=1.0) < full           # coinsurance penalty on a 80% limit


def test_unstated_term_is_read_both_ways():
    ev = model.events(CLIENT, np.random.default_rng(3), 4000)
    q = {**BASE, "liq": None}
    assert model.payout(q, CLIENT, ev, 4000, "included") > model.payout(q, CLIENT, ev, 4000, "excluded")


def test_grid_flags_differences_and_asks_when_unknown_decides():
    a, b = dict(BASE), {**BASE, "liq": None}
    r = grid.compare([a, b], [5000, 4900], CLIENT)
    assert "liq" in r["differs"] and r["missing"] == [(1, "liq")]
    assert r["decision"] == "ASK" and r["ask"] == [(1, "liq")]


def test_grid_picks_when_gap_is_clear():
    thin = {**BASE, "valuation": "ACV", "liq": "excluded", "eq": "excluded", "deductible": 10000.0}
    r = grid.compare([BASE, thin], [5000, 5000], CLIENT)
    assert r["decision"] == "PICK" and r["leader"] == 0
