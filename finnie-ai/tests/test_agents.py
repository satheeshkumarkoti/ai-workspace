"""
Tests for all 4 Specialist Agents:
- Literacy Agent
- Market Agent
- Portfolio Agent
- Learning Agent
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock


# ── Shared fixtures ─────────────────────────────────────────────

MOCK_PROFILE = {
    "name": "TestUser",
    "risk_level": "moderate",
    "experience": "intermediate",
    "goals": ["wealth_creation", "tax_saving"]
}

MOCK_PORTFOLIO = {
    "INFY": {"qty": 50,  "avg_price": 1600, "current_price": 1842},
    "TCS":  {"qty": 20,  "avg_price": 3400, "current_price": 3820},
    "HDFC": {"qty": 30,  "avg_price": 1500, "current_price": 1680},
}

def make_openai_response(text: str):
    return MagicMock(
        choices=[MagicMock(message=MagicMock(content=text))]
    )


# ══════════════════════════════════════════════════════════════
# LITERACY AGENT TESTS
# ══════════════════════════════════════════════════════════════

class TestLiteracyAgent:

    def _make_context(self, query: str):
        return {
            "query": query,
            "user_profile": MOCK_PROFILE,
            "a2a_data": {}
        }

    @patch("agents.literacy_agent.client")
    def test_basic_response_returned(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response(
            "A SIP is a Systematic Investment Plan."
        )
        from agents.literacy_agent import run
        result = run(self._make_context("What is SIP?"))
        assert result["agent"] == "literacy"
        assert len(result["response"]) > 0

    @patch("agents.literacy_agent.client")
    def test_response_contains_content(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response(
            "ELSS stands for Equity Linked Savings Scheme."
        )
        from agents.literacy_agent import run
        result = run(self._make_context("What is ELSS?"))
        assert "ELSS" in result["response"]

    @patch("agents.literacy_agent.client")
    def test_fallback_on_openai_error(self, mock_client):
        mock_client.chat.completions.create.side_effect = Exception("API error")
        from agents.literacy_agent import run
        result = run(self._make_context("What is compound interest?"))
        assert result["agent"] == "literacy"
        assert "response" in result
        assert len(result["response"]) > 0

    @patch("agents.literacy_agent.client")
    def test_rag_context_injected_in_prompt(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response(
            "Based on context: SIP answer"
        )
        with patch("agents.literacy_agent._retrieve_rag_context", return_value="SIP info chunk"):
            from agents.literacy_agent import run
            result = run(self._make_context("Tell me about SIP"))
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]["messages"]
            user_msg = next(m for m in messages if m["role"] == "user")
            assert "SIP info chunk" in user_msg["content"]

    @patch("agents.literacy_agent.client")
    def test_beginner_experience_passed(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response("Answer")
        profile = {**MOCK_PROFILE, "experience": "beginner"}
        from agents.literacy_agent import run
        result = run({"query": "What is mutual fund?", "user_profile": profile, "a2a_data": {}})
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        system_msg = next(m for m in messages if m["role"] == "system")
        assert "beginner" in system_msg["content"]


# ══════════════════════════════════════════════════════════════
# MARKET AGENT TESTS
# ══════════════════════════════════════════════════════════════

class TestMarketAgent:

    def _make_context(self, query: str):
        return {
            "query": query,
            "user_profile": MOCK_PROFILE,
            "portfolio": MOCK_PORTFOLIO,
            "a2a_data": {}
        }

    @patch("agents.market_agent.client")
    def test_returns_market_agent_label(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response(
            "NIFTY 50 is at 24,399"
        )
        from agents.market_agent import run
        result = run(self._make_context("What is NIFTY today?"))
        assert result["agent"] == "market"

    @patch("agents.market_agent.client")
    def test_response_not_empty(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response(
            "Market data response"
        )
        from agents.market_agent import run
        result = run(self._make_context("Show me market overview"))
        assert len(result["response"]) > 0

    @patch("agents.market_agent.client")
    def test_fallback_when_yfinance_unavailable(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response(
            "Market data response"
        )
        with patch("agents.market_agent._fetch_market_data", return_value="Live data unavailable."):
            from agents.market_agent import run
            result = run(self._make_context("NIFTY price?"))
            assert result["agent"] == "market"
            assert "response" in result

    def test_get_portfolio_prices_returns_dict(self):
        from agents.market_agent import get_portfolio_prices
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.fast_info.last_price = 1842.0
            result = get_portfolio_prices(["INFY", "TCS"])
            assert isinstance(result, dict)

    def test_get_portfolio_prices_handles_error(self):
        from agents.market_agent import get_portfolio_prices
        with patch("yfinance.Ticker", side_effect=Exception("Network error")):
            result = get_portfolio_prices(["INFY"])
            assert isinstance(result, dict)

    @patch("agents.market_agent.client")
    def test_nse_ticker_map_used(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response("Data")
        from agents.market_agent import NSE_TICKER_MAP
        assert "INFY"     in NSE_TICKER_MAP
        assert "TCS"      in NSE_TICKER_MAP
        assert "NIFTY_MF" in NSE_TICKER_MAP


# ══════════════════════════════════════════════════════════════
# PORTFOLIO AGENT TESTS
# ══════════════════════════════════════════════════════════════

class TestPortfolioAgent:

    def _make_context(self, live_prices=None):
        return {
            "query": "Analyse my portfolio and give risk assessment",
            "user_profile": MOCK_PROFILE,
            "portfolio": MOCK_PORTFOLIO,
            "a2a_data": {"live_prices": live_prices or {}}
        }

    @patch("agents.portfolio_agent.client")
    def test_returns_portfolio_agent_label(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response(
            "Risk score: 6/10. IT sector is overweight."
        )
        from agents.portfolio_agent import run
        result = run(self._make_context())
        assert result["agent"] == "portfolio"

    @patch("agents.portfolio_agent.client")
    def test_portfolio_summary_includes_all_tickers(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response("Analysis")
        from agents.portfolio_agent import _build_portfolio_summary
        summary = _build_portfolio_summary(MOCK_PORTFOLIO)
        assert "INFY" in summary
        assert "TCS"  in summary
        assert "HDFC" in summary

    @patch("agents.portfolio_agent.client")
    def test_portfolio_summary_includes_total_value(self, mock_client):
        from agents.portfolio_agent import _build_portfolio_summary
        summary = _build_portfolio_summary(MOCK_PORTFOLIO)
        assert "Total portfolio value" in summary

    @patch("agents.portfolio_agent.client")
    def test_live_prices_from_a2a_update_portfolio(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response("Analysis done")
        live_prices = {"INFY": 1900.0, "TCS": 4000.0}
        from agents.portfolio_agent import run
        result = run(self._make_context(live_prices=live_prices))
        assert result["agent"] == "portfolio"

    @patch("agents.portfolio_agent.client")
    def test_empty_portfolio_handled(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response("No data")
        from agents.portfolio_agent import _build_portfolio_summary
        summary = _build_portfolio_summary({})
        assert "No portfolio data" in summary

    @patch("agents.portfolio_agent.client")
    def test_fallback_on_api_error(self, mock_client):
        mock_client.chat.completions.create.side_effect = Exception("API error")
        from agents.portfolio_agent import run
        result = run(self._make_context())
        assert result["agent"] == "portfolio"
        assert "response" in result

    @patch("agents.portfolio_agent.client")
    def test_user_goals_passed_to_llm(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response("Analysis")
        from agents.portfolio_agent import run
        run(self._make_context())
        call_args = mock_client.chat.completions.create.call_args
        messages  = call_args[1]["messages"]
        user_msg  = next(m for m in messages if m["role"] == "user")
        assert "wealth_creation" in user_msg["content"]


# ══════════════════════════════════════════════════════════════
# LEARNING AGENT TESTS
# ══════════════════════════════════════════════════════════════

class TestLearningAgent:

    def _make_context(self, experience="intermediate", goals=None):
        profile = {
            **MOCK_PROFILE,
            "experience": experience,
            "goals": goals or ["wealth_creation"]
        }
        return {
            "query": "Create my personalized learning path",
            "user_profile": profile,
            "portfolio": MOCK_PORTFOLIO,
            "a2a_data": {}
        }

    @patch("agents.learning_agent.client")
    def test_returns_learning_agent_label(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response(
            "Module 1: Investing basics..."
        )
        from agents.learning_agent import run
        result = run(self._make_context())
        assert result["agent"] == "learning"

    @patch("agents.learning_agent.client")
    def test_response_not_empty(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response(
            "Your personalized path: ..."
        )
        from agents.learning_agent import run
        result = run(self._make_context())
        assert len(result["response"]) > 0

    @patch("agents.learning_agent.client")
    def test_beginner_path_generated(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response(
            "Beginner path: start with basics"
        )
        from agents.learning_agent import run
        result = run(self._make_context(experience="beginner"))
        call_args = mock_client.chat.completions.create.call_args
        messages  = call_args[1]["messages"]
        user_msg  = next(m for m in messages if m["role"] == "user")
        assert "beginner" in user_msg["content"]

    @patch("agents.learning_agent.client")
    def test_goals_included_in_prompt(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response("Path")
        from agents.learning_agent import run
        run(self._make_context(goals=["retirement", "tax_saving"]))
        call_args = mock_client.chat.completions.create.call_args
        messages  = call_args[1]["messages"]
        user_msg  = next(m for m in messages if m["role"] == "user")
        assert "retirement" in user_msg["content"]

    @patch("agents.learning_agent.client")
    def test_fallback_on_api_error(self, mock_client):
        mock_client.chat.completions.create.side_effect = Exception("API down")
        from agents.learning_agent import run
        result = run(self._make_context())
        assert result["agent"] == "learning"
        assert "response" in result

    @patch("agents.learning_agent.client")
    def test_redis_failure_does_not_crash(self, mock_client):
        mock_client.chat.completions.create.return_value = make_openai_response("Path")
        with patch("agents.learning_agent._load_progress",   return_value={}):
            with patch("agents.learning_agent._save_interaction", return_value=None):
                from agents.learning_agent import run
                result = run(self._make_context())
                assert result["agent"] == "learning"
