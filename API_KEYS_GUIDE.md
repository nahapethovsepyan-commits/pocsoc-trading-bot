# 🔑 Complete API Keys Guide

## Quick Links

| API | Sign Up Link | Time | Cost |
|-----|-------------|------|------|
| **Telegram** | https://t.me/BotFather | 5 min | FREE |
| **Twelve Data** | https://twelvedata.com/pricing | 5 min | FREE tier |
| **Alpha Vantage** | https://www.alphavantage.co/support/#api-key | 2 min | FREE tier |

---

## 1. Telegram Bot Token (REQUIRED)

### Step-by-Step

1. **Open Telegram app** (mobile or desktop)

2. **Search for BotFather:**
   - In search bar, type: `@BotFather`
   - Click the official BotFather (verified checkmark)

3. **Create new bot:**
   ```
   Send: /newbot
   ```

4. **Choose a name:**
   ```
   Example: EUR USD Trading Bot
   (This is the display name users see)
   ```

5. **Choose a username:**
   ```
   Example: my_eurusd_signals_bot
   (Must end with 'bot' and be unique)
   ```

6. **Copy the token:**
   ```
   BotFather will send you a token like:
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   
   ⚠️ KEEP THIS SECRET!
   ```

7. **Save token** to `.env` file:
   ```
   BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

### Security Tips
- Never share your bot token
- Don't commit `.env` to git
- Regenerate token if exposed: `/revoke` in BotFather

---

## 2. Twelve Data API (RECOMMENDED)

### Why Twelve Data?
- ✅ Real forex EUR/USD data (not crypto)
- ✅ 800 API calls per day FREE
- ✅ 1-minute candlesticks
- ✅ High quality, professional data
- ✅ Technical indicators built-in

### Free Tier Limits
- **800 requests/day**
- **8 requests/minute**
- Perfect for our bot (3-min intervals = ~480 calls/day)

### Step-by-Step

1. **Go to:** https://twelvedata.com

2. **Click "Get Free API Key"** (top right)

3. **Sign up:**
   - Enter email
   - Create password
   - Verify email (check inbox)

4. **Access dashboard:**
   - After verification, log in
   - Go to: https://twelvedata.com/account/api

5. **Copy API Key:**
   ```
   Your key looks like:
   abc123def456ghi789jkl012mno345pqr
   ```

6. **Add to .env:**
   ```
   TWELVE_DATA_API_KEY=abc123def456ghi789jkl012mno345pqr
   ```

### Test Your Key

```bash
# Test in terminal (replace YOUR_KEY)
curl "https://api.twelvedata.com/time_series?symbol=EUR/USD&interval=1min&outputsize=10&apikey=YOUR_KEY"
```

Should return JSON with EUR/USD data.

### Pricing (if you need more)

| Plan | Calls/Day | Calls/Min | Price |
|------|-----------|-----------|-------|
| **Free** | 800 | 8 | $0 |
| **Basic** | 8,000 | 60 | $19/mo |
| **Pro** | 30,000 | 120 | $79/mo |

**For our bot:** Free tier is enough! ✓

---

## 3. Alpha Vantage API (BACKUP)

### Why Alpha Vantage?
- ✅ Instant free key (no email verification!)
- ✅ Good backup when Twelve Data hits limit
- ✅ Simple to get
- ⚠️ Only 25 calls/day on free tier

### Free Tier Limits
- **25 requests/day** (limited!)
- 5 requests/minute
- Use as backup only

### Step-by-Step

1. **Go to:** https://www.alphavantage.co/support/#api-key

2. **Enter email** in the form

3. **Click "GET FREE API KEY"**

4. **Copy key immediately:**
   ```
   You'll see:
   Your API Key: ABCDEFG123456789
   ```

5. **Add to .env:**
   ```
   ALPHA_VANTAGE_KEY=ABCDEFG123456789
   ```

### Test Your Key

```bash
# Test in terminal
curl "https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol=EUR&to_symbol=USD&interval=1min&apikey=YOUR_KEY"
```

### Pricing (if you need more)

| Plan | Calls/Day | Price |
|------|-----------|-------|
| **Free** | 25 | $0 |
| **Premium** | Unlimited | $49.99/mo |

---

## 4. Fallback: Binance (No Key Needed)

The bot automatically uses Binance EURUSDT if other APIs fail.

### Pros:
- ✅ No API key needed
- ✅ Unlimited free requests
- ✅ High-quality crypto data

### Cons:
- ⚠️ EURUSDT = EUR priced in Tether (crypto)
- ⚠️ Not true forex EUR/USD
- ⚠️ Small price differences from real forex

**Use for:** Testing, or when API limits reached

---

## 📝 Your .env File Should Look Like:

```bash
# ==========================================
# REQUIRED
# ==========================================
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# ==========================================
# FOREX DATA (At least ONE)
# ==========================================

# Primary (RECOMMENDED)
TWELVE_DATA_API_KEY=abc123def456ghi789jkl012mno345pqr

