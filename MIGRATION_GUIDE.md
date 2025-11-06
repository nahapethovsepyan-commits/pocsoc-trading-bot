# Migration Guide: From Monolithic to Modular Structure

## Overview

This guide helps you understand the changes made during Phase 1-2 refactoring and how to work with the new modular structure.

---

## What Changed?

### Before (Monolithic)
- Single file: `PocSocSig_Enhanced.py` (~2908 lines)
- All code in one place
- Hard to maintain and test

### After (Modular)
- Main file: `PocSocSig_Enhanced.py` (776 lines, 73% reduction)
- 9 modules in `src/` directory
- Clean separation of concerns
- Easy to maintain and test

---

## Key Changes

### 1. Configuration

**Before:**
```python
# In PocSocSig_Enhanced.py
CONFIG = {...}
BOT_TOKEN = os.getenv("BOT_TOKEN")
```

**After:**
```python
# Import from modules
from src.config import CONFIG, get_bot_token, get_api_keys
BOT_TOKEN = get_bot_token()
```

**Location:** `src/config/settings.py` and `src/config/env.py`

---

### 2. Global State

**Before:**
```python
# In PocSocSig_Enhanced.py
SUBSCRIBED_USERS = set()
STATS = {...}
```

**After:**
```python
# Import from modules
from src.models.state import SUBSCRIBED_USERS, STATS, stats_lock
```

**Location:** `src/models/state.py`

---

### 3. Database Operations

**Before:**
```python
# In PocSocSig_Enhanced.py
async def init_database():
    ...
```

**After:**
```python
# Import from modules
from src.database import init_database, save_signal_to_db
await init_database()
```

**Location:** `src/database/repository.py`

---

### 4. API Calls

**Before:**
```python
# In PocSocSig_Enhanced.py
async def fetch_forex_data():
    ...
```

**After:**
```python
# Import from modules
from src.api import fetch_forex_data
df = await fetch_forex_data()
```

**Location:** `src/api/fetcher.py`

---

### 5. Signal Generation

**Before:**
```python
# In PocSocSig_Enhanced.py
async def generate_signal():
    ...
```

**After:**
```python
# Import from modules
from src.signals import generate_signal, main_analysis
signal = await generate_signal()
```

**Location:** `src/signals/generator.py`

---

### 6. Dependency Injection

**Important Change:** Some functions now require dependencies to be passed:

**Before:**
```python
# Functions accessed bot and TEXTS directly
await main_analysis()
await check_system_health()
```

**After:**
```python
# Functions receive dependencies as parameters
await main_analysis(bot=bot, TEXTS=TEXTS)
await check_system_health(bot=bot)
```

**Why?** Avoids circular dependencies and makes testing easier.

---

## Working with the New Structure

### Adding a New Feature

1. **Identify the module:**
   - Database? → `src/database/`
   - API? → `src/api/`
   - Indicator? → `src/indicators/`
   - Signal logic? → `src/signals/`

2. **Add your code to the appropriate module**

3. **Export from `__init__.py`:**
   ```python
   # src/your_module/__init__.py
   from .your_file import your_function
   __all__ = ['your_function']
   ```

4. **Import in main file:**
   ```python
   from src.your_module import your_function
   ```

### Modifying Configuration

**Edit:** `src/config/settings.py`

```python
CONFIG = {
    "your_setting": value,
    ...
}
```

### Adding a New Handler

1. **Add handler function in `PocSocSig_Enhanced.py`**
2. **Use decorators:**
   ```python
   @dp.message(Command("your_command"))
   @require_subscription
   @with_error_handling
   async def your_handler(message):
       ...
   ```

### Adding a New API Source

1. **Create new file:** `src/api/yoursource.py`
2. **Add fetch function:**
   ```python
   async def fetch_from_yoursource(pair, session):
       ...
   ```
3. **Update:** `src/api/fetcher.py` to include new source

---

## Common Tasks

### Changing Signal Logic

**File:** `src/signals/generator.py`
- Function: `generate_signal()`
- Modify scoring logic, thresholds, etc.

### Adding a New Indicator

**File:** `src/indicators/calculator.py`
- Add calculation function
- Update `calculate_indicators_parallel()`
- Add to scoring in `calculate_ta_score()`

### Modifying Database Schema

**File:** `src/database/repository.py`
- Update `init_database()` to add new tables/columns
- Update `save_signal_to_db()` if needed

### Changing Localization

**File:** `src/telegram/localization.py`
- Edit `TEXTS` dictionary
- Add new languages if needed

---

## Testing

### Run Integration Tests

```bash
python3 test_phase3_integration.py
```

### Test Individual Modules

```python
# Test config
from src.config import CONFIG
print(CONFIG)

# Test database
from src.database import init_database
await init_database()

# Test API
from src.api import fetch_forex_data
df = await fetch_forex_data()
```

---

## Troubleshooting

### Import Errors

**Problem:** `ImportError: cannot import name 'X' from 'src.module'`

**Solution:**
1. Check `src/module/__init__.py` exports the function
2. Verify the function exists in the module
3. Check for circular dependencies

### Missing Dependencies

**Problem:** Function requires `bot` or `TEXTS` parameter

**Solution:**
- Pass dependencies when calling:
  ```python
  await function_name(bot=bot, TEXTS=TEXTS)
  ```

### Module Not Found

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
- Ensure you're running from project root
- Check Python path includes current directory

---

## Benefits of New Structure

1. **Maintainability:** Easy to find and modify code
2. **Testability:** Each module can be tested independently
3. **Scalability:** Easy to add new features
4. **Readability:** Clear organization
5. **Reusability:** Modules can be reused

---

## Quick Reference

| Old Location | New Location |
|--------------|--------------|
| `CONFIG` dict | `src/config/settings.py` |
| `init_database()` | `src/database/repository.py` |
| `fetch_forex_data()` | `src/api/fetcher.py` |
| `generate_signal()` | `src/signals/generator.py` |
| `TEXTS` dict | `src/telegram/localization.py` |
| Global state | `src/models/state.py` |
| Helper functions | `src/utils/helpers.py` |

---

*Last updated: Phase 4 - December 2024*

