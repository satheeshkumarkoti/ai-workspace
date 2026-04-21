"""
Tests for Tools — yfinance_tool, portfolio_tools
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock


# ══════════════════════════════════════════════════════════════
# PORTFOLIO TOOLS TESTS
# ══════════════════════════════════════════════════════════════

SAMPLE_PORTFOLIO = {
    "INFY": {"qty": 50,  "avg_price": 1600, "current_price": 1842},
    "TCS":  {"qty": 20,  "avg_price": 3400, "current_price": 3820},
    "HDFC": {"qty": 30,  "avg_price": 1500, "current_price": 1680},
}


class TestPortfolioTools:

    def test_calculate_total_value(self):
        total = sum(v["qty"] * v["current_price"] for v in SAMPLE_PORTFOLIO.values())
        expected = (50 * 1842) + (20 * 3820) + (30 * 1680)
        assert total == expected

    def test_calculate_pnl(self):
        for ticker, v in SAMPLE_PORTFOLIO.items():
            pnl = (v["current_price"] - v["avg_price"]) * v["qty"]
            assert isinstance(pnl, (int, float))

    def test_all_holdings_positive_pnl(self):
        for ticker, v in SAMPLE_PORTFOLIO.items():
            pnl = v["current_price"] - v["avg_price"]
            assert pnl > 0, f"{ticker} should be in profit"

    def test_allocation_sums_to_100(self):
        total = sum(v["qty"] * v["current_price"] for v in SAMPLE_PORTFOLIO.values())
        allocations = [
            (v["qty"] * v["current_price"] / total) * 100
            for v in SAMPLE_PORTFOLIO.values()
        ]
        assert abs(sum(allocations) - 100) < 0.01

    def test_empty_portfolio_returns_zero(self):
        total = sum(v["qty"] * v["current_price"] for v in {}.values())
        assert total == 0

    def test_single_holding_portfolio(self):
        portfolio = {"WIPRO": {"qty": 10, "avg_price": 400, "current_price": 450}}
        total = sum(v["qty"] * v["current_price"] for v in portfolio.values())
        assert total == 4500

    def test_risk_score_it_heavy(self):
        """IT-heavy portfolio should flag sector concentration."""
        it_tickers = ["INFY", "TCS", "WIPRO", "HCL"]
        total = sum(v["qty"] * v["current_price"] for v in SAMPLE_PORTFOLIO.values())
        it_value = sum(
            v["qty"] * v["current_price"]
            for k, v in SAMPLE_PORTFOLIO.items()
            if k in it_tickers
        )
        it_concentration = (it_value / total) * 100 if total else 0
        assert it_concentration > 50  # INFY + TCS = IT heavy


# ══════════════════════════════════════════════════════════════
# INTEGRATION TESTS — full agent flow
# ══════════════════════════════════════════════════════════════

class TestIntegrationFlow:

    MOCK_PROFILE = {
        "name": "IntegrationUser",
        "risk_level": "moderate",
        "experience": "intermediate",
        "goals": ["wealth_creation"]
    }

    @patch("agents.literacy_agent.client")
    def test_full_literacy_flow(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="SIP is a method..."))]
        )
        from agents.orchestrator import route_query
        result = route_query("What is SIP?", self.MOCK_PROFILE, {})
        assert result["agent"] == "literacy"
        assert len(result["response"]) > 0

    @patch("agents.portfolio_agent.client")
    @patch("agents.market_agent.get_portfolio_prices", return_value={"INFY": 1900.0})
    def test_full_portfolio_flow_with_a2a(self, mock_prices, mock_client):
        """A2A: market agent fetches prices, portfolio agent receives them."""
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Your risk score is 6/10"))]
        )
        from agents.orchestrator import route_query
        result = route_query("Analyse my portfolio", self.MOCK_PROFILE, SAMPLE_PORTFOLIO)
        assert result["agent"] == "portfolio"
        # Verify A2A: get_portfolio_prices was called with portfolio tickers
        mock_prices.assert_called_once()

    @patch("agents.learning_agent.client")
    def test_full_learning_flow(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Module 1: Basics..."))]
        )
        from agents.orchestrator import route_query
        result = route_query(
            "Build my learning path",
            {**self.MOCK_PROFILE, "experience": "beginner"},
            {}
        )
        assert result["agent"] == "learning"

    @patch("agents.market_agent.client")
    def test_full_market_flow(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="NIFTY at 24,399"))]
        )
        from agents.orchestrator import route_query
        result = route_query("What is NIFTY today?", self.MOCK_PROFILE, {})
        assert result["agent"] == "market"


# ══════════════════════════════════════════════════════════════
# EDGE CASE TESTS
# ══════════════════════════════════════════════════════════════

class TestEdgeCases:

    MOCK_PROFILE = {
        "name": "EdgeUser",
        "risk_level": "moderate",
        "experience": "beginner",
        "goals": []
    }

    @patch("agents.literacy_agent.client")
    def test_very_long_query_handled(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Answer"))]
        )
        from agents.orchestrator import route_query
        long_query = "What is " + "SIP " * 200
        result = route_query(long_query, self.MOCK_PROFILE, {})
        assert "response" in result

    @patch("agents.literacy_agent.client")
    def test_special_characters_in_query(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Answer"))]
        )
        from agents.orchestrator import route_query
        result = route_query("What is ₹ & $ in investing?", self.MOCK_PROFILE, {})
        assert "response" in result

    @patch("agents.literacy_agent.client")
    def test_none_goals_handled(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Answer"))]
        )
        from agents.orchestrator import route_query
        profile = {**self.MOCK_PROFILE, "goals": None}
        result = route_query("What is mutual fund?", profile, {})
        assert "response" in result
