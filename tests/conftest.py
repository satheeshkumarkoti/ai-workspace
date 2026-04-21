"""
conftest.py — shared pytest fixtures for Finnie test suite
"""
import pytest
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set dummy API key so OpenAI client doesn't fail on import
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-for-testing")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")


@pytest.fixture
def mock_user_profile():
    return {
        "name": "TestUser",
        "risk_level": "moderate",
        "experience": "intermediate",
        "goals": ["wealth_creation", "tax_saving"]
    }


@pytest.fixture
def mock_portfolio():
    return {
        "INFY": {"qty": 50,  "avg_price": 1600, "current_price": 1842},
        "TCS":  {"qty": 20,  "avg_price": 3400, "current_price": 3820},
        "HDFC": {"qty": 30,  "avg_price": 1500, "current_price": 1680},
    }


@pytest.fixture
def mock_context(mock_user_profile, mock_portfolio):
    return {
        "query": "What is SIP?",
        "user_profile": mock_user_profile,
        "portfolio": mock_portfolio,
        "a2a_data": {}
    }


@pytest.fixture
def mock_openai_response():
    from unittest.mock import MagicMock
    return MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response from LLM"))]
    )