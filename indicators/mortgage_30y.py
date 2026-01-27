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

def get_mortgage_30y():
    df = fetch_fred_data("MORTGAGE30US", 120)
    if df.empty:
        return {"indicator": "30Y Mortgage Rate", "signal": "Neutral", "explanation": "No data", "value": 0}

    current_val = float(df.iloc[-1].iloc[0])
    # 3 months is ~13 weeks
    prev_val = float(df.iloc[-13].iloc[0]) if len(df) >= 13 else float(df.iloc[0].iloc[0])
    change_bps = (current_val - prev_val) * 100

    if change_bps < -30:
        signal = "Bullish"
        explanation = f"Mortgage rates down {abs(change_bps):.0f} bps over 3m, housing tailwind"
    elif change_bps > 30:
        signal = "Bearish"
        explanation = f"Mortgage rates up {change_bps:.0f} bps over 3m, housing headwind"
    else:
        signal = "Neutral"
        explanation = f"Mortgage rates stable ({change_bps:+.0f} bps over 3m)"

    return {
        "indicator": "30Y Mortgage Rate",
        "value": round(current_val, 2),
        "signal": signal,
        "explanation": explanation,
        "last_updated": df.index[-1].strftime("%Y-%m-%d"),
        "source": "FRED (Freddie Mac)"
    }

if __name__ == "__main__":
    print(get_mortgage_30y())
