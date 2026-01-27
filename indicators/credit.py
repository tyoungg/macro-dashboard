import pandas as pd

def hy_credit_spread(df):
    """
    Metric: Level and 1-month change
    Signal: Bullish if < 350 bps and down, Bearish if > 450 bps or up > 50 bps
    """
    if df.empty: return 0, "Neutral", "No data"

    current_val = df.iloc[-1].iloc[0]
    prev_val = df.iloc[-21].iloc[0] if len(df) >= 21 else df.iloc[0].iloc[0]
    change = (current_val - prev_val) * 100 # in bps

    level_bps = current_val * 100

    if level_bps < 350 and change < 0:
        signal = "Bullish"
        explanation = f"HY spreads tight ({level_bps:.0f} bps) and compressing"
    elif level_bps > 450 or change > 50:
        signal = "Bearish"
        explanation = f"HY spreads wide ({level_bps:.0f} bps) or widening rapidly (+{change:.0f} bps)"
    else:
        signal = "Neutral"
        explanation = f"HY spreads at {level_bps:.0f} bps, stable"

    return current_val, signal, explanation

def treasury_auctions(df_10y, df_30y):
    """
    Metric: Tail + bid-to-cover
    Signal: Bullish if No tail + BTC > 2.5, Bearish if Tail > 1bp or BTC < 2.2
    """
    if df_10y.empty or df_30y.empty: return 0, "Neutral", "No data"

    # Latest 10Y auction
    latest_10y = df_10y.iloc[0]
    btc_10y = float(latest_10y['bid_to_cover_ratio'])
    tail_10y = (float(latest_10y['high_yield']) - float(latest_10y['avg_med_yield'])) * 100

    # Latest 30Y auction
    latest_30y = df_30y.iloc[0]
    btc_30y = float(latest_30y['bid_to_cover_ratio'])
    tail_30y = (float(latest_30y['high_yield']) - float(latest_30y['avg_med_yield'])) * 100

    avg_btc = (btc_10y + btc_30y) / 2
    max_tail = max(tail_10y, tail_30y)

    if max_tail <= 0 and avg_btc > 2.5:
        signal = "Bullish"
        explanation = f"Strong auctions: Avg BTC {avg_btc:.2f}, no tail"
    elif max_tail > 1.0 or avg_btc < 2.2:
        signal = "Bearish"
        explanation = f"Weak auctions: Avg BTC {avg_btc:.2f}, max tail {max_tail:.1f}bps"
    else:
        signal = "Neutral"
        explanation = f"Mixed auctions: Avg BTC {avg_btc:.2f}, max tail {max_tail:.1f}bps"

    return avg_btc, signal, explanation
