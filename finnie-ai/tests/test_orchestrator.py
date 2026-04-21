"""
Tests for Orchestrator Agent — intent detection and routing
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from agents.orchestrator import _detect_intent, route_query


# ── Intent Detection Tests ──────────────────────────────────────

class TestDetectIntent:

    def test_market_intent_nifty(self):
        assert _detect_intent("What is NIFTY 50 today?") == "market"

    def test_market_intent_price(self):
        assert _detect_intent("What is the current price of Infosys?") == "market"

    def test_market_intent_sensex(self):
        assert _detect_intent("How is SENSEX performing?") == "market"

    def test_market_intent_news(self):
        assert _detect_intent("Show me latest market news") == "market"

    def test_portfolio_intent_my_portfolio(self):
        assert _detect_intent("Analyse my portfolio") == "portfolio"

    def test_portfolio_intent_my_holdings(self):
        assert _detect_intent("How are my holdings performing?") == "portfolio"

    def test_portfolio_intent_risk(self):
        assert _detect_intent("What is my portfolio risk?") == "portfolio"

    def test_portfolio_intent_rebalance(self):
        assert _detect_intent("Should I rebalance my investments?") == "portfolio"

    def test_learning_intent_learn(self):
        assert _detect_intent("I want to learn investing") == "learning"

    def test_learning_intent_path(self):
        assert _detect_intent("Create my learning path") == "learning"

    def test_learning_intent_beginner(self):
        assert _detect_intent("I am a beginner, guide me") == "learning"

    def test_literacy_intent_fallback(self):
        assert _detect_intent("What is a SIP?") == "literacy"

    def test_literacy_intent_explain(self):
        assert _detect_intent("Explain mutual funds") == "literacy"

    def test_literacy_intent_what_is(self):
        assert _detect_intent("What is compound interest?") == "literacy"

    def test_empty_query_defaults_literacy(self):
        assert _detect_intent("") == "literacy"


# ── Route Query Tests ───────────────────────────────────────────

class TestRouteQuery:

    MOCK_PROFILE = {
        "name": "Test",
        "risk_level": "moderate",
        "experience": "intermediate",
        "goals": ["wealth_creation"]
    }

    MOCK_PORTFOLIO = {
        "INFY": {"qty": 10, "avg_price": 1600, "current_price": 1800}
    }

    @patch("agents.literacy_agent.client")
    def test_routes_to_literacy_agent(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="SIP explanation"))]
        )
        result = route_query("What is SIP?", self.MOCK_PROFILE, self.MOCK_PORTFOLIO)
        assert result["agent"] == "literacy"
        assert "response" in result

    @patch("agents.market_agent.client")
    @patch("agents.market_agent.yfinance", create=True)
    def test_routes_to_market_agent(self, mock_yf, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="NIFTY is at 24000"))]
        )
        result = route_query("What is NIFTY today?", self.MOCK_PROFILE, self.MOCK_PORTFOLIO)
        assert result["agent"] == "market"
        assert "response" in result

    @patch("agents.portfolio_agent.client")
    @patch("agents.market_agent.get_portfolio_prices", return_value={})
    def test_routes_to_portfolio_agent(self, mock_prices, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Your portfolio analysis"))]
        )
        result = route_query("Analyse my portfolio", self.MOCK_PROFILE, self.MOCK_PORTFOLIO)
        assert result["agent"] == "portfolio"
        assert "response" in result

    @patch("agents.learning_agent.client")
    def test_routes_to_learning_agent(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Your learning path"))]
        )
        result = route_query("Create my learning path", self.MOCK_PROFILE, self.MOCK_PORTFOLIO)
        assert result["agent"] == "learning"
        assert "response" in result

    @patch("agents.literacy_agent.client")
    def test_response_always_has_required_keys(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Answer"))]
        )
        result = route_query("What is a bond?", self.MOCK_PROFILE, self.MOCK_PORTFOLIO)
        assert "agent"    in result
        assert "response" in result

    @patch("agents.literacy_agent.client")
    def test_empty_portfolio_handled(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Answer"))]
        )
        result = route_query("What is equity?", self.MOCK_PROFILE, {})
        assert result is not None
        assert "response" in result
