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

def get_fed_balance_sheet():
    df = fetch_fred_data("WALCL", 60)
    if df.empty:
        return {"indicator": "Fed Balance Sheet", "signal": "Neutral", "explanation": "No data", "value": 0}

    current_val = float(df.iloc[-1].iloc[0])
    prev_val = float(df.iloc[-5].iloc[0]) if len(df) >= 5 else float(df.iloc[0].iloc[0])
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

    return {
        "indicator": "Fed Balance Sheet",
        "value": round(current_val, 0),
        "weekly_change": round(change, 0),
        "signal": signal,
        "explanation": explanation,
        "last_updated": df.index[-1].strftime("%Y-%m-%d"),
        "source": "FRED"
    }

if __name__ == "__main__":
    print(get_fed_balance_sheet())
