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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

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

# Load data
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame()

# ==========================
# SAFE COLUMN STRUCTURE FIX
# ==========================

required_columns = [
    "Order Entry Date",
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
]

for col in required_columns:
    if col not in df.columns:
        if col == "Order Entry Date":
            df[col] = datetime.today().date()
        else:
            df[col] = ""

# Convert date columns safely
df["Est Delivery"] = pd.to_datetime(df["Est Delivery"], errors="coerce")
df["Order Entry Date"] = pd.to_datetime(df["Order Entry Date"], errors="coerce")

# ==========================
# SORT BY DELIVERY DATE
# ==========================

df = df.sort_values(by="Est Delivery", ascending=True)

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
            "Order Entry Date": datetime.today().date(),
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
# EDIT TABLE
# ==========================

st.subheader("📋 All Orders")

if not df.empty:

    df_display = df.copy()

    # Format dates for display
    df_display["Est Delivery"] = df_display["Est Delivery"].dt.strftime("%d-%m-%Y")
    df_display["Order Entry Date"] = df_display["Order Entry Date"].dt.strftime("%d-%m-%Y")

    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        num_rows="dynamic",
        disabled=["Order Entry Date"]  # LOCK THIS COLUMN
    )

    if st.button("Save Changes"):
        # Restore locked column from original df
        edited_df["Order Entry Date"] = df["Order Entry Date"]

        # Convert back to datetime
        edited_df["Est Delivery"] = pd.to_datetime(
            edited_df["Est Delivery"],
            format="%d-%m-%Y",
            errors="coerce"
        )

        edited_df.to_csv(FILE_NAME, index=False)

        st.success("Changes Saved Successfully!")
        time.sleep(1)
        st.rerun()
