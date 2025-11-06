"""
Comprehensive test script for Phase 1 module structure.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_module_structure():
    """Test all module imports and structure."""
    print("=" * 60)
    print("PHASE 1 MODULE STRUCTURE TEST")
    print("=" * 60)
    
    tests = []
    
    # Test 1: Config module
    try:
        from src.config import CONFIG, get_bot_token, get_api_keys, get_openai_client
        assert isinstance(CONFIG, dict)
        assert 'pair' in CONFIG
        tests.append(("Config Module", True, ""))
    except Exception as e:
        tests.append(("Config Module", False, str(e)))
    
    # Test 2: Utils module
    try:
        from src.utils import safe_divide, format_time, sanitize_user_input, get_http_session
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 0) == 0.0
        tests.append(("Utils Module", True, ""))
    except Exception as e:
        tests.append(("Utils Module", False, str(e)))
    
    # Test 3: Database module
    try:
        from src.database import init_database, save_signal_to_db, load_recent_signals_from_db
        tests.append(("Database Module", True, ""))
    except Exception as e:
        tests.append(("Database Module", False, str(e)))
    
    # Test 4: Models/State module
    try:
        from src.models import STATS, METRICS, SUBSCRIBED_USERS, SIGNAL_HISTORY
        assert isinstance(STATS, dict)
        assert isinstance(METRICS, dict)
        assert isinstance(SUBSCRIBED_USERS, set)
        tests.append(("Models/State Module", True, ""))
    except Exception as e:
        tests.append(("Models/State Module", False, str(e)))
    
    # Test 5: API module
    try:
        from src.api import fetch_from_twelvedata, fetch_from_alphavantage, fetch_from_binance
        from src.api import fetch_forex_data, fetch_forex_data_parallel
        tests.append(("API Module", True, ""))
    except Exception as e:
        tests.append(("API Module", False, str(e)))
    
    # Test 6: Indicators module
    try:
        from src.indicators import (
            calculate_ta_score, 
            calculate_indicators_parallel,
            get_adaptive_cache_duration,
            get_adaptive_thresholds,
            analyze_volume,
            calculate_confidence
        )
        # Test a simple calculation
        score = calculate_ta_score(30, 0.0001, 25, 30, 25, 28)
        assert 0 <= score <= 100
        tests.append(("Indicators Module", True, ""))
    except Exception as e:
        tests.append(("Indicators Module", False, str(e)))
    
    # Test 7: Placeholder modules exist
    try:
        from src.signals import __all__
        from src.monitoring import __all__
        from src.telegram import __all__
        tests.append(("Placeholder Modules", True, ""))
    except Exception as e:
        tests.append(("Placeholder Modules", False, str(e)))
    
    # Print results
    print("\nTest Results:")
    print("-" * 60)
    all_passed = True
    for name, passed, error in tests:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {name}")
        if not passed:
            print(f"         Error: {error}")
            all_passed = False
    
    print("-" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nModule structure is ready for Phase 1 completion.")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease fix the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = test_module_structure()
    sys.exit(0 if success else 1)


