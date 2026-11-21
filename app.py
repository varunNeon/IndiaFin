import logging

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from Analysis import analyze_market_data
from DataCollection import STOCKS, fetch_all_stock_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="IndiaFin Dashboard", page_icon="📈", layout="wide")

# --- Design tokens -----------------------------------------------------------
# Series colours validated for the dark chart surface (lightness band, CVD
# separation and contrast) with the dataviz palette validator.
SURFACE = "#0b1627"
INK = "#e7eefc"
INK_SOFT = "#93a8cf"
INK_MUTED = "#6f82a8"
GRID = "rgba(124, 151, 201, 0.12)"
SERIES_BLUE = "#3d8fef"
SERIES_AMBER = "#c97d18"
UP = "#1fa36a"
DOWN = "#e5484d"
NEUTRAL_MID = "#383835"

TICKER_NAMES = {ticker.replace(".NS", ""): name for name, ticker in STOCKS.items()}
WINDOWS = {"1M": 1, "3M": 3, "6M": 6}

st.markdown(
    f"""
<style>
  [data-testid="stAppViewContainer"] {{
    background:
      radial-gradient(circle at top left, rgba(59, 130, 246, 0.14), transparent 32%),
      linear-gradient(180deg, #08111d 0%, #07111f 48%, #040914 100%);
    color: {INK};
  }}
  [data-testid="stHeader"] {{ background: rgba(4, 9, 20, 0.25); }}
  [data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #091222 0%, #08101d 100%);
    border-right: 1px solid rgba(118, 162, 255, 0.12);
  }}
  [data-testid="stSidebar"] * {{ color: {INK} !important; }}
  [data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background: rgba(14, 28, 50, 0.9);
    border: 1px solid rgba(118, 162, 255, 0.18);
    border-radius: 12px;
  }}
  [data-testid="stMarkdownContainer"] p,
  [data-testid="stMarkdownContainer"] li,
  [data-testid="stCaptionContainer"] {{ color: {INK_SOFT}; }}
  h1, h2, h3 {{ color: {INK}; letter-spacing: -0.02em; }}
  .block-container {{ padding-top: 2rem; max-width: 1400px; }}

  .hero {{
    padding: 1.3rem 1.5rem;
    border-radius: 20px;
    border: 1px solid rgba(118, 162, 255, 0.2);
    background: linear-gradient(135deg, rgba(15, 32, 56, 0.94) 0%, rgba(8, 18, 33, 0.94) 100%);
    margin-bottom: 1rem;
    display: flex; justify-content: space-between; align-items: flex-end; gap: 1rem; flex-wrap: wrap;
  }}
  .hero-kicker {{
    color: #8cb6ff; font-size: 0.75rem; text-transform: uppercase;
    letter-spacing: 0.16em; font-weight: 700; margin-bottom: 0.35rem;
  }}
  .hero-title {{ font-size: 2rem; line-height: 1.1; font-weight: 800; color: #f5f8ff; }}
  .hero-title span {{ color: {INK_MUTED}; font-weight: 600; font-size: 1.1rem; margin-left: 0.4rem; }}
  .hero-sub {{ color: {INK_SOFT}; font-size: 0.9rem; margin-top: 0.35rem; }}
  .hero-price {{ text-align: right; }}
  .hero-price .px {{ font-size: 2rem; font-weight: 800; color: #f5f8ff; font-variant-numeric: tabular-nums; }}
  .hero-price .chg {{ font-size: 0.95rem; font-weight: 700; font-variant-numeric: tabular-nums; }}

  [data-testid="stMetric"] {{
    background: linear-gradient(180deg, rgba(15, 30, 55, 0.9) 0%, rgba(10, 22, 40, 0.9) 100%);
    border: 1px solid rgba(118, 162, 255, 0.16);
    border-radius: 16px;
    padding: 14px 16px;
  }}
  [data-testid="stMetricLabel"] p {{
    color: {INK_SOFT} !important; text-transform: uppercase; letter-spacing: 0.08em;
    font-size: 0.72rem !important; font-weight: 700;
  }}
  [data-testid="stMetricValue"] {{
    color: #f5f8ff; font-weight: 800; font-size: 1.55rem !important;
    font-variant-numeric: tabular-nums;
  }}

  .section-title {{
    font-size: 1.05rem; font-weight: 700; color: {INK}; margin: 1.2rem 0 0.1rem 0;
  }}
  .section-sub {{ font-size: 0.82rem; color: {INK_MUTED}; margin-bottom: 0.4rem; }}

  .insight {{
    border-radius: 14px; padding: 0.85rem 1rem; margin-bottom: 0.7rem;
    background: rgba(12, 24, 44, 0.88);
    border: 1px solid rgba(118, 162, 255, 0.14);
    border-left: 4px solid var(--tone);
  }}
  .insight .tag {{
    font-size: 0.7rem; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--tone);
  }}
  .insight .head {{ font-size: 1rem; font-weight: 700; color: {INK}; margin: 0.15rem 0; }}
  .insight .body {{ font-size: 0.85rem; color: {INK_SOFT}; line-height: 1.45; }}

  .footnote {{ font-size: 0.75rem; color: {INK_MUTED}; margin-top: 1.5rem; }}
  hr {{ border-color: rgba(118, 162, 255, 0.12); }}
</style>
""",
    unsafe_allow_html=True,
)

