import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Add the project root to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators.yield_10y import get_yield_10y
from indicators.term_premium import get_term_premium
from indicators.yield_curve import get_yield_curve
from indicators.fed_balance_sheet import get_fed_balance_sheet
from indicators.bank_reserves import get_bank_reserves
from indicators.treasury_auctions import get_treasury_auctions
from indicators.credit_spread import get_credit_spread
from indicators.bank_stress import get_bank_stress
from indicators.mortgage_30y import get_mortgage_30y
from indicators.equity_breadth import get_equity_breadth
from indicators.gold import get_gold_signal

from dashboard.regime import classify, get_regime_emoji
from dashboard.signals import get_signal_color

def main():
    print("Starting Macro Dashboard Update...")

    # 1. Calculate Indicators
    print("Calculating indicators...")
    indicator_results = [
        get_yield_10y(),
        get_term_premium(),
        get_yield_curve(),
        get_fed_balance_sheet(),
        get_bank_reserves(),
        get_treasury_auctions(),
        get_credit_spread(),
        get_bank_stress(),
        get_mortgage_30y(),
        get_equity_breadth(),
        get_gold_signal()
    ]

    # Convert list to dict for classification logic
    signals_dict = {
        res['indicator']: (res.get('value', 0), res['signal'], res['explanation'])
        for res in indicator_results
    }

    # 2. Classify Regime
    regime = classify(signals_dict)
    regime_emoji = get_regime_emoji(regime)
    print(f"Current Regime: {regime} {regime_emoji}")

    # 3. Save Data
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/history", exist_ok=True)
    os.makedirs("charts/history", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    os.makedirs("docs", exist_ok=True)

    # Save a summary of indicators
    results_df = pd.DataFrame(indicator_results)
    results_df.to_csv("data/processed/latest_indicators.csv", index=False)

    # Append to regime history
    regime_history_file = "data/history/regime_history.csv"
    today_str = datetime.now().strftime("%Y-%m-%d")
    regime_entry = pd.DataFrame([{
        "Date": today_str,
        "Regime": regime,
        "Bearish_Count": [res['signal'] for res in indicator_results].count("Bearish"),
        "Bullish_Count": [res['signal'] for res in indicator_results].count("Bullish")
    }])
    if os.path.exists(regime_history_file):
        try:
            rh_df = pd.read_csv(regime_history_file)
            rh_df = pd.concat([rh_df, regime_entry], ignore_index=True).drop_duplicates(subset=['Date'], keep='last')
            rh_df.to_csv(regime_history_file, index=False)
        except:
            regime_entry.to_csv(regime_history_file, index=False)
    else:
        regime_entry.to_csv(regime_history_file, index=False)

    # Append to indicators history
    ind_history_file = "data/history/indicators_history.csv"
    ind_entry_data = {"Date": today_str}
    for res in indicator_results:
        ind_entry_data[res['indicator']] = res.get('value', 0)

    ind_entry = pd.DataFrame([ind_entry_data])
    if os.path.exists(ind_history_file):
        try:
            ih_df = pd.read_csv(ind_history_file)
            ih_df = pd.concat([ih_df, ind_entry], ignore_index=True).drop_duplicates(subset=['Date'], keep='last')
            ih_df.to_csv(ind_history_file, index=False)
        except:
            ind_entry.to_csv(ind_history_file, index=False)
    else:
        ind_entry.to_csv(ind_history_file, index=False)

    # 4. Generate Charts
    print("Generating charts...")
    # Signal Distribution Chart
    plt.figure(figsize=(10, 6))
    counts = results_df['signal'].value_counts()
    color_map = {"Bullish": "green", "Bearish": "red", "Neutral": "yellow"}
    plt.bar(counts.index, counts.values, color=[color_map.get(s, "gray") for s in counts.index])
    plt.title(f"Macro Signals Distribution - {today_str}")
    plt.ylabel("Count")
    plt.savefig("charts/signal_distribution.png")
    plt.savefig("docs/signal_distribution.png")
    plt.close()

    # Individual History Charts
    ih_df = pd.read_csv(ind_history_file)
    ih_df['Date'] = pd.to_datetime(ih_df['Date'])
    ih_df = ih_df.sort_values('Date')

    history_charts = []
    for res in indicator_results:
        ind_name = res['indicator']
        filename = f"{ind_name.lower().replace(' ', '_')}_history.png"
        plt.figure(figsize=(10, 4))
        plt.plot(ih_df['Date'], ih_df[ind_name], marker='o', linestyle='-', color='#2188ff')
        plt.title(f"{ind_name} Trend")
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"charts/history/{filename}")
        plt.savefig(f"docs/{filename}")
        plt.close()
        history_charts.append({"name": ind_name, "file": filename})

    # 5. Build Markdown Report
    print("Building reports...")
    with open("reports/latest.md", "w") as f:
        f.write(f"# Macro Dashboard - {today_str}\n\n")
        f.write(f"## Current Regime: {regime} {regime_emoji}\n\n")
        f.write("### Indicator Summary\n\n")
        f.write("| Indicator | Value | Signal | Explanation | Data Date | Source |\n")
        f.write("|-----------|-------|--------|-------------|-----------|--------|\n")
        for res in indicator_results:
            color = get_signal_color(res['signal'])
            val = res.get('value', 0)
            date = res.get('last_updated', 'N/A')
            f.write(f"| {res['indicator']} | {val} | {color} {res['signal']} | {res['explanation']} | {date} | {res.get('source', 'N/A')} |\n")
        f.write("\n![Signal Distribution](../charts/signal_distribution.png)\n")
        f.write("\n\n*Auto-generated by Macro Dashboard Bot*")

    # 6. Build HTML Pages
    common_style = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }
            nav { margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
            nav a { margin-right: 20px; text-decoration: none; color: #0366d6; font-weight: bold; }
            h1, h2 { border-bottom: 2px solid #eee; padding-bottom: 10px; }
            .regime { font-size: 2em; font-weight: bold; margin: 20px 0; padding: 20px; border-radius: 8px; text-align: center; }
            .regime-EASING { background-color: #e6ffed; color: #22863a; border: 1px solid #34d058; }
            .regime-TIGHT { background-color: #ffeef0; color: #cb2431; border: 1px solid #f97583; }
            .regime-TRANSITION { background-color: #fffdef; color: #735c0f; border: 1px solid #ffea7f; }
            .regime-PRE-STRESS { background-color: #fff5f5; color: #d73a49; border: 2px dashed #cb2431; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { text-align: left; padding: 12px; border-bottom: 1px solid #eee; }
            th { background-color: #f6f8fa; }
            .signal-Bullish { color: #22863a; font-weight: bold; }
            .signal-Bearish { color: #cb2431; font-weight: bold; }
            .signal-Neutral { color: #735c0f; font-weight: bold; }
            img { max-width: 100%; height: auto; margin: 20px 0; border: 1px solid #eee; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 20px; }
            .card { border: 1px solid #eee; border-radius: 8px; padding: 10px; background: #fff; }
            footer { margin-top: 50px; font-size: 0.8em; color: #666; text-align: center; }
        </style>
    """

    nav_html = """
        <nav>
            <a href="index.html">Current Status</a>
            <a href="history.html">Historical Trends</a>
        </nav>
    """

    # Index Page
    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Macro Dashboard</title>
        {common_style}
    </head>
    <body>
        {nav_html}
        <h1>Macro Dashboard</h1>
        <p>Dashboard Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>

        <div class="regime regime-{regime.split(' ')[0]}">
            Current Regime: {regime} {regime_emoji}
        </div>

        <h2>Current Indicators</h2>
        <table>
            <thead>
                <tr><th>Indicator</th><th>Value</th><th>Signal</th><th>Explanation</th><th>Data Date</th><th>Source</th></tr>
            </thead>
            <tbody>
    """
    for res in indicator_results:
        color_emoji = get_signal_color(res['signal'])
        index_html += f"""
                <tr>
                    <td>{res['indicator']}</td>
                    <td>{res.get('value', 0):.2f}</td>
                    <td class="signal-{res['signal']}">{color_emoji} {res['signal']}</td>
                    <td>{res['explanation']}</td>
                    <td>{res.get('last_updated', 'N/A')}</td>
                    <td>{res.get('source', 'N/A')}</td>
                </tr>
        """
    index_html += f"""
            </tbody>
        </table>
        <h2>Signal Distribution</h2>
        <img src="signal_distribution.png" alt="Signal Distribution">
        <footer><p>Auto-generated by Macro Dashboard Bot</p></footer>
    </body></html>
    """
    with open("docs/index.html", "w") as f:
        f.write(index_html)

    # History Page
    history_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Macro History</title>
        {common_style}
    </head>
    <body>
        {nav_html}
        <h1>Historical Trends</h1>
        <p>Last Updated: {today_str}</p>

        <div class="grid">
    """
    for chart in history_charts:
        history_html += f"""
            <div class="card">
                <h3>{chart['name']}</h3>
                <img src="{chart['file']}" alt="{chart['name']} history">
            </div>
        """
    history_html += """
        </div>
        <footer><p>Auto-generated by Macro Dashboard Bot</p></footer>
    </body></html>
    """
    with open("docs/history.html", "w") as f:
        f.write(history_html)

    print("Dashboard Update Complete!")

if __name__ == "__main__":
    main()
