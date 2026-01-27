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

def get_credit_spread():
    df = fetch_fred_data("BAMLH0A0HYM2", 60)
    if df.empty:
        return {"indicator": "High Yield Credit Spread", "signal": "Neutral", "explanation": "No data", "value": 0}

    current_val = float(df.iloc[-1].iloc[0])
    prev_val = float(df.iloc[-21].iloc[0]) if len(df) >= 21 else float(df.iloc[0].iloc[0])
    change_bps = (current_val - prev_val) * 100
    level_bps = current_val * 100

    if level_bps < 350 and change_bps < 0:
        signal = "Bullish"
        explanation = f"HY spreads tight ({level_bps:.0f} bps) and compressing"
    elif level_bps > 450 or change_bps > 50:
        signal = "Bearish"
        explanation = f"HY spreads wide ({level_bps:.0f} bps) or widening rapidly (+{change_bps:.0f} bps)"
    else:
        signal = "Neutral"
        explanation = f"HY spreads at {level_bps:.0f} bps, stable"

    return {
        "indicator": "High Yield Credit Spread",
        "value": round(current_val, 2),
        "signal": signal,
        "explanation": explanation,
        "last_updated": df.index[-1].strftime("%Y-%m-%d"),
        "source": "FRED (ICE BofA)"
    }

if __name__ == "__main__":
    print(get_credit_spread())
