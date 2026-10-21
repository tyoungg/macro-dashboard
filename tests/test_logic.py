import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from dashboard.regime import classify

def test_logic():
    print("Running tests...")

    # Test Bullish
    signals_bull = {f'I{i}': (0, 'Bullish', '') for i in range(5)}
    assert classify(signals_bull) == "EASING / RISK-ON"
    print("✅ Bullish classification passed")

    # Test Bearish
    signals_bear = {f'I{i}': (0, 'Bearish', '') for i in range(5)}
    assert classify(signals_bear) == "TIGHT / FRAGILE"
    print("✅ Bearish classification passed")

    # Test Pre-Stress (Standard)
    signals_pre = {
        'High Yield Credit Spread': (0, 'Bearish', ''),
        'I2': (0, 'Bearish', ''),
        'I3': (0, 'Bearish', '')
    }
    assert classify(signals_pre) == "PRE-STRESS"
    print("✅ Pre-Stress (Standard) classification passed")

    # Test Pre-Stress Gold Veto
    signals_gold_veto = {
        'Gold vs Real Rates': (0, 'Bullish', ''),
        'High Yield Credit Spread': (0, 'Neutral', ''),
        'Treasury Auctions': (0, 'Neutral', '')
    }
    assert classify(signals_gold_veto) == "PRE-STRESS"
    print("✅ Pre-Stress (Gold Veto) classification passed")

    # Test Transition
    signals_trans = {'I1': (0, 'Bullish', ''), 'I2': (0, 'Bearish', '')}
    assert classify(signals_trans) == "TRANSITION"
    print("✅ Transition classification passed")

    print("All logic tests passed!")

def test_fetch_fred_data_html_response(mocker=None):
    from unittest.mock import patch, MagicMock
    import pandas as pd
    from indicators.yield_10y import fetch_fred_data, get_yield_10y

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<!doctype html><html><body>We'll be back soon!</body></html>"

    with patch("requests.get", return_value=mock_response):
        df = fetch_fred_data("DGS10", 120)
        assert isinstance(df, pd.DataFrame)
        assert df.empty

        result = get_yield_10y()
        assert result["indicator"] == "10Y Treasury Yield"
        assert result["signal"] == "Neutral"
        assert result["explanation"] == "No data"
        assert result["value"] == 0

def test_history_fallback_logic():
    import pandas as pd
    from dashboard.build_dashboard import main
    from unittest.mock import patch

    # Mock indicator results where Equity Breadth failed and returned value 0 with 'No data'
    fake_results = [
        {"indicator": "10Y Treasury Yield", "value": 4.2, "signal": "Neutral", "explanation": "Rates stable", "last_updated": "2026-10-21", "source": "FRED"},
        {"indicator": "10Y Term Premium", "value": 0.5, "signal": "Neutral", "explanation": "Moderate", "last_updated": "2026-10-21", "source": "FRED"},
        {"indicator": "2s10s Yield Curve", "value": 0.3, "signal": "Neutral", "explanation": "Curve", "last_updated": "2026-10-21", "source": "FRED"},
        {"indicator": "Fed Balance Sheet", "value": 6500000, "signal": "Neutral", "explanation": "Flat", "last_updated": "2026-10-21", "source": "FRED"},
        {"indicator": "Bank Reserves", "value": 3000000, "signal": "Neutral", "explanation": "Stable", "last_updated": "2026-10-21", "source": "FRED"},
        {"indicator": "Treasury Auctions", "value": 2.5, "signal": "Neutral", "explanation": "Stable", "last_updated": "2026-10-21", "source": "Treasury"},
        {"indicator": "High Yield Credit Spread", "value": 3.0, "signal": "Neutral", "explanation": "HY spreads", "last_updated": "2026-10-21", "source": "FRED"},
        {"indicator": "Bank Stress", "value": 2.0, "signal": "Neutral", "explanation": "In line", "last_updated": "2026-10-21", "source": "Yahoo"},
        {"indicator": "30Y Mortgage Rate", "value": 6.2, "signal": "Neutral", "explanation": "Stable", "last_updated": "2026-10-21", "source": "FRED"},
        {"indicator": "Equity Breadth", "value": 0, "signal": "Neutral", "explanation": "No data", "last_updated": "2026-10-21", "source": "S&P 500"},
        {"indicator": "Gold vs Real Rates", "value": 4000, "signal": "Neutral", "explanation": "Aligned", "last_updated": "2026-10-21", "source": "Yahoo"}
    ]

    with patch("dashboard.build_dashboard.get_yield_10y", return_value=fake_results[0]), \
         patch("dashboard.build_dashboard.get_term_premium", return_value=fake_results[1]), \
         patch("dashboard.build_dashboard.get_yield_curve", return_value=fake_results[2]), \
         patch("dashboard.build_dashboard.get_fed_balance_sheet", return_value=fake_results[3]), \
         patch("dashboard.build_dashboard.get_bank_reserves", return_value=fake_results[4]), \
         patch("dashboard.build_dashboard.get_treasury_auctions", return_value=fake_results[5]), \
         patch("dashboard.build_dashboard.get_credit_spread", return_value=fake_results[6]), \
         patch("dashboard.build_dashboard.get_bank_stress", return_value=fake_results[7]), \
         patch("dashboard.build_dashboard.get_mortgage_30y", return_value=fake_results[8]), \
         patch("dashboard.build_dashboard.get_equity_breadth", return_value=fake_results[9]), \
         patch("dashboard.build_dashboard.get_gold_signal", return_value=fake_results[10]):

        main()

        ih_df = pd.read_csv("data/history/indicators_history.csv")
        latest_row = ih_df.iloc[-1]

        # Equity Breadth in latest row should equal forward-filled value instead of 0
        assert latest_row["Equity Breadth"] > 0

if __name__ == "__main__":
    test_logic()
