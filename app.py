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

# ==========================================
# HELPER FUNCTION
# ==========================================

def format_indian(number):
    if pd.isna(number) or number == "":
        return "-"
    return "{:,}".format(int(round(float(number))))

# ==========================================
# LOGIN SYSTEM
# ==========================================

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

# ==========================================
# DATA SETUP
# ==========================================

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

# ==========================================
# ADD ORDER FORM (TRUE BLANK + AUTO RESET)
# ==========================================

st.title("📦 DressKraft Orders Dashboard")
st.subheader("➕ Add Order")

with st.form("order_form", clear_on_submit=True):

    est_delivery = st.text_input("Est Delivery (DD-MM-YYYY)")
    name_customer = st.text_input("Customer Name")

    addon = st.selectbox(
        "Add-on",
        ["-- Select --"] + ADDON_OPTIONS
    )

    jacket_type = st.selectbox(
        "Jacket Type",
        ["-- Select --","Couple (M + F)","Single","Custom / More than 2"]
    )

    sizes_value = ""

    if jacket_type == "Couple (M + F)":
        male = st.text_input("Male Size")
        female = st.text_input("Female Size")
        if male and female:
            sizes_value = f"{male}M | {female}F"

    elif jacket_type == "Single":
        single = st.text_input("Size")
        if single:
            sizes_value = single

    elif jacket_type == "Custom / More than 2":
        sizes_value = "Read Chat"

    count = st.text_input("Count")
    city = st.text_input("City")

    production_status = st.selectbox(
        "Production Status",
        ["-- Select --"] + PRODUCTION_OPTIONS
    )

    price = st.text_input("Price")
    received = st.text_input("Received")
    remarks = st.text_area("Remarks")

    submitted = st.form_submit_button("Add Order")

if submitted:

    if (
        not est_delivery or
        not name_customer or
        addon == "-- Select --" or
        jacket_type == "-- Select --" or
        production_status == "-- Select --"
    ):
        st.error("Please fill mandatory fields.")
        st.stop()

    try:
        est_date_parsed = datetime.strptime(est_delivery, "%d-%m-%Y")
    except:
        st.error("Date must be DD-MM-YYYY format.")
        st.stop()

    price_val = float(price) if price else 0
    received_val = float(received) if received else 0
    balance = price_val - received_val
    payment_status = "Paid" if balance == 0 else "Pending"

    new_row = {
        "Est Delivery": est_date_parsed,
        "Name": name_customer,
        "Add-on": addon,
        "Sizes": sizes_value if sizes_value else "-",
        "Count": count if count else "-",
        "City": city if city else "-",
        "Production Status": production_status,
        "Price": price_val,
        "Received": received_val,
        "Balance": balance,
        "Payment Status": payment_status,
        "Remarks": remarks if remarks else "-",
        "Order Entry Date": datetime.today()
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)

    st.success("Order Added Successfully!")

# ==========================================
# ALL ORDERS
# ==========================================

st.subheader("📋 All Orders")

if not df.empty:

    df_display = df.copy()
    df_display["Est Delivery"] = pd.to_datetime(df_display["Est Delivery"]).dt.strftime("%d-%m-%Y")
    df_display["Order Entry Date"] = pd.to_datetime(df_display["Order Entry Date"]).dt.strftime("%d-%m-%Y")

    df_display = df_display.fillna("-")

    df_display["Price"] = df_display["Price"].apply(format_indian)
    df_display["Received"] = df_display["Received"].apply(format_indian)
    df_display["Balance"] = df_display["Balance"].apply(format_indian)

    df_display.columns = [
        "Est Dt","Name","Add-on","Sizes","Qty","City",
        "Prod Status","Price","Received","Balance",
        "Pay Status","Remarks","Entry Dt"
    ]

    st.dataframe(df_display, use_container_width=True)

    idx = st.selectbox(
        "Delete Order",
        df_display.index,
        format_func=lambda x: f"{df_display.loc[x,'Name']} - {df_display.loc[x,'Est Dt']}"
    )

    if st.button("Delete Selected Order"):
        df = df.drop(idx).reset_index(drop=True)
        df.to_csv(FILE_NAME, index=False)
        st.success("Deleted")

    st.download_button(
        "📥 Download CSV",
        df_display.to_csv(index=False).encode(),
        "dresskraft_orders.csv"
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    data = [df_display.columns.tolist()] + df_display.values.tolist()
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('GRID',(0,0),(-1,-1),0.25,colors.grey),
        ('FONTSIZE',(0,0),(-1,-1),6),
    ]))
    doc.build([table])

    st.download_button(
        "📄 Download PDF",
        buffer.getvalue(),
        "dresskraft_orders.pdf"
    )
