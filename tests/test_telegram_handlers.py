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
        
        # Mock bot and persistence
        with patch('PocSocSig_Enhanced.bot'):
            mock_message.answer = AsyncMock()
            with patch('PocSocSig_Enhanced.add_subscriber_to_db', new_callable=AsyncMock) as mock_add:
                await PocSocSig_Enhanced.start_handler(mock_message)
                
                # Check user was added
                assert mock_message.chat.id in PocSocSig_Enhanced.SUBSCRIBED_USERS
                
                # DB persistence called
                mock_add.assert_called_once()
                
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
        
        with patch('PocSocSig_Enhanced.add_subscriber_to_db', new_callable=AsyncMock):
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
        
        with patch('PocSocSig_Enhanced.get_expiration_keyboard') as mock_keyboard:
            keyboard = MagicMock()
            mock_keyboard.return_value = keyboard
            mock_message.answer = AsyncMock()
            
            await PocSocSig_Enhanced.manual_signal_handler(mock_message)
            
            # Ensure prompt was sent with keyboard
            mock_message.answer.assert_called_once()
            args, kwargs = mock_message.answer.call_args
            assert "⏱" in args[0] or "Choose" in args[0]
            assert kwargs.get('reply_markup') == keyboard
    
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
        
        t = PocSocSig_Enhanced.TEXTS['ru']
        with patch.dict(PocSocSig_Enhanced.CONFIG, {"max_signals_per_hour": 12}):
            with patch('PocSocSig_Enhanced.check_rate_limit', new_callable=AsyncMock) as mock_check:
                mock_check.return_value = False
                with patch('PocSocSig_Enhanced.bot') as mock_bot:
                    mock_bot.send_message = AsyncMock()
                    
                    await PocSocSig_Enhanced._run_manual_signal(12345, 'ru', t)
                    
                    # Check rate limit message was sent
                    mock_bot.send_message.assert_awaited()
                    args, _ = mock_bot.send_message.call_args
                    assert args[0] == 12345
                    assert args[1] == t['rate_limit']
    
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

