import pandas as pd
import requests
# io and datetime already imported in previous step for term_premium,
# but each file is standalone.
from io import StringIO
from datetime import datetime, timedelta

SERIES_ID = "DGS10"
LOOKBACK_DAYS = 120

def fetch_fred_data(series_id, days):
    end = datetime.today()
    start = end - timedelta(days=days)
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start.strftime('%Y-%m-%d')}&coed={end.strftime('%Y-%m-%d')}"
    response = requests.get(url)
    if response.status_code == 200:
        df = pd.read_csv(StringIO(response.text), index_col=0, parse_dates=True)
        # Handle non-numeric
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        return df
    return pd.DataFrame()

def get_yield_10y():
    df = fetch_fred_data(SERIES_ID, LOOKBACK_DAYS)
    if df.empty:
        return {"indicator": "10Y Treasury Yield", "signal": "Neutral", "explanation": "No data", "value": 0}

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
