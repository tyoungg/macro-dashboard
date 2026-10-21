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

if __name__ == "__main__":
    test_logic()
