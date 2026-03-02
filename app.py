import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager

# ==============================
# COOKIE SETUP (24 Hour Login)
# ==============================

cookies = EncryptedCookieManager(
    prefix="dresskraft_",
    password="super_secret_cookie_key"
)

if not cookies.ready():
    st.stop()

PASSWORD = "Diksha@1999"
COOKIE_DURATION = 60 * 60 * 24  # 24 hours


def check_password():
    # If cookie exists and not expired
    if "login_time" in cookies:
        login_time = float(cookies["login_time"])
        if time.time() - login_time < COOKIE_DURATION:
            return True

    # Show password input
    password = st.text_input("Enter Password", type="password", key="password_input")

    if password == PASSWORD:
        cookies["login_time"] = str(time.time())
        cookies.save()
        st.rerun()

    return False


if not check_password():
    st.stop()

# ==============================
# DASHBOARD STARTS HERE
# ==============================

st.set_page_config(page_title="DressKraft Orders Dashboard", layout="wide")
st.title("📦 DressKraft Orders Dashboard")

FILE_NAME = "orders.csv"

# Load existing data
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame(columns=[
        "Est Delivery",
        "Name",
        "Add-on",
        "Sizes",
        "Count",
        "City",
        "Production Status",
        "Price",
        "Received",
        "Balance",
        "Payment Status"
    ])

# ===== Dashboard Metrics =====

st.subheader("📊 Overview")

total_orders = len(df)
total_revenue = df["Price"].sum() if not df.empty else 0
total_received = df["Received"].sum() if not df.empty else 0
total_balance = df["Balance"].sum() if not df.empty else 0

col1, col2 = st.columns(2)
col1.metric("Total Orders", total_orders)
col2.metric("Total Revenue", total_revenue)

col3, col4 = st.columns(2)
col3.metric("Total Received", total_received)
col4.metric("Total Balance", total_balance)

st.divider()

# ===== Add New Order =====

st.subheader("➕ Add New Order")

with st.form("order_form"):
    est_delivery = st.date_input("Est Delivery")
    name = st.text_input("Customer Name")
    addon = st.text_input("Add-on")
    sizes = st.text_input("Sizes")
    count = st.number_input("Count", min_value=1)
    city = st.text_input("City")
    production_status = st.selectbox("Production Status", ["Pending", "In Progress", "Completed"])
    price = st.number_input("Price", min_value=0.0)
    received = st.number_input("Received", min_value=0.0)

    balance = price - received
    payment_status = "Paid" if balance == 0 else "Pending"

    submitted = st.form_submit_button("Add Order")

    if submitted:
        new_row = {
            "Est Delivery": est_delivery,
            "Name": name,
            "Add-on": addon,
            "Sizes": sizes,
            "Count": count,
            "City": city,
            "Production Status": production_status,
            "Price": price,
            "Received": received,
            "Balance": balance,
            "Payment Status": payment_status
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(FILE_NAME, index=False)
        st.success("Order Added Successfully!")
        st.rerun()

# ===== Orders Table =====

st.subheader("📋 All Orders")
st.dataframe(df, use_container_width=True)
