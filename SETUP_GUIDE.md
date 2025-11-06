# 🚀 Enhanced EUR/USD Trading Bot - Setup Guide

## 📋 Prerequisites

- Python 3.8 or higher
- Internet connection
- Telegram account

---

## 🔑 Step 1: Get API Keys (15 minutes total)

### 1.1 Telegram Bot Token (5 min) - REQUIRED

1. Open Telegram
2. Search for `@BotFather`
3. Send `/newbot`
4. Choose a name: e.g., "My EUR USD Bot"
5. Choose a username: e.g., "my_eurusd_bot"
6. Copy the token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
7. Save it for later

### 1.2 Twelve Data API (5 min) - RECOMMENDED

1. Go to https://twelvedata.com
2. Click **"Get Free API Key"**
3. Sign up with email
4. Verify email
5. Go to dashboard
6. Copy your API key
7. Save it for later

**Why Twelve Data?**
- ✓ Real forex EUR/USD data
- ✓ 800 requests/day (enough for bot)
- ✓ 1-minute candles
- ✓ Best quality data

### 1.3 Alpha Vantage API (2 min) - OPTIONAL BACKUP

1. Go to https://www.alphavantage.co/support/#api-key
2. Enter your email
3. Get instant free key (no verification needed!)
4. Save it for later

**Why Alpha Vantage?**
- ✓ Instant free key
- ✓ Good backup when Twelve Data hits limit
- ⚠️ Only 25 requests/day (limited)

---

## 💻 Step 2: Install Python Dependencies

### Option A: Using pip (recommended)

```bash
cd pocsoc-trading-bot
pip install -r requirements.txt
```

### Option B: Using conda

```bash
conda create -n trading_bot python=3.10
conda activate trading_bot
pip install -r requirements.txt
```

### Verify Installation

```bash
python -c "import tensorflow; print('TensorFlow version:', tensorflow.__version__)"
python -c "import aiogram; print('Aiogram installed ✓')"
```

---

## ⚙️ Step 3: Configure the Bot

### 3.1 Create .env file

```bash
cd pocsoc-trading-bot
cp .env.template .env
```

### 3.2 Edit .env file

Open `.env` in a text editor and add your keys:

```bash
# Required
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# At least ONE of these (both is better)
TWELVE_DATA_API_KEY=your_twelvedata_key_here
ALPHA_VANTAGE_KEY=your_alphavantage_key_here
```

**Important:** 
- Replace `your_telegram_bot_token_here` with your actual token
- Add at least ONE forex API key
- Having both APIs gives you backup if one fails

---

## 🎯 Step 4: Run the Bot

### Start the Enhanced Bot

```bash
cd pocsoc-trading-bot
python PocSocSig_Enhanced.py
```

You should see:

```
==================================================
🚀 Enhanced EUR/USD Signal Bot Starting
==================================================
✓ Twelve Data API key found
✓ Alpha Vantage API key found
Config: Min Score=55, Confidence=45%
Analysis Interval: 3 minutes
```

### Start Your Bot on Telegram

1. Open Telegram
2. Search for your bot (the username you created)
3. Send `/start`
4. You should receive:
   ```
   🤖 Enhanced EUR/USD Signal Bot
   
   ✓ Real Forex Data APIs
   ✓ Advanced AI Model
   ✓ Multi-Indicator Analysis
   ✓ Risk Management
   
   📊 Press 'СИГНАЛ' for analysis
   📈 Press 'СТАТИСТИКА' for stats
   
   Starting automated analysis...
   ```

---

## 📊 Using the Bot

### Buttons

| Button | Function |
|--------|----------|
| 📊 СИГНАЛ | Get immediate analysis and signal |
| 📈 СТАТИСТИКА | View bot statistics and performance |
| ⚙️ НАСТРОЙКИ | View current configuration |
| 📜 ИСТОРИЯ | View recent signal history |

### Automated Signals

The bot will automatically analyze EUR/USD every **2 minutes** and send signals when:
- Score ≥ 55/100
- Confidence ≥ 60% (fixed)
- Not exceeding 12 signals per hour

### Signal Format

When a signal is generated:

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

## 🔧 Configuration Options

Edit `PocSocSig_Enhanced.py` line 39-50 to customize:

```python
CONFIG = {
    "analysis_interval_minutes": 2,  # How often to check (default: 2)
    "min_signal_score": 55,          # Minimum score (default: 55)
    "min_confidence": 60,            # Fixed confidence (default: 60)
    "max_signals_per_hour": 12,      # Rate limit (default: 12)
    "risk_reward_ratio": 1.8,        # R:R ratio (default: 1.8)
    "use_gpt": True,                 # Use GPT analysis (default: True)
}
```

### Recommended Settings

**Conservative (fewer, higher quality signals):**
```python
"min_signal_score": 65,
```

