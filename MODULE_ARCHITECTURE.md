# Module Architecture Documentation

## 📁 Project Structure

After Phase 1-2 refactoring, the project is now organized into a clean modular structure:

```
pocsoc_final/
├── PocSocSig_Enhanced.py    # Main entry point (776 lines)
├── requirements.txt          # Python dependencies
├── render.yaml              # Render.com deployment config
├── runtime.txt              # Python version
├── env.example.txt          # Environment variables template
│
└── src/                     # Modular source code
    ├── __init__.py
    │
    ├── config/              # Configuration management
    │   ├── __init__.py
    │   ├── env.py          # Environment variables loading
    │   └── settings.py     # CONFIG dictionary
    │
    ├── utils/               # Utility functions
    │   ├── __init__.py
    │   ├── helpers.py      # Helper functions (safe_divide, format_time, etc.)
    │   └── http_session.py # HTTP session management
    │
    ├── models/              # Data models and state
    │   ├── __init__.py
    │   └── state.py        # Global state (STATS, METRICS, locks, caches)
    │
    ├── database/            # Database operations
    │   ├── __init__.py
    │   └── repository.py   # SQLite operations (init, save, load, backup)
    │
    ├── api/                 # API clients
    │   ├── __init__.py
    │   ├── twelvedata.py   # Twelve Data API client
    │   ├── alphavantage.py # Alpha Vantage API client
    │   ├── binance.py      # Binance API client
    │   └── fetcher.py      # Main fetcher with parallel fallback
    │
    ├── indicators/          # Technical indicators
    │   ├── __init__.py
    │   └── calculator.py   # Indicator calculations (RSI, MACD, BB, etc.)
    │
    ├── signals/             # Signal generation
    │   ├── __init__.py
    │   ├── generator.py    # Signal generation logic + main_analysis
    │   ├── messaging.py    # Signal messaging functions
    │   └── utils.py        # Signal utilities (trading hours, rate limit)
    │
    ├── monitoring/          # System monitoring
    │   ├── __init__.py
    │   └── health.py       # Health checks and alerts
    │
    └── telegram/            # Telegram bot components
        ├── __init__.py
        ├── localization.py # TEXTS dictionary (ru/en)
        ├── keyboards.py    # Keyboard definitions
        ├── decorators.py   # Handler decorators (@require_subscription, etc.)
        └── handlers/       # Handler modules (placeholder)
            └── __init__.py
```

---

## 🔄 Dependency Injection Pattern

To avoid circular dependencies, the project uses **dependency injection**:

### Functions that require dependencies:

1. **`main_analysis(bot=None, TEXTS=None)`**
   - Located in: `src/signals/generator.py`
   - Requires: `bot` (Telegram Bot instance), `TEXTS` (localization dict)
   - Usage: Called from scheduler with `await main_analysis(bot=bot, TEXTS=TEXTS)`

2. **`check_system_health(bot)`**
   - Located in: `src/monitoring/health.py`
   - Requires: `bot` (Telegram Bot instance)
   - Usage: Called from scheduler with `await check_system_health(bot=bot)`

3. **`send_signal_message(signal_data, lang, bot=None, TEXTS=None)`**
   - Located in: `src/signals/messaging.py`
   - Requires: `bot` and `TEXTS`
   - Usage: Called from handlers with `await send_signal_message(signal_data, lang, bot=bot, TEXTS=TEXTS)`

### Why Dependency Injection?

- **Avoids circular imports:** Modules don't need to import bot/telegram components
- **Better testability:** Easy to mock dependencies in tests
- **Cleaner architecture:** Clear separation of concerns

---

## 📦 Module Responsibilities

### `src/config/`
- **env.py:** Loads environment variables (BOT_TOKEN, API keys)
- **settings.py:** Central CONFIG dictionary with all bot settings

### `src/utils/`
- **helpers.py:** Utility functions (safe_divide, format_time, sanitize_user_input)
- **http_session.py:** HTTP session management (get_http_session, close_http_session)

### `src/models/`
- **state.py:** Global state variables:
  - `SUBSCRIBED_USERS` (set)
  - `STATS` (dict)
  - `SIGNAL_HISTORY` (deque)
  - `API_CACHE`, `INDICATOR_CACHE` (OrderedDict)
  - `METRICS` (dict)
  - Locks: `stats_lock`, `history_lock`, `config_lock`, etc.

