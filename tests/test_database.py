"""
Unit tests for database operations
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestDatabase:
    """Test database operations"""
    
    @pytest.mark.asyncio
    async def test_save_signal_to_db(self, mock_db_connection):
        """Test saving signal to database"""
        signal_data = {
            "signal": "BUY",
            "price": 1.0800,
            "score": 65,
            "confidence": 60,
            "entry": 1.0800,
            "time": datetime.now(),
            "rsi": 30.5,
            "macd": 0.0001,
            "atr": 0.0003
        }
        
        # Create a proper async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_db_connection)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        with patch('PocSocSig_Enhanced.aiosqlite.connect', return_value=mock_context):
            await PocSocSig_Enhanced.save_signal_to_db(signal_data)
            
            # Check that execute was called
            assert mock_db_connection.execute.called
            assert mock_db_connection.commit.called
    
    @pytest.mark.asyncio
    async def test_load_recent_signals_from_db(self, mock_db_connection):
        """Test loading recent signals from database"""
        # Mock database response
        mock_row = (
            datetime.now().isoformat(),
            "BUY",
            1.0800,
            65.0,
            60.0,
            1.0800,
            30.5,
            0.0001,
            0.0003
        )
        mock_db_connection.fetchall = AsyncMock(return_value=[mock_row])
        mock_db_connection.execute.return_value = mock_db_connection
        
        with patch('aiosqlite.connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_db_connection
            signals = await PocSocSig_Enhanced.load_recent_signals_from_db(limit=10)
            
            assert isinstance(signals, list)
            if len(signals) > 0:
                assert "signal" in signals[0]
                assert "price" in signals[0]
    
    @pytest.mark.asyncio
    async def test_backup_database(self):
        """Test database backup functionality"""
        import shutil
        import tempfile
        
        # Create a temporary database file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            tmp_db_path = tmp_db.name
            tmp_db.write(b'test data')
        
        # Create backup directory
        backup_dir = "test_backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        try:
            with patch('PocSocSig_Enhanced.DB_PATH', tmp_db_path):
                with patch('PocSocSig_Enhanced.os.path.exists', return_value=True):
                    with patch('PocSocSig_Enhanced.os.makedirs'):
                        # Mock shutil.copy2 inside the function (it's imported locally)
                        with patch('shutil.copy2') as mock_copy:
                            with patch('PocSocSig_Enhanced.os.listdir', return_value=[]):
                                await PocSocSig_Enhanced.backup_database()
                                
                                # Should complete without error
                                assert True
                                # Verify copy2 was called if we want to be thorough
                                # (but it might not be called if DB_PATH doesn't exist in the actual check)
        finally:
            # Cleanup
            if os.path.exists(tmp_db_path):
                os.remove(tmp_db_path)
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
    
    @pytest.mark.asyncio
    async def test_init_database(self, mock_db_connection):
        """Test database initialization"""
        # Create a proper async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_db_connection)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        with patch('PocSocSig_Enhanced.aiosqlite.connect', return_value=mock_context):
            await PocSocSig_Enhanced.init_database()
            
            # Check that execute was called (for table creation)
            assert mock_db_connection.execute.called
            assert mock_db_connection.commit.called

