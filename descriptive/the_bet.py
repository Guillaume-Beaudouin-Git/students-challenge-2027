"""The relative bet of the application file: against the developed-equity index, half the weight in
the six largest AI names and six times the weight in regulated electricity networks.

Descriptive, on public data, written on 24 November 2026 and corrected the same night after a
review that asked for the unfavourable periods, the days after the cut-off, the range of the
valuation arithmetic and the same test on the networks. Not pre-registered.

The six: NVIDIA, Microsoft, Alphabet, Amazon, Broadcom, Meta, weighted as in the iShares MSCI World
ETF today. Four of them buy the AI build-out (Microsoft, Alphabet, Amazon, Meta); two sell it
(NVIDIA, Broadcom). Applying today's index weights to the past overstates their past weight, hence
the past cost of the bet, and understates its gain in the autumn of 2026, when their weight was higher.
Networks: eight developed-market companies whose business is regulated electricity networks and
which, on our reading of their reports, own no coal-fired plant, equally weighted, in dollars:
Exelon, Consolidated Edison, Eversource, National Grid, Terna, Redeia, E.ON, Hydro One. Three
network-heavy utilities with coal-fired generation are left out (American Electric Power, PPL,
Fortis); one line of the output shows the basket with them in.
Index: iShares MSCI World ETF (URTH). Total returns from adjusted closes, Yahoo Finance; company
cash flows from Yahoo Finance (trailing twelve months and quarters); ten-year Treasury yield from
FRED (DGS10, fetched with curl).

Our weights: the six at half their index weight; three network lines of 1.5% of the portfolio, 15% of
a 30% equity sleeve, against 2.5% for all utilities in the index. The bet, in points of the equity
sleeve: (our weight - index weight) x (basket return - index return), summed over the two baskets.
All headline figures stop at the close of 20 November 2026; what happened after is printed apart.

    python3 the_bet.py > outputs/the_bet.txt
"""
import io
import json
import subprocess
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

CUT = "2026-11-20"
SIX = {"NVDA": 5.2333, "MSFT": 4.0961, "GOOGL": 1.8284 + 1.4446, "AMZN": 2.5866, "AVGO": 1.6395, "META": 1.5020}   # % of URTH
BUYERS, SELLERS = ["MSFT", "GOOGL", "AMZN", "META"], ["NVDA", "AVGO"]
NETWORKS = {"EXC": "USD", "ED": "USD", "ES": "USD", "NG.L": "GBP", "TRN.MI": "EUR", "RED.MC": "EUR", "EOAN.DE": "EUR", "H.TO": "CAD"}
LEFT_OUT = {"AEP": "USD", "PPL": "USD", "FTS.TO": "CAD"}
W_SIX = sum(SIX.values()) / 100            # 18.3% of the index
W_UTILITIES_INDEX = 0.025                  # all utilities in the index (sector weights of URTH)
W_SIX_OURS, W_NETWORKS_OURS = W_SIX / 2, 4.5 / 30
ACTIVE_SIX, ACTIVE_NET = W_SIX_OURS - W_SIX, W_NETWORKS_OURS - W_UTILITIES_INDEX
EQUITY_SLEEVE = 0.30
R, G_TERMINAL, YEARS = 0.085, 0.025, 10    # the reverse discounted cash flow of the stock example


