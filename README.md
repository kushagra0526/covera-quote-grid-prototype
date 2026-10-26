# quotegrid: compare carrier quotes when some terms are not stated

Covera's quote comparison "lines up the quotes received for the same risk on a coverage grid" and leaves the choice to the broker (https://www.covera-agents.com/agents/quote-comparison). The hard cell is the term a quote never states: is liquor liability excluded, or just not mentioned? This prototype is a simulator with known truth for that question. It is not Covera's system and uses no carrier or agency data.

## The setup
- `quotegrid/model.py`: a small-business package risk (value, daily income, serves alcohol, refrigeration) with six loss types (fire, water, theft, equipment breakdown, general liability, liquor liability), and what a quote pays: limit, replacement cost vs actual cash value, coinsurance penalty, deductible, water and equipment sublimits, liquor included/sublimit/excluded, business-income waiting period and cap, liability limit. A quote's premium is its expected payout under generic assumptions times a carrier load. Some terms are hidden ("not stated") in the quote the broker sees.
- `quotegrid/grid.py`: the grid. It lists which fields differ, reads every unstated term both ways (generous and thin), prices each quote as premium minus expected payout under a generic loss profile plus the client's known facts, and returns PICK only when the leader's worst case beats every other quote's best case. Otherwise ASK, naming the unstated terms worth asking a carrier about.
- Truth: each client's real loss rates differ from the generic ones; the true cost of a quote = premium minus its expected payout under the true rates, from the same simulated events for all four quotes.

## Results (4 quotes per comparison)
Dev: 60 comparisons, 18% of terms hidden, loss rates vary by 30%. Held-out (seeds 1000-1099, config fixed in git before the first run): 100 comparisons, 25% hidden, thinner coverage, rates vary by 60%, and 1 client in 4 has a water-damage rate 4x the generic one that the grid does not know about.

| held-out | picked the truly cheapest-to-own quote | mean regret per year | no answer |
|---|---|---|---|
| cheapest premium | 66% | $1,164 | 0% |
| premium + deductible | 44% | $1,691 | 0% |
| grid, always take its leader | 70% | $739 | 0% |
| grid, pick only when clear | 77% (of 65) | $431 | 35% asked a question instead |

The last row is scored only on the comparisons where it names a winner. Added after the held-out run (`quotegrid/subset.py`, `out/subset.txt`): on the same 65 comparisons, cheapest premium was wrong 29% of the time with $1,061 a year regret, premium + deductible 57% / $1,656, the grid 23% / $431. On the 35 comparisons the grid refused, cheapest premium was wrong 43% of the time ($1,356 a year).
Dev: 80% right (of 41 named) vs 73% for cheapest premium.

## Read this before believing the table
- Premium here already tracks coverage (it is generated from expected payout), so cheapest premium is a decent baseline. Real carriers price on much more.
- The grid is still wrong 23% of the time when it names a winner: the generic profile misses client-specific risk (the water-damage clients). It lowers regret, it does not remove it.
- All loss rates, sublimits and loads are invented. Valuation, coinsurance and sublimits are simplified; there are no aggregate limits, no claims-made vs occurrence and no exclusions beyond the ones listed. This is not insurance advice and not a statement about any carrier.
- Quotes are already structured here. Reading real PDFs is a separate problem this does not touch.

## Run it (3 commands)
```
pip install numpy pytest
python -m pytest -q tests
python -m quotegrid.run
```
numpy only. 4 tests; the run takes a few seconds.

Unofficial prototype by Kushagra Pratap Singh. Not affiliated with Covera.
