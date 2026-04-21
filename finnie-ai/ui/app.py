import streamlit as st
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import route_query

st.set_page_config(
    page_title="Finnie — AI Finance Assistant",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── API Key guard — friendly error instead of crash ──
if not os.getenv("OPENAI_API_KEY"):
    st.error("**OpenAI API key not found!** Add OPENAI_API_KEY to your .env file and restart.")
    st.stop()


st.markdown("""
<style>
.agent-badge {
    display: inline-block;
    font-size: 11px;
    padding: 2px 10px;
    border-radius: 20px;
    font-weight: 600;
    margin-bottom: 4px;
}
.badge-literacy     { background:#E1F5EE; color:#0F6E56; }
.badge-market       { background:#E6F1FB; color:#185FA5; }
.badge-portfolio    { background:#EEEDFE; color:#534AB7; }
.badge-learning     { background:#FAECE7; color:#993C1D; }
.badge-orchestrator { background:#F1EFE8; color:#5F5E5A; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ──
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "name": "User",
        "risk_level": "moderate",
        "experience": "intermediate",
        "goals": ["wealth_creation", "tax_saving"]
    }

if "portfolio" not in st.session_state:
    st.session_state.portfolio = {
        "INFY":     {"qty": 50,  "avg_price": 1600, "current_price": 1842},
        "HDFC":     {"qty": 30,  "avg_price": 1500, "current_price": 1680},
        "TCS":      {"qty": 20,  "avg_price": 3400, "current_price": 3820},
        "NIFTY_MF": {"qty": 500, "avg_price": 120,  "current_price": 142},
    }

# ── Header ──
col1, col2, col3 = st.columns([1, 6, 2])
with col1:
    st.markdown("## 💹")
with col2:
    st.markdown("## Finnie")
    st.caption("AI Finance Assistant — 4 specialist agents online")
with col3:
    st.success("● All 4 agents active")

st.divider()

# ── Tabs ──
tab1, tab2, tab3, tab4 = st.tabs([
    "💬  Chat",
    "📊  Portfolio",
    "📈  Market Trends",
    "🎓  Learning Path"
])

# ═══════════════════════════════════════════════════
# TAB 1 — CHAT
# ═══════════════════════════════════════════════════
with tab1:
    chat_col, side_col = st.columns([3, 1])

    with side_col:
        st.markdown("**Try asking Finnie**")
        suggestions = [
            "What is a SIP and how does it work?",
            "What is NIFTY 50 at today?",
            "Analyse my portfolio risk",
            "Explain P/E ratio simply",
            "Compare SIP vs lump sum",
            "Build my learning path",
            "What are ELSS mutual funds?",
            "Should I invest in IT stocks now?",
        ]
        for s in suggestions:
            if st.button(s, key=f"sug_{s[:20]}", width="stretch"):
                st.session_state.messages.append({"role": "user", "content": s})
                st.rerun()

        st.divider()
        st.markdown("**Agent routing legend**")
        st.markdown("""
<small>
<span class='agent-badge badge-literacy'>Literacy</span> concepts &amp; education<br><br>
<span class='agent-badge badge-market'>Market</span> live prices &amp; news<br><br>
<span class='agent-badge badge-portfolio'>Portfolio</span> analysis &amp; risk<br><br>
<span class='agent-badge badge-learning'>Learning</span> your path
</small>
""", unsafe_allow_html=True)

    with chat_col:
        # Welcome message on first load
        if not st.session_state.messages:
            with st.chat_message("assistant", avatar="💹"):
                st.markdown("""
<span class='agent-badge badge-orchestrator'>Finnie Orchestrator</span>

Hi! I'm **Finnie**, your personal AI finance assistant. I have 4 specialist agents ready:

- 📚 **Financial Literacy Agent** — explains concepts in plain language
- 📈 **Market Data Agent** — live prices and market news
- 💼 **Portfolio Analyst Agent** — analyses your holdings and risk
- 🎓 **Learning Path Agent** — personalized financial education

What would you like to explore today?
""", unsafe_allow_html=True)

        # Render conversation history
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant", avatar="💹"):
                    agent = msg.get("agent", "orchestrator")
                    label = agent.replace("_", " ").title() + " Agent"
                    st.markdown(
                        f"<span class='agent-badge badge-{agent}'>{label}</span>",
                        unsafe_allow_html=True
                    )
                    st.write(msg["content"])

        # Chat input box
        if prompt := st.chat_input("Ask Finnie anything about finance..."):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant", avatar="💹"):
                with st.spinner("Finnie is thinking..."):
                    result = route_query(
                        query=prompt,
                        user_profile=st.session_state.user_profile,
                        portfolio=st.session_state.portfolio
                    )
                agent = result.get("agent", "orchestrator")
                label  = agent.replace("_", " ").title() + " Agent"
                st.markdown(
                    f"<span class='agent-badge badge-{agent}'>{label}</span>",
                    unsafe_allow_html=True
                )
                st.write(result.get("response", "Sorry, I could not process that."))

            st.session_state.messages.append({
                "role": "assistant",
                "content": result.get("response", ""),
                "agent": result.get("agent", "orchestrator")
            })
            st.rerun()

# ═══════════════════════════════════════════════════
# TAB 2 — PORTFOLIO
# ═══════════════════════════════════════════════════
with tab2:
    portfolio = st.session_state.portfolio
    total_invested = sum(v["qty"] * v["avg_price"]       for v in portfolio.values())
    total_current  = sum(v["qty"] * v["current_price"]   for v in portfolio.values())
    total_pnl      = total_current - total_invested
    pnl_pct        = (total_pnl / total_invested * 100)  if total_invested else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total invested",  f"₹{total_invested:,.0f}")
    m2.metric("Current value",   f"₹{total_current:,.0f}")
    m3.metric("Total P&L",       f"₹{total_pnl:,.0f}", f"{pnl_pct:.1f}%")
    m4.metric("No. of holdings", str(len(portfolio)))

    st.divider()
    hold_col, risk_col = st.columns([3, 2])

    with hold_col:
        st.subheader("Holdings")
        import pandas as pd
        rows = []
        for ticker, v in portfolio.items():
            cur_val  = v["qty"] * v["current_price"]
            inv_val  = v["qty"] * v["avg_price"]
            pnl      = cur_val - inv_val
            pnl_p    = (pnl / inv_val * 100) if inv_val else 0
            alloc    = (cur_val / total_current * 100) if total_current else 0
            rows.append({
                "Ticker":      ticker,
                "Qty":         v["qty"],
                "Avg price":   f"₹{v['avg_price']:,}",
                "Current":     f"₹{v['current_price']:,}",
                "Value":       f"₹{cur_val:,.0f}",
                "P&L":         f"₹{pnl:,.0f}",
                "P&L %":       f"{pnl_p:.1f}%",
                "Allocation":  f"{alloc:.1f}%",
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True)

        with st.expander("➕ Add a holding"):
            c1, c2, c3, c4 = st.columns(4)
            new_t = c1.text_input("Ticker",         placeholder="e.g. WIPRO")
            new_q = c2.number_input("Qty",          min_value=1, value=10)
            new_a = c3.number_input("Avg price ₹",  min_value=1, value=100)
            new_c = c4.number_input("Current ₹",    min_value=1, value=100)
            if st.button("Add holding"):
                if new_t:
                    st.session_state.portfolio[new_t.upper()] = {
                        "qty": new_q, "avg_price": new_a, "current_price": new_c
                    }
                    st.success(f"Added {new_t.upper()}")
                    st.rerun()

    with risk_col:
        st.subheader("AI risk analysis")
        if st.button("🤖 Analyse my portfolio", width="stretch"):
            with st.spinner("Portfolio Analyst Agent working..."):
                result = route_query(
                    query="Analyse my portfolio. Give risk score, sector concentration issues, and rebalancing advice.",
                    user_profile=st.session_state.user_profile,
                    portfolio=portfolio
                )
            st.markdown(
                "<span class='agent-badge badge-portfolio'>Portfolio Agent</span>",
                unsafe_allow_html=True
            )
            st.write(result.get("response", ""))
        else:
            risk_items = [
                ("Overall risk",       "Moderate",       "warning"),
                ("Sector focus",       "IT heavy (70%)", "error"),
                ("Liquidity",          "Good",           "normal"),
                ("Diversification",    "Needs work",     "warning"),
                ("Debt/Equity ratio",  "Needs rebalance","error"),
            ]
            for label, value, status in risk_items:
                r1, r2 = st.columns([2, 1])
                r1.caption(label)
                if   status == "error":   r2.error(value)
                elif status == "warning": r2.warning(value)
                else:                     r2.success(value)

# ═══════════════════════════════════════════════════
# TAB 3 — MARKET TRENDS
# ═══════════════════════════════════════════════════
with tab3:
    st.subheader("Live market overview")

    if st.button("🔄 Fetch live prices via Market Agent"):
        with st.spinner("Market Data Agent fetching prices..."):
            result = route_query(
                query="Give current prices for NIFTY 50, SENSEX, INFY, TCS, HDFC and brief market summary",
                user_profile=st.session_state.user_profile,
                portfolio=st.session_state.portfolio
            )
        st.markdown(
            "<span class='agent-badge badge-market'>Market Data Agent</span>",
            unsafe_allow_html=True
        )
        st.write(result.get("response", ""))
    else:
        # Static placeholder indices
        indices = [
            ("NIFTY 50",   "24,382",  "+0.82%", True),
            ("SENSEX",     "80,148",  "+0.71%", True),
            ("BANK NIFTY", "52,310",  "-0.23%", False),
            ("USD/INR",    "83.42",   "-0.12%", False),
            ("Gold/10g",   "₹73,450", "+0.34%", True),
            ("Crude/bbl",  "$82.10",  "-1.20%", False),
        ]
        cols = st.columns(3)
        for i, (name, price, chg, up) in enumerate(indices):
            with cols[i % 3]:
                st.metric(name, price, chg,
                          delta_color="normal" if up else "inverse")

    st.divider()
    st.subheader("AI news digest")

    if st.button("📰 Fetch latest market news"):
        with st.spinner("Searching and summarising news..."):
            result = route_query(
                query="Get latest Indian stock market news headlines and classify each as bullish, bearish or neutral",
                user_profile=st.session_state.user_profile,
                portfolio=st.session_state.portfolio
            )
        st.markdown(
            "<span class='agent-badge badge-market'>Market Data Agent</span>",
            unsafe_allow_html=True
        )
        st.write(result.get("response", ""))
    else:
        news = [
            ("🟢 Bullish", "RBI holds repo rate at 6.5% — positive for equities",   "Economic Times · 2h ago"),
            ("🔴 Bearish",  "IT sector faces headwinds as US tech spending slows",    "Mint · 4h ago"),
            ("🔵 Neutral",  "Infosys Q4 results inline — guidance maintained",        "Bloomberg · 6h ago"),
            ("🟢 Bullish", "FII inflows surge ₹4,200 Cr into Indian markets today",  "NDTV Profit · 8h ago"),
        ]
        for tag, headline, src in news:
            c1, c2 = st.columns([1, 6])
            c1.markdown(tag)
            c2.markdown(f"**{headline}**")
            c2.caption(src)
            st.divider()

# ═══════════════════════════════════════════════════
# TAB 4 — LEARNING PATH
# ═══════════════════════════════════════════════════
with tab4:
    st.subheader("Your personalized learning path")
    prof_col, path_col = st.columns([1, 2])

    with prof_col:
        st.markdown("**Your profile**")
        experience = st.selectbox(
            "Experience level",
            ["beginner", "intermediate", "advanced"],
            index=["beginner","intermediate","advanced"].index(
                st.session_state.user_profile.get("experience","intermediate")
            )
        )
        risk = st.selectbox(
            "Risk appetite",
            ["conservative", "moderate", "aggressive"],
            index=["conservative","moderate","aggressive"].index(
                st.session_state.user_profile.get("risk_level","moderate")
            )
        )
        goals = st.multiselect(
            "Financial goals",
            ["wealth_creation","tax_saving","retirement","child_education","emergency_fund"],
            default=st.session_state.user_profile.get("goals",["wealth_creation"])
        )
        if st.button("🤖 Generate my learning path", width="stretch"):
            st.session_state.user_profile.update(
                {"experience": experience, "risk_level": risk, "goals": goals}
            )
            with st.spinner("Learning Path Agent personalising your journey..."):
                result = route_query(
                    query=(
                        f"Create a personalized step-by-step financial learning path for a "
                        f"{experience} investor with {risk} risk appetite. "
                        f"Goals: {', '.join(goals)}. "
                        "List 5-6 modules with topics and why each is relevant."
                    ),
                    user_profile=st.session_state.user_profile,
                    portfolio=st.session_state.portfolio
                )
            st.markdown(
                "<span class='agent-badge badge-learning'>Learning Path Agent</span>",
                unsafe_allow_html=True
            )
            st.write(result.get("response", ""))

    with path_col:
        st.markdown("**Curriculum progress**")
        modules = [
            ("What is investing? Types of assets",          100, "beginner"),
            ("Understanding mutual funds and SIPs",         100, "beginner"),
            ("Portfolio diversification and risk",           60, "intermediate"),
            ("Reading financial statements",                  0, "intermediate"),
            ("Tax-efficient investing (ELSS, LTCG, STCG)",   0, "advanced"),
            ("Options and derivatives basics",                0, "advanced"),
        ]
        icons = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
        for name, pct, level in modules:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"{icons[level]} **{name}**")
            c2.caption(f"{pct}%")
            st.progress(pct / 100)
            if pct == 100:
                st.caption("✅ Completed")
            elif pct > 0:
                st.caption(f"🔄 In progress — {pct}% done")
            else:
                st.caption("⏳ Not started")
            st.write("")