PLOTLY_CONFIG = {"displayModeBar": False}


def base_layout(height: int, **overrides) -> dict:
    axis = dict(
        gridcolor=GRID,
        linecolor=GRID,
        zerolinecolor=GRID,
        tickfont=dict(color=INK_SOFT, size=11),
        showspikes=False,
    )
    layout = dict(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=SURFACE,
        font=dict(family="Source Sans Pro, sans-serif", color=INK, size=12),
        margin=dict(l=8, r=8, t=36, b=8),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#0f1e36", bordercolor="rgba(118,162,255,0.3)", font=dict(color=INK)),
        legend=dict(
            orientation="h", x=0, y=1.02, xanchor="left", yanchor="bottom",
            bgcolor="rgba(0,0,0,0)", font=dict(color=INK_SOFT),
        ),
        xaxis=dict(axis),
        yaxis=dict(axis),
    )
    layout.update(overrides)
    return layout


def section(title: str, subtitle: str = ""):
    sub = f'<div class="section-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="section-title">{title}</div>{sub}', unsafe_allow_html=True)


def insight_card(tone: str, tag: str, head: str, body: str) -> str:
    return (
        f'<div class="insight" style="--tone:{tone}">'
        f'<div class="tag">{tag}</div><div class="head">{head}</div>'
        f'<div class="body">{body}</div></div>'
    )


def fmt_signed(value: float, suffix: str = "%") -> str:
    return f"{value:+.2f}{suffix}"


def fmt_volume(value: float) -> str:
    for unit, size in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if value >= size:
            return f"{value / size:.1f}{unit}"
    return f"{value:.0f}"


# --- Data --------------------------------------------------------------------
@st.cache_data(ttl=900, show_spinner="Fetching NSE prices…")
def load_market_data(period: str = "6mo"):
    combined = fetch_all_stock_data(period=period)
    analyzed = analyze_market_data(combined)
    return combined, analyzed


def _clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Ticker" in df.columns:
        df["Ticker"] = df["Ticker"].str.replace(".NS", "", regex=False)
    if "Date" in df.columns and not df.empty:
        dates = pd.to_datetime(df["Date"])
        if dates.dt.tz is not None:
            dates = dates.dt.tz_localize(None)
        df["Date"] = dates.dt.normalize()
    return df


def prepare_display_data(combined, analyzed):
    return _clean_frame(combined), _clean_frame(analyzed)


def slice_window(df: pd.DataFrame, months: int) -> pd.DataFrame:
    if df.empty:
        return df
    start = df["Date"].max() - pd.DateOffset(months=months)
    return df[df["Date"] > start]


def momentum(row) -> tuple[str, bool]:
    """Single trend rule used everywhere: 7-day MA vs 30-day MA."""
    bullish = row["MA7"] > row["MA30"]
    return ("Bullish" if bullish else "Bearish"), bullish


