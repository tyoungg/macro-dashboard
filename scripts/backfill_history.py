import os
import pandas as pd
import numpy as np
import requests
import yfinance as yf
from io import StringIO
from datetime import datetime, timedelta
import sys

# Add the project root to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.regime import classify

def fetch_fred_history(series_id, start_date):
    end_date = datetime.today().strftime('%Y-%m-%d')
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start_date}&coed={end_date}"
    response = requests.get(url)
    if response.status_code == 200:
        df = pd.read_csv(StringIO(response.text), index_col=0, parse_dates=True)
        # Handle non-numeric and fill missing
        df = df.apply(pd.to_numeric, errors='coerce').ffill().bfill()
        return df
    return pd.DataFrame()

def fetch_treasury_auctions_history():
    # Fetch enough auctions to cover 2024-2025
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query?filter=security_type:in:(Note,Bond)&limit=500&sort=-auction_date"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('data', [])
    return []

def get_sp500_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))
        df = tables[0]
        return df['Symbol'].tolist()
    except:
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "MA", "PG"]

def main():
    print("Starting Backfill...")
    start_history = "2023-01-01" # Earlier to allow for 200DMA and 3m lookbacks

    # 1. Fetch all required data
    print("Fetching FRED data...")
    fred_series = {
        "DGS10": "10Y Treasury Yield",
        "THREEFYTP10": "10Y Term Premium",
        "T10Y2Y": "2s10s Yield Curve",
        "WALCL": "Fed Balance Sheet",
        "WRESBAL": "Bank Reserves",
        "BAMLH0A0HYM2": "High Yield Credit Spread",
        "MORTGAGE30US": "30Y Mortgage Rate",
        "DFII10": "10Y Real Yield"
    }

    fred_data = {}
    for sid in fred_series:
        print(f"  Fetching {sid}...")
        fred_data[sid] = fetch_fred_history(sid, start_history)

    print("Fetching Yahoo Finance data...")
    tickers = ["GC=F", "KRE", "SPY"]
    sp500_tickers = get_sp500_tickers()[:50]
    tickers.extend(sp500_tickers)

    # Yahoo download can return multi-index or simple index depending on version and number of tickers
    yf_raw = yf.download(tickers, start=start_history, progress=False)
    yf_data = yf_raw['Close']
    yf_data = yf_data.ffill().bfill()

    print("Fetching Treasury Auctions...")
    auctions = fetch_treasury_auctions_history()
    auc_df = pd.DataFrame(auctions)
    auc_df['auction_date'] = pd.to_datetime(auc_df['auction_date'])
    auc_df['bid_to_cover_ratio'] = pd.to_numeric(auc_df['bid_to_cover_ratio'], errors='coerce')
    auc_df['high_yield'] = pd.to_numeric(auc_df['high_yield'], errors='coerce')
    auc_df['avg_med_yield'] = pd.to_numeric(auc_df['avg_med_yield'], errors='coerce')
    auc_df = auc_df.sort_values('auction_date', ascending=True)

    # 2. Define Backfill Dates (Business Days from 2024-01-01)
    dates = pd.date_range(start="2024-01-01", end=datetime.today(), freq='B')

    indicators_history = []
    regime_history = []

    print(f"Processing {len(dates)} dates...")

    for d in dates:
        d_str = d.strftime('%Y-%m-%d')
        signals = {}
        row_data = {"Date": d_str}

        # Helper to get value before or at date d
        def get_val(df, date):
            try:
                res = df.loc[:date].iloc[-1]
                return float(res.iloc[0]) if isinstance(res, pd.Series) else float(res)
            except: return None

        # --- 10Y Yield ---
        val = get_val(fred_data["DGS10"], d)
        if val is not None:
            idx = fred_data["DGS10"].index.get_indexer([d], method='pad')[0]
            prev_val = fred_data["DGS10"].iloc[max(0, idx-63)].iloc[0]
            change = (val - prev_val) * 100
            if change < -25: sig = "Bullish"
            elif change > 25: sig = "Bearish"
            else: sig = "Neutral"
            signals["10Y Treasury Yield"] = (val, sig, "")
            row_data["10Y Treasury Yield"] = val
        else: signals["10Y Treasury Yield"] = (0, "Neutral", ""); row_data["10Y Treasury Yield"] = 0

        # --- 10Y Term Premium ---
        val = get_val(fred_data["THREEFYTP10"], d)
        if val is not None:
            if val < 0: sig = "Bullish"
            elif val > 0.50: sig = "Bearish"
            else: sig = "Neutral"
            signals["10Y Term Premium"] = (val, sig, "")
            row_data["10Y Term Premium"] = val
        else: signals["10Y Term Premium"] = (0, "Neutral", ""); row_data["10Y Term Premium"] = 0

        # --- 2s10s Yield Curve ---
        val = get_val(fred_data["T10Y2Y"], d)
        y10_val = get_val(fred_data["DGS10"], d)
        if val is not None and y10_val is not None:
            idx = fred_data["T10Y2Y"].index.get_indexer([d], method='pad')[0]
            prev_val = fred_data["T10Y2Y"].iloc[max(0, idx-21)].iloc[0]
            y10_idx = fred_data["DGS10"].index.get_indexer([d], method='pad')[0]
            y10_prev = fred_data["DGS10"].iloc[max(0, y10_idx-21)].iloc[0]

            steepening = val > prev_val
            ten_year_down = y10_val < y10_prev
            if steepening and ten_year_down: sig = "Bullish"
            elif steepening and not ten_year_down: sig = "Bearish"
            else: sig = "Neutral"
            signals["2s10s Yield Curve"] = (val, sig, "")
            row_data["2s10s Yield Curve"] = val
        else: signals["2s10s Yield Curve"] = (0, "Neutral", ""); row_data["2s10s Yield Curve"] = 0

        # --- Fed Balance Sheet ---
        val = get_val(fred_data["WALCL"], d)
        if val is not None:
            idx = fred_data["WALCL"].index.get_indexer([d], method='pad')[0]
            prev_val = fred_data["WALCL"].iloc[max(0, idx-4)].iloc[0]
            change = val - prev_val
            if change > 0: sig = "Bullish"
            elif change < 0: sig = "Bearish"
            else: sig = "Neutral"
            signals["Fed Balance Sheet"] = (val, sig, "")
            row_data["Fed Balance Sheet"] = val
        else: signals["Fed Balance Sheet"] = (0, "Neutral", ""); row_data["Fed Balance Sheet"] = 0

        # --- Bank Reserves ---
        val = get_val(fred_data["WRESBAL"], d)
        if val is not None:
            idx = fred_data["WRESBAL"].index.get_indexer([d], method='pad')[0]
            prev_val = fred_data["WRESBAL"].iloc[max(0, idx-4)].iloc[0]
            change_b = (val - prev_val) / 1000
            if change_b > 50: sig = "Bullish"
            elif change_b < -50: sig = "Bearish"
            else: sig = "Neutral"
            signals["Bank Reserves"] = (val, sig, "")
            row_data["Bank Reserves"] = val
        else: signals["Bank Reserves"] = (0, "Neutral", ""); row_data["Bank Reserves"] = 0

        # --- Treasury Auctions ---
        try:
            rel_aucs = auc_df[auc_df['auction_date'] <= d]
            auc_10y = rel_aucs[(rel_aucs['security_term'] == '10-Year') & (rel_aucs['security_type'] == 'Note')].iloc[-1]
            auc_30y = rel_aucs[(rel_aucs['security_term'] == '30-Year') & (rel_aucs['security_type'] == 'Bond')].iloc[-1]

            btc_10y = float(auc_10y['bid_to_cover_ratio'])
            tail_10y = (float(auc_10y['high_yield']) - float(auc_10y['avg_med_yield'])) * 100
            btc_30y = float(auc_30y['bid_to_cover_ratio'])
            tail_30y = (float(auc_30y['high_yield']) - float(auc_30y['avg_med_yield'])) * 100

            avg_btc = (btc_10y + btc_30y) / 2
            max_tail = max(tail_10y, tail_30y)

            if max_tail <= 0 and avg_btc > 2.5: sig = "Bullish"
            elif max_tail > 1.0 or avg_btc < 2.2: sig = "Bearish"
            else: sig = "Neutral"
            signals["Treasury Auctions"] = (avg_btc, sig, "")
            row_data["Treasury Auctions"] = avg_btc
        except: signals["Treasury Auctions"] = (0, "Neutral", ""); row_data["Treasury Auctions"] = 0

        # --- High Yield Credit Spread ---
        val = get_val(fred_data["BAMLH0A0HYM2"], d)
        if val is not None:
            idx = fred_data["BAMLH0A0HYM2"].index.get_indexer([d], method='pad')[0]
            prev_val = fred_data["BAMLH0A0HYM2"].iloc[max(0, idx-21)].iloc[0]
            change_bps = (val - prev_val) * 100
            level_bps = val * 100
            if level_bps < 350 and change_bps < 0: sig = "Bullish"
            elif level_bps > 450 or change_bps > 50: sig = "Bearish"
            else: sig = "Neutral"
            signals["High Yield Credit Spread"] = (val, sig, "")
            row_data["High Yield Credit Spread"] = val
        else: signals["High Yield Credit Spread"] = (0, "Neutral", ""); row_data["High Yield Credit Spread"] = 0

        # --- Bank Stress ---
        try:
            kre_val = float(yf_data["KRE"].loc[:d].iloc[-1])
            spy_val = float(yf_data["SPY"].loc[:d].iloc[-1])
            idx_k = yf_data.index.get_indexer([d], method='pad')[0]
            kre_prev = float(yf_data["KRE"].iloc[max(0, idx_k-21)])
            spy_prev = float(yf_data["SPY"].iloc[max(0, idx_k-21)])

            kre_ret = (kre_val / kre_prev) - 1
            spy_ret = (spy_val / spy_prev) - 1
            rel_perf = (kre_ret - spy_ret) * 100
            if rel_perf > 0: sig = "Bullish"
            elif rel_perf < -5: sig = "Bearish"
            else: sig = "Neutral"
            signals["Bank Stress"] = (rel_perf, sig, "")
            row_data["Bank Stress"] = rel_perf
        except: signals["Bank Stress"] = (0, "Neutral", ""); row_data["Bank Stress"] = 0

        # --- 30Y Mortgage Rate ---
        val = get_val(fred_data["MORTGAGE30US"], d)
        if val is not None:
            idx = fred_data["MORTGAGE30US"].index.get_indexer([d], method='pad')[0]
            prev_val = fred_data["MORTGAGE30US"].iloc[max(0, idx-13)].iloc[0]
            change_bps = (val - prev_val) * 100
            if change_bps < -30: sig = "Bullish"
            elif change_bps > 30: sig = "Bearish"
            else: sig = "Neutral"
            signals["30Y Mortgage Rate"] = (val, sig, "")
            row_data["30Y Mortgage Rate"] = val
        else: signals["30Y Mortgage Rate"] = (0, "Neutral", ""); row_data["30Y Mortgage Rate"] = 0

        # --- Equity Breadth ---
        try:
            above_count = 0
            valid_count = 0
            idx_d = yf_data.index.get_indexer([d], method='pad')[0]
            for t in sp500_tickers:
                try:
                    price = float(yf_data[t].iloc[idx_d])
                    if idx_d >= 200:
                        dma200 = yf_data[t].iloc[idx_d-200:idx_d].mean()
                        if not np.isnan(price) and not np.isnan(dma200):
                            valid_count += 1
                            if price > dma200: above_count += 1
                except: continue

            if valid_count > 0:
                pct = (above_count / valid_count) * 100
                if pct > 65: sig = "Bullish"
                elif pct < 40: sig = "Bearish"
                else: sig = "Neutral"
            else:
                pct = 0; sig = "Neutral"
            signals["Equity Breadth"] = (pct, sig, "")
            row_data["Equity Breadth"] = pct
        except: signals["Equity Breadth"] = (0, "Neutral", ""); row_data["Equity Breadth"] = 0

        # --- Gold vs Real Rates ---
        try:
            gold_val = float(yf_data["GC=F"].loc[:d].iloc[-1])
            idx_g = yf_data.index.get_indexer([d], method='pad')[0]
            gold_prev = float(yf_data["GC=F"].iloc[max(0, idx_g-21)])
            gold_change = (gold_val / gold_prev) - 1

            ry_val = get_val(fred_data["DFII10"], d)
            idx_ry = fred_data["DFII10"].index.get_indexer([d], method='pad')[0]
            ry_prev = fred_data["DFII10"].iloc[max(0, idx_ry-21)].iloc[0]
            ry_change = ry_val - ry_prev

            if gold_change > 0 and ry_change < 0: sig = "Bullish"
            elif gold_change < 0 and ry_change > 0: sig = "Bearish"
            else: sig = "Neutral"
            signals["Gold vs Real Rates"] = (gold_val, sig, "")
            row_data["Gold vs Real Rates"] = gold_val
        except: signals["Gold vs Real Rates"] = (0, "Neutral", ""); row_data["Gold vs Real Rates"] = 0

        # --- Regime Classification ---
        regime = classify(signals)
        regime_history.append({
            "Date": d_str,
            "Regime": regime,
            "Bearish_Count": [v[1] for v in signals.values()].count("Bearish"),
            "Bullish_Count": [v[1] for v in signals.values()].count("Bullish")
        })
        indicators_history.append(row_data)

    # 3. Save History
    ih_df = pd.DataFrame(indicators_history)
    rh_df = pd.DataFrame(regime_history)

    ih_df.to_csv("data/history/indicators_history.csv", index=False)
    rh_df.to_csv("data/history/regime_history.csv", index=False)

    print("Backfill Complete!")

if __name__ == "__main__":
    main()
