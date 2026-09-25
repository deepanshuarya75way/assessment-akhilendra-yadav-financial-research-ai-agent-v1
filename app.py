import streamlit as st
import plotly.graph_objects as go
import requests
from src.fundamentals import fetch_fundamentals
from src.watchlist_db import add_watchlist_symbol, get_watchlist_symbols, init_watchlist_db, remove_watchlist_symbol
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from plotly.subplots import make_subplots
from src.stock_universe import load_indian_stock_options
from src.data import extract_stock_symbol, fetch_history, normalize_symbol
from src.indicators import add_indicators
from src.metrics import performance_summary, rsi_signal, trend_signal
from src.reporting import build_text_report
from src.alerts_db import (
    init_alerts_db,
    add_alert,
    get_alerts,
    set_alert_enabled,
    delete_alert,
)

from src.alerts import is_alert_triggered
def format_inr(value):
    return f"INR {value:,.2f}"
def get_sentiment_label(text):
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)["compound"]

    if score >= 0.05:
        return "Positive", score
    elif score <= -0.05:
        return "Negative", score
    else:
        return "Neutral", score

st.set_page_config(page_title="Financial Research AI Agent", layout="wide")
init_watchlist_db()
init_alerts_db()
st.markdown(
    """
    <style>
    h1, h2, h3, h4,
    div[data-testid="stHeading"] h1,
    div[data-testid="stHeading"] h2,
    div[data-testid="stHeading"] h3,
    div[data-testid="stHeading"] h4 {
                color: #e5e7eb !important;
    }

    div[data-baseweb="select"] span {
        color: #22c55e !important;
    }

    input {
        color: #22c55e !important;
    }

    textarea {
        color: #22c55e !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60, show_spinner=False)
def cached_history(symbol, period):
    return fetch_history(symbol, period)
@st.cache_data(ttl=300, show_spinner=False)
def cached_fundamentals(symbol):
    return fetch_fundamentals(symbol)
@st.cache_data(ttl=86400, show_spinner=False)
def cached_indian_stock_options():
    return load_indian_stock_options()


def price_chart(data, symbol):
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.72, 0.28],
        vertical_spacing=0.05,
        subplot_titles=(f"{symbol} price action", "Volume"),
    )
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=data.index, y=data["SMA20"], name="SMA 20", line={"width": 1.5}),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=data.index, y=data["SMA50"], name="SMA 50", line={"width": 1.5}),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["BB_UPPER"],
            name="Bollinger upper",
            line={"width": 1, "dash": "dot"},
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["BB_LOWER"],
            name="Bollinger lower",
            line={"width": 1, "dash": "dot"},
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(x=data.index, y=data["Volume"], name="Volume", marker_color="#6b7280"),
        row=2,
        col=1,
    )
    fig.update_layout(height=680, xaxis_rangeslider_visible=False, margin={"t": 60})
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    return fig


def rsi_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data["RSI"], name="RSI", line={"width": 2}))
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444")
    fig.add_hline(y=30, line_dash="dash", line_color="#22c55e")
    fig.update_layout(height=320, yaxis_range=[0, 100], margin={"t": 20})
    return fig


def macd_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data["MACD"], name="MACD"))
    fig.add_trace(go.Scatter(x=data.index, y=data["MACD_SIGNAL"], name="Signal"))
    fig.add_trace(go.Bar(x=data.index, y=data["MACD_HIST"], name="Histogram"))
    fig.update_layout(height=320, margin={"t": 20})
    return fig


def comparison_chart(series_map):
    fig = go.Figure()

    for symbol, data in series_map.items():
        if data is None or data.empty:
            continue

        normalized = data["Close"] / data["Close"].iloc[0] * 100
        fig.add_trace(go.Scatter(x=data.index, y=normalized, name=symbol))

    fig.update_layout(
        title="Normalized performance comparison",
        yaxis_title="Indexed value, first day = 100",
        height=480,
    )
    return fig
st.title("Financial Research AI Agent")
st.caption(
    "Analyze stocks with price charts, technical indicators, risk metrics, "
    "news sentiment, and downloadable research reports."
)
st.warning("Educational analysis only. This app does not provide investment advice.")
st.info("Indian market hours: 9:15 AM to 3:30 PM IST, Monday to Friday.")
stock_options = cached_indian_stock_options()
stock_symbols = [item["symbol"] for item in stock_options]
stock_label_map = {item["symbol"]: item["label"] for item in stock_options}


def show_stock_label(stock_symbol):
    return stock_label_map.get(stock_symbol, stock_symbol)


def default_stock_index(default_symbol):
    return stock_symbols.index(default_symbol) if default_symbol in stock_symbols else 0
with st.container():
    col_a, col_b, col_c, col_d = st.columns([1.2, 1.2, 1.2, 0.8])

    with col_a:
        symbol_input = st.selectbox(
            "Stock symbol",
            stock_symbols,
            index=default_stock_index("RELIANCE.NS"),
            format_func=show_stock_label,
        )

    with col_b:
        compare_options = [""] + stock_symbols
        compare_input = st.selectbox(
            "Compare with",
            compare_options,
            index=compare_options.index("TCS.NS") if "TCS.NS" in compare_options else 0,
            format_func=lambda value: "None" if value == "" else show_stock_label(value),
        )

    with col_c:
        benchmark_input = st.text_input("Benchmark index", "^NSEI")

    with col_d:
       period = st.selectbox("History period", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"], index=5)

    if "research_loaded" not in st.session_state:
        st.session_state.research_loaded = False

    if st.button("Analyze stock", type="primary", use_container_width=True):
        st.session_state.research_loaded = True

    news_api_key = st.text_input("News API key", type="password")


chat_question = st.text_input(
    "Stock price chatbot",
    "What is the latest price of RELIANCE.NS?",
)

if st.button("Ask chatbot"):
    chatbot_symbol = extract_stock_symbol(chat_question)

    if chatbot_symbol is None:
        st.error("Include a symbol like RELIANCE.NS, TCS.NS, INFY.NS, or HDFCBANK.NS.")
    else:
        chatbot_data = cached_history(chatbot_symbol, "5d")

        if chatbot_data.empty:
            st.error(f"No recent data found for {chatbot_symbol}.")
        else:
            price = chatbot_data["Close"].iloc[-1]
            date = chatbot_data.index[-1].date()
            st.success(f"{chatbot_symbol} latest close was {format_inr(price)} on {date}.")


if not st.session_state.research_loaded:
    st.info("Run research to load market data, indicators, comparison, risk metrics, and report export.")
    st.stop()


symbol = normalize_symbol(symbol_input)
compare_symbol = normalize_symbol(compare_input) if compare_input else ""
benchmark_symbol = benchmark_input.strip().upper()

st.caption(
    f"Using symbols: Main = {symbol}, Compare = {compare_symbol or 'None'}, Benchmark = {benchmark_symbol}"
)
compare_symbol = normalize_symbol(compare_input) if compare_input else ""

benchmark_symbol = benchmark_input.strip().upper()

data = cached_history(symbol, period)
compare_data = cached_history(compare_symbol, period) if compare_symbol else None
benchmark_data = cached_history(benchmark_symbol, period) if benchmark_symbol else None

if data.empty:
    st.error("No data found. Try RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, or SBIN.NS.")
    st.stop()


data = add_indicators(data)
summary = performance_summary(data)
latest_price = data["Close"].iloc[-1]
latest_rsi = data["RSI"].dropna().iloc[-1] if not data["RSI"].dropna().empty else None

overview, charts, risk, compare, watchlist, fundamentals, news,alerts_tab, export = st.tabs(
    ["Overview", "Charts", "Risk", "Comparison", "Watchlist", "Fundamentals", "News Sentiment", "Alerts","Export"]
)



with overview:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Latest close", format_inr(latest_price))
    col2.metric("Total return", f"{summary['total_return']:.2%}")
    col3.metric("Annual volatility", f"{summary['annual_volatility']:.2%}")
    col4.metric("Max drawdown", f"{summary['max_drawdown']:.2%}")

    col5, col6, col7 = st.columns(3)
    col5.metric("Sharpe ratio", f"{summary['sharpe_ratio']:.2f}")
    col6.metric("Trend", trend_signal(data))
    col7.metric("RSI signal", rsi_signal(latest_rsi))

    st.dataframe(
        data[["Open", "High", "Low", "Close", "Volume", "SMA20", "SMA50", "RSI", "MACD"]]
        .tail(15)
        .round(2),
        use_container_width=True,
    )

with charts:
    st.plotly_chart(price_chart(data, symbol), use_container_width=True)
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("RSI")
        st.plotly_chart(rsi_chart(data), use_container_width=True)

    with col_right:
        st.subheader("MACD")
        st.plotly_chart(macd_chart(data), use_container_width=True)

with risk:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Best day", f"{summary['best_day']:.2%}")
    col2.metric("Worst day", f"{summary['worst_day']:.2%}")
    col3.metric("Average daily return", f"{summary['average_daily_return']:.2%}")
    col4.metric("Positive days", f"{summary['positive_day_ratio']:.2%}")

    drawdown = data["Close"] / data["Close"].cummax() - 1
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=drawdown, fill="tozeroy", name="Drawdown"))
    fig.update_layout(height=420, yaxis_tickformat=".0%", yaxis_title="Drawdown")
    st.plotly_chart(fig, use_container_width=True)

with compare:
    series_map = {symbol: data}

    if compare_data is not None and not compare_data.empty:
        series_map[compare_symbol] = add_indicators(compare_data)

    if benchmark_data is not None and not benchmark_data.empty:
        series_map[benchmark_symbol] = add_indicators(benchmark_data)

    st.plotly_chart(comparison_chart(series_map), use_container_width=True)

    metric_rows = []
    for item_symbol, item_data in series_map.items():
        item_summary = performance_summary(item_data)
        metric_rows.append(
            {
                "Symbol": item_symbol,
                "Total Return": f"{item_summary['total_return']:.2%}",
                "Annual Volatility": f"{item_summary['annual_volatility']:.2%}",
                "Max Drawdown": f"{item_summary['max_drawdown']:.2%}",
                "Sharpe": f"{item_summary['sharpe_ratio']:.2f}",
            }
        )

    st.dataframe(metric_rows, use_container_width=True)
    news_report_summary = "News sentiment: Not available. News API key was not provided."

with watchlist:
    st.subheader("Saved Stock Watchlist")

    watch_symbol = st.text_input("Add stock to watchlist", symbol)

    if st.button("Add to watchlist"):
        saved_symbol = normalize_symbol(watch_symbol)
        add_watchlist_symbol(saved_symbol)
        st.success(f"{saved_symbol} added to watchlist.")
        st.rerun()

    saved_symbols = get_watchlist_symbols()

    if not saved_symbols:
        st.info("No stocks saved yet.")
    else:
        for saved_symbol in saved_symbols:
            col1, col2 = st.columns([3, 1])
            col1.write(saved_symbol)

            if col2.button("Remove", key=f"remove_{saved_symbol}"):
                remove_watchlist_symbol(saved_symbol)
                st.rerun()
with fundamentals:
    st.subheader("Fundamental Analysis")
    st.caption("Fundamentals are latest available company data, not real-time tick data.")

    if st.button("Refresh fundamentals"):
        cached_fundamentals.clear()
        st.rerun()

    with st.spinner("Loading fundamentals..."):
        fundamentals_data = cached_fundamentals(symbol)
        compare_fundamentals = cached_fundamentals(compare_symbol) if compare_symbol else None

    if not fundamentals_data:
        st.info("Fundamental data not available for this symbol.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Company", fundamentals_data.get("Company", "N/A"))
        col2.metric("Sector", fundamentals_data.get("Sector", "N/A"))
        col3.metric("Industry", fundamentals_data.get("Industry", "N/A"))

        st.dataframe(
            [{"Metric": key, "Value": value} for key, value in fundamentals_data.items()],
            use_container_width=True,
        )

        if compare_fundamentals:
            st.subheader("Fundamental Comparison")

            comparison_rows = []
            for metric in ["Market Cap", "P/E Ratio", "Debt/Equity", "Profit Margin", "Revenue Growth", "Dividend Yield"]:
                comparison_rows.append(
                    {
                        "Metric": metric,
                        symbol: fundamentals_data.get(metric, "N/A"),
                        compare_symbol: compare_fundamentals.get(metric, "N/A"),
                    }
                )

            st.dataframe(comparison_rows, use_container_width=True)

with news:
    st.subheader("News Sentiment Analysis")

    if not news_api_key:
        st.info("Enter News API key to fetch stock news.")
    else:
        news_query = symbol.replace(".NS", "").replace(".BO", "")

        if news_query == "RELIANCE":
            news_query = "Reliance Industries"
        elif news_query == "TCS":
            news_query = "Tata Consultancy Services"
        elif news_query == "INFY":
            news_query = "Infosys"
        elif news_query == "HDFCBANK":
            news_query = "HDFC Bank"

        response = requests.get(
            "https://newsapi.org/v2/everything",
            headers={"X-Api-Key": news_api_key},
            params={
                "q": news_query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 5,
            },
            timeout=10,
        )

        news_data = response.json()

        if response.status_code != 200:
            error_message = news_data.get("message", "Could not fetch news.")
            news_report_summary = f"News sentiment: Could not fetch news. {error_message}"
            st.error(error_message)
        else:
            articles = news_data.get("articles", [])

            if not articles:
                news_report_summary = "News sentiment: No recent news found."
                st.info("No recent news found.")
            else:
                sentiment_scores = []
                sentiment_labels = []
                prepared_articles = []

                for article in articles:
                    title = article.get("title", "No title")
                    description = article.get("description") or ""
                    source = article.get("source", {}).get("name", "Unknown source")
                    url = article.get("url")

                    text_for_sentiment = f"{title} {description}"
                    sentiment, score = get_sentiment_label(text_for_sentiment)

                    sentiment_scores.append(score)
                    sentiment_labels.append(sentiment)

                    prepared_articles.append(
                        {
                            "title": title,
                            "description": description,
                            "source": source,
                            "url": url,
                            "sentiment": sentiment,
                            "score": score,
                        }
                    )

                average_score = sum(sentiment_scores) / len(sentiment_scores)

                if average_score >= 0.05:
                    overall_sentiment = "Positive"
                elif average_score <= -0.05:
                    overall_sentiment = "Negative"
                else:
                    overall_sentiment = "Neutral"

                positive_count = sentiment_labels.count("Positive")
                negative_count = sentiment_labels.count("Negative")
                neutral_count = sentiment_labels.count("Neutral")

                news_report_summary = "\n".join(
                    [
                        "News Sentiment Summary",
                        f"Overall sentiment: {overall_sentiment}",
                        f"Average sentiment score: {average_score:.2f}",
                        f"Positive articles: {positive_count}",
                        f"Negative articles: {negative_count}",
                        f"Neutral articles: {neutral_count}",
                    ]
                )

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Overall Sentiment", overall_sentiment)
                col2.metric("Positive", positive_count)
                col3.metric("Negative", negative_count)
                col4.metric("Neutral", neutral_count)

                st.write(f"Average sentiment score: **{average_score:.2f}**")
                st.divider()

                for article in prepared_articles:
                    st.markdown(f"**{article['title']}**")
                    st.caption(article["source"])
                    st.write(article["description"])
                    st.write(
                        f"Sentiment: **{article['sentiment']}** "
                        f"({article['score']:.2f})"
                    )

                    if article["url"]:
                        st.link_button("Read article", article["url"])
                        st.caption(article["source"])
                        st.write(article["description"])
                        st.write(
                            f"Sentiment: **{article['sentiment']}** "
                            f"({article['score']:.2f})"
                        )

                        if article["url"]:
                            st.link_button("Read article", article["url"])
                 
with alerts_tab:
    st.subheader("Stock Price Alerts")

    with st.form("create alert_form"):
        alert_symbol= st.text_input(
            "Stock symbol",
            placeholder="For example:TCS or RELIANCE.NS",
        )
       
       alert_condition= st.selectbox(
        "Condition",
        ["Price above", "Price below"],
       )

       alert_target= st.number_input(
        "Target price",
        min_value=0.01,
        value=100.0,
        step=0.50,
       )
       
       create_alert_button = st.form_submitbutton("Create Alert")

       if create_alert_button:
        if not alert_symbol.strip():
            st.error("Please enter a stock symbol.")
            else:
                add_alert(
                    alert_symbol,
                    alert_condition,
                    alert_target,
                )

                st.success("Alert created successfully.")
                st.rerun()

                st.divider()
                st.subheader("Existing Alerts")

                alerts= get_alerts()

                if not alerts:
                    st.info("No alerts have been created yet.")
                    
                    else:

                        for alert in alerts:
                            alert_id = alert["id"]
                            enabled = bool(alert["enabled"])

                            col1,col2,col3,col4,col5 = st.columns(
                                [2,2,1,5,1,1]
                            )

                            with col1:
                                st.write(
                                    f"**{alert['symbol']}**"
                                    f"{alert['condition_type']}"
                                )

                                with col2:
                                    st.write(
                                        f"Target:**{alert['target_value']:.2f}**"
                                    )

                                with col3:
                                    st.write(
                                        "Enabled"if enabled else "Diabled"
                                    )

                                    with col4:
                                        toggle_label = "Disable"if enabled else "Enable"

                                        if st.button(
                                            toggle_lable,
                                            key=f"toggle_alert_{alert_id}",
                                        ):
                                        set_alert_enabled(alert_id,not enabled)
                                        st.return()

                                        with col5:
                                            if st.button(
                                                "Delete",
                                                key = f"delete_alert_{alert_id}",
                                            );
                                            delete_alert(alert_id)
                                            st.rerun()

                                            if enabled:
                                                triggered,latedt_price,message = is_alert_triggered(
                                                    alert["symbol"],
                                                    alert["condition_type"],
                                                    alert["target_value"],
                                                )

                                                if triggered:
                                                    st.warning(f"Alert triggered:{message}")
                                                    elif message:
                                                        st.caption(message)
                                                        else:
                                                            st.caption(
                                                                f"Current price:{latest_price:.2f}"
                                                            )

with export:
    st.subheader("Export Reports")

    base_report = build_text_report(symbol, data, summary, latest_rsi)

    compare_report = "Comparison Summary: No comparison stock selected."
    if compare_symbol and compare_data is not None and not compare_data.empty:
        compare_indicator_data = add_indicators(compare_data)
        compare_summary = performance_summary(compare_indicator_data)
        compare_latest_price = compare_indicator_data["Close"].iloc[-1]
        compare_latest_date = compare_indicator_data.index[-1].date()

        compare_report = "\n".join(
            [
                f"Comparison Stock Report: {compare_symbol}",
                f"Latest close: {format_inr(compare_latest_price)} on {compare_latest_date}",
                f"Total return: {compare_summary['total_return']:.2%}",
                f"Annual volatility: {compare_summary['annual_volatility']:.2%}",
                f"Maximum drawdown: {compare_summary['max_drawdown']:.2%}",
                f"Sharpe ratio: {compare_summary['sharpe_ratio']:.2f}",
            ]
        )

    safe_fundamentals = fundamentals_data if "fundamentals_data" in locals() else {}
    fundamentals_report = "\n".join(
        [
            "Fundamental Analysis Summary",
            f"Company: {safe_fundamentals.get('Company', 'N/A')}",
            f"Sector: {safe_fundamentals.get('Sector', 'N/A')}",
            f"Market Cap: {safe_fundamentals.get('Market Cap', 'N/A')}",
            f"P/E Ratio: {safe_fundamentals.get('P/E Ratio', 'N/A')}",
            f"Fundamental Score: {safe_fundamentals.get('Fundamental Score', 'N/A')}",
        ]
    )

    safe_news_summary = (
        news_report_summary
        if "news_report_summary" in locals()
        else "News sentiment: Not available."
    )

    report = f"{base_report}\n\n{compare_report}\n\n{fundamentals_report}\n\n{safe_news_summary}"

    st.text_area("Research summary", report, height=320)

    st.download_button(
        "Download indicator CSV",
        data.to_csv().encode("utf-8"),
        file_name=f"{symbol.replace('.', '_')}_research.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download text report",
        report.encode("utf-8"),
        file_name=f"{symbol.replace('.', '_')}_report.txt",
        mime="text/plain",
    )