# --- Charts ------------------------------------------------------------------
def price_volume_chart(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.74, 0.26], vertical_spacing=0.04,
    )
    fig.add_trace(
        go.Candlestick(
            x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            name="Price",
            increasing=dict(line=dict(color=UP, width=1), fillcolor=UP),
            decreasing=dict(line=dict(color=DOWN, width=1), fillcolor=DOWN),
            showlegend=False,
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df["Date"], y=df["MA7"], name="7-day MA",
                   line=dict(color=SERIES_AMBER, width=2), hovertemplate="₹%{y:,.2f}"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df["Date"], y=df["MA30"], name="30-day MA",
                   line=dict(color=SERIES_BLUE, width=2), hovertemplate="₹%{y:,.2f}"),
        row=1, col=1,
    )
    bar_colors = [UP if c >= o else DOWN for o, c in zip(df["Open"], df["Close"])]
    fig.add_trace(
        go.Bar(x=df["Date"], y=df["Volume"], name="Volume", marker_color=bar_colors,
               opacity=0.55, showlegend=False, hovertemplate="%{y:.3s}"),
        row=2, col=1,
    )

    # Hide weekends and exchange holidays so candles sit next to each other.
    all_days = pd.date_range(df["Date"].min(), df["Date"].max(), freq="D")
    missing = all_days.difference(pd.DatetimeIndex(df["Date"]))

    fig.update_layout(**base_layout(520, xaxis_rangeslider_visible=False, bargap=0.15))
    axis_style = dict(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID,
                      tickfont=dict(color=INK_SOFT, size=11))
    fig.update_xaxes(**axis_style, rangebreaks=[dict(values=missing)])
    fig.update_yaxes(**axis_style)
    fig.update_yaxes(tickprefix="₹", tickformat=",.0f", row=1, col=1)
    fig.update_yaxes(tickformat=".2s", row=2, col=1)
    return fig


def volatility_chart(df: pd.DataFrame) -> go.Figure:
    avg = df["Volatility"].mean()
    fig = go.Figure(
        go.Scatter(
            x=df["Date"], y=df["Volatility"], name="7-day volatility",
            fill="tozeroy", fillcolor="rgba(61, 143, 239, 0.14)",
            line=dict(color=SERIES_BLUE, width=2), hovertemplate="%{y:.2f}%",
        )
    )
    fig.add_hline(
        y=avg, line=dict(color=INK_MUTED, width=1, dash="dot"),
        annotation_text=f"Window avg {avg:.2f}%", annotation_position="top left",
        annotation_font=dict(color=INK_SOFT, size=11),
    )
    fig.update_layout(**base_layout(300, showlegend=False, margin=dict(l=8, r=8, t=12, b=8)))
    fig.update_yaxes(ticksuffix="%")
    return fig


def correlation_chart(window_combined: pd.DataFrame) -> go.Figure | None:
    pivot = window_combined.pivot_table(index="Date", columns="Ticker", values="Close")
    corr = pivot.pct_change().dropna(how="all").corr()
    if corr.empty or corr.shape[0] < 2:
        return None

    labels = [TICKER_NAMES.get(t, t) for t in corr.columns]
    # Lower triangle only: the matrix is symmetric and the diagonal is always 1.
    masked = corr.where(pd.DataFrame(
        [[i > j for j in range(len(corr))] for i in range(len(corr))],
        index=corr.index, columns=corr.columns,
    ))
    masked = masked.iloc[1:, :-1]
    text = masked.map(lambda v: "" if pd.isna(v) else f"{v:.2f}")

    fig = go.Figure(
        go.Heatmap(
            z=masked.values, x=labels[:-1], y=labels[1:],
            text=text.values, texttemplate="%{text}", textfont=dict(color=INK, size=12),
            colorscale=[[0.0, DOWN], [0.5, NEUTRAL_MID], [1.0, SERIES_BLUE]],
            zmin=-1, zmax=1, zmid=0, xgap=2, ygap=2, hoverongaps=False,
            hovertemplate="%{y} ↔ %{x}<br>Correlation %{z:.2f}<extra></extra>",
            colorbar=dict(thickness=10, len=0.8, tickfont=dict(color=INK_SOFT),
                          tickvals=[-1, 0, 1], outlinewidth=0),
        )
    )
    fig.update_layout(**base_layout(420, hovermode="closest", margin=dict(l=8, r=8, t=8, b=8)))
    fig.update_xaxes(showgrid=False, tickangle=-30)
    fig.update_yaxes(showgrid=False, autorange="reversed")
    return fig


