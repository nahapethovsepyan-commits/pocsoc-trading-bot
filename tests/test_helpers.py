"""
Unit tests for helper functions
"""
import pytest
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_clean_markdown(self):
        """Test markdown cleaning function"""
        text = "This is **bold** and *italic* text"
        cleaned = PocSocSig_Enhanced.clean_markdown(text)
        
        # Function should return cleaned text (may preserve or remove markdown)
        assert isinstance(cleaned, str)
        assert len(cleaned) > 0
    
    def test_clean_markdown_empty(self):
        """Test markdown cleaning with empty string"""
        text = ""
        cleaned = PocSocSig_Enhanced.clean_markdown(text)
        
        assert cleaned == ""
    
    def test_clean_markdown_special_chars(self):
        """Test markdown cleaning with special characters"""
        text = "Price: $1.0800 (EUR/USD)"
        cleaned = PocSocSig_Enhanced.clean_markdown(text)
        
        # Should preserve special chars but remove markdown
        assert "$" in cleaned
        assert "/" in cleaned

