"""
Bluestock MF Capstone — Streamlit Web App (B2 bonus)

Usage:
    streamlit run scripts/streamlit_app.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "db" / "bluestock_mf.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

st.set_page_config(page_title="Bluestock MF Analytics", layout="wide")

@st.cache_data
def query(sql):
    return pd.read_sql(sql, engine)


st.sidebar.title("Bluestock MF Analytics")
fund_houses = query("SELECT DISTINCT fund_house FROM dim_fund ORDER BY fund_house")["fund_house"].tolist()
categories = query("SELECT DISTINCT category FROM dim_fund ORDER BY category")["category"].tolist()

fh = st.sidebar.selectbox("Fund House", ["All"] + fund_houses)
cat = st.sidebar.multiselect("Category", categories, default=categories[:3])

tab1, tab2, tab3, tab4 = st.tabs(["Industry Overview", "Fund Performance", "Investor Analytics", "SIP Trends"])

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    aum = query("SELECT SUM(aum_cr) as total FROM fact_aum WHERE date_id = (SELECT MAX(date_id) FROM fact_aum)")
    sip = query("SELECT SUM(amount) as total FROM fact_transactions WHERE transaction_type = 'SIP'")
    folios = query("SELECT MAX(total_folios_crore) as total FROM fact_folio")
    schemes = query("SELECT COUNT(DISTINCT amfi_code) as total FROM dim_fund")
    col1.metric("Total AUM", f"₹{aum['total'].iloc[0]/100:.0f}L Cr" if aum['total'].iloc[0] else "N/A")
    col2.metric("SIP Inflow", f"₹{sip['total'].iloc[0]/1e7:.0f} Cr" if sip['total'].iloc[0] else "N/A")
    col3.metric("Total Folios", f"{folios['total'].iloc[0]:.2f} Cr" if folios['total'].iloc[0] else "N/A")
    col4.metric("Schemes", str(schemes['total'].iloc[0]))

    aum_trend = query("""
        SELECT d.year || '-' || printf('%02d', d.month) as yr_mo, SUM(a.aum_cr) as total_aum
        FROM fact_aum a JOIN dim_date d ON a.date_id = d.date_id
        GROUP BY yr_mo ORDER BY yr_mo
    """)
    if not aum_trend.empty:
        fig = px.line(aum_trend, x="yr_mo", y="total_aum", title="AUM Trend")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    scorecard = query("""
        SELECT f.scheme_name, f.fund_house, f.category, p.return_3yr, p.expense_ratio
        FROM fact_performance p JOIN dim_fund f ON p.amfi_code = f.amfi_code
    """)
    st.dataframe(scorecard, use_container_width=True)

with tab3:
    state_data = query("""
        SELECT state, SUM(amount) as total FROM fact_transactions
        WHERE transaction_type = 'SIP' GROUP BY state ORDER BY total DESC LIMIT 15
    """)
    if not state_data.empty:
        fig = px.bar(state_data, x="total", y="state", orientation="h", title="SIP by State")
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    sip_trend = query("""
        SELECT d.year || '-' || printf('%02d', d.month) as yr_mo,
               SUM(CASE WHEN t.transaction_type = 'SIP' THEN t.amount ELSE 0 END) as sip_amount
        FROM fact_transactions t JOIN dim_date d ON t.date_id = d.date_id
        GROUP BY yr_mo ORDER BY yr_mo
    """)
    if not sip_trend.empty:
        fig = px.line(sip_trend, x="yr_mo", y="sip_amount", title="SIP Trend")
        st.plotly_chart(fig, use_container_width=True)
