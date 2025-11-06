# Deployment Quick Start Guide

This guide provides quick commands for each deployment method.

---

## Prerequisites

1. ✅ Add your API keys to `.env` file
2. ✅ Run `python3 validate_setup.py` - should pass all checks
3. ✅ Test locally: `python3 PocSocSig_Enhanced.py`

---

## Option A: Render.com (Recommended - Easiest)

### Steps:
1. Go to https://render.com and sign up
2. Click "New" → "Background Worker"
3. Connect your GitHub repository
4. Configure:
   - **Name:** `pocsoc-trading-bot`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python PocSocSig_Enhanced.py`
   - **Plan:** `Free` or `Starter $7/mo`
5. Add environment variables (from your `.env` file):
   - `BOT_TOKEN`
   - `TWELVE_DATA_API_KEY`
   - `OPENAI_API_KEY` (optional)
   - `ALPHA_VANTAGE_KEY` (optional)
6. Click "Create Background Worker"
7. Wait 2-5 minutes for deployment
8. Check logs for successful startup

**See:** `RENDER_DEPLOY.md` for detailed instructions

---

## Option B: Local Server / VPS (systemd)

### Steps:
1. Copy service file:
   ```bash
   sudo cp trading-bot.service /etc/systemd/system/trading-bot.service
   ```

2. Edit service file:
   ```bash
   sudo nano /etc/systemd/system/trading-bot.service
   ```
   - Replace `YOUR_USER` with your username
   - Replace `/path/to/pocsoc_final` with actual path

3. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable trading-bot
   sudo systemctl start trading-bot
   ```

4. Check status:
   ```bash
   sudo systemctl status trading-bot
   ```

5. View logs:
   ```bash
   journalctl -u trading-bot -f
   ```

---

## Option C: Heroku

### Steps:
1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli

2. Login:
   ```bash
   heroku login
   ```

3. Create app:
   ```bash
   heroku create your-bot-name
   ```

4. Set environment variables:
   ```bash
   heroku config:set BOT_TOKEN=your_token
   heroku config:set TWELVE_DATA_API_KEY=your_key
   heroku config:set OPENAI_API_KEY=your_key
   ```

5. Deploy:
   ```bash
   git push heroku main
   ```

6. Check logs:
   ```bash
   heroku logs --tail
   ```

---

## Post-Deployment Verification

### 1. Check Bot is Running
- View deployment platform logs
- Look for: "🚀 Enhanced EUR/USD Signal Bot Starting"
- Verify: "✓ Database initialized"

### 2. Test Telegram Bot
- Open Telegram, find your bot
- Send `/start` - should respond immediately
- Send `/signal` - should generate signal within 10 seconds
- Send `/health` - should show system status

### 3. Monitor First Signals
- Wait 2-5 minutes for automatic signal generation
- Verify signals are being generated (if market is open)
- Check signal quality and format

---

## Troubleshooting

### Bot won't start
- Check logs for errors
- Verify all environment variables are set
- Check Python version (3.8+)

### No signals
- Check trading hours (default: 24/7 UTC)
- Verify API keys are valid
- Lower thresholds in CONFIG if needed

### API rate limits
- Check `/metrics` command
- Increase cache duration in CONFIG
- Verify API usage at provider dashboard

**See:** `TROUBLESHOOTING.md` for more help

---

## Monitoring

### Logs
- **Render/Heroku:** Use platform's log viewer
- **Local/VPS:** `journalctl -u trading-bot -f` or `tail -f logs/enhanced_bot.log`

### Health Checks
- Use `/health` command in Telegram
- Monitor via platform metrics (CPU, memory)
- Set up UptimeRobot for external monitoring

### Database Backups
- **Local/VPS:** Set up cron job:
  ```bash
  0 */6 * * * cd /path/to/bot && python3 backup_db.py
  ```
- **Cloud:** Use platform backup features

---

**Ready to deploy?** Choose your method above and follow the steps!

