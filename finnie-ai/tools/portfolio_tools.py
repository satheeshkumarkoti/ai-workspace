"""
Portfolio Tools — Finnie
Calculation utilities for portfolio analysis, risk scoring,
and rebalancing recommendations. Used by Portfolio Agent.
"""
from typing import Dict, Any, List, Tuple


def calculate_portfolio_metrics(portfolio: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate key portfolio metrics.
    Input: {ticker: {qty, avg_price, current_price}}
    Returns: total_invested, total_current, total_pnl, pnl_pct, allocations
    """
    if not portfolio:
        return {
            "total_invested": 0,
            "total_current":  0,
            "total_pnl":      0,
            "pnl_pct":        0.0,
            "allocations":    {},
            "holdings_count": 0
        }

    total_invested = sum(v["qty"] * v["avg_price"]     for v in portfolio.values())
    total_current  = sum(v["qty"] * v["current_price"] for v in portfolio.values())
    total_pnl      = total_current - total_invested
    pnl_pct        = round((total_pnl / total_invested * 100), 2) if total_invested else 0.0

    allocations = {}
    for ticker, v in portfolio.items():
        cur_val = v["qty"] * v["current_price"]
        allocations[ticker] = round((cur_val / total_current * 100), 2) if total_current else 0.0

    return {
        "total_invested": round(total_invested, 2),
        "total_current":  round(total_current, 2),
        "total_pnl":      round(total_pnl, 2),
        "pnl_pct":        pnl_pct,
        "allocations":    allocations,
        "holdings_count": len(portfolio)
    }


def calculate_risk_score(portfolio: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate portfolio risk score (1-10) based on:
    - Sector concentration
    - Number of holdings (diversification)
    - Individual stock weight

    Returns: {score, level, factors}
    """
    if not portfolio:
        return {"score": 0, "level": "Unknown", "factors": []}

    metrics     = calculate_portfolio_metrics(portfolio)
    allocations = metrics["allocations"]
    factors     = []
    risk_score  = 5  # baseline moderate

    # Factor 1 — Concentration in single stock
    max_alloc = max(allocations.values()) if allocations else 0
    if max_alloc > 40:
        risk_score += 2
        factors.append(f"High concentration: {max(allocations, key=allocations.get)} at {max_alloc:.1f}%")
    elif max_alloc > 25:
        risk_score += 1
        factors.append(f"Moderate concentration: {max(allocations, key=allocations.get)} at {max_alloc:.1f}%")

    # Factor 2 — Number of holdings (diversification)
    count = len(portfolio)
    if count < 3:
        risk_score += 2
        factors.append(f"Low diversification: only {count} holding(s)")
    elif count < 5:
        risk_score += 1
        factors.append(f"Moderate diversification: {count} holdings")
    elif count >= 8:
        risk_score -= 1
        factors.append(f"Good diversification: {count} holdings")

    # Factor 3 — IT sector concentration (common for Indian portfolios)
    it_tickers  = ["INFY", "TCS", "WIPRO", "HCLTECH", "TECHM"]
    it_alloc    = sum(allocations.get(t, 0) for t in it_tickers)
    if it_alloc > 60:
        risk_score += 2
        factors.append(f"IT sector overweight: {it_alloc:.1f}% — consider diversifying")
    elif it_alloc > 40:
        risk_score += 1
        factors.append(f"IT sector heavy: {it_alloc:.1f}%")

    # Clamp score between 1 and 10
    risk_score = max(1, min(10, risk_score))

    if   risk_score <= 3:  level = "Low"
    elif risk_score <= 6:  level = "Moderate"
    elif risk_score <= 8:  level = "High"
    else:                  level = "Very High"

    return {
        "score":   risk_score,
        "level":   level,
        "factors": factors
    }


def get_holding_details(portfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Return detailed breakdown for each holding.
    """
    if not portfolio:
        return []

    total_current = sum(v["qty"] * v["current_price"] for v in portfolio.values())
    details       = []

    for ticker, v in portfolio.items():
        cur_val  = v["qty"] * v["current_price"]
        inv_val  = v["qty"] * v["avg_price"]
        pnl      = cur_val - inv_val
        pnl_pct  = round((pnl / inv_val * 100), 2) if inv_val else 0.0
        alloc    = round((cur_val / total_current * 100), 2) if total_current else 0.0

        details.append({
            "ticker":        ticker,
            "quantity":      v["qty"],
            "avg_price":     v["avg_price"],
            "current_price": v["current_price"],
            "invested":      round(inv_val, 2),
            "current_value": round(cur_val, 2),
            "pnl":           round(pnl, 2),
            "pnl_pct":       pnl_pct,
            "allocation":    alloc,
            "status":        "profit" if pnl >= 0 else "loss"
        })

    return sorted(details, key=lambda x: x["allocation"], reverse=True)


def suggest_rebalancing(
    portfolio: Dict[str, Any],
    target_allocations: Dict[str, float] = None
) -> List[str]:
    """
    Generate simple rebalancing suggestions based on current allocations.
    target_allocations: {ticker: target_%} — optional custom targets
    """
    metrics     = calculate_portfolio_metrics(portfolio)
    allocations = metrics["allocations"]
    suggestions = []

    # Default targets: no single stock > 30%, diversify into 5+ holdings
    for ticker, alloc in allocations.items():
        if alloc > 35:
            suggestions.append(
                f"Consider reducing {ticker} from {alloc:.1f}% — "
                f"high single-stock concentration increases risk"
            )

    if len(portfolio) < 5:
        suggestions.append(
            "Consider adding more holdings for better diversification — "
            "aim for at least 5-8 stocks across different sectors"
        )

    it_tickers = ["INFY", "TCS", "WIPRO", "HCLTECH"]
    it_alloc   = sum(allocations.get(t, 0) for t in it_tickers)
    if it_alloc > 50:
        suggestions.append(
            f"IT sector is {it_alloc:.1f}% of portfolio — "
            "consider adding BFSI, FMCG, or Pharma stocks for balance"
        )

    if not suggestions:
        suggestions.append(
            "Your portfolio looks reasonably balanced. "
            "Review again after significant market moves or every 6 months."
        )

    return suggestions
