# 🤖 Enhanced EUR/USD Trading Signal Bot

Professional Telegram bot for EUR/USD forex trading signals with AI predictions and advanced technical analysis.

> **Unified Project:** This is the final unified version combining performance optimizations from `pocsoc 2` with code quality improvements from `pocsoc`. Features parallel indicator calculations, adaptive thresholds, decorator-based handlers, and comprehensive test coverage.

---

## ✨ Features

- 🌍 **Real Forex Data** - True EUR/USD from Twelve Data & Alpha Vantage APIs
- 🤖 **GPT-4o-mini AI** - Advanced AI analysis with OpenAI
- 📊 **Multiple Indicators** - RSI, MACD, Bollinger Bands, ADX, Stochastic, ATR
- 🎯 **Simple Scoring** - 0-100 point system with aggressive thresholds
- 💰 **Risk Management** - Automatic Stop Loss & Take Profit calculation
- 📱 **Telegram Interface** - Clean UI with real-time notifications
- 🔄 **Auto-Fallback** - 3-level API fallback system
- 📈 **Performance Tracking** - Win rate, statistics, signal history

---

## 🚀 Quick Start

### 1. Get API Keys (15 min)

You need:
- ✅ Telegram bot token (from @BotFather)
- ✅ Twelve Data API key (from https://twelvedata.com)
- ⚪ Alpha Vantage API key (optional backup)

👉 **[Detailed instructions in API_KEYS_GUIDE.md](API_KEYS_GUIDE.md)**

### 2. Install (2 min)

```bash
cd pocsoc-trading-bot
pip install -r requirements.txt
```

### 3. Configure (2 min)

Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Your `.env` should look like:
```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TWELVE_DATA_API_KEY=your_twelvedata_key
ALPHA_VANTAGE_KEY=your_alphavantage_key
```

### 4. Test (1 min)

```bash
python test_apis.py
```

Expected output:
```
✅ Telegram Bot: YourBot (@your_bot)
✅ Twelve Data: EUR/USD @ 1.08450
✅ Alpha Vantage: EUR/USD @ 1.08452
🎉 SUCCESS: Bot can run!
```

### 5. Run!

```bash
python PocSocSig_Enhanced.py
```

Then:
1. Open Telegram
2. Find your bot
3. Send `/start`
4. Receive EUR/USD signals!

---

## 📊 Example Signal

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

---

## 📱 Telegram Commands

| Button | Function |
|--------|----------|
| 📊 СИГНАЛ | Get immediate analysis and signal |
| 📈 СТАТИСТИКА | View performance statistics |
| ⚙️ НАСТРОЙКИ | View current configuration |
| 📜 ИСТОРИЯ | View recent signal history |

---

## 🎯 How It Works

```
1. Fetch EUR/USD Data (Twelve Data API)
   ↓
2. Calculate 10+ Technical Indicators
   ↓
3. AI Predicts Price Movement (LSTM)
   ↓
4. Score Signal Quality (0-100 points)
   ↓
5. If Score ≥ 55:
   → Calculate Stop Loss (ATR-based)
   → Calculate Take Profit (R:R ratio)
   → Send Telegram Notification
```

### Scoring Breakdown

- **GPT-4o-mini** (35% weight) - AI analysis
- **RSI** - Overbought/oversold (main indicator)
- **MACD** - Momentum (main indicator)
- **Bollinger Bands** - Volatility (bonus confirmation)
- **ATR** - For Stop Loss/Take Profit calculation
- **ADX** - Trend Strength (display only)
- **Stochastic** - Momentum oscillator (display only)

**Formula:** final_score = gpt_weight × gpt_score + ta_weight × ta_score

---

## 💰 Cost

**FREE!** All APIs have generous free tiers:

- ✅ Telegram: Unlimited free
- ✅ Twelve Data: 800 calls/day free
- ✅ Alpha Vantage: 25 calls/day free
- ✅ Binance: Unlimited free (fallback)

Bot uses ~480 calls/day → well within limits ✓

---

## ⚙️ Configuration

Configuration is now centralized in `src/config/settings.py`:

```python
CONFIG = {
    "analysis_interval_minutes": 2,    # Check every 2 min
    "min_signal_score": 55,            # Quality threshold
    "min_confidence": 60,              # Minimum confidence
    "max_signals_per_hour": 12,        # Rate limit
    "risk_reward_ratio": 1.8,          # TP/SL ratio
    "use_gpt": True,                   # Enable GPT
    # ... and 30+ more settings
}
```

**To modify:** Edit `src/config/settings.py` or use `/config` command in Telegram bot.

### GPT analysis tuning

- `gpt_model`: switch between `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`, etc.
- `gpt_request_timeout`: how long to wait for the OpenAI API call (seconds).
- `gpt_wait_timeout`: how long the bot waits for GPT before falling back to TA-only output.
- `gpt_temperature`: controls randomness (0 = deterministic, 1 = creative).
- `gpt_weight` / `ta_weight`: adjust hybrid scoring balance (`/config gpt_weight=0.30` in Telegram updates both).
- `gpt_prompt_template`: multi-line string used to build the user prompt (editable directly in `settings.py`).
- `gpt_system_prompt`: system instruction for GPT (also editable in `settings.py`).

### Admin tools

- Set `ADMIN_USER_IDS` in `.env` (comma-separated Telegram chat IDs) to restrict who can run maintenance commands.
- Use `/reset_rate` in Telegram (from an admin chat ID) to flush cached per-user rate limits if someone gets stuck behind a stale limiter or after stress testing.

### Preset Configurations

**Conservative** (fewer, higher quality):
```python
"min_signal_score": 65,
```

**Aggressive** (more frequent):
```python
"min_signal_score": 50,
```

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| [START_HERE.md](START_HERE.md) | 📖 Quick overview & checklist |
| [API_KEYS_GUIDE.md](API_KEYS_GUIDE.md) | 🔑 How to get all API keys |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | ⚙️ Detailed setup instructions |
| [MODULE_ARCHITECTURE.md](MODULE_ARCHITECTURE.md) | 🏗️ Module structure & architecture |
| [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) | 🔄 Guide for working with modules |
| [CODE_ANALYSIS_FINAL.md](CODE_ANALYSIS_FINAL.md) | 📊 Technical analysis |

---

## 📁 Project Structure

**Modular Architecture (Phase 1-2 Refactoring):**

```
pocsoc_final/
├── PocSocSig_Enhanced.py    # Main entry point (776 lines)
├── requirements.txt          # Python dependencies
├── render.yaml              # Render.com deployment config
│
└── src/                     # Modular source code
    ├── config/              # Configuration & environment variables
    ├── utils/               # Helper functions & HTTP session
    ├── models/              # Global state management
    ├── database/            # SQLite operations
    ├── api/                 # API clients (Twelve Data, Alpha Vantage, Binance)
    ├── indicators/          # Technical indicator calculations
    ├── signals/             # Signal generation & messaging
    ├── monitoring/          # Health checks & alerts
    └── telegram/            # Telegram UI (localization, keyboards, decorators)
```

👉 **[Full architecture documentation: MODULE_ARCHITECTURE.md](MODULE_ARCHITECTURE.md)**

---

## 🐛 Troubleshooting

### Bot won't start?

```bash
python test_apis.py  # Diagnose issues
```

### No signals?

1. Lower thresholds in CONFIG
2. Wait 3-5 minutes for first analysis
3. Press 📊 СИГНАЛ button manually

### API rate limits?

- Bot automatically switches to backup APIs
- Check usage at API provider dashboards
- If rate limiting locks a user, run `/reset_rate` from an admin account to clear cached counters.

### More help?

See [SETUP_GUIDE.md](SETUP_GUIDE.md) → Troubleshooting section

---

## 📈 Performance

### Expected Results

- **Signal Logic:** Simple and aggressive (as old code)
- **Frequency:** Up to 12 signals per hour
- **Analysis:** Every 2 minutes
- **Confidence:** Fixed at 60%
- **Response Time:** 3-5 seconds

### Features

- ✅ Real forex data (EUR/USD)
- ✅ GPT-4o-mini AI analysis
- ✅ Multiple technical indicators
- ✅ Professional risk management
- ✅ Multi-user support
- ✅ Database for signal history

---

## ⚠️ Disclaimer

**Educational purposes only.**

- Not financial advice
- Trading involves risk
- Test with demo account first
- Never risk more than you can lose
- Past performance ≠ future results

---

## 🎓 Technical Details

### Signal Generation Logic

**Simple and Aggressive (as old code):**
- RSI + MACD as main indicators
- Bollinger Bands as bonus confirmation
- GPT-4o-mini for AI analysis
- Fixed confidence = 60%
- Ports: 55/45 (aggressive)

### Data Pipeline

1. **Fetch** from Twelve Data (primary)
2. **Fallback** to Alpha Vantage if needed
3. **Fallback** to Binance if needed
4. **Cache** for 90 seconds
5. **Process** OHLCV data
6. **Calculate** all indicators
7. **Predict** with AI model
8. **Score** signal quality
9. **Generate** signal if thresholds met

---

## 🚀 Getting Started

1. **New user?** → Read [START_HERE.md](START_HERE.md)
2. **Need API keys?** → Read [API_KEYS_GUIDE.md](API_KEYS_GUIDE.md)
3. **Ready to install?** → Read [SETUP_GUIDE.md](SETUP_GUIDE.md)
4. **Want technical details?** → Read [CODE_ANALYSIS_FINAL.md](CODE_ANALYSIS_FINAL.md)

**Total setup time:** 20-30 minutes

---

## 📞 Quick Help

```bash
# Test your setup
python test_apis.py

# Run the bot
python PocSocSig_Enhanced.py

# Test signal logic
python test_signal_logic.py

# Install dependencies
pip install -r requirements.txt
```

---

## ✅ Pre-Flight Checklist

- [ ] Python 3.8+ installed (Minimum: 3.8 | Recommended: 3.12 | Tested: 3.8-3.13)
- [ ] Got Telegram bot token
- [ ] Got Twelve Data API key
- [ ] Got Alpha Vantage API key (optional)
- [ ] Installed requirements
- [ ] Created `.env` file
- [ ] Tested with `test_apis.py`
- [ ] Ready to trade!

---

## 🌟 Features at a Glance

| Feature | Status |
|---------|--------|
| Real Forex Data | ✅ |
| Multi-API Fallback | ✅ |
| Advanced AI Model | ✅ |
| 10+ Indicators | ✅ |
| Risk Management | ✅ |
| Stop Loss/Take Profit | ✅ |
| Telegram Interface | ✅ |
| Performance Tracking | ✅ |
| Signal History | ✅ |
| Comprehensive Docs | ✅ |
| Testing Tools | ✅ |
| Free to Use | ✅ |

---

## 📊 Stats

- **Lines of Code:** 2,938 (optimized with parallel calculations)
- **Indicators:** 6 (RSI, MACD, Bollinger Bands, ADX, Stochastic, ATR)
- **API Sources:** 3 (Twelve Data, Alpha Vantage, Binance)
- **Documentation Files:** 18
- **Test Files:** 19 (comprehensive unit test coverage)
- **Setup Time:** 20-30 min
- **Cost:** $0
- **Code Quality:** ✅ Decorators, no duplication, well-documented

---

## 🎉 Ready to Start?

```bash
# Clone or download this repository
cd pocsoc-trading-bot

# Follow the guides
cat START_HERE.md

# Get your API keys
cat API_KEYS_GUIDE.md

# Set up and run
cat SETUP_GUIDE.md
```

**Let's make some profitable trades! 📈💰**

---

*Built with Python, TensorFlow, and ❤️ for forex traders*

