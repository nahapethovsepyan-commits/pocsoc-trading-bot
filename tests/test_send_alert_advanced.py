"""
Advanced tests for send_alert function
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestSendAlertAdvanced:
    """Advanced tests for send_alert"""
    
    @pytest.mark.asyncio
    async def test_send_alert_multiple_users(self):
        """Test sending alert to multiple users"""
        # Clear and add multiple users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        user1 = 11111
        user2 = 22222
        user3 = 33333
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(user1)
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(user2)
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(user3)
        
        with patch('PocSocSig_Enhanced.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()
            
            await PocSocSig_Enhanced.send_alert("Test alert message")
            
            # Should send to all users
            assert mock_bot.send_message.call_count == 3
    
    @pytest.mark.asyncio
    async def test_send_alert_with_failures(self):
        """Test sending alert when some sends fail"""
        # Clear and add users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        user1 = 11111
        user2 = 22222
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(user1)
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(user2)
        
        call_count = 0
        async def mock_send(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Failed to send")
            return MagicMock()
        
        with patch('PocSocSig_Enhanced.bot') as mock_bot:
            mock_bot.send_message = AsyncMock(side_effect=mock_send)
            
            # Should complete without raising
            await PocSocSig_Enhanced.send_alert("Test alert")
            
            # Should attempt to send to both
            assert mock_bot.send_message.call_count == 2

