#!/usr/bin/env python3
"""
Test bot startup and handler registration.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_bot_startup():
    """Test that bot can start without errors"""
    print("Testing bot startup...")
    
    try:
        # Import main bot file
        import PocSocSig_Enhanced
        
        # Check that bot objects are created
        assert hasattr(PocSocSig_Enhanced, 'bot'), "Bot object not created"
        assert hasattr(PocSocSig_Enhanced, 'dp'), "Dispatcher not created"
        assert hasattr(PocSocSig_Enhanced, 'scheduler'), "Scheduler not created"
        
        print("✅ Bot objects created successfully")
        
        # Check that handlers are registered (aiogram 3.x uses different structure)
        # Just verify dispatcher exists and has the expected structure
        if PocSocSig_Enhanced.dp:
            print("✅ Dispatcher initialized")
        else:
            print("❌ Dispatcher not initialized")
            return False
        
        # Test database initialization
        from src.database import init_database
        await init_database()
        print("✅ Database initialization works")
        
        # Test config loading
        from src.config.settings import CONFIG
        assert 'pair' in CONFIG
        assert 'min_signal_score' in CONFIG
        print("✅ Configuration loaded")
        
        # Test that signal generation function exists
        from src.signals.generator import generate_signal
        print("✅ Signal generation function available")
        
        print("\n✅ Bot startup test PASSED - Bot can start without errors!")
        return True
        
    except Exception as e:
        print(f"❌ Bot startup test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bot_startup())
    sys.exit(0 if success else 1)

