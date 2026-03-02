import streamlit as st
import pandas as pd
import os
import time
import extra_streamlit_components as stx
from datetime import datetime, timedelta
from io import BytesIO

# PDF Imports
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4

st.set_page_config(page_title="DressKraft Orders Dashboard", layout="wide")

# =====================================================
# LOGIN SYSTEM
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
            cookie_manager.set(
                "dresskraft_login",
                f"{username}|{expiry_time.isoformat()}",
                expires_at=expiry_time
            )
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
# DATA SETUP
# =====================================================

FILE_NAME = "orders.csv"

ADDON_OPTIONS = [
    "Pearls",
    "Studs",
    "Both Mix",
    "No Add On",
    "Read Chat"
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
# FORM
# =====================================================

est_delivery = st.date_input(
    "Est Delivery",
    value=row["Est Delivery"].date() if row is not None and pd.notna(row["Est Delivery"]) else datetime.today()
)

name_customer = st.text_input("Customer Name", value=row["Name"] if row is not None else "")

addon = st.selectbox(
    "Add-on",
    ADDON_OPTIONS,
    index=ADDON_OPTIONS.index(row["Add-on"]) if row is not None and row["Add-on"] in ADDON_OPTIONS else 0
)

jacket_type = st.selectbox("Jacket Type", ["Couple (M + F)", "Single", "Custom / More than 2"])

if jacket_type == "Couple (M + F)":
    col1, col2 = st.columns(2)
    male = col1.number_input("Male Size", 30, 60, 44)
    female = col2.number_input("Female Size", 30, 60, 38)
    sizes_value = f"{int(male)}M | {int(female)}F"
elif jacket_type == "Single":
    single = st.number_input("Size", 30, 60, 38)
    sizes_value = str(int(single))
else:
    sizes_value = "Read Chat"

count = st.number_input("Count", min_value=1, value=1)
city = st.text_input("City", value=row["City"] if row is not None else "")

production_status = st.selectbox(
    "Production Status",
    PRODUCTION_OPTIONS,
    index=PRODUCTION_OPTIONS.index(row["Production Status"]) if row is not None and row["Production Status"] in PRODUCTION_OPTIONS else 0
)

price = st.number_input("Price", min_value=0.0, value=0.0)
received = st.number_input("Received", min_value=0.0, value=0.0)

balance = price - received
payment_status = "Paid" if balance == 0 else "Pending"

remarks = st.text_area("Remarks", value=row["Remarks"] if row is not None else "")

submit = st.button("Add Order" if st.session_state.edit_index is None else "Update Order")

if submit:

    new_row = {
        "Est Delivery": pd.to_datetime(est_delivery),
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
        "Order Entry Date": pd.Timestamp.today().normalize()
    }

    if st.session_state.edit_index is None:
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df.loc[st.session_state.edit_index] = new_row
        st.session_state.edit_index = None

    df.to_csv(FILE_NAME, index=False)
    st.success("Saved Successfully!")
    time.sleep(1)
    st.rerun()

# =====================================================
# ALL ORDERS SECTION (SMALLER SIZE)
# =====================================================

st.subheader("📋 All Orders")

if not df.empty:

    df_display = df.copy()
    df_display["Est Delivery"] = df_display["Est Delivery"].dt.strftime("%d-%m-%Y")
    df_display["Order Entry Date"] = df_display["Order Entry Date"].dt.strftime("%d-%m-%Y")

    # Reduce table font size slightly
    st.markdown("""
        <style>
        .stDataFrame div {
            font-size: 13px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.dataframe(df_display, use_container_width=True)

    # DELETE OPTION
    st.markdown("### 🗑 Delete Order")
    delete_index = st.selectbox(
        "Select Order To Delete",
        df_display.index,
        format_func=lambda x: f"{df_display.loc[x,'Name']} - {df_display.loc[x,'Est Delivery']}"
    )

    if st.button("Delete Selected Order"):
        df = df.drop(delete_index).reset_index(drop=True)
        df.to_csv(FILE_NAME, index=False)
        st.success("Order Deleted")
        time.sleep(1)
        st.rerun()

    # DOWNLOADS
    csv = df_display.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, "dresskraft_orders.csv", "text/csv")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))

    data = [df_display.columns.tolist()] + df_display.values.tolist()
    pdf_table = Table(data)

    pdf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
    ]))

    doc.build([pdf_table])

    st.download_button("📄 Download PDF", buffer.getvalue(), "dresskraft_orders.pdf", "application/pdf")
