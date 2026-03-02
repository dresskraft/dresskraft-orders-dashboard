import streamlit as st
import pandas as pd
import os
import extra_streamlit_components as stx
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4

st.set_page_config(page_title="DressKraft Orders Dashboard", layout="wide")

# =====================================================
# HELPER
# =====================================================

def format_indian(number):
    if pd.isna(number):
        return "-"
    return "{:,}".format(int(round(float(number))))

# =====================================================
# LOGIN
# =====================================================

USERS = ["srinath", "diksha", "megha"]
PASSWORD = "Diksha@1999"
cookie_manager = stx.CookieManager()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

cookie = cookie_manager.get("dresskraft_login")

if cookie:
    user, expiry = cookie.split("|")
    expiry = datetime.fromisoformat(expiry)
    if datetime.now() < expiry:
        st.session_state.logged_in = True
        st.session_state.username = user
    else:
        cookie_manager.delete("dresskraft_login")

if not st.session_state.logged_in:
    st.title("🔐 Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user.lower() in USERS and pwd == PASSWORD:
            expiry = datetime.now() + timedelta(hours=24)
            cookie_manager.set(
                "dresskraft_login",
                f"{user}|{expiry.isoformat()}",
                expires_at=expiry
            )
            st.session_state.logged_in = True
            st.session_state.username = user
            st.rerun()
        else:
            st.error("Invalid username or password")
    st.stop()

st.sidebar.write(f"Welcome {st.session_state.username}")
if st.sidebar.button("Logout"):
    cookie_manager.delete("dresskraft_login")
    st.session_state.logged_in = False
    st.rerun()

# =====================================================
# DATA
# =====================================================

FILE_NAME = "orders.csv"

ADDON_OPTIONS = ["Pearls", "Studs", "Both Mix", "No Add On", "Read Chat"]
PRODUCTION_OPTIONS = ["To Start", "Ongoing", "Pending for Payment", "Paid - To Dispatch", "Dispatched"]

if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame(columns=[
        "Est Delivery","Name","Add-on","Sizes","Count","City",
        "Production Status","Price","Received","Balance",
        "Payment Status","Remarks","Order Entry Date"
    ])

# =====================================================
# RESET LOGIC
# =====================================================

if "form_reset" not in st.session_state:
    st.session_state.form_reset = True

if st.session_state.form_reset:
    st.session_state.est_delivery = datetime.today()
    st.session_state.order_entry_date = datetime.today()
    st.session_state.name_customer = ""
    st.session_state.addon = "-- Select --"
    st.session_state.jacket_type = "-- Select --"
    st.session_state.male = 40
    st.session_state.female = 36
    st.session_state.single = 40
    st.session_state.count = 1
    st.session_state.city = ""
    st.session_state.production_status = "-- Select --"
    st.session_state.price = 0
    st.session_state.received = 0
    st.session_state.remarks = ""
    st.session_state.form_reset = False

# =====================================================
# ADD ORDER
# =====================================================

st.title("📦 DressKraft Orders Dashboard")
st.subheader("➕ Add Order")

est_delivery = st.date_input("Est Delivery", key="est_delivery")
order_entry_date = st.date_input("Order Entry Date", key="order_entry_date")

name_customer = st.text_input("Customer Name", key="name_customer")

addon = st.selectbox(
    "Add-on",
    ["-- Select --"] + ADDON_OPTIONS,
    key="addon"
)

jacket_type = st.selectbox(
    "Jacket Type",
    ["-- Select --","Couple (M + F)","Single","Custom / More than 2"],
    key="jacket_type"
)

sizes_value = ""

# 🔥 DYNAMIC SIZE WITH NUMBER INPUT

if jacket_type == "Couple (M + F)":
    col1, col2 = st.columns(2)
    male = col1.number_input("Male Size", min_value=30, max_value=60, step=1, key="male")
    female = col2.number_input("Female Size", min_value=30, max_value=60, step=1, key="female")
    sizes_value = f"{male}M | {female}F"

elif jacket_type == "Single":
    single = st.number_input("Size", min_value=30, max_value=60, step=1, key="single")
    sizes_value = str(single)

elif jacket_type == "Custom / More than 2":
    st.info("Sizes automatically set as Read Chat")
    sizes_value = "Read Chat"

count = st.number_input("Count", min_value=1, step=1, key="count")

city = st.text_input("City", key="city")

production_status = st.selectbox(
    "Production Status",
    ["-- Select --"] + PRODUCTION_OPTIONS,
    key="production_status"
)

price = st.number_input("Price", min_value=0, step=100, key="price")
received = st.number_input("Received", min_value=0, step=100, key="received")

balance = price - received
payment_status = "Paid" if balance == 0 else "Pending"

remarks = st.text_area("Remarks", key="remarks")

if st.button("Add Order"):

    if (
        not name_customer or
        addon == "-- Select --" or
        jacket_type == "-- Select --" or
        production_status == "-- Select --"
    ):
        st.error("Please fill mandatory fields.")
        st.stop()

    new_row = {
        "Est Delivery": est_delivery,
        "Name": name_customer,
        "Add-on": addon,
        "Sizes": sizes_value,
        "Count": count,
        "City": city if city else "-",
        "Production Status": production_status,
        "Price": price,
        "Received": received,
        "Balance": balance,
        "Payment Status": payment_status,
        "Remarks": remarks if remarks else "-",
        "Order Entry Date": order_entry_date
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)

    st.success("Order Added Successfully!")

    st.session_state.form_reset = True
    st.rerun()

# =====================================================
# ALL ORDERS
# =====================================================

st.subheader("📋 All Orders")

if not df.empty:

    df_display = df.copy()

    df_display["Est Delivery"] = pd.to_datetime(df_display["Est Delivery"]).dt.strftime("%d-%m-%Y")
    df_display["Order Entry Date"] = pd.to_datetime(df_display["Order Entry Date"]).dt.strftime("%d-%m-%Y")

    df_display["Price"] = df_display["Price"].apply(format_indian)
    df_display["Received"] = df_display["Received"].apply(format_indian)
    df_display["Balance"] = df_display["Balance"].apply(format_indian)

    df_display.columns = [
        "Est Dt","Name","Add-on","Sizes","Qty","City",
        "Prod Status","Price","Received","Balance",
        "Pay Status","Remarks","Entry Dt"
    ]

    st.dataframe(df_display, use_container_width=True)
