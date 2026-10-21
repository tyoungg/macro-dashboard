import os
import pandas as pd

def get_last_known_history(indicator_name):
    """
    Looks up the most recent valid (non-null and non-zero unless legitimate)
    historical entry for indicator_name from data/history/indicators_history.csv.
    Returns (value, date_str).
    """
    path = "data/history/indicators_history.csv"
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if indicator_name in df.columns:
                valid = df.dropna(subset=[indicator_name])
                # Filter out zeroes except for 2s10s Yield Curve where 0.0 can be a valid spread
                if indicator_name != "2s10s Yield Curve":
                    valid = valid[valid[indicator_name] != 0]
                if not valid.empty:
                    last_row = valid.iloc[-1]
                    val = float(last_row[indicator_name])
                    date_str = str(last_row["Date"])
                    return val, date_str
        except Exception:
            pass
    return None, None