def adj(ticker: str, start: str = "2014-12-20") -> pd.Series:
    df = yf.download(ticker, start=start, end="2026-11-26", auto_adjust=False, progress=False, threads=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df["Adj Close"].dropna()


def ols(y: np.ndarray, X: np.ndarray):
    """Coefficients and standard errors of y on X (X already holds the constant)."""
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - X @ b
    cov = resid @ resid / (len(y) - X.shape[1]) * np.linalg.inv(X.T @ X)
    return b, np.sqrt(np.diag(cov))


fx = {"GBP": adj("GBPUSD=X"), "EUR": adj("EURUSD=X"), "CAD": adj("CADUSD=X")}
px = {t: adj(t) for t in list(SIX) + ["URTH"]}
for t, ccy in {**NETWORKS, **LEFT_OUT, "SU.PA": "EUR"}.items():
    s = adj(t)
    px[t] = s if ccy == "USD" else (s * fx[ccy].reindex(s.index).ffill()).dropna()
full = pd.DataFrame(px).ffill()
ret_all = full.pct_change()
w6 = pd.Series(SIX) / sum(SIX.values())
six_all = (ret_all[list(SIX)] * w6).sum(axis=1)
net_all = ret_all[list(NETWORKS)].mean(axis=1)            # the mean of the names listed at the time
idx_all = ret_all["URTH"]
last_close = full.index[-1]
six, net, idx = six_all.loc[:CUT], net_all.loc[:CUT], idx_all.loc[:CUT]
out = {"weights_%_of_sleeve": {"six_ours": round(W_SIX_OURS * 100, 2), "six_index": round(W_SIX * 100, 2), "networks_ours": round(W_NETWORKS_OURS * 100, 1), "utilities_index": W_UTILITIES_INDEX * 100},
       "active_weights_points_of_sleeve": {"six": round(ACTIVE_SIX * 100, 2), "networks": round(ACTIVE_NET * 100, 2)}}
print("weights, % of the equity sleeve:", out["weights_%_of_sleeve"], "| active:", out["active_weights_points_of_sleeve"])


def total(series: pd.Series, a: str, b: str) -> float:
    return float((1 + series.loc[a:b].iloc[1:]).prod() - 1)


def bet(a: str, b: str, s6=six_all, sn=net_all, si=idx_all) -> dict:
    r6, rn, ri = total(s6, a, b), total(sn, a, b), total(si, a, b)
    tilt = ACTIVE_SIX * (r6 - ri) + ACTIVE_NET * (rn - ri)
    return {"six_%": round(r6 * 100, 1), "networks_%": round(rn * 100, 1), "index_%": round(ri * 100, 1),
            "bet_points_of_sleeve": round(tilt * 100, 2), "bet_%_of_portfolio": round(tilt * EQUITY_SLEEVE * 100, 2)}


PERIODS = {"2023": ("2022-12-30", "2023-12-29"), "2024": ("2023-12-29", "2024-12-31"), "2025": ("2024-12-31", "2025-12-31"),
           "2026 to 20 Nov": ("2025-12-31", CUT), "oil shock, 27 Feb - 31 Mar 2026": ("2026-02-27", "2026-03-31"),
           "between the two shocks, 31 Mar - 6 Oct 2026": ("2026-03-31", "2026-10-06"),
           "AI correction, 6 Oct - 20 Nov 2026": ("2026-10-06", CUT)}
out["periods"] = {name: bet(a, b) for name, (a, b) in PERIODS.items()}
print(f"\n{'period':46s} {'six':>8s} {'networks':>9s} {'index':>8s} {'bet, pts of sleeve':>19s} {'% of portfolio':>15s}")
for name, v in out["periods"].items():
    print(f"{name:46s} {v['six_%']:+7.1f}% {v['networks_%']:+8.1f}% {v['index_%']:+7.1f}% {v['bet_points_of_sleeve']:+18.2f} {v['bet_%_of_portfolio']:+14.2f}")
out["with_the_three_left_out_networks_%"] = {name: round(total(ret_all[list(NETWORKS) + list(LEFT_OUT)].mean(axis=1), a, b) * 100, 1) for name, (a, b) in PERIODS.items()}
print("networks with AEP, PPL and Fortis put back:", out["with_the_three_left_out_networks_%"])

# after the cut-off: what the bet did on the sessions that followed 20 November
after = {str(d.date()): {"six_%": round(float(six_all.loc[d]) * 100, 1), "networks_%": round(float(net_all.loc[d]) * 100, 1), "index_%": round(float(idx_all.loc[d]) * 100, 1),
                         "bet_%_of_portfolio": round(float(ACTIVE_SIX * (six_all.loc[d] - idx_all.loc[d]) + ACTIVE_NET * (net_all.loc[d] - idx_all.loc[d])) * EQUITY_SLEEVE * 100, 2)}
         for d in full.index[full.index > pd.Timestamp(CUT)]}
out["after_the_cut_off_by_day"] = after
out["ai_correction_to_last_close"] = {"last_close": str(last_close.date()), **bet("2026-10-06", str(last_close.date()))}
print("\nafter the cut-off, day by day:", after)
print("AI correction measured to the last close available:", out["ai_correction_to_last_close"])

# the bet over every window of 63 sessions, since 2016 and since 2023, in % of the portfolio
active = (ACTIVE_SIX * (six - idx) + ACTIVE_NET * (net - idx)).dropna()
for start in ("2016-01-01", "2023-01-01"):
    roll = (active.loc[start:].rolling(63).sum() * EQUITY_SLEEVE * 100).dropna()
    out[f"windows_of_63_sessions_since_{start[:4]}_%_of_portfolio"] = {
        "worst": round(float(roll.min()), 2), "worst_window_ends": str(roll.idxmin().date()), "best": round(float(roll.max()), 2), "median": round(float(roll.median()), 2),
        "5th_percentile": round(float(roll.quantile(0.05)), 2), "95th_percentile": round(float(roll.quantile(0.95)), 2), "share_of_windows_that_lose_%": round(float((roll < 0).mean()) * 100)}
    print(f"\nwindows of 63 sessions since {start[:4]}:", out[f"windows_of_63_sessions_since_{start[:4]}_%_of_portfolio"])

# after each fall of 20% of the six from a high, since 2016: the bet over the next 63 sessions
level = (1 + six.loc["2016-01-01":]).cumprod()
episodes, armed = [], True
peak = level.cummax()
for d in level.index:
    dd = level.loc[d] / peak.loc[d] - 1
    if armed and dd <= -0.20:
        pos = active.index.get_loc(d)
        nxt = active.iloc[pos + 1: pos + 64]
        episodes.append({"date": str(d.date()), "sessions_available": int(len(nxt)), "bet_next_63_sessions_%_of_portfolio": round(float(nxt.sum()) * EQUITY_SLEEVE * 100, 2)})
        armed = False
    if dd == 0:
        armed = True
out["after_a_fall_of_20%_of_the_six"] = episodes
print("\nafter each fall of 20% of the six from a high:", episodes)

# how the bet and the networks move: weekly data
wk_all = (1 + pd.DataFrame({"six": six, "net": net, "idx": idx, "su": ret_all["SU.PA"].loc[:CUT]}).loc["2022-12-30":]).resample("W-FRI").prod() - 1
csv = subprocess.run(["curl", "-s", "--max-time", "40", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10&cosd=2022-12-20&coed=2026-11-25"], capture_output=True, text=True).stdout
y10d = pd.to_numeric(pd.read_csv(io.StringIO(csv), index_col=0, parse_dates=True).iloc[:, 0], errors="coerce").dropna()
d = wk_all.join(y10d.resample("W-FRI").last().diff().rename("dy")).dropna()
d["bet"] = ACTIVE_SIX * (d["six"] - d["idx"]) + ACTIVE_NET * (d["net"] - d["idx"])
d["factor"] = d["six"] - (d["idx"] - W_SIX * d["six"]) / (1 - W_SIX)        # the six less the rest of the index
one = np.ones(len(d))
stats = {"weeks": int(len(d)), "from": str(d.index[0].date())}
b, se = ols(d["bet"].to_numpy(), np.column_stack([one, d["idx"]]))
stats["beta_of_the_bet_to_the_index"] = [round(float(b[1]), 3), round(float(se[1]), 3)]
b, se = ols(d["net"].to_numpy(), np.column_stack([one, d["idx"], d["dy"]]))
stats["networks_%_per_0.10_point_on_the_10y_yield"] = [round(float(b[2]) * 10, 2), round(float(se[2]) * 10, 2)]
b, se = ols(d["net"].to_numpy(), np.column_stack([one, d["idx"], d["factor"]]))
stats["networks_loading_on_the_six_less_the_rest"] = [round(float(b[2]), 2), round(float(se[2]), 2)]
b, se = ols(d["su"].to_numpy(), np.column_stack([one, d["idx"], d["factor"]]))
stats["schneider_loading_on_the_six_less_the_rest"] = [round(float(b[2]), 2), round(float(se[2]), 2)]
d26 = d.loc["2026"]
b, se = ols(d26["net"].to_numpy(), np.column_stack([np.ones(len(d26)), d26["six"]]))
stats["networks_beta_to_the_six_in_2026"] = [round(float(b[1]), 2), round(float(se[1]), 2)]
stats["volatility_2026_%"] = {k: round(float(d26[k].std(ddof=1) * np.sqrt(52)) * 100, 1) for k in ("six", "net", "idx")}
stats["tracking_error_of_the_bet_2026_points_of_sleeve"] = round(float(d26["bet"].std(ddof=1) * np.sqrt(52)) * 100, 2)
corr = out["periods"]["AI correction, 6 Oct - 20 Nov 2026"]
stats["share_of_the_autumn_gain_due_to_lower_market_exposure_%"] = round(stats["beta_of_the_bet_to_the_index"][0] * corr["index_%"] / corr["bet_points_of_sleeve"] * 100)
out["how_it_moves_weekly_since_2023"] = stats
print("\nweekly since 2023 (coefficient, standard error):", stats)
y26 = y10d.loc["2026"]
out["ten_year_yield_%"] = {"31 Mar 2026": float(y10d.loc[:"2026-03-31"].iloc[-1]), "6 Oct 2026": float(y10d.loc[:"2026-10-06"].iloc[-1]), "20 Nov 2026": float(y10d.loc[:CUT].iloc[-1]),
                           "2026 high": float(y26.max()), "2026 high date": str(y26.idxmax().date())}
print("ten-year Treasury yield:", out["ten_year_yield_%"])


# what the six have to deliver: trailing twelve months, and the latest quarter against the same quarter a year before
def row(frame, names):
    for n in names:
        if n in frame.index:
            return frame.loc[n]
    return None


def implied_growth(flow0: float, value: float, r: float = R) -> float:
    if flow0 <= 0:
        return float("nan")
    lo, hi = -0.5, 1.5
    for _ in range(200):
        g = (lo + hi) / 2
        flows = sum(flow0 * (1 + g) ** k / (1 + r) ** k for k in range(1, YEARS + 1))
        terminal = flow0 * (1 + g) ** YEARS * (1 + G_TERMINAL) / (r - G_TERMINAL) / (1 + r) ** YEARS
        lo, hi = (g, hi) if flows + terminal < value else (lo, g)
    return g


rows = {}
for t in SIX:
    tk = yf.Ticker(t)
    ttm, q, inc = tk.ttm_cashflow, tk.quarterly_cashflow, tk.ttm_income_stmt
    g = lambda names, frame=ttm: (lambda r_: float(r_.iloc[0]) if r_ is not None and pd.notna(r_.iloc[0]) else float("nan"))(row(frame, names))
    qd = [c for c in q.columns]
    latest = qd[0]
    year_before = min(qd, key=lambda c: abs((latest - c).days - 365))
    qv = lambda col, names: float(row(q, names)[col])
    rows[t] = {"cfo": g(["Operating Cash Flow"]), "capex": -g(["Capital Expenditure"]), "dep": g(["Depreciation And Amortization", "Depreciation Amortization Depletion"]),
               "sbc": g(["Stock Based Compensation"]), "debt_issued_net": g(["Net Issuance Payments Of Debt"]), "net_income": g(["Net Income", "Net Income Common Stockholders"], inc),
               "latest_quarter": str(latest.date()), "cfo_q": qv(latest, ["Operating Cash Flow"]), "capex_q": -qv(latest, ["Capital Expenditure"]),
               "quarter_a_year_before": str(year_before.date()), "cfo_q_before": qv(year_before, ["Operating Cash Flow"]), "capex_q_before": -qv(year_before, ["Capital Expenditure"]),
               "mcap": float(full[t].loc[:CUT].iloc[-1] / tk.fast_info["lastPrice"] * tk.fast_info["marketCap"])}      # value at the close of 20 November
    print(t, {k: (round(v / 1e9, 1) if isinstance(v, float) else v) for k, v in rows[t].items()})


def cash(names: list) -> dict:
    S = lambda k: float(np.nansum([rows[t][k] for t in names]))
    cfo, capex, mcap = S("cfo"), S("capex"), S("mcap")
    fcf = cfo - capex
    return {"operating_cash_flow_bn": round(cfo / 1e9), "capex_bn": round(capex / 1e9), "free_cash_flow_bn": round(fcf / 1e9), "depreciation_bn": round(S("dep") / 1e9),
            "net_income_bn": round(S("net_income") / 1e9), "stock_based_compensation_bn": round(S("sbc") / 1e9), "debt_issued_net_bn": round(S("debt_issued_net") / 1e9),
            "market_value_bn": round(mcap / 1e9), "capex_over_cfo_%": round(capex / cfo * 100, 1), "capex_over_depreciation": round(capex / S("dep"), 2),
            "fcf_yield_%": round(fcf / mcap * 100, 2), "price_to_earnings": round(mcap / S("net_income"), 1),
            "growth_needed_on_free_cash_flow_%": round(implied_growth(fcf, mcap) * 100, 1), "same_at_7.5%_and_9.5%_discount": [round(implied_growth(fcf, mcap, r) * 100, 1) for r in (0.075, 0.095)],
            "growth_needed_on_free_cash_flow_after_stock_pay_%": round(implied_growth(fcf - S("sbc"), mcap) * 100, 1), "growth_needed_on_net_income_%": round(implied_growth(S("net_income"), mcap) * 100, 1),
            "latest_quarter": {"operating_cash_flow_bn": round(S("cfo_q") / 1e9), "capex_bn": round(S("capex_q") / 1e9), "free_cash_flow_bn": round((S("cfo_q") - S("capex_q")) / 1e9)},
            "same_quarter_a_year_before": {"operating_cash_flow_bn": round(S("cfo_q_before") / 1e9), "capex_bn": round(S("capex_q_before") / 1e9), "free_cash_flow_bn": round((S("cfo_q_before") - S("capex_q_before")) / 1e9)}}


out["cash"] = {"per_company": {t: {k: (round(v / 1e9, 1) if isinstance(v, float) else v) for k, v in d_.items()} for t, d_ in rows.items()},
               "the_six": cash(list(SIX)), "four_buyers": cash(BUYERS), "two_sellers": cash(SELLERS)}
for k in ("the_six", "four_buyers", "two_sellers"):
    print(f"\n{k}:", out["cash"][k])
out["returns_buyers_and_sellers_%"] = {name: {"buyers": round(total((ret_all[BUYERS] * w6[BUYERS] / w6[BUYERS].sum()).sum(axis=1), a, b) * 100, 1),
                                               "sellers": round(total((ret_all[SELLERS] * w6[SELLERS] / w6[SELLERS].sum()).sum(axis=1), a, b) * 100, 1)} for name, (a, b) in PERIODS.items()}
print("buyers and sellers:", out["returns_buyers_and_sellers_%"])

# the networks, put to the same test
pe, dy, ncfo, ncapex = [], [], 0.0, 0.0
for t in NETWORKS:
    tk = yf.Ticker(t)
    info = tk.info
    if info.get("trailingPE"): pe.append(float(info["trailingPE"]))
    if info.get("trailingAnnualDividendYield"): dy.append(float(info["trailingAnnualDividendYield"]) * 100)
    ttm = tk.ttm_cashflow
    c1, c2 = row(ttm, ["Operating Cash Flow"]), row(ttm, ["Capital Expenditure"])
    if c1 is not None and c2 is not None and pd.notna(c1.iloc[0]) and pd.notna(c2.iloc[0]):
        rate = 1.0 if NETWORKS[t] == "USD" else float(fx[NETWORKS[t]].loc[:CUT].iloc[-1])
        ncfo += float(c1.iloc[0]) * rate; ncapex += -float(c2.iloc[0]) * rate
y = float(np.median(dy)) / 100
out["networks_valuation"] = {"median_price_to_earnings": round(float(np.median(pe)), 1), "median_dividend_yield_%": round(y * 100, 1), "capex_over_operating_cash_flow_%": round(ncapex / ncfo * 100),
                             "dividend_growth_needed_at_8.5%": round(implied_growth(y, 1.0) * 100, 1), "dividend_growth_needed_at_6.5%": round(implied_growth(y, 1.0, 0.065) * 100, 1),
                             "dividend_yield_less_ten_year_yield_points": round(y * 100 - out["ten_year_yield_%"]["20 Nov 2026"], 2)}
print("\nnetworks:", out["networks_valuation"])
json.dump(out, open("outputs/the_bet.json", "w"), indent=1)

# figure: the two baskets and the index in 2026
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
INK, TEAL, GREY, RED, LIGHT = "#1B2A41", "#0E7C7B", "#9AA5B1", "#B5382A", "#E6EAEE"
plt.rcParams.update({"font.family": ["Avenir Next", "Helvetica Neue", "DejaVu Sans"], "font.size": 7, "axes.edgecolor": GREY, "axes.linewidth": 0.6,
                     "xtick.color": INK, "ytick.color": INK, "text.color": INK, "xtick.major.size": 0, "ytick.major.size": 0, "svg.fonttype": "none"})
lv = (1 + pd.DataFrame({"six": six, "net": net, "idx": idx}).loc["2026-01-01":CUT]).cumprod() * 100
fig, ax = plt.subplots(figsize=(3.45, 1.95))
for a, b in (("2026-02-27", "2026-03-31"), ("2026-10-06", CUT)):
    ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color=LIGHT, linewidth=0)
ax.plot(lv.index, lv["six"], color=RED, linewidth=1.2)
ax.plot(lv.index, lv["net"], color=TEAL, linewidth=1.2)
ax.plot(lv.index, lv["idx"], color=GREY, linewidth=0.9)
ax.axhline(100, color=INK, linewidth=0.5)
last = lv.index[-1]
for col, color, lab in (("six", RED, "Six AI giants"), ("net", TEAL, "Networks"), ("idx", GREY, "MSCI World")):
    ax.text(last + pd.Timedelta(days=5), lv[col].iloc[-1], f"{lab}\n{lv[col].iloc[-1] - 100:+.0f}%".replace("-", "\u2212"), color=color, fontsize=6.4, fontweight="bold", va="center", linespacing=1.1, clip_on=False)
ax.text(pd.Timestamp("2026-03-15"), ax.get_ylim()[1], "oil shock", fontsize=6.2, color=INK, ha="center", va="top")
ax.text(pd.Timestamp("2026-10-29"), ax.get_ylim()[1], "AI correction", fontsize=6.2, color=INK, ha="center", va="top")
ax.set_xlim(lv.index[0], last + pd.Timedelta(days=4))
ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=(1, 4, 7, 10)))
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b"))
ax.grid(axis="y", color=LIGHT, linewidth=0.5)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.subplots_adjust(left=0.09, right=0.775, top=0.97, bottom=0.11)
fig.savefig("figures/fig_bet.svg")
print("figure written")
