import pandas as pd
import requests
# io and datetime already imported in previous step for term_premium,
# but each file is standalone.
from io import StringIO
from datetime import datetime, timedelta
from indicators.utils import get_last_known_history

SERIES_ID = "DGS10"
LOOKBACK_DAYS = 120

def fetch_fred_data(series_id, days):
    end = datetime.today()
    start = end - timedelta(days=days)
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start.strftime('%Y-%m-%d')}&coed={end.strftime('%Y-%m-%d')}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            text = response.text
            if text.lstrip().startswith("<") or "<html" in text[:200].lower():
                return pd.DataFrame()
            df = pd.read_csv(StringIO(text), index_col=0, parse_dates=True)
            # Handle non-numeric
            df = df.apply(pd.to_numeric, errors='coerce').dropna()
            return df
    except Exception:
        pass
    return pd.DataFrame()

def get_yield_10y():
    df = fetch_fred_data(SERIES_ID, LOOKBACK_DAYS)
    if df.empty:
        val, date_str = get_last_known_history("10Y Treasury Yield")
        if val is not None:
            return {
                "indicator": "10Y Treasury Yield",
                "value": round(val, 3),
                "weekly_change_bps": 0.0,
                "signal": "Neutral",
                "explanation": f"Latest cached value: {val:.2f}%",
                "last_updated": date_str,
                "source": f"FRED (Cached: {date_str})"
            }
        return {"indicator": "10Y Treasury Yield", "signal": "Neutral", "explanation": "No data", "value": None}

    current_val = float(df.iloc[-1].iloc[0])
    # 3 months change
    prev_val = float(df.iloc[-63].iloc[0]) if len(df) >= 63 else float(df.iloc[0].iloc[0])
    change = (current_val - prev_val) * 100 # bps

    # Weekly change for metadata
    weekly_prior = float(df.iloc[-5].iloc[0]) if len(df) >= 5 else current_val
    weekly_delta = (current_val - weekly_prior) * 100

    if change < -25:
        signal = "Bullish"
        explanation = f"Rates down {abs(change):.1f}bps over 3m, easing pressure"
    elif change > 25:
        signal = "Bearish"
        explanation = f"Rates up {change:.1f}bps over 3m, tightening pressure"
    else:
        signal = "Neutral"
        explanation = f"Rates stable ({change:+.1f}bps over 3m)"

    return {
        "indicator": "10Y Treasury Yield",
        "value": round(current_val, 3),
        "weekly_change_bps": round(weekly_delta, 1),
        "signal": signal,
        "explanation": explanation,
        "last_updated": df.index[-1].strftime("%Y-%m-%d"),
        "source": "FRED"
    }

if __name__ == "__main__":
    print(get_yield_10y())
