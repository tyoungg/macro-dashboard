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

def get_yield_curve():
    df_2s10s = fetch_fred_data("T10Y2Y", 60)
    df_10y = fetch_fred_data("DGS10", 60)

    if df_2s10s.empty or df_10y.empty:
        return {"indicator": "2s10s Yield Curve", "signal": "Neutral", "explanation": "No data", "value": 0}

    current_spread = float(df_2s10s.iloc[-1].iloc[0])
    prev_spread = float(df_2s10s.iloc[-21].iloc[0]) if len(df_2s10s) >= 21 else float(df_2s10s.iloc[0].iloc[0])

    current_10y = float(df_10y.iloc[-1].iloc[0])
    prev_10y = float(df_10y.iloc[-21].iloc[0]) if len(df_10y) >= 21 else float(df_10y.iloc[0].iloc[0])

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

    return {
        "indicator": "2s10s Yield Curve",
        "value": round(current_spread, 3),
        "signal": signal,
        "explanation": explanation,
        "last_updated": df_2s10s.index[-1].strftime("%Y-%m-%d"),
        "source": "FRED"
    }

if __name__ == "__main__":
    print(get_yield_curve())
