import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="The Vault - Aegis Dashboard", layout="wide")

st.title("🛡️ The Vault - AgentPay Dashboard")

st.sidebar.header("Vault Settings")
max_amount = st.sidebar.slider("Max Amount Per Tx ($)", 10, 500, 50)
allowed_categories = st.sidebar.multiselect("Allowed Vendors", ["AWS", "Cloudflare", "OpenAI", "Anthropic", "GitHub"], default=["AWS", "Cloudflare"])
block_hallucination = st.sidebar.checkbox("Block Hallucination Loops", value=True)

st.write("### Semantic Engine Logs & Activity")

col1, col2 = st.columns(2)

with col1:
    st.subheader("💳 Issued Seals (VCC)")
    issued_data = pd.DataFrame([
        {"Time": "2026-03-20 14:00", "Agent": "Claude-Code", "Vendor": "Cloudflare", "Amount": 15.0, "CVV": "***"},
        {"Time": "2026-03-20 15:30", "Agent": "OpenHands", "Vendor": "AWS", "Amount": 45.0, "CVV": "***"}
    ])
    st.dataframe(issued_data, use_container_width=True)

with col2:
    st.subheader("🚫 Rejected Attempts (Intercepted)")
    rejected_data = pd.DataFrame([
        {"Time": "2026-03-20 10:15", "Agent": "AutoGPT", "Vendor": "AWS", "Amount": 1500.0, "Reason": "Exceeds max transaction limit"},
        {"Time": "2026-03-20 16:10", "Agent": "Claude-Code", "Vendor": "Unknown", "Amount": 10.0, "Reason": "Hallucination / infinite loop detected"}
    ])
    st.dataframe(rejected_data, use_container_width=True)

st.write("---")
st.markdown("*Aegis Project MVP Dashboard - Mock Data Stream*")
