import streamlit as st
import pandas as pd
import requests

# ================== CONFIG ==================
FMP_API_KEY = "HqzTGhnPIFYXS3O1VWOiOq7WZexJEJ9R"   # Your key is safely inside quotes here

# Correct FMP endpoints for latest disclosures (these work with free tier)
HOUSE_URL = f"https://financialmodelingprep.com/stable/house-latest?apikey={FMP_API_KEY}&limit=100"
SENATE_URL = f"https://financialmodelingprep.com/stable/senate-latest?apikey={FMP_API_KEY}&limit=100"
# ===========================================

@st.cache_data(ttl=3600)  # Refresh every hour
def load_data():
    try:
        house_resp = requests.get(HOUSE_URL)
        senate_resp = requests.get(SENATE_URL)
        
        house = pd.DataFrame(house_resp.json() if house_resp.ok else [])
        senate = pd.DataFrame(senate_resp.json() if senate_resp.ok else [])
        
        # Add chamber
        if not house.empty:
            house["chamber"] = "House"
        if not senate.empty:
            senate["chamber"] = "Senate"
        
        # Combine
        df = pd.concat([house, senate], ignore_index=True)
        
        # Standardize date column (FMP uses different names sometimes)
        date_cols = ["transactionDate", "filingDate", "date"]
        for col in date_cols:
            if col in df.columns:
                df["transaction_date"] = pd.to_datetime(df[col], errors="coerce")
                break
        else:
            df["transaction_date"] = pd.NaT
        
        return df
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return pd.DataFrame()

df = load_data()

st.title("🗳️ Congress Stock Trades Tracker")
st.caption("Data from Financial Modeling Prep • Not financial advice")

if df.empty:
    st.warning("⚠️ No data loaded. Check your API key or try refreshing the app.")
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
    name_cols = ["name", "representative", "senator", "politician"]
    name_col = next((col for col in name_cols if col in filtered.columns), None)
    if name_col:
        filtered = filtered[filtered[name_col].str.contains(pol_filter, case=False, na=False)]

if ticker_filter and not filtered.empty:
    ticker_cols = ["ticker", "symbol"]
    ticker_col = next((col for col in ticker_cols if col in filtered.columns), None)
    if ticker_col:
        filtered = filtered[filtered[ticker_col].str.contains(ticker_filter, case=False, na=False)]

# Display columns that actually exist
display_cols = [col for col in ["chamber", "name", "representative", "senator", "politician", 
                                "ticker", "symbol", "transaction_date", "transactionType", 
                                "type", "amount", "assetDescription", "description", "asset"] 
                if col in filtered.columns]

st.dataframe(
    filtered[display_cols].sort_values("transaction_date", ascending=False) if not filtered.empty else filtered,
    use_container_width=True
)

st.info("💡 Data has up to 45-day disclosure delay. Tap any column header to sort.")
