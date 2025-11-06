# 🚀 START HERE - EUR/USD Trading Bot

Welcome! This directory contains a professional EUR/USD trading signal bot for Telegram.

---

## 📁 What Files Do I Need?

### ✅ USE THESE FILES:

1. **`PocSocSig_Enhanced.py`** - The main bot (USE THIS ONE!)
2. **`.env`** - Your API keys (create from `.env.template`)
3. **`requirements.txt`** - Python dependencies

### 📚 DOCUMENTATION (Read These):

4. **`API_KEYS_GUIDE.md`** - How to get all API keys (START HERE!)
5. **`SETUP_GUIDE.md`** - Complete setup instructions
6. **`CODE_ANALYSIS_FINAL.md`** - Technical analysis of the bot

### 🔧 UTILITIES:

7. **`test_apis.py`** - Test your API keys before running
8. **`test_signal_logic.py`** - Test signal generation logic

---

## ⚡ Quick Start (20 Minutes)

### Step 1: Get API Keys (15 min)

Read **`API_KEYS_GUIDE.md`** and get:

1. ✅ **Telegram Bot Token** (required)
   - From: @BotFather on Telegram
   - Takes: 5 minutes
   - Cost: FREE

2. ✅ **Twelve Data API Key** (recommended)
   - From: https://twelvedata.com
   - Takes: 5 minutes
   - Cost: FREE (800 calls/day)

3. ⚪ **Alpha Vantage API Key** (optional backup)
   - From: https://www.alphavantage.co/support/#api-key
   - Takes: 2 minutes
   - Cost: FREE (25 calls/day)

### Step 2: Install Dependencies (2 min)

```bash
cd pocsoc-trading-bot
pip install -r requirements.txt
```

### Step 3: Configure (2 min)

```bash
# Create .env file
cp .env.template .env

# Edit .env and add your keys:
# BOT_TOKEN=your_telegram_token
# TWELVE_DATA_API_KEY=your_twelvedata_key
# ALPHA_VANTAGE_KEY=your_alphavantage_key (optional)
```

### Step 4: Test (1 min)

```bash
python test_apis.py
```

Should show:
```
✅ Telegram Bot: YourBot (@your_bot)
✅ Twelve Data: EUR/USD @ 1.08450 (5 candles)
✅ Alpha Vantage: EUR/USD @ 1.08452
🎉 SUCCESS: Bot can run!
```

### Step 5: Run! (immediate)

```bash
python PocSocSig_Enhanced.py
```

Then open Telegram → find your bot → send `/start`

---

## 🎯 What Does This Bot Do?

### The Bot:
1. ✅ Fetches **real EUR/USD forex data** (not crypto)
2. ✅ Analyzes with **AI + 10+ technical indicators**
3. ✅ Generates **high-quality BUY/SELL signals**
4. ✅ Sends **Telegram notifications** with:
   - Entry price
   - Stop Loss
   - Take Profit
   - Risk/Reward ratio
   - Confidence score
   - Detailed analysis

### Automatic Operation:
- Checks market every **2 minutes**
- Sends signal if:
  - Score ≥ 55/100
  - Confidence ≥ 60% (fixed)
  - Not exceeding 12 signals/hour

### Manual Operation:
- Press **📊 СИГНАЛ** button for immediate analysis
- Press **📈 СТАТИСТИКА** for performance stats
- Press **⚙️ НАСТРОЙКИ** to view configuration
- Press **📜 ИСТОРИЯ** for recent signals

---

## 🤔 Which Bot Should I Use?

### Main Bot:

| File | Description | Use? |
|------|-------------|------|
| `PocSocSig_Enhanced.py` | Enhanced bot with GPT analysis | ✅ **USE THIS!** |

### Features:

- ✅ Real forex data (EUR/USD from Twelve Data)
- ✅ GPT-4o-mini AI analysis
- ✅ Multiple technical indicators (RSI, MACD, BB, ADX, Stochastic, ATR)
- ✅ Full risk management (Stop Loss + Take Profit)
- ✅ Multi-user support
- ✅ Database for signal history
- ✅ Simple and aggressive signal logic

---

## 📊 Example Signal

What you'll receive on Telegram:

```
🚨 ТОРГОВЫЙ СИГНАЛ 🚨

Пара: EUR/USD
Действие: BUY
Цена: 1.08450
Балл: 68/100
Уверенность: 60%

📈 Индикаторы:
RSI: 28.3 | MACD: 0.00015

🎲 Рекомендации POCKETOPTION:
⏱️ Срок: 3 минут
💵 Размер ставки: 3.0% баланса
💰 Рекомендуемая: $30 (если баланс = $1000)
🟢 Уровень риска: LOW

⚙️ Управление рисками:
🛑 Стоп-лосс: 1.08420
🎯 Тейк-профит: 1.08510
📊 R:R = 1:1.8

⏰ 14:32:15
```

**You get:**
- Clear action (BUY or SELL)
- Exact entry price
- Calculated stop loss
- Calculated take profit
- Multiple reasons why signal was generated

---

## 💰 Cost

**Total Cost: $0 (FREE)**

Everything uses free tiers:
- ✅ Telegram: Always free
- ✅ Twelve Data: 800 calls/day free (enough!)
- ✅ Alpha Vantage: 25 calls/day free (backup)
- ✅ Binance: Unlimited free (fallback)

Bot uses ~480 calls/day → well within free limits!

---

## 🎓 Learning Path

### Beginner:
1. Read `API_KEYS_GUIDE.md`
2. Get API keys
3. Follow `SETUP_GUIDE.md`
4. Run bot
5. Watch signals for a week

### Intermediate:
1. Adjust CONFIG settings in bot
2. Test different thresholds
3. Monitor win rate
4. Optimize for your style

