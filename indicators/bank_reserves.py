import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta

def fetch_fred_data(series_id, days):
    end = datetime.today()
    start = end - timedelta(days=days)
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start.strftime('%Y-%m-%d')}&coed={end.strftime('%Y-%m-%d')}"
    response = requests.get(url)
    if response.status_code == 200:
        df = pd.read_csv(StringIO(response.text), index_col=0, parse_dates=True)
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        return df
    return pd.DataFrame()

def get_bank_reserves():
    # Using WRESBAL for weekly reserve balances
    df = fetch_fred_data("WRESBAL", 60)
    if df.empty:
        return {"indicator": "Bank Reserves", "signal": "Neutral", "explanation": "No data", "value": 0}

    current_val = float(df.iloc[-1].iloc[0]) # Millions
    prev_val = float(df.iloc[-5].iloc[0]) if len(df) >= 5 else float(df.iloc[0].iloc[0])
    change_m = current_val - prev_val
    change_b = change_m / 1000

    if change_b > 50:
        signal = "Bullish"
        explanation = f"Bank reserves up ${change_b:.1f}B over 4w, liquidity easing"
    elif change_b < -50:
        signal = "Bearish"
        explanation = f"Bank reserves down ${abs(change_b):.1f}B over 4w, liquidity tightening"
    else:
        signal = "Neutral"
        explanation = f"Bank reserves stable (${change_b:+.1f}B over 4w)"

    return {
        "indicator": "Bank Reserves",
        "value": round(current_val, 0),
        "weekly_change_billions": round(change_b, 1),
        "signal": signal,
        "explanation": explanation,
        "last_updated": df.index[-1].strftime("%Y-%m-%d"),
        "source": "FRED (WRESBAL)"
    }

if __name__ == "__main__":
    import json
    print(json.dumps(get_bank_reserves(), indent=2))
