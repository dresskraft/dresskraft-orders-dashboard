import streamlit as st
import pandas as pd
import os
import time
import extra_streamlit_components as stx
from datetime import datetime, timedelta

st.set_page_config(page_title="DressKraft Orders Dashboard", layout="wide")

# =====================================================
# LOGIN SYSTEM (24 HOURS PER DEVICE)
# =====================================================

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

if not st.session_state.logged_in:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username.lower() in USERS and password == PASSWORD:
            expiry_time = datetime.now() + timedelta(hours=24)
            cookie_value = f"{username}|{expiry_time.isoformat()}"
            cookie_manager.set("dresskraft_login", cookie_value, expires_at=expiry_time)
            st.session_state.logged_in = True
            st.session_state.username = username
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
# DATA SECTION
# =====================================================

FILE_NAME = "orders.csv"

ADDON_OPTIONS = [
    "Studs",
    "Both Mix",
    "No add on",
    "Read Chat",
    "Pearl + Stud",
    "Pearls"
]

PRODUCTION_OPTIONS = [
    "To Start",
    "Ongoing",
    "Pending for Payment",
    "Paid - To Dispatch",
    "Dispatched"
]

if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame()

required_columns = [
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
    "Payment Status",
    "Remarks",
    "Order Entry Date"
]

for col in required_columns:
    if col not in df.columns:
        df[col] = ""

df["Est Delivery"] = pd.to_datetime(df["Est Delivery"], errors="coerce")
df["Order Entry Date"] = pd.to_datetime(df["Order Entry Date"], errors="coerce")

# Fill only missing Order Entry Date (old rows)
df["Order Entry Date"] = df["Order Entry Date"].fillna(pd.Timestamp.today().normalize())

df = df.sort_values(by="Est Delivery", ascending=True).reset_index(drop=True)

# =====================================================
# EDIT MODE
# =====================================================

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

st.title("📦 DressKraft Orders Dashboard")
st.subheader("➕ Add / Edit Order")

if st.session_state.edit_index is not None:
    row = df.loc[st.session_state.edit_index]
else:
    row = None

# =====================================================
# LIVE FORM
# =====================================================

est_delivery = st.date_input(
    "Est Delivery",
    value=row["Est Delivery"] if row is not None and pd.notna(row["Est Delivery"]) else datetime.today()
)

name_customer = st.text_input(
    "Customer Name",
    value=row["Name"] if row is not None else ""
)

addon = st.selectbox(
    "Add-on",
    ADDON_OPTIONS,
    index=ADDON_OPTIONS.index(row["Add-on"]) if row is not None and row["Add-on"] in ADDON_OPTIONS else 0
)

# =========================
# STRUCTURED SIZE MODE
# =========================

jacket_type = st.selectbox(
    "Jacket Type",
    ["Couple (M + F)", "Single", "Custom / More than 2"]
)

if jacket_type == "Couple (M + F)":
    col1, col2 = st.columns(2)
    male_size = col1.number_input("Male Size", min_value=30, max_value=60, value=44)
    female_size = col2.number_input("Female Size", min_value=30, max_value=60, value=38)
    sizes_value = f"{int(male_size)}M | {int(female_size)}F"

elif jacket_type == "Single":
    single_size = st.number_input("Size", min_value=30, max_value=60, value=38)
    sizes_value = str(int(single_size))

else:
    st.info("Size will be stored as 'Read Chat'")
    sizes_value = "Read Chat"

count = st.number_input(
    "Count",
    min_value=1,
    value=int(row["Count"]) if row is not None and str(row["Count"]).isdigit() else 1
)

city = st.text_input(
    "City",
    value=row["City"] if row is not None else ""
)

production_status = st.selectbox(
    "Production Status",
    PRODUCTION_OPTIONS,
    index=PRODUCTION_OPTIONS.index(row["Production Status"]) if row is not None and row["Production Status"] in PRODUCTION_OPTIONS else 0
)

price = st.number_input(
    "Price",
    min_value=0.0,
    value=float(row["Price"]) if row is not None and str(row["Price"]) != "" else 0.0
)

received = st.number_input(
    "Received",
    min_value=0.0,
    value=float(row["Received"]) if row is not None and str(row["Received"]) != "" else 0.0
)

balance = price - received
payment_status = "Paid" if balance == 0 else "Pending"

remarks = st.text_area(
    "Remarks",
    value=row["Remarks"] if row is not None else ""
)

if st.session_state.edit_index is None:
    submit = st.button("Add Order")
else:
    submit = st.button("Update Order")

if submit:

    if est_delivery is None:
        st.error("Est Delivery is required")
        st.stop()

    if st.session_state.edit_index is None:
        new_row = {
            "Est Delivery": est_delivery,
            "Name": name_customer,
            "Add-on": addon,
            "Sizes": sizes_value,
            "Count": count,
            "City": city,
            "Production Status": production_status,
            "Price": price,
            "Received": received,
            "Balance": balance,
            "Payment Status": payment_status,
            "Remarks": remarks,
            "Order Entry Date": datetime.today().date()
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    else:
        df.loc[st.session_state.edit_index, [
            "Est Delivery", "Name", "Add-on", "Sizes",
            "Count", "City", "Production Status",
            "Price", "Received", "Balance",
            "Payment Status", "Remarks"
        ]] = [
            est_delivery, name_customer, addon, sizes_value,
            count, city, production_status,
            price, received, balance,
            payment_status, remarks
        ]
        st.session_state.edit_index = None

    df.to_csv(FILE_NAME, index=False)
    st.success("Saved Successfully!")
    time.sleep(1)
    st.rerun()

# =====================================================
# DISPLAY TABLE (AUTO WIDTH)
# =====================================================

st.subheader("📋 All Orders")

if not df.empty:

    df_display = df.copy()

    df_display["Est Delivery"] = df_display["Est Delivery"].apply(
        lambda x: x.strftime("%d-%m-%Y") if pd.notna(x) else ""
    )

    df_display["Order Entry Date"] = df_display["Order Entry Date"].apply(
        lambda x: x.strftime("%d-%m-%Y") if pd.notna(x) else ""
    )

    table_html = df_display.to_html(index=False)

    st.markdown("""
        <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 8px;
            text-align: left;
            white-space: nowrap;
        }
        th {
            background-color: #f3f4f6;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("### ✏️ Select Order To Edit")

    selected_index = st.selectbox(
        "Choose Order",
        options=df_display.index,
        format_func=lambda x: f"{df_display.loc[x,'Name']} - {df_display.loc[x,'Est Delivery']}"
    )

    if st.button("Edit"):
        st.session_state.edit_index = selected_index
        st.rerun()