### `src/database/`
- **repository.py:** All database operations:
  - `init_database()` - Create tables
  - `save_signal_to_db()` - Save signal
  - `load_recent_signals_from_db()` - Load history
  - `save_stats_to_db()` - Save statistics
  - `backup_database()` - Create backup

### `src/api/`
- **twelvedata.py:** Twelve Data API client
- **alphavantage.py:** Alpha Vantage API client
- **binance.py:** Binance API client (fallback)
- **fetcher.py:** Main fetcher with parallel API fallback

### `src/indicators/`
- **calculator.py:** All technical indicator calculations:
  - `calculate_ta_score()` - Technical analysis scoring
  - `calculate_indicators_parallel()` - Parallel indicator calculation
  - `get_adaptive_cache_duration()` - Adaptive caching
  - `get_adaptive_thresholds()` - Adaptive signal thresholds
  - `analyze_volume()` - Volume analysis
  - `calculate_confidence()` - Dynamic confidence calculation

### `src/signals/`
- **generator.py:** Signal generation:
  - `generate_signal()` - Main signal generation logic
  - `main_analysis()` - Scheduled analysis function
- **messaging.py:** Signal messaging:
  - `send_signal_message()` - Send to all users
  - `send_signal_to_user()` - Send to single user
- **utils.py:** Signal utilities:
  - `is_trading_hours()` - Trading hours check
  - `check_rate_limit()` - Rate limiting
  - `get_local_time()` - Local time with timezone
  - `clean_markdown()` - Markdown cleaning

### `src/monitoring/`
- **health.py:** System monitoring:
  - `check_system_health()` - Health check with alerts
  - `send_alert()` - Send alert to users

### `src/telegram/`
- **localization.py:** `TEXTS` dictionary (ru/en)
- **keyboards.py:** Keyboard definitions (`get_main_keyboard()`, `language_keyboard`)
- **decorators.py:** Handler decorators:
  - `@require_subscription` - Check user subscription
  - `@with_error_handling` - Error handling wrapper
  - `get_user_locale()` - Get user language

---

## 🔗 Module Dependencies

```
PocSocSig_Enhanced.py (main)
    ↓
    ├── src.config → CONFIG, API keys
    ├── src.models.state → Global state
    ├── src.database → DB operations
    ├── src.api → Fetch forex data
    ├── src.signals → Generate signals
    ├── src.monitoring → Health checks
    └── src.telegram → UI components

src.signals.generator
    ↓
    ├── src.api → fetch_forex_data()
    ├── src.indicators → calculate_indicators_parallel()
    └── src.config → CONFIG

src.signals.messaging
    ↓
    ├── src.models.state → SUBSCRIBED_USERS, STATS
    ├── src.database → save_signal_to_db()
    └── src.telegram → TEXTS (via dependency injection)

src.monitoring.health
    ↓
    ├── src.models.state → METRICS, STATS
    └── src.telegram → bot (via dependency injection)
```

---

## 🎯 Key Design Patterns

### 1. Dependency Injection
- Functions receive `bot` and `TEXTS` as parameters
- Avoids circular dependencies
- Makes testing easier

### 2. Centralized State
- All global state in `src/models/state.py`
- Thread-safe with async locks
- Easy to manage and test

### 3. Modular Structure
- Each module has single responsibility
- Clear separation of concerns
- Easy to maintain and extend

### 4. Error Handling
- Decorators for handler error handling
- Try-except blocks in all critical functions
- Graceful degradation

---

## 📊 Code Statistics

- **Main file:** 776 lines (down from 2908, 73% reduction)
- **Modules:** 9 modules, 29 Python files
- **Total code:** ~3000+ lines (well-organized)
- **Test coverage:** Integration tests passing

---

## 🚀 Benefits of Modular Structure

1. **Maintainability:** Easy to find and modify code
2. **Testability:** Each module can be tested independently
3. **Scalability:** Easy to add new features
4. **Readability:** Clear structure and organization
5. **Reusability:** Modules can be reused in other projects

---

*Last updated: Phase 4 - December 2024*

