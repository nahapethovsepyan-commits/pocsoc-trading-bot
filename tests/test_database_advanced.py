"""
Advanced tests for database operations
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestDatabaseAdvanced:
    """Advanced tests for database operations"""
    
    @pytest.mark.asyncio
    async def test_save_signal_to_db_with_all_fields(self):
        """Test saving signal with all fields"""
        signal_data = {
            "signal": "BUY",
            "price": 1.0800,
            "score": 65.5,
            "confidence": 60.0,
            "entry": 1.0800,
            "time": datetime.now(),
            "reasoning": "Test reasoning",
            "indicators": {
                "rsi": 30.5,
                "macd": 0.0001,
                "bb_position": 10.0,
                "atr": 0.0003,
                "adx": 25.0,
                "stoch_k": 20.0,
                "stoch_d": 18.0
            },
            "atr": 0.0003
        }
        
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_db)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        with patch('src.database.repository.aiosqlite.connect', return_value=mock_context):
            await PocSocSig_Enhanced.save_signal_to_db(signal_data)
            
            assert mock_db.execute.called
            assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_load_recent_signals_with_all_fields(self):
        """Test loading signals with all fields"""
        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            "timestamp": datetime.now().isoformat(),
            "signal": "BUY",
            "price": 1.0800,
            "score": 65.0,
            "confidence": 60.0,
            "entry": 1.0800,
            "rsi": 30.5,
            "macd": 0.0001,
            "atr": 0.0003
        }.get(key, None)
        mock_row.get = lambda key, default=None: {
            "timestamp": datetime.now().isoformat(),
            "signal": "BUY",
            "price": 1.0800,
            "score": 65.0,
            "confidence": 60.0,
            "entry": 1.0800,
            "rsi": 30.5,
            "macd": 0.0001,
            "atr": 0.0003
        }.get(key, default)
        
        mock_cursor.fetchall = AsyncMock(return_value=[mock_row])
        mock_cursor.close = AsyncMock(return_value=None)
        mock_db.execute.return_value = mock_cursor
        mock_db.row_factory = None
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_db)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        with patch('src.database.repository.aiosqlite.connect', return_value=mock_context):
            signals = await PocSocSig_Enhanced.load_recent_signals_from_db(limit=10)
            
            assert isinstance(signals, list)
    
    @pytest.mark.asyncio
    async def test_save_stats_to_db_updates(self):
        """Test saving stats updates database"""
        # Set some stats
        PocSocSig_Enhanced.STATS["total_signals"] = 10
        PocSocSig_Enhanced.STATS["BUY"] = 6
        PocSocSig_Enhanced.STATS["SELL"] = 4
        PocSocSig_Enhanced.STATS["wins"] = 7
        PocSocSig_Enhanced.STATS["losses"] = 3
        
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_db)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        with patch('src.database.repository.aiosqlite.connect', return_value=mock_context):
            await PocSocSig_Enhanced.save_stats_to_db()
            
            assert mock_db.execute.called
            assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_init_database_creates_tables(self):
        """Test database initialization creates all tables"""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_db)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        with patch('src.database.repository.aiosqlite.connect', return_value=mock_context):
            await PocSocSig_Enhanced.init_database()
            
            # Should create signals and stats tables
            assert mock_db.execute.call_count >= 2
            assert mock_db.commit.called

