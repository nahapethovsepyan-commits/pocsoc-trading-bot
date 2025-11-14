"""
Telegram bot localization strings.
"""

TEXTS = {
    'ru': {
        'choose_language': "Выберите язык / Choose language",
        'welcome': (
            "🤖 Улучшенный бот сигналов для EUR/USD\n\n"
            "✓ Реальные API данных Forex\n"
            "✓ Продвинутый ИИ-модель\n"
            "✓ Анализ нескольких индикаторов\n"
            "✓ Управление рисками\n\n"
            "📊 Нажмите 'СИГНАЛ' для анализа\n"
            "📈 Нажмите 'СТАТИСТИКА' для статистики\n\n"
            "Запуск автоматического анализа..."
        ),
        'analyzing': "🤖 Анализ EUR/USD... (макс 10 сек)",
        'rate_limit': "⏱️ Достигнут лимит. Попробуйте позже.",
        'timeout': "⏱️ Таймаут анализа. Попробуйте снова.",
        'error': "❌ Ошибка: {error}",
        'stats_title': "📊 Статистика\n\n",
        'stats_total': "Всего сигналов: {total}\n",
        'stats_call': "BUY: {call}\n",
        'stats_put': "SELL: {put}\n",
        'stats_ai': "AI-сигналы: {ai}\n\n",
        'stats_wins': "Победы: {wins}\n",
        'stats_losses': "Поражения: {losses}\n",
        'stats_winrate': "Процент побед: {winrate:.1f}%\n\n",
        'stats_api': "Источник API: {api}\n",
        'stats_interval': "Интервал: {interval} мин\n",
        'settings_title': "⚙️ Настройки\n\n",
        'settings_min_score': "Мин. балл: {score}/100\n",
        'settings_min_conf': "Мин. уверенность: {conf}%\n",
        'settings_ai_weight': "Вес ИИ: {weight}%\n",
        'settings_rr': "Риск/Прибыль: 1:{rr}\n",
        'settings_lookback': "Обзор: {lookback} мин\n",
        'settings_max_signals': "Макс. сигналов/час: {max}\n",
        'history_title': "📜 Недавние сигналы\n\n",
        'no_history': "Нет истории сигналов.",
        'unsubscribed': "✅ Вы отписались от сигналов",
        'not_subscribed': "ℹ️ Вы не подписаны. Отправьте /start для подписки.",
        'signal_alert': "ТОРГОВЫЙ СИГНАЛ",
        'signal_pair': "Пара: EUR/USD",
        'signal_action': "Действие: {action}",
        'signal_price': "Цена: {price:.5f}",
        'signal_score': "Балл: {score}/100",
        'signal_conf': "Уверенность: {conf}%",
        'signal_po_rec': "Рекомендации POCKETOPTION:",
        'signal_exp_minutes': "Срок: {exp} минут",
        'signal_exp_seconds': "Срок: {exp} секунд",
        'signal_bet': "Размер ставки: {bet:.1f}% баланса",
        'signal_suggested': "Рекомендуемая: ${suggested:.0f} (если баланс = $1000)",
        'signal_risk': "Уровень риска: {risk}",
        'signal_risk_mgmt': "Управление рисками:",
        'signal_sl': "Стоп-лосс: {sl:.5f}",
        'signal_tp': "Тейк-профит: {tp:.5f}",
        'signal_rr': "R:R = 1:{rr:.1f}",
        'signal_analysis': "Анализ:",
        'signal_gpt': "GPT: {reasoning}",
        'signal_scores': "Баллы:",
        'signal_call_score': "CALL: {call}/100",
        'signal_put_score': "PUT: {put}/100",
        'signal_conf2': "Уверенность: {conf}%",
        'signal_why_no': "Почему нет сигнала:",
        'signal_time': "⏰ {time}",
        'indicators': "Индикаторы:",
        'risk_low': "LOW",
        'risk_medium': "MEDIUM",
        'risk_high': "HIGH",
        'select_expiration': "⏱️ Выберите срок экспирации:",
        'expiration_saved': "✅ Срок {exp} установлен. Запускаю анализ...",
        'expiration_button_seconds': "{value} сек",
        'expiration_button_minutes': "{value} мин",
        'expiration_not_supported': "⚠️ Такой срок недоступен.",
        'expiration_no_users': "Нет подписчиков для отправки сигнала."
    },
    'en': {
        'choose_language': "Choose language / Выберите язык",
        'welcome': (
            "🤖 Enhanced EUR/USD Signal Bot\n\n"
            "✓ Real Forex Data APIs\n"
            "✓ Advanced AI Model\n"
            "✓ Multi-Indicator Analysis\n"
            "✓ Risk Management\n\n"
            "📊 Press 'SIGNAL' for analysis\n"
            "📈 Press 'STATISTICS' for stats\n\n"
            "Starting automated analysis..."
        ),
        'analyzing': "🤖 Analyzing EUR/USD... (max 10 sec)",
        'rate_limit': "⏱️ Rate limit reached. Try later.",
        'timeout': "⏱️ Analysis timeout. Try again.",
        'error': "❌ Error: {error}",
        'stats_title': "📊 Statistics\n\n",
        'stats_total': "Total Signals: {total}\n",
        'stats_call': "BUY: {call}\n",
        'stats_put': "SELL: {put}\n",
        'stats_ai': "AI Signals: {ai}\n\n",
        'stats_wins': "Wins: {wins}\n",
        'stats_losses': "Losses: {losses}\n",
        'stats_winrate': "Win Rate: {winrate:.1f}%\n\n",
        'stats_api': "API Source: {api}\n",
        'stats_interval': "Interval: {interval} min\n",
        'settings_title': "⚙️ Configuration\n\n",
        'settings_min_score': "Min Score: {score}/100\n",
        'settings_min_conf': "Min Confidence: {conf}%\n",
        'settings_ai_weight': "AI Weight: {weight}%\n",
        'settings_rr': "Risk/Reward: 1:{rr}\n",
        'settings_lookback': "Lookback: {lookback} min\n",
        'settings_max_signals': "Max Signals/Hour: {max}\n",
        'history_title': "📜 Recent Signals\n\n",
        'no_history': "No signal history yet.",
        'unsubscribed': "✅ You have unsubscribed from signals",
        'not_subscribed': "ℹ️ You are not subscribed. Send /start to subscribe.",
        'signal_alert': "TRADING SIGNAL",
        'signal_pair': "Pair: EUR/USD",
        'signal_action': "Action: {action}",
        'signal_price': "Price: {price:.5f}",
        'signal_score': "Score: {score}/100",
        'signal_conf': "Confidence: {conf}%",
        'signal_po_rec': "POCKETOPTION RECOMMENDATIONS:",
        'signal_exp_minutes': "Expiration: {exp} minutes",
        'signal_exp_seconds': "Expiration: {exp} seconds",
        'signal_bet': "Bet Size: {bet:.1f}% of balance",
        'signal_suggested': "Suggested: ${suggested:.0f} (if balance = $1000)",
        'signal_risk': "Risk Level: {risk}",
        'signal_risk_mgmt': "Risk Management:",
        'signal_sl': "Stop Loss: {sl:.5f}",
        'signal_tp': "Take Profit: {tp:.5f}",
        'signal_rr': "R:R = 1:{rr:.1f}",
        'signal_analysis': "Analysis:",
        'signal_gpt': "GPT: {reasoning}",
        'signal_scores': "Scores:",
        'signal_call_score': "CALL: {call}/100",
        'signal_put_score': "PUT: {put}/100",
        'signal_conf2': "Confidence: {conf}%",
        'signal_why_no': "Why no signal:",
        'signal_time': "⏰ {time}",
        'indicators': "Indicators:",
        'risk_low': "LOW",
        'risk_medium': "MEDIUM",
        'risk_high': "HIGH",
        'select_expiration': "⏱️ Choose expiration:",
        'expiration_saved': "✅ Expiration {exp} set. Running analysis...",
        'expiration_button_seconds': "{value}s",
        'expiration_button_minutes': "{value}m",
        'expiration_not_supported': "⚠️ This expiration is not available.",
        'expiration_no_users': "No subscribers to send the signal."
    }
}

