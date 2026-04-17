import streamlit as st
import pandas as pd
import requests

st.title("🗳️ Congress Stock Trades Tracker")
st.caption("Data from public House & Senate Stock Watcher • Not financial advice")

@st.cache_data(ttl=1800)  # Refresh every 30 minutes
def load_data():
    try:
        house_url = "https://housestockwatcher.com/api"
        senate_url = "https://senatestockwatcher.com/api"
        
        house_resp = requests.get(house_url, timeout=10)
        senate_resp = requests.get(senate_url, timeout=10)
        
        if not house_resp.ok:
            st.warning(f"House API returned status {house_resp.status_code}")
            house = pd.DataFrame()
        else:
            house = pd.DataFrame(house_resp.json())
        
        if not senate_resp.ok:
            st.warning(f"Senate API returned status {senate_resp.status_code}")
            senate = pd.DataFrame()
        else:
            senate = pd.DataFrame(senate_resp.json())
        
        # Add chamber
        if not house.empty:
            house["chamber"] = "House"
        if not senate.empty:
            senate["chamber"] = "Senate"
        
        df = pd.concat([house, senate], ignore_index=True)
        
        # Standardize date
        if "transaction_date" in df.columns:
            df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
        elif "TransactionDate" in df.columns:
            df["transaction_date"] = pd.to_datetime(df["TransactionDate"], errors="coerce")
        else:
            df["transaction_date"] = pd.NaT
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ Could not load data right now. The public APIs may be temporarily down. Try refreshing the page in a few minutes.")
    st.info("Alternative: FMP congressional data now requires a paid plan on the free tier.")
    st.stop()

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

if pol_filter and not filtered.empty:
    name_col = next((col for col in ["representative", "Senator", "name"] if col in filtered.columns), None)
    if name_col:
        filtered = filtered[filtered[name_col].str.contains(pol_filter, case=False, na=False)]

if ticker_filter and not filtered.empty:
    ticker_col = next((col for col in ["ticker", "symbol"] if col in filtered.columns), None)
    if ticker_col:
        filtered = filtered[filtered[ticker_col].str.contains(ticker_filter, case=False, na=False)]

# Show table
display_cols = [col for col in ["chamber", "representative", "Senator", "ticker", "transaction_date", 
                                "transaction_type", "amount", "asset_description"] 
                if col in filtered.columns]

st.dataframe(
    filtered[display_cols].sort_values("transaction_date", ascending=False),
    use_container_width=True
)

st.info("💡 Data usually updates daily but has disclosure delays (up to 45 days). Tap column headers to sort.")
