import sys
sys.path.insert(0, 'src')

def test_addition():
    """Test basic addition"""
    assert 1 + 1 == 2

def test_string():
    """Test string operations"""
    assert "hello".upper() == "HELLO"

def test_boolean():
    """Test boolean logic"""
    assert True is True