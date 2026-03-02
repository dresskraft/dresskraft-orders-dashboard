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
# HELPER FUNCTION (Indian Format)
# =====================================================

def format_indian(number):
    if pd.isna(number) or number == "":
        return "-"
    number = round(float(number))
    return "{:,}".format(number)

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

ADDON_OPTIONS = ["Pearls", "Studs", "Both Mix", "No Add On", "Read Chat"]
PRODUCTION_OPTIONS = ["To Start", "Ongoing", "Pending for Payment", "Paid - To Dispatch", "Dispatched"]

if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame()

required_columns = [
    "Est Delivery", "Name", "Add-on", "Sizes", "Count",
    "City", "Production Status", "Price", "Received",
    "Balance", "Payment Status", "Remarks", "Order Entry Date"
]

for col in required_columns:
    if col not in df.columns:
        df[col] = ""

df["Est Delivery"] = pd.to_datetime(df["Est Delivery"], errors="coerce")
df["Order Entry Date"] = pd.to_datetime(df["Order Entry Date"], errors="coerce")
df["Order Entry Date"] = df["Order Entry Date"].fillna(pd.Timestamp.today().normalize())

df = df.sort_values(by="Est Delivery", ascending=True).reset_index(drop=True)

# =====================================================
# ADD ORDER FORM
# =====================================================

st.title("📦 DressKraft Orders Dashboard")
st.subheader("➕ Add Order")

est_delivery = st.date_input("Est Delivery", datetime.today())
name_customer = st.text_input("Customer Name", "")
addon = st.selectbox("Add-on", ADDON_OPTIONS)
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
city = st.text_input("City", "")
production_status = st.selectbox("Production Status", PRODUCTION_OPTIONS)

price = st.number_input("Price", min_value=0.0, value=0.0)
received = st.number_input("Received", min_value=0.0, value=0.0)

balance = price - received
payment_status = "Paid" if balance == 0 else "Pending"

remarks = st.text_area("Remarks", "")

if st.button("Add Order"):

    new_row = {
        "Est Delivery": pd.to_datetime(est_delivery),
        "Name": name_customer,
        "Add-on": addon,
        "Sizes": sizes_value,
        "Count": count,
        "City": city,
        "Production Status": production_status,
        "Price": round(price),
        "Received": round(received),
        "Balance": round(balance),
        "Payment Status": payment_status,
        "Remarks": remarks,
        "Order Entry Date": pd.Timestamp.today().normalize()
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)

    st.success("Saved Successfully!")
    time.sleep(1)
    st.rerun()

# =====================================================
# ALL ORDERS SECTION
# =====================================================

st.subheader("📋 All Orders")

if not df.empty:

    df_display = df.copy()

    df_display["Est Delivery"] = df_display["Est Delivery"].dt.strftime("%d-%m-%Y")
    df_display["Order Entry Date"] = df_display["Order Entry Date"].dt.strftime("%d-%m-%Y")

    df_display = df_display.fillna("-").replace("", "-")

    df_display["Price"] = df_display["Price"].apply(format_indian)
    df_display["Received"] = df_display["Received"].apply(format_indian)
    df_display["Balance"] = df_display["Balance"].apply(format_indian)

    df_display.columns = [
        "Est Dt", "Name", "Add-on", "Sizes", "Qty",
        "City", "Prod Status", "Price", "Received",
        "Balance", "Pay Status", "Remarks", "Entry Dt"
    ]

    st.markdown("""
        <style>
        .stDataFrame div { font-size: 13px; }
        .stDataFrame thead th { text-align: center !important; }
        </style>
    """, unsafe_allow_html=True)

    st.dataframe(df_display, use_container_width=True)

    # DELETE OPTION
    st.markdown("### 🗑 Delete Order")
    delete_index = st.selectbox(
        "Select Order To Delete",
        df_display.index,
        format_func=lambda x: f"{df_display.loc[x,'Name']} - {df_display.loc[x,'Est Dt']}"
    )

    if st.button("Delete Selected Order"):
        df = df.drop(delete_index).reset_index(drop=True)
        df.to_csv(FILE_NAME, index=False)
        st.success("Order Deleted")
        time.sleep(1)
        st.rerun()

    # CSV DOWNLOAD
    csv = df_display.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, "dresskraft_orders.csv", "text/csv")

    # PDF DOWNLOAD
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
