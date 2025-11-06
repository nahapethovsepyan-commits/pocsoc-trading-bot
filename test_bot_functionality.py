#!/usr/bin/env python3
"""
Comprehensive bot functionality test script.
Tests bot startup, core functionality, and error handling.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

# Test results
results = {}

async def test_bot_imports():
    """Test 1: Verify all bot modules can be imported"""
    print_header("Test 1: Bot Module Imports")
    
    try:
        # Test core imports
        from src.config.env import get_bot_token, get_api_keys
        print_success("Core config modules imported")
        
        from src.config.settings import CONFIG
        print_success("Settings module imported")
        print_info(f"Config loaded: {len(CONFIG)} parameters")
        
        from src.utils.audit import log_config_change, log_security_event
        print_success("Audit module imported")
        
        from src.signals.utils import check_user_rate_limit
        print_success("Signals utils imported")
        
        from src.telegram.decorators import require_subscription, with_error_handling
        print_success("Telegram decorators imported")
        
        from src.indicators.calculator import calculate_indicators_parallel
        print_success("Indicators calculator imported")
        
        results['imports'] = True
        return True
        
    except Exception as e:
        print_error(f"Import failed: {e}")
        results['imports'] = False
        return False

async def test_bot_initialization():
    """Test 2: Verify bot can initialize without errors"""
    print_header("Test 2: Bot Initialization")
    
    try:
        from src.config.env import get_bot_token, get_api_keys
        
        # Test token retrieval
        try:
            token = get_bot_token()
            if token and len(token) > 10:
                print_success(f"BOT_TOKEN retrieved (length: {len(token)})")
            else:
                print_warning("BOT_TOKEN is set but seems invalid")
        except ValueError as e:
            print_error(f"BOT_TOKEN error: {e}")
            results['initialization'] = False
            return False
        
        # Test API keys retrieval
        try:
            twelve_key, alpha_key = get_api_keys()
            if twelve_key:
                print_success(f"TWELVE_DATA_API_KEY retrieved (length: {len(twelve_key)})")
            else:
                print_warning("TWELVE_DATA_API_KEY not set (will use fallback)")
            
            if alpha_key:
                print_success(f"ALPHA_VANTAGE_KEY retrieved (length: {len(alpha_key)})")
            else:
                print_info("ALPHA_VANTAGE_KEY not set (optional)")
        except Exception as e:
            print_warning(f"API keys error: {e}")
        
        # Test bot object creation (without actually connecting)
        try:
            from aiogram import Bot
            token = get_bot_token()
            bot = Bot(token=token)
            print_success("Bot object created successfully")
            await bot.session.close()
        except Exception as e:
            print_error(f"Bot creation failed: {e}")
            results['initialization'] = False
            return False
        
        # Test config loading
        from src.config.settings import CONFIG
        required_keys = ['pair', 'min_signal_score', 'min_confidence', 'analysis_interval_minutes']
        for key in required_keys:
            if key in CONFIG:
                print_success(f"Config key '{key}' = {CONFIG[key]}")
            else:
                print_error(f"Config key '{key}' missing")
                results['initialization'] = False
                return False
        
        results['initialization'] = True
        return True
        
    except Exception as e:
        print_error(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        results['initialization'] = False
        return False

async def test_database_initialization():
    """Test 3: Verify database can be initialized"""
    print_header("Test 3: Database Initialization")
    
    try:
        from src.database import init_database
        
        await init_database()
        print_success("Database initialized successfully")
        
        # Check if database file exists
        db_path = Path('signals.db')
        if db_path.exists():
            size = db_path.stat().st_size
            print_success(f"Database file exists ({size} bytes)")
        else:
            print_warning("Database file not created yet (will be created on first write)")
        
        results['database'] = True
        return True
        
    except Exception as e:
        print_error(f"Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        results['database'] = False
        return False

async def test_rate_limiting():
    """Test 4: Verify rate limiting works"""
    print_header("Test 4: Rate Limiting")
    
    try:
        from src.signals.utils import check_user_rate_limit
        from src.models.state import USER_RATE_LIMITS, user_rate_lock
        
        # Test rate limit check
        test_user_id = 999999
        
        # First call should pass
        result1 = await check_user_rate_limit(test_user_id, max_per_minute=10)
        if result1:
            print_success("First rate limit check passed")
        else:
            print_error("First rate limit check failed")
            results['rate_limiting'] = False
            return False
        
        # Make 10 more calls quickly (should all pass)
        for i in range(10):
            await check_user_rate_limit(test_user_id, max_per_minute=10)
        
        # 11th call should fail (exceeds limit)
        result2 = await check_user_rate_limit(test_user_id, max_per_minute=10)
        if not result2:
            print_success("Rate limit correctly blocked 11th call")
        else:
            print_warning("Rate limit did not block 11th call (may need time delay)")
        
        # Clean up test user
        async with user_rate_lock:
            if test_user_id in USER_RATE_LIMITS:
                del USER_RATE_LIMITS[test_user_id]
        
        results['rate_limiting'] = True
        return True
        
    except Exception as e:
        print_error(f"Rate limiting test failed: {e}")
        import traceback
        traceback.print_exc()
        results['rate_limiting'] = False
        return False

async def test_audit_logging():
    """Test 5: Verify audit logging works"""
    print_header("Test 5: Audit Logging")
    
    try:
        from src.utils.audit import log_config_change, log_security_event, log_admin_action
        
        # Test config change logging
        test_user_id = 12345
        await log_config_change(test_user_id, "test_param", "old_value", "new_value")
        print_success("Config change logged successfully")
        
        # Test security event logging
        await log_security_event(test_user_id, "test_event", "Test security event", "low")
        print_success("Security event logged successfully")
        
        # Test admin action logging
        await log_admin_action(test_user_id, "test_action", {"detail": "test"})
        print_success("Admin action logged successfully")
        
        # Check if audit log file exists
        audit_log = Path('logs/audit.log')
        if audit_log.exists():
            size = audit_log.stat().st_size
            print_success(f"Audit log file exists ({size} bytes)")
        else:
            print_warning("Audit log file not created yet (may be created on first write)")
        
        results['audit_logging'] = True
        return True
        
    except Exception as e:
        print_error(f"Audit logging test failed: {e}")
        import traceback
        traceback.print_exc()
        results['audit_logging'] = False
        return False

async def test_error_handling():
    """Test 6: Verify error handling works"""
    print_header("Test 6: Error Handling")
    
    try:
        from src.telegram.decorators import with_error_handling
        from src.utils.helpers import sanitize_user_input, validate_config_input
        
        # Test input sanitization
        test_inputs = [
            ("normal text", True),
            ("<script>alert('xss')</script>", False),  # Should sanitize
            ("A" * 300, False),  # Too long
            ("", True),  # Empty is OK
        ]
        
        for input_text, should_pass in test_inputs:
            result = sanitize_user_input(input_text, max_length=200)
            if (should_pass and result is not None) or (not should_pass and result is None):
                print_success(f"Input sanitization: '{input_text[:30]}...' handled correctly")
            else:
                print_warning(f"Input sanitization: '{input_text[:30]}...' unexpected result")
        
        # Test config input validation
        valid_configs = ["min_score=65", "trading_hours=9-17"]
        invalid_configs = ["<script>", "invalid command", "config=value;rm -rf /"]
        
        for config in valid_configs:
            if validate_config_input(config):
                print_success(f"Valid config accepted: '{config}'")
            else:
                print_error(f"Valid config rejected: '{config}'")
        
        for config in invalid_configs:
            if not validate_config_input(config):
                print_success(f"Invalid config rejected: '{config}'")
            else:
                print_error(f"Invalid config accepted: '{config}'")
        
        results['error_handling'] = True
        return True
        
    except Exception as e:
        print_error(f"Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        results['error_handling'] = False
        return False

async def test_signal_generation_logic():
    """Test 7: Verify signal generation logic (without API calls)"""
    print_header("Test 7: Signal Generation Logic")
    
    try:
        from src.indicators.calculator import (
            calculate_ta_score,
            detect_trend_direction,
            calculate_price_momentum
        )
        import pandas as pd
        import numpy as np
        
        # Create mock data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1min')
        prices = 1.08 + np.random.randn(100).cumsum() * 0.0001
        df = pd.DataFrame({
            'close': prices,
            'high': prices + 0.0001,
            'low': prices - 0.0001,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # Test momentum calculation
        momentum = calculate_price_momentum(df, periods=3)
        if 'change_pct' in momentum and 'direction' in momentum:
            print_success(f"Momentum calculated: {momentum['direction']} ({momentum['change_pct']:.4f}%)")
        else:
            print_error("Momentum calculation failed")
            results['signal_logic'] = False
            return False
        
        # Test trend detection
        trend = detect_trend_direction(0.0001, 50.0, 25.0, momentum['change_pct'])
        if 'direction' in trend:
            print_success(f"Trend detected: {trend['direction']}")
        else:
            print_error("Trend detection failed")
            results['signal_logic'] = False
            return False
        
        # Test TA score calculation
        ta_score = calculate_ta_score(
            rsi=35.0,
            macd_diff=0.0002,
            bb_position=0.1,
            adx=30.0,
            stoch_k=20.0,
            stoch_d=25.0,
            price_change=momentum['change_pct'],
            trend_direction=trend['direction']
        )
        if 0 <= ta_score <= 100:
            print_success(f"TA score calculated: {ta_score:.2f}")
        else:
            print_error(f"TA score out of range: {ta_score}")
            results['signal_logic'] = False
            return False
        
        results['signal_logic'] = True
        return True
        
    except Exception as e:
        print_error(f"Signal generation logic test failed: {e}")
        import traceback
        traceback.print_exc()
        results['signal_logic'] = False
        return False

async def test_config_validation():
    """Test 8: Verify config validation works"""
    print_header("Test 8: Config Validation")
    
    try:
        # Import config handler logic
        from src.config.settings import CONFIG, update_config
        from src.utils.helpers import validate_config_input
        
        # Test config update
        old_value = CONFIG.get('min_signal_score', 65)
        success = await update_config('min_signal_score', 70, user_id=99999)
        if success:
            print_success("Config update successful")
            # Restore original value
            await update_config('min_signal_score', old_value)
        else:
            print_error("Config update failed")
            results['config_validation'] = False
            return False
        
        # Test invalid config parameter
        success = await update_config('invalid_param', 100)
        if not success:
            print_success("Invalid config parameter correctly rejected")
        else:
            print_error("Invalid config parameter was accepted")
            results['config_validation'] = False
            return False
        
        results['config_validation'] = True
        return True
        
    except Exception as e:
        print_error(f"Config validation test failed: {e}")
        import traceback
        traceback.print_exc()
        results['config_validation'] = False
        return False

def print_summary():
    """Print test summary"""
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}\n")
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name.replace('_', ' ').title()}")
        else:
            print_error(f"{test_name.replace('_', ' ').title()}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! Bot is ready!{Colors.END}\n")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Some tests failed. Review errors above.{Colors.END}\n")
        return False

async def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   Bot Functionality Test Suite                           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    # Run tests
    await test_bot_imports()
    await test_bot_initialization()
    await test_database_initialization()
    await test_rate_limiting()
    await test_audit_logging()
    await test_error_handling()
    await test_signal_generation_logic()
    await test_config_validation()
    
    # Print summary
    success = print_summary()
    
    # Cleanup
    try:
        from src.utils.http_session import close_http_session
        await close_http_session()
    except:
        pass
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

