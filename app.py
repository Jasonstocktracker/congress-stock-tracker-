import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.title("🗳️ Congress Stock Trades Tracker")
st.caption("Improved scraper from Capitol Trades • Not financial advice • Up to 45-day delay")

@st.cache_data(ttl=1800)  # 30 min cache
def load_data():
    try:
        st.info("Fetching latest trades from Capitol Trades...")
        url = "https://www.capitoltrades.com/trades"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; CongressTracker/1.0; +https://github.com/Jasonstocktracker)"}
        
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Find all tables and try to locate the main trades table by class or size
        tables = soup.find_all("table")
        if not tables:
            st.error("No tables found on the page.")
            return pd.DataFrame()
        
        # Try each table until we get one with meaningful rows
        for table in tables:
            try:
                df = pd.read_html(str(table))[0]
                if len(df) > 5 and any(col for col in df.columns if "politician" in str(col).lower() or "traded" in str(col).lower()):
                    df["source"] = "Capitol Trades"
                    st.success(f"✅ Loaded {len(df)} recent trades!")
                    return df
            except:
                continue  # try next table
        
        st.warning("Could not parse any valid trades table.")
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Scrape error: {str(e)[:250]}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ Still couldn't load data automatically.")
    st.info("→ Visit https://www.capitoltrades.com/trades directly in Safari for the latest trades (e.g., recent buys by Rep. August Pfluger).")
    st.stop()

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    sources = st.multiselect("Source", df["source"].unique().tolist(), default=df["source"].unique().tolist())
with col2:
    pol_filter = st.text_input("Politician (e.g., Pfluger, Larsen)")
with col3:
    ticker_filter = st.text_input("Ticker/Issuer (e.g., UHAL, BRK/B)")

filtered = df[df["source"].isin(sources)] if not df.empty else df

if pol_filter and not filtered.empty:
    name_cols = [c for c in filtered.columns if any(k in str(c).lower() for k in ["politician", "name"])]
    if name_cols:
        filtered = filtered[filtered[name_cols[0]].astype(str).str.contains(pol_filter, case=False, na=False)]

if ticker_filter and not filtered.empty:
    ticker_cols = [c for c in filtered.columns if any(k in str(c).lower() for k in ["ticker", "issuer", "traded"])]
    if ticker_cols:
        filtered = filtered[filtered[ticker_cols[0]].astype(str).str.contains(ticker_filter, case=False, na=False)]

st.dataframe(
    filtered,
    use_container_width=True
)

st.info("💡 Recent example: Rep. August Pfluger bought UHAL, BRK/B, etc. on ~March 12, 2026. Always verify on official sites.")
