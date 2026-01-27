import pandas as pd

def thirty_year_mortgage(df):
    """
    Metric: Level and 3-month change
    Signal: Bullish if down > 30 bps, Bearish if up > 30 bps
    """
    if df.empty: return 0, "Neutral", "No data"

    current_val = df.iloc[-1].iloc[0]
    # MORTGAGE30US is weekly
    prev_val = df.iloc[-13].iloc[0] if len(df) >= 13 else df.iloc[0].iloc[0]
    change = (current_val - prev_val) * 100 # in bps

    if change < -30:
        signal = "Bullish"
        explanation = f"Mortgage rates down {abs(change):.0f} bps over 3m, housing tailwind"
    elif change > 30:
        signal = "Bearish"
        explanation = f"Mortgage rates up {change:.0f} bps over 3m, housing headwind"
    else:
        signal = "Neutral"
        explanation = f"Mortgage rates stable ({change:+.0f} bps over 3m)"

    return current_val, signal, explanation