# --- Watchlist ---------------------------------------------------------------
def watchlist_table(analyzed: pd.DataFrame, months: int) -> pd.DataFrame:
    rows = []
    for ticker, df in analyzed.groupby("Ticker"):
        window = slice_window(df.sort_values("Date"), months)
        if window.empty:
            continue
        last = window.iloc[-1]
        label, _ = momentum(last)
        rows.append({
            "Stock": TICKER_NAMES.get(ticker, ticker),
            "Ticker": ticker,
            "Last (₹)": last["Close"],
            "1D %": last["Daily_Return"],
            "Window %": (last["Close"] / window.iloc[0]["Close"] - 1) * 100,
            "Volatility %": last["Volatility"],
            "Signal": ("▲ " if label == "Bullish" else "▼ ") + label,
            "Trend": window["Close"].round(2).tolist(),
        })
    table = pd.DataFrame(rows)
    return table.sort_values("Window %", ascending=False) if not table.empty else table


def render_watchlist(table: pd.DataFrame, window_label: str):
    def tone(v):
        return f"color: {UP}" if v > 0 else (f"color: {DOWN}" if v < 0 else "")

    styled = (
        table.style
        .format({"Last (₹)": "₹{:,.2f}", "1D %": "{:+.2f}%", "Window %": "{:+.2f}%",
                 "Volatility %": "{:.2f}%"})
        .map(tone, subset=["1D %", "Window %"])
    )
    st.dataframe(
        styled,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Trend": st.column_config.LineChartColumn(f"{window_label} close", width="medium"),
        },
    )


# --- Page --------------------------------------------------------------------
def render_empty_state():
    st.markdown(
        """
<div class="hero"><div>
  <div class="hero-kicker">IndiaFin · NSE watchlist</div>
  <div class="hero-title">Market data unavailable</div>
  <div class="hero-sub">Yahoo Finance did not return usable prices. The page will recover once the upstream feed responds.</div>
</div></div>
""",
        unsafe_allow_html=True,
    )
    st.info("Charts are hidden until stock data is available. Try again in a few minutes.")


