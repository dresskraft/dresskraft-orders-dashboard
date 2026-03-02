import streamlit as st
import pandas as pd
import os
import streamlit_authenticator as stauth

st.set_page_config(page_title="DressKraft Orders Dashboard", layout="wide")

# ==========================
# LOGIN CONFIG
# ==========================

# Hashed password for: Diksha@1999
hashed_password = "$2b$12$KIXQnL6z2bB6wQe1G9z5ZeZ0eV0pY2k0M1Hj1qZkVvK8gZxJrY9bS"

credentials = {
    "usernames": {
        "srinath": {"name": "Srinath", "password": hashed_password},
        "diksha": {"name": "Diksha", "password": hashed_password},
        "megha": {"name": "Megha", "password": hashed_password},
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "dresskraft_dashboard_cookie",
    "super_secret_key_123",
    cookie_expiry_days=1,
)

# ✅ Render login in sidebar (IMPORTANT)
name, authentication_status, username = authenticator.login("Login", "sidebar")

if authentication_status is False:
    st.error("Incorrect Username or Password")
    st.stop()

if authentication_status is None:
    st.warning("Please login from sidebar")
    st.stop()

authenticator.logout("Logout", "sidebar")
st.sidebar.write(f"Welcome {name}")

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
        st.rerun()

st.subheader("📋 All Orders")
st.dataframe(df, use_container_width=True)
