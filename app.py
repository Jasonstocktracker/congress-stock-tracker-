import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.title("🗳️ Congress Stock Trades Tracker")
st.caption("Fallback scraper from Capitol Trades • Not financial advice • Up to 45-day disclosure delay")

@st.cache_data(ttl=1800)  # Cache 30 minutes
def load_data():
    # Try old watchers first (quick timeout)
    df_list = []
    for name, url in [("House", "https://housestockwatcher.com/api"), ("Senate", "https://senatestockwatcher.com/api")]:
        try:
            resp = requests.get(url, timeout=5)
            if resp.ok:
                temp = pd.DataFrame(resp.json())
                temp["source"] = name
                df_list.append(temp)
                st.success(f"Loaded from {name} watcher")
        except:
            pass  # silent if down

    # Main fallback: Scrape Capitol Trades latest trades
    if not df_list:
        try:
            st.info("Using Capitol Trades scraper for recent trades...")
            url = "https://www.capitoltrades.com/trades"
            headers = {"User-Agent": "Mozilla/5.0 (compatible; CongressTrackerApp/1.0)"}
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            tables = soup.find_all("table")
            
            if tables:
                # Read the first main trades table
                cap_df = pd.read_html(str(tables[0]))[0]
                cap_df["source"] = "Capitol Trades"
                df_list.append(cap_df)
                st.success(f"Loaded {len(cap_df)} recent trades from Capitol Trades")
            else:
                st.warning("No table found on Capitol Trades page")
        except Exception as e:
            st.error(f"Scrape failed: {str(e)[:200]}")

    if df_list:
        df = pd.concat(df_list, ignore_index=True)
        # Try to find a date column and standardize
        date_cols = [col for col in df.columns if any(k in str(col).lower() for k in ["traded", "date", "published", "filed"])]
        if date_cols:
            df["transaction_date"] = pd.to_datetime(df[date_cols[0]], errors="coerce")
        else:
            df["transaction_date"] = pd.NaT
        return df
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ Still no data. Capitol Trades may have changed structure or be temporarily blocked.")
    st.info("Try refreshing in 30 minutes. As a last resort, you can manually visit https://www.capitoltrades.com/trades and copy data.")
    st.stop()

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    sources = st.multiselect("Source", options=df["source"].unique().tolist(), default=df["source"].unique().tolist())
with col2:
    pol_filter = st.text_input("Politician (e.g., Pfluger, Larsen, Pelosi)")
with col3:
    ticker_filter = st.text_input("Ticker or Issuer (e.g., UHAL, BRK/B, AXP)")

filtered = df[df["source"].isin(sources)] if not df.empty else df

if pol_filter and not filtered.empty:
    name_cols = [c for c in filtered.columns if any(k in str(c).lower() for k in ["politician", "name"])]
    if name_cols:
        filtered = filtered[filtered[name_cols[0]].astype(str).str.contains(pol_filter, case=False, na=False)]

if ticker_filter and not filtered.empty:
    ticker_cols = [c for c in filtered.columns if any(k in str(c).lower() for k in ["ticker", "issuer", "symbol"])]
    if ticker_cols:
        filtered = filtered[filtered[ticker_cols[0]].astype(str).str.contains(ticker_filter, case=False, na=False)]

# Show available columns
st.dataframe(
    filtered.sort_values("transaction_date", ascending=False) if "transaction_date" in filtered.columns else filtered,
    use_container_width=True
)

st.info("💡 Data from public sources. Always cross-check official filings at disclosures-clerk.house.gov or efdsearch.senate.gov.")
