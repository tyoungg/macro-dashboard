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

if __name__ == "__main__":
    test_logic()
