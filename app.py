import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Fetch data from free public APIs
@st.cache_data(ttl=3600)  # Refresh every hour
def load_data():
    house_url = "https://housestockwatcher.com/api"
    senate_url = "https://senatestockwatcher.com/api"
    
    house = pd.DataFrame(requests.get(house_url).json())
    senate = pd.DataFrame(requests.get(senate_url).json())
    
    # Standardize columns
    for df, body in zip([house, senate], ["House", "Senate"]):
        df["chamber"] = body
        if "transaction_date" in df.columns:
            df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        elif "TransactionDate" in df.columns:
            df["transaction_date"] = pd.to_datetime(df["TransactionDate"])
    
    return pd.concat([house, senate], ignore_index=True)

df = load_data()

st.title("🗳️ Congress Stock Trades Tracker")
st.caption("Data from House & Senate Stock Watcher • Updated daily • Not financial advice")

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    chamber = st.multiselect("Chamber", ["House", "Senate"], default=["House", "Senate"])
with col2:
    pol_filter = st.text_input("Politician name (e.g., Pelosi, Cruz)")
with col3:
    ticker_filter = st.text_input("Stock ticker (e.g., NVDA, AAPL)")

filtered = df.copy()
if chamber:
    filtered = filtered[filtered["chamber"].isin(chamber)]
if pol_filter:
    filtered = filtered[filtered.get("representative", filtered.get("Senator", "")).str.contains(pol_filter, case=False, na=False)]
if ticker_filter:
    filtered = filtered[filtered.get("ticker", "").str.contains(ticker_filter, case=False, na=False)]

# Display table
st.dataframe(
    filtered[["chamber", "representative" if "representative" in filtered.columns else "Senator", 
              "ticker", "transaction_date", "transaction_type", "amount", "asset_description"]]
    .sort_values("transaction_date", ascending=False),
    use_container_width=True
)

st.info("Tip: Tap column headers to sort. Data has disclosure delays.")