### Advanced:
1. Customize indicators
2. Add new features
3. Backtest on historical data
4. Train model on more data

---

## 🛠️ Customization

All settings in `PocSocSig_Enhanced.py` (lines 39-50):

```python
CONFIG = {
    "analysis_interval_minutes": 2,    # How often to check
    "min_signal_score": 55,            # Quality threshold
    "min_confidence": 60,              # Fixed confidence (as in old code)
    "max_signals_per_hour": 12,        # Rate limit
    "risk_reward_ratio": 1.8,          # R:R for TP/SL
    "use_gpt": True,                   # Enable/disable GPT
}
```

**Conservative (fewer signals, higher quality):**
```python
"min_signal_score": 65,
```

**Aggressive (more signals, lower threshold):**
```python
"min_signal_score": 50,
```

---

## 📈 How It Works

### Data Flow:

```
1. Fetch EUR/USD Data
   ↓
2. Calculate 10+ Indicators
   ↓
3. AI Predicts Price Movement
   ↓
4. Scoring System (0-100)
   ↓
5. If Score ≥ 55:
   → Calculate Stop Loss
   → Calculate Take Profit
   → Send Telegram Signal
```

### Indicators Used:

1. **RSI** - Overbought/Oversold (main indicator)
2. **MACD** - Momentum (main indicator)
3. **Bollinger Bands** - Volatility (bonus confirmation)
4. **ATR** - For Stop Loss/Take Profit calculation
5. **GPT-4o-mini** - AI analysis (35% weight)
6. **ADX** - Trend Strength (display only)
7. **Stochastic** - Momentum oscillator (display only)

Scoring: GPT (35%) + Technical Analysis (65%)

---

## 🐛 Troubleshooting

### Bot won't start?

```bash
# Check .env file exists
ls -la .env

# Test API keys
python test_apis.py

# Check logs
tail -f enhanced_bot.log
```

### No signals being sent?

1. Lower thresholds in CONFIG (min_signal_score)
2. Check API keys are working (run test_apis.py)
3. Wait 2-3 minutes for first analysis
4. Press 📊 СИГНАЛ button manually

### "API rate limit exceeded"?

- Twelve Data: 800/day (resets daily)
- Alpha Vantage: 25/day (resets daily)
- Bot automatically switches to backup

### More help?

Read **`SETUP_GUIDE.md`** → Troubleshooting section

---

## ⚠️ Important Notes

1. **Not Financial Advice**
   - This is educational software
   - Test thoroughly before trading real money
   - Never risk more than you can afford to lose

2. **API Keys**
   - Keep `.env` file private
   - Never share API keys
   - Never commit `.env` to git

3. **Performance**
   - Simple and aggressive signal logic (as old code)
   - Fixed confidence = 60%
   - Past performance ≠ future results
   - Monitor and adjust settings

4. **Testing**
   - Run for 24-48 hours first
   - Use demo account to verify
   - Track actual results

---

## 📚 File Reference

| File | Purpose | When to Read |
|------|---------|--------------|
| **START_HERE.md** | Overview (this file) | First! |
| **API_KEYS_GUIDE.md** | Get API keys | Before setup |
| **SETUP_GUIDE.md** | Installation guide | During setup |
| **CODE_ANALYSIS_FINAL.md** | Technical analysis | Understanding the code |
| **test_apis.py** | Test your keys | Before running bot |
| **test_signal_logic.py** | Test signal logic | Testing signal generation |
| **requirements.txt** | Python packages | During install |
| **PocSocSig_Enhanced.py** | Main bot code | Run this! |

---

## ✅ Pre-Flight Checklist

Before running the bot:

- [ ] Read this file (START_HERE.md)
- [ ] Read API_KEYS_GUIDE.md
- [ ] Got Telegram bot token
- [ ] Got at least one forex API key
- [ ] Installed requirements.txt
- [ ] Created .env file with keys
- [ ] Ran test_apis.py successfully
- [ ] Read SETUP_GUIDE.md
- [ ] Understand how signals work
- [ ] Ready to start!

---

## 🚀 Ready to Go?

### Your Next Steps:

1. **If you haven't read `API_KEYS_GUIDE.md`:**
   → Read it now to get your API keys

2. **If you have API keys:**
   → Read `SETUP_GUIDE.md` for setup instructions

3. **If bot is already set up:**
   → Run: `python PocSocSig_Enhanced.py`
   → Open Telegram and send `/start` to your bot

4. **Questions?**
   → Check `SETUP_GUIDE.md` → Troubleshooting section

---

## 📞 Quick Help

**Bot won't start?**
```bash
python test_apis.py  # Test your setup
```

**Want to understand the code?**
```bash
Read: CODE_ANALYSIS_FINAL.md
```

**Need detailed setup help?**
```bash
Read: SETUP_GUIDE.md
```

**Need to get API keys?**
```bash
Read: API_KEYS_GUIDE.md
```

---

## 🎉 Success Looks Like:

1. ✅ Bot runs without errors
2. ✅ Telegram receives `/start` message
3. ✅ First signal arrives within 3-5 minutes
4. ✅ Signals include entry, SL, TP
5. ✅ Statistics button shows data
6. ✅ Bot runs 24/7 (optional)

---

**Estimated Total Time:** 20-30 minutes from zero to running

**Good luck with your EUR/USD trading! 📈**

---

## 🆘 Still Stuck?

1. Make sure you're using **PocSocSig_Enhanced.py**
2. Run `test_apis.py` - it will tell you what's wrong
3. Run `test_signal_logic.py` - test signal generation
4. Verify `.env` file has correct format (no spaces around `=`)
5. Make sure Python 3.8+ is installed
6. Check console output for error messages

---

**Now go get those API keys and start trading! 🚀**

