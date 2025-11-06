"""
Phase 3 Integration Test Script
Tests that all modules work together correctly after refactoring.
"""

import sys
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_imports():
    """Test 1: Verify all imports work"""
    print("\n=== Test 1: Module Imports ===")
    try:
        from src.config import CONFIG, get_bot_token, get_api_keys
        from src.models.state import SUBSCRIBED_USERS, STATS, SIGNAL_HISTORY
        from src.database import init_database, save_signal_to_db
        from src.api import fetch_forex_data
        from src.signals import generate_signal, main_analysis, send_signal_message
        from src.monitoring import check_system_health, send_alert
        from src.telegram import TEXTS, get_main_keyboard, language_keyboard
        from src.telegram.decorators import require_subscription, with_error_handling
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_syntax():
    """Test 2: Verify main file syntax"""
    print("\n=== Test 2: Syntax Check ===")
    try:
        import py_compile
        py_compile.compile('PocSocSig_Enhanced.py', doraise=True)
        print("✅ Syntax check passed")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_dependency_injection():
    """Test 3: Verify dependency injection works"""
    print("\n=== Test 3: Dependency Injection ===")
    try:
        from src.signals import main_analysis
        from src.monitoring import check_system_health
        import inspect
        
        # Check function signatures
        main_analysis_sig = inspect.signature(main_analysis)
        health_sig = inspect.signature(check_system_health)
        
        # Verify they accept bot parameter
        assert 'bot' in main_analysis_sig.parameters, "main_analysis missing bot parameter"
        assert 'bot' in health_sig.parameters, "check_system_health missing bot parameter"
        
        print("✅ Dependency injection signatures correct")
        return True
    except Exception as e:
        print(f"❌ Dependency injection error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_init():
    """Test 4: Verify database initialization"""
    print("\n=== Test 4: Database Initialization ===")
    try:
        from src.database import init_database
        await init_database()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database init error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_handlers_exist():
    """Test 5: Verify all handlers are defined"""
    print("\n=== Test 5: Handler Definitions ===")
    try:
        import inspect
        # Import handlers from main file
        import importlib.util
        spec = importlib.util.spec_from_file_location("main", "PocSocSig_Enhanced.py")
        main_module = importlib.util.module_from_spec(spec)
        
        # We'll check handlers exist by importing the file
        # This is a simplified check - actual handler testing requires bot instance
        handlers_to_check = [
            'start_handler', 'language_handler', 'metrics_handler',
            'stop_handler', 'manual_signal_handler', 'stats_handler',
            'settings_handler', 'config_handler', 'backtest_handler',
            'history_handler', 'export_handler', 'health_handler'
        ]
        
        # Read file and check handlers exist
        with open('PocSocSig_Enhanced.py', 'r') as f:
            content = f.read()
            found_handlers = []
            for handler in handlers_to_check:
                if f'async def {handler}' in content or f'def {handler}' in content:
                    found_handlers.append(handler)
        
        print(f"✅ Found {len(found_handlers)}/{len(handlers_to_check)} handlers")
        if len(found_handlers) < len(handlers_to_check):
            missing = set(handlers_to_check) - set(found_handlers)
            print(f"⚠️  Missing handlers: {missing}")
        
        return len(found_handlers) == len(handlers_to_check)
    except Exception as e:
        print(f"❌ Handler check error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_module_structure():
    """Test 6: Verify module structure"""
    print("\n=== Test 6: Module Structure ===")
    try:
        import os
        required_modules = [
            'src/config/__init__.py',
            'src/utils/__init__.py',
            'src/models/__init__.py',
            'src/database/__init__.py',
            'src/api/__init__.py',
            'src/indicators/__init__.py',
            'src/signals/__init__.py',
            'src/monitoring/__init__.py',
            'src/telegram/__init__.py',
        ]
        
        missing = []
        for module in required_modules:
            if not os.path.exists(module):
                missing.append(module)
        
        if missing:
            print(f"❌ Missing modules: {missing}")
            return False
        
        print(f"✅ All {len(required_modules)} modules exist")
        return True
    except Exception as e:
        print(f"❌ Module structure error: {e}")
        return False

def test_config_access():
    """Test 7: Verify CONFIG is accessible"""
    print("\n=== Test 7: Configuration Access ===")
    try:
        from src.config import CONFIG
        required_keys = [
            'pair', 'api_source', 'analysis_interval_minutes',
            'min_signal_score', 'min_confidence', 'use_gpt'
        ]
        
        missing_keys = []
        for key in required_keys:
            if key not in CONFIG:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"❌ Missing CONFIG keys: {missing_keys}")
            return False
        
        print(f"✅ All required CONFIG keys present")
        return True
    except Exception as e:
        print(f"❌ Config access error: {e}")
        return False

async def test_state_access():
    """Test 8: Verify state variables are accessible"""
    print("\n=== Test 8: State Access ===")
    try:
        from src.models.state import (
            SUBSCRIBED_USERS, STATS, SIGNAL_HISTORY,
            stats_lock, history_lock, config_lock
        )
        
        # Verify they exist and are correct types
        assert isinstance(SUBSCRIBED_USERS, set), "SUBSCRIBED_USERS should be set"
        assert isinstance(STATS, dict), "STATS should be dict"
        assert hasattr(SIGNAL_HISTORY, 'append'), "SIGNAL_HISTORY should be deque"
        
        print("✅ State variables accessible and correct types")
        return True
    except Exception as e:
        print(f"❌ State access error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all Phase 3 tests"""
    print("=" * 60)
    print("Phase 3: Integration Testing")
    print("=" * 60)
    
    # Change to correct directory
    # Change to project root directory (adjust path as needed)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Syntax
    results.append(("Syntax", test_syntax()))
    
    # Test 3: Dependency Injection
    results.append(("Dependency Injection", await test_dependency_injection()))
    
    # Test 4: Database
    results.append(("Database Init", await test_database_init()))
    
    # Test 5: Handlers
    results.append(("Handlers", test_handlers_exist()))
    
    # Test 6: Module Structure
    results.append(("Module Structure", test_module_structure()))
    
    # Test 7: Config Access
    results.append(("Config Access", test_config_access()))
    
    # Test 8: State Access
    results.append(("State Access", await test_state_access()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All Phase 3 tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