**Aggressive (more frequent signals):**
```python
"min_signal_score": 50,
```

---

## 📈 Understanding Signals

### Signal Components

1. **GPT-4o-mini (35% weight)**
   - AI analysis of market conditions
   - Considers all indicators together

2. **RSI - Relative Strength Index (main indicator)**
   - < 40: Oversold (bullish)
   - > 60: Overbought (bearish)

3. **MACD - Moving Average Convergence Divergence (main indicator)**
   - Positive: Bullish trend
   - Negative: Bearish trend

4. **Bollinger Bands (bonus confirmation)**
   - Price near lower band: bullish bonus
   - Price near upper band: bearish bonus

5. **ATR - Average True Range**
   - Used for Stop Loss/Take Profit calculation

6. **ADX - Trend Strength (display only)**
   - > 25: Strong trend

7. **Stochastic Oscillator (display only)**
   - Momentum indicator

### Scoring Formula

- **Final Score = GPT Weight (35%) × GPT Score + TA Weight (65%) × TA Score**
- **Minimum to Signal:** 55 points (configurable)
- **Confidence:** Fixed at 60% for signals

---

## 🐛 Troubleshooting

### Bot doesn't start

**Error: "BOT_TOKEN not found"**
- Check `.env` file exists
- Verify `BOT_TOKEN=...` has no spaces
- Make sure token is correct from BotFather

**Error: "No module named 'tensorflow'"**
```bash
pip install tensorflow==2.15.0
```

### No signals being sent

1. **Check API keys:**
   ```bash
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('TD:', bool(os.getenv('TWELVE_DATA_API_KEY')))"
   ```

2. **Lower thresholds:**
   Edit config:
   ```python
   "min_signal_score": 45,
   "min_confidence": 35,
   ```

3. **Check logs:**
   ```bash
   tail -f enhanced_bot.log
   ```

### API rate limits exceeded

**Twelve Data: 800 calls/day**
- With 2-min intervals: ~720 calls/day ✓
- If exceeded: Bot will use Alpha Vantage backup

**Alpha Vantage: 25 calls/day**
- Only used as backup
- If both fail: Bot uses Binance EURUSDT

### AI not training

**Check TensorFlow:**
```bash
python -c "import tensorflow as tf; print(tf.__version__)"
```

**Disable AI temporarily:**
```python
"use_ai": False,
```

---

## 📊 Performance Tips

### 1. Run on Server (24/7)

**Using screen:**
```bash
screen -S trading_bot
python PocSocSig_Enhanced.py
# Press Ctrl+A, then D to detach
# Reattach: screen -r trading_bot
```

**Using nohup:**
```bash
nohup python PocSocSig_Enhanced.py > bot_output.log 2>&1 &
```

### 2. Monitor Logs

```bash
# Watch in real-time (console output)
# Check errors in console output

# Check signals in console
grep "BUY\|SELL" console_output
```

### 3. Optimize Settings

Test different configurations:
- Start conservative (high thresholds)
- Monitor win rate
- Adjust based on performance

---

## 🆚 Comparing Old vs Enhanced Bot

| Feature | Old Bot | Enhanced Bot |
|---------|---------|--------------|
| Data Source | Real Forex APIs (Twelve Data) |
| AI Model | GPT-4o-mini |
| Indicators | RSI, MACD, BB, ADX, Stochastic, ATR |
| Signal Quality | Scored (0-100) |
| Risk Management | Stop Loss + Take Profit |
| Rate Limiting | 12 signals/hour max |
| Performance Tracking | Full history + stats + database |
| Error Handling | Comprehensive with fallbacks |
| Multi-user | Supported |

---

## 🎓 Next Steps

1. **Run for 24 hours** - Let AI train on more data
2. **Monitor performance** - Check win rate in stats
3. **Adjust thresholds** - Optimize for your style
4. **Add more features** - Customize indicators
5. **Backtest** - Test on historical data

---

## 📞 Support

- Check logs: `enhanced_bot.log`
- Review code comments in `PocSocSig_Enhanced.py`
- Test API keys independently
- Start with conservative settings

---

## ⚠️ Disclaimer

This bot is for **educational purposes only**. 

- Not financial advice
- Trading involves risk
- Test with demo accounts first
- Never risk money you can't afford to lose
- Past performance ≠ future results

---

## 🚀 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Got Telegram bot token from @BotFather
- [ ] Got Twelve Data API key (or Alpha Vantage)
- [ ] Installed requirements: `pip install -r requirements.txt`
- [ ] Created `.env` file with keys
- [ ] Started bot: `python PocSocSig_Enhanced.py`
- [ ] Sent `/start` to bot on Telegram
- [ ] Received first analysis

**Estimated Setup Time:** 20-30 minutes

Good luck trading! 📈

