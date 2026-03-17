# 💹 IndiaFin — Indian Stock Market Dashboard

A live financial analytics dashboard built with Python, pulling real-time NSE stock data and visualizing trends, volatility, and market signals through an interactive web app.

🔗 **Live App:** https://indiafin-mf9orp8gbadok3wzmxppj7.streamlit.app

---

## What It Does

- Pulls live stock data from NSE via `yfinance`
- Calculates 7-day and 30-day moving averages
- Detects volatility using rolling standard deviation of returns
- Generates automated bullish/bearish signals based on MA crossover
- Displays a correlation matrix showing how 8 Indian stocks move relative to each other
- Interactive sidebar to switch between stocks and time ranges (1M, 3M, 6M)

## Stocks Tracked

Reliance, TCS, Zomato (Eternal), Infosys, HDFC Bank, Adani Ports, Wipro, ITC

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| yfinance | Live NSE stock data |
| pandas | Data manipulation and feature engineering |
| Streamlit | Interactive web dashboard |
| Plotly | Charts and visualizations |
| Git + GitHub | Version control |
| Streamlit Cloud | Free deployment |

## How to Run Locally
```bash
git clone https://github.com/varunNeon/IndiaFin.git
cd IndiaFin
pip install -r requirements.txt
streamlit run app.py
```

## Skills Demonstrated

- Working with live financial APIs
- Time-series feature engineering (moving averages, rolling volatility)
- Data pipeline architecture across multiple Python modules
- Interactive dashboard design and deployment
```
