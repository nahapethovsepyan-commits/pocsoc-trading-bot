"""
Unit tests for Telegram handlers
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestTelegramHandlers:
    """Test Telegram bot handlers"""
    
    @pytest.mark.asyncio
    async def test_start_handler(self):
        """Test /start command handler"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        
        # Mock bot and message.answer
        with patch('PocSocSig_Enhanced.bot') as mock_bot:
            mock_message.answer = AsyncMock()
            
            await PocSocSig_Enhanced.start_handler(mock_message)
            
            # Check user was added
            assert mock_message.chat.id in PocSocSig_Enhanced.SUBSCRIBED_USERS
            
            # Check message was sent
            mock_message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_language_handler(self):
        """Test language selection handler"""
        # Mock callback
        mock_callback = MagicMock()
        mock_callback.data = "lang_ru"
        mock_callback.message.chat.id = 12345
        mock_callback.message.answer = AsyncMock()
        mock_callback.answer = AsyncMock()
        
        # Mock scheduler
        with patch('PocSocSig_Enhanced.scheduler') as mock_scheduler:
            mock_scheduler.running = False
            mock_scheduler.add_job = MagicMock()
            
            await PocSocSig_Enhanced.language_handler(mock_callback)
            
            # Check language was set
            assert PocSocSig_Enhanced.user_languages[12345] == "ru"
            
            # Check messages were sent
            mock_callback.message.answer.assert_called_once()
            mock_callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_manual_signal_handler(self):
        """Test manual signal request handler"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        
        # Add user to subscribed
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        
        # Mock signal generation
        mock_signal = {
            "signal": "BUY",
            "price": 1.0800,
            "score": 65,
            "confidence": 60,
            "reasoning": "Test signal",
            "time": datetime.now(),
            "indicators": {},
            "atr": 0.0003
        }
        
        with patch('PocSocSig_Enhanced.generate_signal', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_signal
            with patch('PocSocSig_Enhanced.send_signal_message', new_callable=AsyncMock):
                with patch('PocSocSig_Enhanced.bot') as mock_bot:
                    mock_message.answer = AsyncMock()
                    
                    await PocSocSig_Enhanced.manual_signal_handler(mock_message)
                    
                    # Check signal was generated
                    mock_generate.assert_called_once()
                    
                    # Check message was sent (analyzing message)
                    assert mock_message.answer.called
    
    @pytest.mark.asyncio
    async def test_manual_signal_handler_rate_limit(self):
        """Test manual signal handler with rate limit"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        
        # Add user to subscribed
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        
        # Set rate limit exceeded
        PocSocSig_Enhanced.STATS["signals_per_hour"] = 15
        PocSocSig_Enhanced.STATS["hour_start"] = datetime.now()
        
        with patch.dict(PocSocSig_Enhanced.CONFIG, {"max_signals_per_hour": 12}):
            with patch('PocSocSig_Enhanced.check_rate_limit', new_callable=AsyncMock) as mock_check:
                mock_check.return_value = False
                with patch('PocSocSig_Enhanced.bot') as mock_bot:
                    mock_message.answer = AsyncMock()
                    
                    await PocSocSig_Enhanced.manual_signal_handler(mock_message)
                    
                    # Check rate limit message was sent
                    assert mock_message.answer.called
                    call_args = mock_message.answer.call_args[0][0]
                    assert "лимит" in call_args.lower() or "limit" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_get_main_keyboard(self):
        """Test main keyboard generation"""
        # Test Russian keyboard
        keyboard_ru = PocSocSig_Enhanced.get_main_keyboard('ru')
        assert keyboard_ru is not None
        
        # Test English keyboard
        keyboard_en = PocSocSig_Enhanced.get_main_keyboard('en')
        assert keyboard_en is not None
        
        # Test default (should be Russian)
        keyboard_default = PocSocSig_Enhanced.get_main_keyboard()
        assert keyboard_default is not None

