#!/usr/bin/env python3
"""
Setup Validation Script for EUR/USD Trading Signal Bot
Checks that all prerequisites are met before running the bot.
"""

import sys
import os
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def check_python_version():
    """Check Python version"""
    print_header("1. Python Version Check")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major == 3 and version.minor >= 8:
        print_success(f"Python {version_str} (Minimum 3.8 required)")
        return True
    else:
        print_error(f"Python {version_str} - Need Python 3.8 or higher")
        print_info("Install Python 3.8+: https://www.python.org/downloads/")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print_header("2. Dependencies Check")
    
    required = {
        'aiohttp': 'HTTP client for async API calls',
        'aiogram': 'Telegram bot framework',
        'python-dotenv': 'Environment variable management',
        'APScheduler': 'Task scheduling',
        'pandas': 'Data processing',
        'ta': 'Technical analysis indicators',
        'openai': 'GPT integration',
        'httpx': 'HTTP client for OpenAI',
        'aiosqlite': 'Async SQLite database',
    }
    
    all_installed = True
    for package, description in required.items():
        try:
            if package == 'python-dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print_success(f"{package:20s} - {description}")
        except ImportError:
            print_error(f"{package:20s} - NOT INSTALLED ({description})")
            all_installed = False
    
    if not all_installed:
        print_info("\nInstall missing packages:")
        print(f"    pip3 install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and has required keys"""
    print_header("3. Environment Configuration Check")
    
    env_path = Path('.env')
    if not env_path.exists():
        print_error(".env file not found")
        print_info("Create .env file:")
        print(f"    cp .env.example .env")
        print(f"    nano .env  # Add your API keys")
        return False
    
    print_success(".env file exists")
    
    # Try to load and check keys
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        required_keys = {
            'BOT_TOKEN': 'Telegram bot token from @BotFather',
            'TWELVE_DATA_API_KEY': 'Twelve Data API key (primary data source)',
        }
        
        optional_keys = {
            'OPENAI_API_KEY': 'OpenAI API key (for GPT analysis)',
            'ALPHA_VANTAGE_KEY': 'Alpha Vantage API key (fallback data source)',
        }
        
        all_required_present = True
        for key, description in required_keys.items():
            value = os.getenv(key)
            if value and value != f"your_{key.lower()}_here" and len(value) > 10:
                print_success(f"{key:25s} - Set ({description})")
            else:
                print_error(f"{key:25s} - NOT SET or using placeholder ({description})")
                all_required_present = False
        
        for key, description in optional_keys.items():
            value = os.getenv(key)
            if value and value != f"your_{key.lower()}_here" and len(value) > 10:
                print_success(f"{key:25s} - Set ({description})")
            else:
                print_warning(f"{key:25s} - Not set (OPTIONAL: {description})")
        
        if not all_required_present:
            print_info("\nEdit .env file and add your API keys:")
            print(f"    nano .env")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Error loading .env: {e}")
        return False

def check_file_permissions():
    """Check file permissions"""
    print_header("4. File Permissions Check")
    
    main_file = Path('PocSocSig_Enhanced.py')
    if main_file.exists():
        if os.access(main_file, os.R_OK):
            print_success(f"Can read {main_file.name}")
        else:
            print_error(f"Cannot read {main_file.name}")
            return False
    else:
        print_error(f"{main_file.name} not found")
        return False
    
    # Check/create logs directory
    logs_dir = Path('logs')
    if not logs_dir.exists():
        try:
            logs_dir.mkdir()
            print_success("Created logs/ directory")
        except Exception as e:
            print_error(f"Cannot create logs/ directory: {e}")
            return False
    else:
        print_success("logs/ directory exists")
    
    if os.access(logs_dir, os.W_OK):
        print_success("Can write to logs/ directory")
    else:
        print_error("Cannot write to logs/ directory")
        print_info("Fix permissions: chmod 755 logs/")
        return False
    
    return True

def check_database():
    """Check database setup"""
    print_header("5. Database Check")
    
    db_path = Path('signals.db')
    if db_path.exists():
        print_success(f"Database file exists ({db_path.stat().st_size / 1024:.1f} KB)")
    else:
        print_warning("Database doesn't exist yet (will be auto-created on first run)")
    
    return True

def check_imports():
    """Try importing the main bot file"""
    print_header("6. Bot Code Check")
    
    try:
        sys.path.insert(0, '.')
        import PocSocSig_Enhanced
        print_success("Successfully imported PocSocSig_Enhanced.py - No syntax errors")
        return True
    except ImportError as e:
        # This is expected if dependencies aren't installed
        if "No module named" in str(e):
            print_warning(f"Cannot fully import bot (missing dependency: {e})")
            print_info("This is expected if dependencies aren't installed yet")
            return True  # Don't fail for missing deps, we already checked those
        else:
            print_error(f"Import error: {e}")
            return False
    except SyntaxError as e:
        print_error(f"Syntax error in code: {e}")
        return False
    except Exception as e:
        print_error(f"Error importing bot: {e}")
        return False

def print_summary(results):
    """Print final summary"""
    print_header("Validation Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}\n")
    
    for check, result in results.items():
        if result:
            print_success(check)
        else:
            print_error(check)
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL CHECKS PASSED! Ready to start the bot!{Colors.END}\n")
        print(f"{Colors.BLUE}Start the bot with:{Colors.END}")
        print(f"    python3 PocSocSig_Enhanced.py\n")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Some checks failed. Fix the issues above before starting.{Colors.END}\n")
        return False

def main():
    """Run all validation checks"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   EUR/USD Trading Signal Bot - Setup Validation          ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    results = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Environment Config": check_env_file(),
        "File Permissions": check_file_permissions(),
        "Database": check_database(),
        "Bot Code": check_imports(),
    }
    
    success = print_summary(results)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

