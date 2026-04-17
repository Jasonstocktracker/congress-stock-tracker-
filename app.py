import streamlit as st
import pandas as pd
import requests

# ================== CONFIG ==================
# Paste your FMP API key here:
FMP_API_KEY = "YOUR_FMP_API_KEY_HERE"   # ← Change this!

HOUSE_URL = f"https://financialmodelingprep.com/stable/house-trading?apikey={FMP_API_KEY}"
SENATE_URL = f"https://financialmodelingprep.com/stable/senate-trading?apikey={FMP_API_KEY}"
# ===========================================

@st.cache_data(ttl=3600)  # Refresh every hour
def load_data():
    try:
        house = pd.DataFrame(requests.get(HOUSE_URL).json())
        senate = pd.DataFrame(requests.get(SENATE_URL).json())
        
        # Add chamber column
        if not house.empty:
            house["chamber"] = "House"
        if not senate.empty:
            senate["chamber"] = "Senate"
        
        # Combine
        df = pd.concat([house, senate], ignore_index=True)
        
        # Standardize date column if needed
        if "transactionDate" in df.columns:
            df["transaction_date"] = pd.to_datetime(df["transactionDate"], errors="coerce")
        elif "filingDate" in df.columns:
            df["transaction_date"] = pd.to_datetime(df["filingDate"], errors="coerce")
        else:
            df["transaction_date"] = pd.NaT
        
        return df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🗳️ Congress Stock Trades Tracker")
st.caption("Data from Financial Modeling Prep • Free tier • Not financial advice")

if df.empty:
    st.warning("No data loaded yet. Check your API key and try refreshing.")
    st.stop()

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    chamber = st.multiselect("Chamber", ["House", "Senate"], default=["House", "Senate"])
with col2:
    pol_filter = st.text_input("Politician name (e.g., Pelosi)")
with col3:
    ticker_filter = st.text_input("Stock ticker (e.g., NVDA)")

filtered = df.copy()
if chamber:
    filtered = filtered[filtered["chamber"].isin(chamber)]
if pol_filter and not filtered.empty:
    # FMP uses different column names; try common ones
    name_col = next((col for col in ["representative", "senator", "name", "politician"] if col in filtered.columns), None)
    if name_col:
        filtered = filtered[filtered[name_col].str.contains(pol_filter, case=False, na=False)]
if ticker_filter and not filtered.empty:
    ticker_col = next((col for col in ["ticker", "symbol"] if col in filtered.columns), None)
    if ticker_col:
        filtered = filtered[filtered[ticker_col].str.contains(ticker_filter, case=False, na=False)]

# Show table
display_cols = [col for col in ["chamber", "name", "representative", "senator", "politician", 
                                "ticker", "symbol", "transaction_date", "transactionType", 
                                "type", "amount", "assetDescription", "description"] 
                if col in filtered.columns]

st.dataframe(
    filtered[display_cols].sort_values("transaction_date", ascending=False),
    use_container_width=True
)

st.info("💡 Data has disclosure delays (up to 45 days). Tap column headers to sort.")
