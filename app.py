import streamlit as st
import pandas as pd
import os
import time
import extra_streamlit_components as stx
from datetime import datetime, timedelta

st.set_page_config(page_title="DressKraft Orders Dashboard", layout="wide")

# ==========================
# 24 HOUR LOGIN SYSTEM
# ==========================

USERS = ["srinath", "diksha", "megha"]
PASSWORD = "Diksha@1999"

cookie_manager = stx.CookieManager()

# Initialize session
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Check cookie
login_cookie = cookie_manager.get("dresskraft_login")

if login_cookie:
    username, expiry = login_cookie.split("|")
    expiry = datetime.fromisoformat(expiry)

    if datetime.now() < expiry:
        st.session_state.logged_in = True
        st.session_state.username = username
    else:
        cookie_manager.delete("dresskraft_login")
        st.session_state.logged_in = False

# If not logged in → show login
if not st.session_state.logged_in:

    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username.lower() in USERS and password == PASSWORD:
            expiry_time = datetime.now() + timedelta(hours=24)
            cookie_value = f"{username}|{expiry_time.isoformat()}"

            cookie_manager.set(
                "dresskraft_login",
                cookie_value,
                expires_at=expiry_time
            )

            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Invalid username or password")

    st.stop()

# ==========================
# LOGOUT BUTTON
# ==========================

st.sidebar.write(f"Welcome {st.session_state.username}")

if st.sidebar.button("Logout"):
    cookie_manager.delete("dresskraft_login")
    st.session_state.logged_in = False
    st.rerun()

# ==========================
# DASHBOARD STARTS HERE
# ==========================

st.title("📦 DressKraft Orders Dashboard")

FILE_NAME = "orders.csv"

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

# ==========================
# OVERVIEW METRICS
# ==========================

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

# ==========================
# ADD NEW ORDER
# ==========================

st.subheader("➕ Add New Order")

with st.form("order_form"):
    est_delivery = st.date_input("Est Delivery")
    name_customer = st.text_input("Customer Name")
    addon = st.text_input("Add-on")
    sizes = st.text_input("Sizes")
    count = st.number_input("Count", min_value=1)
    city = st.text_input("City")
    production_status = st.selectbox(
        "Production Status",
        ["Pending", "In Progress", "Completed"]
    )
    price = st.number_input("Price", min_value=0.0)
    received = st.number_input("Received", min_value=0.0)

    balance = price - received
    payment_status = "Paid" if balance == 0 else "Pending"

    submitted = st.form_submit_button("Add Order")

    if submitted:
        new_row = {
            "Est Delivery": est_delivery,
            "Name": name_customer,
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
        time.sleep(1)
        st.rerun()

# ==========================
# SHOW ALL ORDERS
# ==========================

st.subheader("📋 All Orders")
st.dataframe(df, use_container_width=True)
