import pandas as pd

def ten_year_yield(df):
    """
    Metric: Level and 3-month change
    Signal: Bullish if down > 25bps, Bearish if up > 25bps over 3 months
    """
    if df.empty: return 0, "Neutral", "No data"

    current_val = df.iloc[-1].iloc[0]
    # 3 months is approx 63 trading days
    prev_val = df.iloc[-63].iloc[0] if len(df) >= 63 else df.iloc[0].iloc[0]
    change = (current_val - prev_val) * 100 # in bps

    if change < -25:
        signal = "Bullish"
        explanation = f"Rates down {abs(change):.1f}bps over 3m, easing pressure"
    elif change > 25:
        signal = "Bearish"
        explanation = f"Rates up {change:.1f}bps over 3m, tightening pressure"
    else:
        signal = "Neutral"
        explanation = f"Rates stable ({change:+.1f}bps over 3m)"

    return current_val, signal, explanation

def term_premium(df):
    """
    Metric: ACM / Kim-Wright estimate
    Signal: Bullish < 0, Neutral 0-0.5, Bearish > 0.5
    """
    # Since ACMTP10 might be missing, we handle it
    if df.empty: return 0.25, "Neutral", "Data unavailable, assuming neutral"

    current_val = df.iloc[-1].iloc[0]

    if current_val < 0.00:
        signal = "Bullish"
        explanation = f"Term premium at {current_val:.2f}%, indicating high demand for duration"
    elif current_val > 0.50:
        signal = "Bearish"
        explanation = f"Term premium at {current_val:.2f}%, indicating demand for trust compensation"
    else:
        signal = "Neutral"
        explanation = f"Term premium at {current_val:.2f}%, within normal range"

    return current_val, signal, explanation

def yield_curve_2s10s(df_2s10s, df_10y):
    """
    Metric: Level and steepening source
    Signal: Bullish if Steepening + 10Y down, Bearish if Steepening + 10Y up
    """
    if df_2s10s.empty or df_10y.empty: return 0, "Neutral", "No data"

    current_spread = df_2s10s.iloc[-1].iloc[0]
    prev_spread = df_2s10s.iloc[-21].iloc[0] if len(df_2s10s) >= 21 else df_2s10s.iloc[0].iloc[0]

    current_10y = df_10y.iloc[-1].iloc[0]
    prev_10y = df_10y.iloc[-21].iloc[0] if len(df_10y) >= 21 else df_10y.iloc[0].iloc[0]

    steepening = current_spread > prev_spread
    ten_year_down = current_10y < prev_10y

    if steepening and ten_year_down:
        signal = "Bullish"
        explanation = "Bull steepening (Spread up, 10Y down) - growth friendly"
    elif steepening and not ten_year_down:
        signal = "Bearish"
        explanation = "Bear steepening (Spread up, 10Y up) - credibility concerns"
    else:
        signal = "Neutral"
        explanation = f"Curve at {current_spread:.2f}%, mixed or flattening signal"

    return current_spread, signal, explanation
