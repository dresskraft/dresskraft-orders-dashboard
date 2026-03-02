import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# -------- PASSWORD PROTECTION (24 HOURS) --------
PASSWORD = "Diksha@1999"
COOKIE_DURATION = 60 * 60 * 24  # 24 hours

def check_password():
    if "login_time" in st.session_state:
        if time.time() - st.session_state["login_time"] < COOKIE_DURATION:
            return True

    def password_entered():
        if st.session_state["password"] == PASSWORD:
            st.session_state["login_time"] = time.time()
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", key="password", on_change=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password", type="password", key="password", on_change=password_entered)
        st.error("Incorrect Password")
        return False
    else:
        return True

if not check_password():
    st.stop()
# ------------------------------------------------
FILE_NAME = "orders.csv"

# Load existing data
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame(columns=[
        "Est Delivery","Name","Add-on","Sizes","Type",
        "Count","City","Production Status",
        "Price","Received","Balance","Payment Status"
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

# ===== Add New Order Form =====
st.subheader("➕ Add New Order")

with st.form("order_form"):
    est_delivery = st.date_input("Estimated Delivery", datetime.today())
    name = st.text_input("Customer Name")

    addon = st.selectbox("Add-on", [
        "No add on","Pearls","Studs","Pearl + Stud","Read Chat"
    ])

    sizes = st.text_input("Sizes (Example: 42M | 40F)")
    
    type_ = st.selectbox("Type", ["LED","Non-LED","Patch"])

    count = st.number_input("Count", min_value=1, step=1)

    city = st.text_input("Delivery City")

    prod_status = st.selectbox("Production Status", [
        "To Start","Ongoing","Printing","Shipped","Delivered"
    ])

    price = st.number_input("Price", min_value=0)

    received = st.number_input("Received", min_value=0)

    payment_status = st.selectbox("Payment Status", [
        "Payment Pending","Partial","Paid"
    ])

    submitted = st.form_submit_button("Save Order")

    if submitted:
        balance = price - received

        new_data = {
            "Est Delivery": est_delivery,
            "Name": name,
            "Add-on": addon,
            "Sizes": sizes,
            "Type": type_,
            "Count": count,
            "City": city,
            "Production Status": prod_status,
            "Price": price,
            "Received": received,
            "Balance": balance,
            "Payment Status": payment_status
        }

        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_csv(FILE_NAME, index=False)
        st.success("Order Saved Successfully!")

st.divider()

# ===== Filter Section =====
st.subheader("🔍 Filter Orders")

status_filter = st.selectbox("Filter by Production Status", ["All"] + list(df["Production Status"].unique()) if not df.empty else ["All"])

if status_filter != "All":
    filtered_df = df[df["Production Status"] == status_filter]
else:
    filtered_df = df

# ===== Display Orders =====
st.subheader("📋 All Orders")
st.dataframe(filtered_df, use_container_width=True)
