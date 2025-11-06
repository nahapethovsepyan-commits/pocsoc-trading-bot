# Deployment Checklist

**Date:** 2025-01-27  
**Status:** Ready for Deployment

---

## Prerequisites

### Required API Keys

Before deploying, you need the following API keys:

1. **BOT_TOKEN** (Required)
   - Get from: [@BotFather](https://t.me/BotFather) on Telegram
   - Command: `/newbot`
   - Format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

2. **TWELVE_DATA_API_KEY** (Required)
   - Get from: [Twelve Data](https://twelvedata.com)
   - Sign up for free account
   - Get API key from dashboard
   - Format: `your_api_key_here`

3. **OPENAI_API_KEY** (Optional but Recommended)
   - Get from: [OpenAI Platform](https://platform.openai.com)
   - Required for GPT-4o-mini AI analysis
   - Bot works without it, but signals are less accurate
   - Format: `sk-...`

4. **ALPHA_VANTAGE_KEY** (Optional)
   - Get from: [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
   - Used as fallback data source
   - Bot can work without it (uses Binance as fallback)
   - Format: `your_api_key_here`

---

## Pre-Deployment Steps

### Step 1: Environment Setup (5-15 minutes)

- [ ] Clone/download the repository
- [ ] Navigate to project directory
- [ ] Copy environment template: `cp env.example.txt .env`
- [ ] Edit `.env` file and add your API keys:
  ```bash
  BOT_TOKEN=your_telegram_bot_token_here
  TWELVE_DATA_API_KEY=your_twelve_data_api_key_here
  OPENAI_API_KEY=your_openai_api_key_here
  ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here
  ```
- [ ] Verify `.env` file is in `.gitignore` (should not be committed)

### Step 2: Install Dependencies (2-5 minutes)

- [ ] Ensure Python 3.8+ is installed (recommended: Python 3.10+)
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify installation: `python3 -c "import aiohttp, aiogram, openai, ta, pandas, aiosqlite; print('✅ All dependencies installed')"`

### Step 3: Validate Setup (1-2 minutes)

- [ ] Run validation script: `python3 validate_setup.py`
- [ ] Verify all checks pass:
  - ✅ Python Version
  - ✅ Dependencies
  - ✅ Environment Config (API keys set)
  - ✅ File Permissions
  - ✅ Database
  - ✅ Bot Code

### Step 4: Local Testing (10-15 minutes)

- [ ] Start bot locally: `python3 PocSocSig_Enhanced.py`
- [ ] Verify bot starts without errors
- [ ] Check logs for successful startup
- [ ] Open Telegram and find your bot
- [ ] Send `/start` command - should receive welcome message
- [ ] Send `/signal` command - should generate a signal
- [ ] Verify signal is saved to database (`signals.db` should be created)
- [ ] Test other commands: `/help`, `/stats`, `/config`
- [ ] Stop bot (Ctrl+C)

---

## Deployment Options

### Option A: Render.com (Recommended - Easiest)

**Time:** 15-20 minutes

- [ ] Go to [Render.com](https://render.com) and sign up/login
- [ ] Click "New" → "Background Worker"
- [ ] Connect your GitHub repository (or deploy from Git)
- [ ] Configure service:
  - **Name:** `pocsoc-trading-bot`
  - **Environment:** `Python 3`
  - **Build Command:** `pip install -r requirements.txt`
  - **Start Command:** `python PocSocSig_Enhanced.py`
  - **Plan:** `Free` or `Starter $7/mo`
- [ ] Add environment variables (from your `.env` file):
  - `BOT_TOKEN`
  - `TWELVE_DATA_API_KEY`
  - `OPENAI_API_KEY` (optional)
  - `ALPHA_VANTAGE_KEY` (optional)
- [ ] Click "Create Background Worker"
- [ ] Wait 2-5 minutes for deployment
- [ ] Check logs for successful startup
- [ ] Test bot in Telegram

**See:** `RENDER_DEPLOY.md` for detailed instructions

---

### Option B: Local Server / VPS (systemd)

**Time:** 20-30 minutes

- [ ] SSH into your server/VPS
- [ ] Clone repository to server
- [ ] Create `.env` file with API keys
- [ ] Install dependencies: `pip3 install -r requirements.txt`
- [ ] Create systemd service file:
  ```bash
  sudo nano /etc/systemd/system/trading-bot.service
  ```
- [ ] Add service configuration:
  ```ini
  [Unit]
  Description=EUR/USD Trading Signal Bot
  After=network.target

  [Service]
  Type=simple
  User=YOUR_USER
  WorkingDirectory=/path/to/pocsoc_final
  Environment="PATH=/usr/bin:/usr/local/bin"
  ExecStart=/usr/bin/python3 /path/to/pocsoc_final/PocSocSig_Enhanced.py
  Restart=always
  RestartSec=10

  [Install]
  WantedBy=multi-user.target
  ```
- [ ] Replace `YOUR_USER` and `/path/to/pocsoc_final` with actual values
- [ ] Enable and start service:
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable trading-bot
  sudo systemctl start trading-bot
  ```
- [ ] Check status: `sudo systemctl status trading-bot`
- [ ] View logs: `journalctl -u trading-bot -f`
- [ ] Test bot in Telegram

---

### Option C: Heroku

**Time:** 20-30 minutes

- [ ] Install Heroku CLI
- [ ] Login: `heroku login`
- [ ] Create app: `heroku create your-bot-name`
- [ ] Set environment variables:
  ```bash
  heroku config:set BOT_TOKEN=your_token
  heroku config:set TWELVE_DATA_API_KEY=your_key
  heroku config:set OPENAI_API_KEY=your_key
  heroku config:set ALPHA_VANTAGE_KEY=your_key
  ```
- [ ] Deploy: `git push heroku main`
- [ ] Check logs: `heroku logs --tail`
- [ ] Test bot in Telegram

---

## Post-Deployment Verification

### Immediate Checks (5 minutes)

- [ ] Bot responds to `/start` command
- [ ] Bot responds to `/help` command
- [ ] Bot generates signals with `/signal` command
- [ ] No errors in logs
- [ ] Database file created (`signals.db`)

### 24-Hour Monitoring

- [ ] Check logs daily for errors
- [ ] Verify signals are being generated
- [ ] Check database is growing (signals being saved)
- [ ] Monitor API usage (don't exceed rate limits)
- [ ] Verify bot stays online (no crashes)

### Performance Checks

- [ ] Signal generation time: Should be 4-6 seconds
- [ ] Bot response time: Should be < 1 second
- [ ] Memory usage: Should be stable
- [ ] CPU usage: Should be low (< 10% on VPS)

---

## Troubleshooting

### Bot Won't Start

**Symptoms:** Bot doesn't start or crashes immediately

**Solutions:**
1. Check API keys are set correctly in `.env`
2. Run `python3 validate_setup.py` to verify setup
3. Check Python version: `python3 --version` (need 3.8+)
4. Verify dependencies: `pip list | grep -E "aiohttp|aiogram|openai"`
5. Check logs for error messages

### Bot Doesn't Respond

**Symptoms:** Bot is running but doesn't respond to commands

**Solutions:**
1. Verify `BOT_TOKEN` is correct
2. Check bot is online in Telegram
3. Send `/start` command first (required for subscription)
4. Check logs for connection errors
5. Verify network connectivity

### No Signals Generated

**Symptoms:** `/signal` command returns "NO_SIGNAL"

**Solutions:**
1. Check `TWELVE_DATA_API_KEY` is valid
2. Verify API key has sufficient quota
3. Check logs for API errors
4. Try fallback APIs (Alpha Vantage or Binance)
5. Review signal thresholds in `src/config/settings.py`

### High API Usage

**Symptoms:** API rate limits exceeded

**Solutions:**
1. Reduce `analysis_interval_minutes` in config
2. Increase cache duration
3. Use multiple API keys (rotate)
4. Monitor API usage in provider dashboard

### Database Errors

**Symptoms:** Database locked or write errors

**Solutions:**
1. Check file permissions: `chmod 644 signals.db`
2. Verify disk space: `df -h`
3. Check database file isn't corrupted
4. Restart bot to release locks

---

## Maintenance

### Daily

- [ ] Check logs for errors
- [ ] Verify bot is online
- [ ] Monitor signal quality

### Weekly

- [ ] Review signal statistics (`/stats`)
- [ ] Check API usage
- [ ] Backup database: `cp signals.db backups/signals_$(date +%Y%m%d).db`

### Monthly

- [ ] Update dependencies: `pip install -r requirements.txt --upgrade`
- [ ] Review and optimize configuration
- [ ] Check for code updates
- [ ] Review audit logs: `logs/audit.log`

---

## Support Resources

### Documentation

- **Quick Start:** `DEPLOYMENT_QUICK_START.md`
- **API Keys Guide:** `API_KEYS_GUIDE.md`
- **Render Deploy:** `RENDER_DEPLOY.md`
- **Troubleshooting:** `TROUBLESHOOTING.md`
- **Production Readiness:** `PRODUCTION_READINESS_CHECKLIST.md`

### Commands Reference

```bash
# Start bot
python3 PocSocSig_Enhanced.py

# Validate setup
python3 validate_setup.py

# Check logs
tail -f logs/enhanced_bot.log

# Check database
sqlite3 signals.db "SELECT COUNT(*) FROM signals;"

# Backup database
cp signals.db backups/signals_$(date +%Y%m%d).db

# Check bot status (systemd)
sudo systemctl status trading-bot

# View logs (systemd)
journalctl -u trading-bot -f
```

---

## Success Criteria

Your deployment is successful when:

- ✅ Bot starts without errors
- ✅ Bot responds to `/start` command
- ✅ Bot generates signals with `/signal`
- ✅ Signals are saved to database
- ✅ No errors in logs for 24 hours
- ✅ Bot stays online (no crashes)

---

## Next Steps After Deployment

1. **Monitor for 24 hours** - Watch logs and verify stability
2. **Test all commands** - Ensure everything works
3. **Review signal quality** - Check if signals are accurate
4. **Adjust configuration** - Tune thresholds if needed
5. **Set up monitoring** - Configure alerts if desired
6. **Backup database** - Regular backups recommended

---

**Last Updated:** 2025-01-27  
**Status:** Ready for Deployment ✅

