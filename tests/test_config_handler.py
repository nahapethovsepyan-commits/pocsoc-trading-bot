"""
Unit tests for config_handler
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced
from src.models.state import SUBSCRIBED_USERS as STATE_SUBSCRIBERS, user_languages as STATE_LANGUAGES


class TestConfigHandler:
    """Test config handler"""
    
    def setup_method(self):
        """Setup before each test"""
        # Clear state from both locations
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        PocSocSig_Enhanced.user_languages.clear()
        PocSocSig_Enhanced.ADMIN_USER_IDS.clear()
        STATE_SUBSCRIBERS.clear()
        STATE_LANGUAGES.clear()
    
    @pytest.mark.asyncio
    async def test_config_handler_min_score(self):
        """Test config handler for min_score"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        mock_message.text = "/config min_score=60"
        mock_message.answer = AsyncMock()
        
        # Add user to subscribed and admin list
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        PocSocSig_Enhanced.ADMIN_USER_IDS.add(12345)
        STATE_SUBSCRIBERS.add(12345)
        STATE_LANGUAGES[12345] = 'ru'
        
        original_value = PocSocSig_Enhanced.CONFIG["min_signal_score"]
        
        try:
            await PocSocSig_Enhanced.config_handler(mock_message)
            
            # Check config was updated
            assert PocSocSig_Enhanced.CONFIG["min_signal_score"] == 60
            assert mock_message.answer.called
        finally:
            # Restore original value
            PocSocSig_Enhanced.CONFIG["min_signal_score"] = original_value
    
    @pytest.mark.asyncio
    async def test_config_handler_min_confidence(self):
        """Test config handler for min_confidence"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        mock_message.text = "/config min_confidence=65"
        mock_message.answer = AsyncMock()
        
        # Add user to subscribed and admin list
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        PocSocSig_Enhanced.ADMIN_USER_IDS.add(12345)
        STATE_SUBSCRIBERS.add(12345)
        STATE_LANGUAGES[12345] = 'ru'
        
        original_value = PocSocSig_Enhanced.CONFIG["min_confidence"]
        
        try:
            await PocSocSig_Enhanced.config_handler(mock_message)
            
            # Check config was updated
            assert PocSocSig_Enhanced.CONFIG["min_confidence"] == 65
            assert mock_message.answer.called
        finally:
            # Restore original value
            PocSocSig_Enhanced.CONFIG["min_confidence"] = original_value
    
    @pytest.mark.asyncio
    async def test_config_handler_invalid_range(self):
        """Test config handler with invalid range"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        mock_message.text = "/config min_score=150"  # Invalid: > 100
        mock_message.answer = AsyncMock()
        
        # Add user to subscribed and admin list
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        PocSocSig_Enhanced.ADMIN_USER_IDS.add(12345)
        STATE_SUBSCRIBERS.add(12345)
        STATE_LANGUAGES[12345] = 'ru'
        
        original_value = PocSocSig_Enhanced.CONFIG["min_signal_score"]
        
        try:
            await PocSocSig_Enhanced.config_handler(mock_message)
            
            # Check config was NOT updated
            assert PocSocSig_Enhanced.CONFIG["min_signal_score"] == original_value
            assert mock_message.answer.called
            # Check error message was sent
            call_args = mock_message.answer.call_args[0][0]
            assert "between 0 and 100" in call_args or "❌" in call_args
        finally:
            # Restore original value
            PocSocSig_Enhanced.CONFIG["min_signal_score"] = original_value
    
    @pytest.mark.asyncio
    async def test_config_handler_no_equals(self):
        """Test config handler without equals sign"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        mock_message.text = "/config min_score"  # No = sign
        mock_message.answer = AsyncMock()
        
        # Add user to subscribed and admin list
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        PocSocSig_Enhanced.ADMIN_USER_IDS.add(12345)
        STATE_SUBSCRIBERS.add(12345)
        STATE_LANGUAGES[12345] = 'ru'
        
        await PocSocSig_Enhanced.config_handler(mock_message)
        
        # Check usage message was sent
        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "Usage" in call_args or "📝" in call_args
    
    @pytest.mark.asyncio
    async def test_config_handler_trading_hours_off(self):
        """Test config handler for trading_hours=off"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        mock_message.text = "/config trading_hours=off"
        mock_message.answer = AsyncMock()
        
        # Add user to subscribed and admin list
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        PocSocSig_Enhanced.ADMIN_USER_IDS.add(12345)
        STATE_SUBSCRIBERS.add(12345)
        STATE_LANGUAGES[12345] = 'ru'
        
        original_value = PocSocSig_Enhanced.CONFIG["trading_hours_enabled"]
        
        try:
            await PocSocSig_Enhanced.config_handler(mock_message)
            
            # Check config was updated
            assert PocSocSig_Enhanced.CONFIG["trading_hours_enabled"] == False
            assert mock_message.answer.called
        finally:
            # Restore original value
            PocSocSig_Enhanced.CONFIG["trading_hours_enabled"] = original_value
    
    @pytest.mark.asyncio
    async def test_config_handler_trading_hours_range(self):
        """Test config handler for trading_hours range"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        mock_message.text = "/config trading_hours=9-17"
        mock_message.answer = AsyncMock()
        
        # Add user to subscribed and admin list
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        PocSocSig_Enhanced.ADMIN_USER_IDS.add(12345)
        STATE_SUBSCRIBERS.add(12345)
        STATE_LANGUAGES[12345] = 'ru'
        
        original_start = PocSocSig_Enhanced.CONFIG["trading_start_hour"]
        original_end = PocSocSig_Enhanced.CONFIG["trading_end_hour"]
        original_enabled = PocSocSig_Enhanced.CONFIG["trading_hours_enabled"]
        
        try:
            await PocSocSig_Enhanced.config_handler(mock_message)
            
            # Check config was updated
            assert PocSocSig_Enhanced.CONFIG["trading_start_hour"] == 9
            assert PocSocSig_Enhanced.CONFIG["trading_end_hour"] == 17
            assert PocSocSig_Enhanced.CONFIG["trading_hours_enabled"] == True
            assert mock_message.answer.called
        finally:
            # Restore original values
            PocSocSig_Enhanced.CONFIG["trading_start_hour"] = original_start
            PocSocSig_Enhanced.CONFIG["trading_end_hour"] = original_end
            PocSocSig_Enhanced.CONFIG["trading_hours_enabled"] = original_enabled
    
    @pytest.mark.asyncio
    async def test_config_handler_not_subscribed(self):
        """Test config handler when user not subscribed"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        mock_message.text = "/config min_score=60"
        mock_message.answer = AsyncMock()
        
        # User NOT subscribed
        PocSocSig_Enhanced.SUBSCRIBED_USERS.discard(12345)
        
        await PocSocSig_Enhanced.config_handler(mock_message)
        
        # Check message was sent asking to subscribe
        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "start" in call_args.lower() or "subscribe" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_config_handler_non_admin(self):
        """Test config handler when user is not admin"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 99999  # Different user ID
        mock_message.text = "/config min_score=60"
        mock_message.answer = AsyncMock()
        
        # Add user to subscribed but NOT to admin list
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(99999)
        PocSocSig_Enhanced.user_languages[99999] = 'ru'
        PocSocSig_Enhanced.ADMIN_USER_IDS.discard(99999)  # Ensure not admin
        STATE_SUBSCRIBERS.add(99999)
        STATE_LANGUAGES[99999] = 'ru'
        
        await PocSocSig_Enhanced.config_handler(mock_message)
        
        # Check access denied message was sent
        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "denied" in call_args.lower() or "restricted" in call_args.lower() or "administrator" in call_args.lower()