# Backup (OPTIONAL but good to have)
ALPHA_VANTAGE_KEY=ABCDEFG123456789
```

---

## 🎯 Recommended Setup

### Beginner (Minimal)
```
✓ Telegram Bot Token
✓ Twelve Data API
```
**Cost:** FREE  
**Calls/Day:** 800

### Recommended (Best)
```
✓ Telegram Bot Token
✓ Twelve Data API (primary)
✓ Alpha Vantage API (backup)
```
**Cost:** FREE  
**Calls/Day:** 800 + 25 = 825  
**Reliability:** Excellent (double backup)

### Professional (Overkill)
```
✓ Telegram Bot Token
✓ Twelve Data Pro ($79/mo)
✓ Alpha Vantage Premium ($49.99/mo)
```
**Cost:** $129/mo  
**Calls/Day:** Unlimited  
**Reliability:** Maximum

---

## ⚙️ Testing Your APIs

### Test Script

Create `test_apis.py`:

```python
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def test_twelvedata():
    key = os.getenv("TWELVE_DATA_API_KEY")
    if not key:
        print("❌ TWELVE_DATA_API_KEY not found")
        return False
    
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": "EUR/USD",
        "interval": "1min",
        "outputsize": 5,
        "apikey": key
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "values" in data:
                        print(f"✅ Twelve Data: OK ({len(data['values'])} candles)")
                        return True
                print(f"❌ Twelve Data error: {await resp.text()}")
                return False
    except Exception as e:
        print(f"❌ Twelve Data exception: {e}")
        return False

async def test_alphavantage():
    key = os.getenv("ALPHA_VANTAGE_KEY")
    if not key:
        print("❌ ALPHA_VANTAGE_KEY not found")
        return False
    
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
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "Time Series FX (1min)" in data:
                        print(f"✅ Alpha Vantage: OK")
                        return True
                print(f"❌ Alpha Vantage error: {await resp.text()}")
                return False
    except Exception as e:
        print(f"❌ Alpha Vantage exception: {e}")
        return False

async def main():
    print("=" * 50)
    print("Testing API Keys")
    print("=" * 50)
    
    # Test Telegram
    bot_token = os.getenv("BOT_TOKEN")
    if bot_token:
        print(f"✅ Telegram Bot Token: Found")
    else:
        print(f"❌ Telegram Bot Token: NOT FOUND")
    
    print()
    
    # Test data APIs
    td = await test_twelvedata()
    av = await test_alphavantage()
    
    print()
    print("=" * 50)
    if td or av:
        print("✅ At least one data API working!")
    else:
        print("⚠️  No data APIs working - will use Binance fallback")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
```

### Run Test:

```bash
python test_apis.py
```

Expected output:
```
==================================================
Testing API Keys
==================================================
✅ Telegram Bot Token: Found

✅ Twelve Data: OK (5 candles)
✅ Alpha Vantage: OK

==================================================
✅ At least one data API working!
==================================================
```

---

## 🚨 Common Issues

### "API key is invalid"

**Twelve Data:**
- Check for typos in .env
- Verify at: https://twelvedata.com/account/api
- Make sure email is verified

**Alpha Vantage:**
- Keys work immediately, no verification needed
- Try getting a new key if old one doesn't work

### "API rate limit exceeded"

**Twelve Data (800/day):**
- Check your usage: https://twelvedata.com/account/usage
- Bot uses ~480 calls/day with 3-min intervals
- Reset: daily at midnight UTC

**Alpha Vantage (25/day):**
- Very limited, only for backup
- Reset: daily at midnight ET
- Consider upgrading if needed

### ".env file not found"

```bash
# Make sure you're in the right directory
cd pocsoc-trading-bot

# Check if .env exists
ls -la .env

# If not, create it
cp .env.template .env
# Then edit with your keys
```

---

## 📊 API Usage Estimate

### Bot Configuration:
- **Analysis Interval:** 3 minutes
- **Hours per day running:** 24h

### Daily Usage:
```
Calls per hour: 60 / 3 = 20
Calls per day: 20 × 24 = 480

Primary (Twelve Data): 480 calls ✓ (under 800 limit)
Backup (Alpha Vantage): 0-10 calls (only if primary fails)
```

### Recommendation:
✅ Use Twelve Data as primary (plenty of headroom)  
✅ Keep Alpha Vantage as backup  
✅ Binance auto-fallback if both fail

---

## 💡 Pro Tips

1. **Get Both APIs**
   - Twelve Data for primary
   - Alpha Vantage for backup
   - Total cost: $0

2. **Monitor Usage**
   - Check Twelve Data dashboard weekly
   - Log API errors in bot

3. **Adjust Interval if Needed**
   ```python
   # If hitting limits, increase interval
   "analysis_interval_minutes": 5,  # Instead of 3
   # Reduces daily calls from 480 to 288
   ```

4. **Keep Keys Secret**
   - Never commit .env to git
   - Add to .gitignore
   - Don't share screenshots with keys

5. **Test Before Running 24/7**
   - Run for 1 hour first
   - Check logs for API errors
   - Verify data quality

---

## ✅ Setup Checklist

- [ ] Created Telegram bot (@BotFather)
- [ ] Got Telegram bot token
- [ ] Signed up for Twelve Data
- [ ] Got Twelve Data API key
- [ ] Signed up for Alpha Vantage (optional)
- [ ] Got Alpha Vantage key (optional)
- [ ] Created .env file
- [ ] Added all keys to .env
- [ ] Tested with test_apis.py script
- [ ] All APIs working ✓

---

**Total Setup Time:** 10-15 minutes  
**Total Cost:** $0 (free tiers)

You're ready to start trading! 🚀

