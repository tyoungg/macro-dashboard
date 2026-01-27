import pandas as pd

def fed_balance_sheet(df):
    """
    Metric: 4-week trend
    Signal: Bullish if up over 4 weeks, Bearish if down
    """
    if df.empty: return 0, "Neutral", "No data"

    current_val = df.iloc[-1].iloc[0]
    # WALCL is weekly (Wednesday)
    prev_val = df.iloc[-5].iloc[0] if len(df) >= 5 else df.iloc[0].iloc[0]
    change = current_val - prev_val

    if change > 0:
        signal = "Bullish"
        explanation = f"Fed balance sheet expanding (+${change/1000:.1f}B over 4w)"
    elif change < 0:
        signal = "Bearish"
        explanation = f"Fed balance sheet contracting (-${abs(change)/1000:.1f}B over 4w)"
    else:
        signal = "Neutral"
        explanation = "Fed balance sheet flat"

    return current_val, signal, explanation

def bank_reserves(df):
    """
    Metric: Reserve balances, 4-week trend
    Signal: Bullish if up > $50B, Bearish if down > $50B
    """
    if df.empty: return 0, "Neutral", "No data"

    current_val = df.iloc[-1].iloc[0] # In Millions
    prev_val = df.iloc[-5].iloc[0] if len(df) >= 5 else df.iloc[0].iloc[0]
    change = current_val - prev_val # In Millions

    change_b = change / 1000 # In Billions

    if change_b > 50:
        signal = "Bullish"
        explanation = f"Bank reserves up ${change_b:.1f}B over 4w, liquidity easing"
    elif change_b < -50:
        signal = "Bearish"
        explanation = f"Bank reserves down ${abs(change_b):.1f}B over 4w, liquidity tightening"
    else:
        signal = "Neutral"
        explanation = f"Bank reserves stable (${change_b:+.1f}B over 4w)"

    return current_val, signal, explanation
