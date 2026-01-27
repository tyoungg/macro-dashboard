import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta

# -----------------------------
# Configuration
# -----------------------------
SERIES_ID = "THREEFYTP10"  # NY Fed ACM 10Y Term Premium
LOOKBACK_DAYS = 120       # ~6 months for context
NEUTRAL_UPPER = 0.50      # 50 bps credibility threshold

def fetch_fred_data(series_id, days):
    end = datetime.today()
    start = end - timedelta(days=days)
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start.strftime('%Y-%m-%d')}&coed={end.strftime('%Y-%m-%d')}"
    response = requests.get(url)
    if response.status_code == 200:
        df = pd.read_csv(StringIO(response.text), index_col=0, parse_dates=True)
        df.dropna(inplace=True)
        return df
    return pd.DataFrame()

def get_term_premium():
    """
    Fetches 10Y term premium, evaluates signal,
    and returns a standardized indicator dictionary.
    """
    df = fetch_fred_data(SERIES_ID, LOOKBACK_DAYS)
    if df.empty:
        return {
            "indicator": "10Y Term Premium",
            "value": 0.0,
            "weekly_change": 0.0,
            "signal": "Neutral",
            "explanation": "Data unavailable",
            "last_updated": datetime.today().strftime("%Y-%m-%d"),
            "source": "FRED"
        }

    latest = float(df.iloc[-1].iloc[0])
    prior = float(df.iloc[-5].iloc[0]) if len(df) >= 5 else latest
    delta = latest - prior

    if latest < 0:
        signal = "Bullish"
        explanation = f"Negative term premium ({latest:.2f}%): strong demand for duration"
    elif latest <= NEUTRAL_UPPER:
        signal = "Neutral"
        explanation = f"Moderate term premium ({latest:.2f}%): balanced risk pricing"
    else:
        signal = "Bearish"
        explanation = f"Elevated term premium ({latest:.2f}%): investors demanding credibility compensation"

    return {
        "indicator": "10Y Term Premium",
        "value": round(latest, 3),
        "weekly_change": round(delta, 3),
        "signal": signal,
        "explanation": explanation,
        "last_updated": df.index[-1].strftime("%Y-%m-%d"),
        "source": "NY Fed ACM via FRED"
    }

if __name__ == "__main__":
    result = get_term_premium()
    for k, v in result.items():
        print(f"{k}: {v}")
