import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import os

# Set page config
st.set_page_config(page_title="The Vault - Point One Percent Dashboard", layout="wide")

st.title("The Vault - AgentPay Dashboard")

# Database path - located in project root
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pop_state.db"))

# Sidebar
st.sidebar.header("Vault Settings")
max_daily_budget = st.sidebar.slider("Max Daily Budget ($)", 10, 2000, 500)

if st.sidebar.button("Refresh Data"):
    st.rerun()

# Helper function to get data
def load_data():
    if not os.path.exists(DB_PATH):
        # Return empty structures if DB doesn't exist
        return pd.DataFrame(columns=["seal_id", "amount", "vendor", "status", "timestamp"]), 0.0

    with sqlite3.connect(DB_PATH) as conn:
        try:
            # Main Screen: Load all issued seals
            issued_df = pd.read_sql_query("SELECT * FROM issued_seals ORDER BY timestamp DESC", conn)
        except (pd.errors.DatabaseError, sqlite3.OperationalError):
            # Table doesn't exist yet
            issued_df = pd.DataFrame(columns=["seal_id", "amount", "vendor", "status", "timestamp"])

        try:
            # Budget Tracking: Query daily_budget for today's spent_amount
            today = date.today().isoformat()
            budget_query = "SELECT spent_amount FROM daily_budget WHERE date = ?"
            budget_df = pd.read_sql_query(budget_query, conn, params=(today,))
            spent_today = budget_df['spent_amount'].iloc[0] if not budget_df.empty else 0.0
        except (pd.errors.DatabaseError, sqlite3.OperationalError):
            spent_today = 0.0

    return issued_df, spent_today

# Load data
issued_df, spent_today = load_data()

# Budget Tracking Section
remaining_budget = max(0.0, max_daily_budget - spent_today)

col1, col2, col3 = st.columns(3)
col1.metric("Today's Spending", f"${spent_today:,.2f}")
col2.metric("Remaining Budget", f"${remaining_budget:,.2f}")
col3.metric("Max Daily Budget", f"${max_daily_budget:,.2f}")

# Progress bar: spending relative to the slider's max budget
progress_val = min(1.0, spent_today / max_daily_budget) if max_daily_budget > 0 else 0
st.write(f"**Budget Utilization ({progress_val*100:.1f}%)**")
st.progress(progress_val)

st.write("---")

# Main Screen: Issued Seals
st.subheader("Issued Seals & Activity")
if not issued_df.empty:
    st.dataframe(issued_df, use_container_width=True)
else:
    st.info("No records found in 'issued_seals' table.")

# Rejected Summary (Optional)
st.write("---")
st.subheader("Rejected Summary")
if not issued_df.empty and 'status' in issued_df.columns:
    rejected_df = issued_df[issued_df['status'].str.lower() == 'rejected']
    if not rejected_df.empty:
        st.dataframe(rejected_df, use_container_width=True)
    else:
        st.success("No rejected attempts found.")
else:
    st.info("No data available to show rejected attempts.")

st.write("---")
st.markdown("*Point One Percent MVP Dashboard - Live Database Stream*")
