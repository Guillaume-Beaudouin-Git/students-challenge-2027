# Entry 002 · Stock example · Schneider Electric after the PTC deal

| | |
|---|---|
| Date | 24 November 2026 |
| Company | Schneider Electric (Paris, in euros) |
| Owner | Alexandre Le Bigaut (equity seat) |
| Challenger | Guillaume Beaudouin (chair) |
| Status | Voted by the six of us, in writing: six for, none against. Recorded by the chair on 25 November 2026 |
| Review | Full-year results in February 2027; first-quarter sales in late April 2027 |

## Decision

**Open at the starter size, 1.5% of the portfolio,** once the February results meet the conditions
below.

## What happened

- 5 October 2026: Schneider agreed to buy PTC, an industrial-software company, for $205 a share in
  cash, $22.6bn, a 42% premium to the last close.
- That day its shares fell 10%, from €303.0 to €272.8: about €17bn of market value on the shares
  then outstanding, nearly three times the €6.0bn premium it had agreed to pay.
- 19 October: it raised €6.0bn by placing 25 million new shares at €240. It then issued €6bn and,
  on 17 November, $10bn of bonds.
- 20 November: €226.55, the lowest close of 2026. That is 25% below the level before the deal and
  5.6% under the placement price.

Arithmetic: [`descriptive/stock_example.py`](../descriptive/stock_example.py).

## 1 · What the business earns

- About 13% on invested capital (2025 operating income of €7.01bn after tax at 23.5%, on €42.1bn).
- Operating margin of 18.0% over the twelve months to June 2026.
- Third quarter of 2026: organic growth of 16.9%, 18.8% in energy management; growth objective for
  2026 raised to 12–14%.
- Net debt was under 2 times EBITDA before the deal: 1.7 on its balance sheet of June 2026, 1.9 on
  the data vendor's summary. Analysts expect about 3 at closing, which the company expects by the
  third quarter of 2027.

## 2 · What the price assumes

- 27 times trailing earnings.
- Free cash flow, defined as operating cash flow less capital expenditure over the twelve months
  to June 2026: €5.74bn, a yield of 4.3% on the market value at the close of 20 November. Same
  definition, same day: ABB 3.5%, Eaton 3.1%.
- That cash flow is what is left for shareholders, so we discount it at a cost of equity, 8.5%,
  with 2.5% growth after ten years. The price then needs it to grow about 6.5% a year for ten
  years (4.1% at a cost of equity of 7.5%, 8.7% at 9.5%). It grew 12% a year from 2022 to 2025, on
  sales growing 5.5%.
- Not in this number: PTC, paid about 20 times its expected EBITDA according to press estimates.

## Why this one, and not Eaton or ABB

Of the three large makers of electrical equipment it is the cheapest on cash flow and has the best
ESG risk rating. It is also the only one carrying a deal.

## 3 · ESG

- What the product does: equipment that cuts electricity use, sold to grids, buildings and data
  centres.
- Our indicator: the share of sales aligned with the EU taxonomy, read in the company's own
  sustainability statement.
- Rated negligible risk by Morningstar Sustainalytics (9.8 on its public page, to be read again on
  FactSet). Our ceiling for that rating is 3.5%. The deal keeps us at 1.5%.

## 4 · Wrong if

- February results: organic growth for 2027 guided below 8%, or no stated path back under
  2.5 times EBITDA.
- Late-April sales: energy management growing less than 10%.
- ESG: the taxonomy-aligned share of sales falls, or a Category 4 controversy.
- If regulators block the purchase of PTC, the entry is rewritten.

## Objection

*Guillaume: press estimates put the return on the deal near 8% with every synergy, under a cost of
capital near 9%. And the share is still a bet on data-centre spending, which our "AI sell-off"
scenario fears.*

Alexandre: the fall already prices in nearly three times the premium. And once the market's move
is removed, the share has not followed the six since 2023: a weekly loading of 0.02, with a
standard error of 0.07 ([`descriptive/the_bet.py`](../descriptive/the_bet.py)). Hence 1.5%, and the
first line cut if that scenario is declared. We add on results, never on price.

## History of this entry

The first draft, written earlier on 24 November 2026, did not mention the PTC deal. An AI review
pointed it out. This version replaces it.

25 November 2026: an outside review asked how free cash flow was defined. The version of the day
before used a figure that the data vendor calculates itself (€5.37bn, a yield of 4.0%, and growth
of about 7% a year), and for ABB it set a cash flow in dollars against a market value in francs
(1.7%; Eaton 2.4%). The three are now measured from their own cash-flow statements and valued on
the same day. Schneider remains the cheapest of the three on cash flow, by less than we first
wrote.

## Sources

Company releases of 5, 16 and 19 October and 17 November 2026; accounts and prices from Yahoo
Finance at 20 November 2026; press reports on the deal (October 2026); our calculations. Every
figure will be done again on FactSet before an order is placed.