def render_dashboard(combined, analyzed):
    tickers = sorted(analyzed["Ticker"].dropna().unique().tolist(), key=lambda t: TICKER_NAMES.get(t, t))
    if not tickers:
        logger.warning("No ticker values are available after analysis")
        render_empty_state()
        return

    st.sidebar.markdown("### IndiaFin")
    selected_ticker = st.sidebar.selectbox(
        "Stock", tickers, format_func=lambda t: f"{TICKER_NAMES.get(t, t)} · {t}",
    )
    window_label = st.sidebar.radio("Window", list(WINDOWS), index=1, horizontal=True)
    months = WINDOWS[window_label]

    full_df = analyzed[analyzed["Ticker"] == selected_ticker].sort_values("Date")
    stock_df = slice_window(full_df, months)
    if stock_df.empty:
        st.warning(f"No data is available for {selected_ticker} right now.")
        return

    latest = stock_df.iloc[-1]
    prev_close = full_df.iloc[-2]["Close"] if len(full_df) > 1 else latest["Close"]
    day_change = latest["Close"] - prev_close
    window_return = (latest["Close"] / stock_df.iloc[0]["Close"] - 1) * 100
    vol_avg = stock_df["Volatility"].mean()
    trend, bullish = momentum(latest)
    as_of = latest["Date"].strftime("%d %b %Y")
    name = TICKER_NAMES.get(selected_ticker, selected_ticker)
    chg_color = UP if day_change >= 0 else DOWN

    st.sidebar.caption(
        f"Prices as of **{as_of}** (daily close). Source: Yahoo Finance via yfinance, "
        "cached for 15 minutes. For exploration, not investment advice."
    )

    st.markdown(
        f"""
<div class="hero">
  <div>
    <div class="hero-kicker">IndiaFin · NSE watchlist</div>
    <div class="hero-title">{name}<span>NSE: {selected_ticker}</span></div>
    <div class="hero-sub">Daily prices to {as_of} · {window_label} window</div>
  </div>
  <div class="hero-price">
    <div class="px">₹{latest['Close']:,.2f}</div>
    <div class="chg" style="color:{chg_color}">{day_change:+,.2f} ({latest['Daily_Return']:+.2f}%) today</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{window_label} return", fmt_signed(window_return),
              delta=f"{latest['Close'] - stock_df.iloc[0]['Close']:+,.2f} ₹")
    c2.metric("Volatility (7D σ)", f"{latest['Volatility']:.2f}%",
              delta=f"{latest['Volatility'] - vol_avg:+.2f} vs avg", delta_color="inverse")
    c3.metric("Momentum", trend,
              delta=f"MA7 {'above' if bullish else 'below'} MA30",
              delta_color="normal" if bullish else "inverse")
    c4.metric("Volume", fmt_volume(latest["Volume"]),
              delta=f"{(latest['Volume'] / stock_df['Volume'].mean() - 1) * 100:+.0f}% vs avg",
              delta_color="off")

    section("Price & volume", "Daily candles with 7- and 30-day moving averages")
    st.plotly_chart(price_volume_chart(stock_df), use_container_width=True, config=PLOTLY_CONFIG)

    left, right = st.columns([3, 2], gap="large")
    with left:
        section("Volatility", "Rolling 7-day standard deviation of daily returns")
        st.plotly_chart(volatility_chart(stock_df), use_container_width=True, config=PLOTLY_CONFIG)
    with right:
        section("Signals", "Descriptive reads of the current window, not forecasts")
        gap_pct = (latest["MA7"] / latest["MA30"] - 1) * 100
        cards = [
            insight_card(
                UP if bullish else DOWN,
                ("▲ " if bullish else "▼ ") + trend,
                f"MA7 is {abs(gap_pct):.1f}% {'above' if bullish else 'below'} MA30",
                "Short-term momentum is positive." if bullish else "Short-term momentum is weakening.",
            ),
            insight_card(
                SERIES_AMBER if latest["Volatility"] > vol_avg else SERIES_BLUE,
                "Volatility",
                f"{'Above' if latest['Volatility'] > vol_avg else 'Below'} the {window_label} average",
                f"Daily σ is {latest['Volatility']:.2f}% vs a window average of {vol_avg:.2f}%.",
            ),
            insight_card(
                UP if window_return >= 0 else DOWN,
                "Range",
                f"₹{stock_df['Low'].min():,.0f} – ₹{stock_df['High'].max():,.0f}",
                f"Last close sits {((latest['Close'] - stock_df['Low'].min()) / max(stock_df['High'].max() - stock_df['Low'].min(), 1e-9)) * 100:.0f}% "
                f"of the way up the {window_label} range.",
            ),
        ]
        st.markdown("".join(cards), unsafe_allow_html=True)

    section("Watchlist", f"All tracked stocks over the {window_label} window, sorted by return")
    table = watchlist_table(analyzed, months)
    if not table.empty:
        render_watchlist(table, window_label)

    section("Return correlation", f"Pairwise correlation of daily returns over the {window_label} window")
    heat_col, note_col = st.columns([3, 2], gap="large")
    with heat_col:
        fig = correlation_chart(slice_window(combined, months))
        if fig is None:
            st.warning("Not enough overlapping data to build the correlation matrix yet.")
        else:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
    with note_col:
        st.markdown(
            f"""
<div class="insight" style="--tone:{SERIES_BLUE}">
  <div class="tag">How to read it</div>
  <div class="body">
    <b style="color:{SERIES_BLUE}">Blue, near +1</b>: the pair tends to move together.<br>
    <b style="color:#b9b9b4">Grey, near 0</b>: little linear relationship.<br>
    <b style="color:{DOWN}">Red, near −1</b>: the pair tends to move in opposite directions.<br><br>
    A watchlist full of strongly correlated stocks offers little diversification:
    when one falls, the rest usually follow.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="footnote">IndiaFin is a learning project. Data from Yahoo Finance via yfinance; '
        "not affiliated with NSE. Not investment advice.</div>",
        unsafe_allow_html=True,
    )


def main():
    try:
        combined, analyzed = load_market_data()
        combined, analyzed = prepare_display_data(combined, analyzed)
    except Exception:
        logger.exception("Unexpected application error while loading market data")
        render_empty_state()
        return

    if combined.empty or analyzed.empty:
        logger.warning("Dashboard entered empty state because combined=%s analyzed=%s", combined.empty, analyzed.empty)
        render_empty_state()
        return

    render_dashboard(combined, analyzed)


if __name__ == "__main__":
    main()
