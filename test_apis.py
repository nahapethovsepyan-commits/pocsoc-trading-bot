"""
API Keys Testing Script
Test your Telegram, Twelve Data, and Alpha Vantage API keys
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_telegram():
    """Test Telegram Bot Token"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN not found in .env")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("ok"):
                        bot_info = data.get("result", {})
                        print(f"✅ Telegram Bot: {bot_info.get('first_name', 'Unknown')} (@{bot_info.get('username', 'Unknown')})")
                        return True
                print(f"❌ Telegram error: {await resp.text()}")
                return False
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False


async def test_twelvedata():
    """Test Twelve Data API"""
    key = os.getenv("TWELVE_DATA_API_KEY")
    if not key:
        print("⚠️  TWELVE_DATA_API_KEY not found (optional)")
        return None
    
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": "EUR/USD",
        "interval": "1min",
        "outputsize": 5,
        "apikey": key,
        "format": "JSON"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "values" in data and len(data["values"]) > 0:
                        latest = data["values"][0]
                        print(f"✅ Twelve Data: EUR/USD @ {latest.get('close', 'N/A')} ({len(data['values'])} candles)")
                        return True
                    else:
                        error_msg = data.get("message", "Unknown error")
                        print(f"❌ Twelve Data error: {error_msg}")
                        if "limit" in error_msg.lower():
                            print("   💡 Hint: You may have exceeded free tier limit (800/day)")
                        return False
                else:
                    print(f"❌ Twelve Data HTTP {resp.status}")
                    return False
    except asyncio.TimeoutError:
        print("❌ Twelve Data: Timeout")
        return False
    except Exception as e:
        print(f"❌ Twelve Data exception: {e}")
        return False


async def test_alphavantage():
    """Test Alpha Vantage API"""
    key = os.getenv("ALPHA_VANTAGE_KEY")
    if not key:
        print("⚠️  ALPHA_VANTAGE_KEY not found (optional)")
        return None
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "FX_INTRADAY",
        "from_symbol": "EUR",
        "to_symbol": "USD",
        "interval": "1min",
        "apikey": key
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Check for rate limit message
                    if "Note" in data or "Information" in data:
                        msg = data.get("Note", data.get("Information", ""))
                        print(f"⚠️  Alpha Vantage: {msg}")
                        if "premium" in msg.lower() or "5 API" in msg:
                            print("   💡 Hint: Free tier limit reached (25/day or 5/min)")
                        return False
                    
                    if "Time Series FX (1min)" in data:
                        time_series = data["Time Series FX (1min)"]
                        latest_time = list(time_series.keys())[0]
                        latest_close = time_series[latest_time]["4. close"]
                        print(f"✅ Alpha Vantage: EUR/USD @ {latest_close}")
                        return True
                    else:
                        print(f"❌ Alpha Vantage: Unexpected response format")
                        return False
                else:
                    print(f"❌ Alpha Vantage HTTP {resp.status}")
                    return False
    except asyncio.TimeoutError:
        print("❌ Alpha Vantage: Timeout")
        return False
    except Exception as e:
        print(f"❌ Alpha Vantage exception: {e}")
        return False


async def test_binance():
    """Test Binance fallback (no key needed)"""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "EURUSDT",
        "interval": "1m",
        "limit": 5
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if len(data) > 0:
                        latest_close = float(data[-1][4])
                        print(f"✅ Binance: EURUSDT @ {latest_close:.5f} (fallback works)")
                        return True
                print(f"❌ Binance error")
                return False
    except Exception as e:
        print(f"❌ Binance exception: {e}")
        return False


async def main():
    print("=" * 60)
    print("🔍 Testing API Keys")
    print("=" * 60)
    print()
    
    # Test Telegram (required)
    print("📱 Testing Telegram Bot Token (REQUIRED):")
    telegram_ok = await test_telegram()
    print()
    
    # Test forex data APIs
    print("📊 Testing Forex Data APIs (need at least ONE):")
    print()
    
    td_ok = await test_twelvedata()
    print()
    
    av_ok = await test_alphavantage()
    print()
    
    # Test Binance fallback
    print("💰 Testing Binance Fallback (automatic):")
    binance_ok = await test_binance()
    print()
    
    # Summary
    print("=" * 60)
    print("📋 Summary")
    print("=" * 60)
    
    if not telegram_ok:
        print("❌ CRITICAL: Telegram bot token is invalid or missing!")
        print("   → Get token from @BotFather on Telegram")
        print("   → Add to .env: BOT_TOKEN=your_token_here")
    else:
        print("✅ Telegram bot ready")
    
    print()
    
    forex_apis_working = []
    if td_ok:
        forex_apis_working.append("Twelve Data")
    if av_ok:
        forex_apis_working.append("Alpha Vantage")
    
    if len(forex_apis_working) >= 2:
        print(f"✅ EXCELLENT: {len(forex_apis_working)} forex APIs working!")
        print(f"   Working: {', '.join(forex_apis_working)}")
        print(f"   You have redundancy if one fails")
    elif len(forex_apis_working) == 1:
        print(f"✅ GOOD: 1 forex API working ({forex_apis_working[0]})")
        print(f"   Consider adding a backup API")
    else:
        print("⚠️  WARNING: No forex APIs working")
        if binance_ok:
            print("   Bot will use Binance EURUSDT as fallback")
            print("   (crypto pair, not true forex)")
        else:
            print("   ❌ Even Binance fallback failed!")
    
    print()
    
    if binance_ok:
        print("✅ Binance fallback available")
    
    print()
    print("=" * 60)
    
    if telegram_ok and (td_ok or av_ok or binance_ok):
        print("🎉 SUCCESS: Bot can run!")
        print()
        print("Next steps:")
        print("1. Run: python PocSocSig_Enhanced.py")
        print("2. Open Telegram and send /start to your bot")
        print("3. Start receiving EUR/USD signals!")
    else:
        print("⚠️  SETUP INCOMPLETE")
        print()
        print("Required fixes:")
        if not telegram_ok:
            print("❌ Get Telegram bot token from @BotFather")
        if not (td_ok or av_ok or binance_ok):
            print("❌ Get at least one forex API key:")
            print("   - Twelve Data: https://twelvedata.com (recommended)")
            print("   - Alpha Vantage: https://www.alphavantage.co/support/#api-key")
    
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")

