import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from DataCollection import combined
from Analysis import analyzed

st.set_page_config(page_title="IndiaFin Dashboard", layout="wide")

# ── Theme: white + blue (Research360-style) ──────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #f0f6ff; }
  [data-testid="stSidebar"]          { background: #1a56db; }
  [data-testid="stSidebar"] *        { color: #ffffff !important; }
  [data-testid="stSidebar"] .stSelectbox label { color: #dbeafe !important; }
  [data-testid="stSidebar"] [data-baseweb="select"] > div { background: #1648c0; border-color: #3b82f6; }
  h1, h2, h3 { color: #111827; }
  [data-testid="stMetricValue"]  { color: #1a56db; font-weight: 600; }
  [data-testid="stMetricLabel"]  { color: #6b7280; }
  [data-testid="metric-container"] {
    background: white;
    border: 1px solid #dbeafe;
    border-radius: 12px;
    padding: 16px;
  }
  .stInfo { background: #eff6ff !important; border-left: 4px solid #1a56db !important; color: #1e3a8a !important; }
  hr { border-color: #dbeafe; }
</style>
""", unsafe_allow_html=True)

# ── Common chart layout applied to every figure ───────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#f8faff",
    font_color="#111827",
    font_family="sans-serif",
    xaxis=dict(gridcolor="#dbeafe", linecolor="#dbeafe", tickcolor="#9ca3af"),
    yaxis=dict(gridcolor="#dbeafe", linecolor="#dbeafe", tickcolor="#9ca3af"),
    legend=dict(bgcolor="white", bordercolor="#dbeafe", borderwidth=1),
)

# ── Data prep ─────────────────────────────────────────────────────────────────
analyzed["Ticker"] = analyzed["Ticker"].str.replace(".NS", "", regex=False)
combined["Ticker"] = combined["Ticker"].str.replace(".NS", "", regex=False)

st.title("📊 IndiaFin — Indian Stock Market Dashboard")
st.markdown("---")

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.header("Filters")
tickers = analyzed["Ticker"].unique().tolist()
selected_ticker = st.sidebar.selectbox("Select Stock", tickers)

time_range = st.sidebar.selectbox("Time Range", ["1 Month", "3 Months", "6 Months"])
range_map = {"1 Month": 30, "3 Months": 90, "6 Months": 180}
days = range_map[time_range]

# ── Filter data ───────────────────────────────────────────────────────────────
stock_df = analyzed[analyzed["Ticker"] == selected_ticker].copy()
stock_df = stock_df.tail(days)

latest = stock_df.iloc[-1]
prev   = stock_df.iloc[-2]

current_price = latest["Close"]
daily_return  = latest["Daily_Return"]
volatility    = latest["Volatility"]
above_ma30    = latest["Close"] > latest["MA30"]
trend         = "Bullish 📈" if above_ma30 else "Bearish 📉"

# ── KPI tiles ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Current Price", f"₹{current_price:.2f}")
col2.metric("Daily Return",  f"{daily_return:.2f}%")
col3.metric("Volatility",    f"{volatility:.2f}%")
col4.metric("Trend",         trend)

st.markdown("---")

# ── Market insight ────────────────────────────────────────────────────────────
ma7  = latest["MA7"]
ma30 = latest["MA30"]

if ma7 > ma30:
    signal = "🟢 Bullish — 7-day MA is above 30-day MA. Short-term momentum is positive."
else:
    signal = "🔴 Bearish — 7-day MA is below 30-day MA. Short-term momentum is weakening."

if volatility > stock_df["Volatility"].mean():
    vol_insight = "⚠️ Volatility is above average — higher risk period."
else:
    vol_insight = "✅ Volatility is below average — relatively stable."

st.subheader(f"Market Insight — {selected_ticker}")
st.info(signal)
st.info(vol_insight)

st.markdown("---")

# ── Price trend chart ─────────────────────────────────────────────────────────
st.subheader(f"Price Trend — {selected_ticker}")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=stock_df["Date"], y=stock_df["Close"],
    name="Close Price", line=dict(color="#1a56db", width=2)
))
fig.add_trace(go.Scatter(
    x=stock_df["Date"], y=stock_df["MA7"],
    name="7-Day MA", line=dict(color="#f59e0b", width=1.5, dash="dot")
))
fig.add_trace(go.Scatter(
    x=stock_df["Date"], y=stock_df["MA30"],
    name="30-Day MA", line=dict(color="#10b981", width=1.5, dash="dash")
))
fig.update_layout(**CHART_LAYOUT)
st.plotly_chart(fig, use_container_width=True)

# ── Volatility chart ──────────────────────────────────────────────────────────
st.subheader("Volatility (7-Day Rolling Std Dev of Returns)")
fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=stock_df["Date"], y=stock_df["Volatility"],
    name="Volatility",
    fill="tozeroy",
    fillcolor="rgba(26, 86, 219, 0.10)",
    line=dict(color="#1a56db", width=2)
))
fig2.update_layout(**CHART_LAYOUT)
st.plotly_chart(fig2, use_container_width=True)

# ── Volume bar chart ──────────────────────────────────────────────────────────
st.subheader("Trading Volume")
fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=stock_df["Date"], y=stock_df["Volume"],
    name="Volume",
    marker_color="#1a56db",
    marker_line_color="#1648c0",
    marker_line_width=0.5,
    opacity=0.85
))
fig3.update_layout(**CHART_LAYOUT)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ── Correlation heatmap ───────────────────────────────────────────────────────
st.subheader("Stock Correlation Matrix")
pivot   = combined.pivot_table(index="Date", columns="Ticker", values="Close")
returns = pivot.pct_change().dropna()
corr    = returns.corr()

fig4 = px.imshow(
    corr,
    text_auto=True,
    color_continuous_scale="Blues",
    zmin=-1, zmax=1
)
fig4.update_layout(paper_bgcolor="white", font_color="#111827")
st.plotly_chart(fig4, use_container_width=True)

st.caption("""
**How to read this:** Each cell shows how closely two stocks move together, scored from -1 to +1.
- **+1 (dark blue)** → They move in the same direction almost always
- **0 (light)** → No relationship
- **-1** → They move in opposite directions

**Why this matters:** If all your stocks are highly correlated, your portfolio has no diversification — when one falls, they all fall. A good portfolio mixes low-correlation stocks to reduce risk. This is a core concept in portfolio theory.
""")
