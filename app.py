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
# HELPERS
# =====================================================

def format_indian(number):
    try:
        number = float(number)
        return "{:,.0f}".format(round(number))
    except:
        return "-"

def payment_status_logic(price, received):
    try:
        price = float(price)
        received = float(received)
    except:
        return "-"

    if price == 0:
        return "-"
    if received == 0:
        return "Unpaid"
    if received < price:
        return "Partial Paid"
    if received == price:
        return "Fully Paid"
    return "-"

# =====================================================
# LOGIN SYSTEM (24 HOURS)
# =====================================================

USERS = ["srinath", "diksha", "megha"]
PASSWORD = "Diksha@1999"

cookie_manager = stx.CookieManager()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

cookie = cookie_manager.get("dresskraft_login")

if cookie:
    try:
        user, expiry = cookie.split("|")
        expiry = datetime.fromisoformat(expiry)
        if datetime.now() < expiry:
            st.session_state.logged_in = True
            st.session_state.username = user
        else:
            cookie_manager.delete("dresskraft_login")
    except:
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
            st.error("Invalid credentials")
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

if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame(columns=[
        "Est Delivery","Name","Add-on","Sizes","Count","City",
        "Production Status","Price","Received","Balance",
        "Remarks","Order Entry Date"
    ])

# =====================================================
# ADD ORDER (DYNAMIC SIZE FILTER)
# =====================================================

st.title("📦 DressKraft Orders Dashboard")
st.subheader("➕ Add Order")

jacket_type = st.selectbox(
    "Jacket Type",
    ["-- Select --","Couple (M + F)","Single","Custom / More than 2"]
)

sizes_value = "-"
male = female = single = None

if jacket_type == "Couple (M + F)":
    col1, col2 = st.columns(2)
    male = col1.number_input("Male Size", 30, 60, step=1)
    female = col2.number_input("Female Size", 30, 60, step=1)

elif jacket_type == "Single":
    single = st.number_input("Size", 30, 60, step=1)

elif jacket_type == "Custom / More than 2":
    st.info("Size will be marked as 'Read Chat'")

with st.form("order_form", clear_on_submit=True):

    est_delivery = st.date_input("Est Delivery")
    name_customer = st.text_input("Customer Name")

    addon = st.selectbox(
        "Add-on",
        ["-- Select --","Pearls","Studs","Both Mix","No Add On","Read Chat"]
    )

    count = st.number_input("Count", min_value=1, step=1)
    city = st.text_input("City")

    production_status = st.selectbox(
        "Production Status",
        ["-- Select --","To Start","Ongoing","Pending for Payment","Paid - To Dispatch","Dispatched"]
    )

    price = st.number_input("Price", min_value=0.0, step=1.0)
    received = st.number_input("Received", min_value=0.0, step=1.0)
    remarks = st.text_area("Remarks")

    submitted = st.form_submit_button("Add Order")

if submitted:

    if (
        not name_customer or
        addon == "-- Select --" or
        jacket_type == "-- Select --" or
        production_status == "-- Select --"
    ):
        st.error("Please fill mandatory fields.")
        st.stop()

    if jacket_type == "Couple (M + F)":
        if male is None or female is None:
            st.error("Enter both sizes.")
            st.stop()
        sizes_value = f"{male}M | {female}F"

    elif jacket_type == "Single":
        if single is None:
            st.error("Enter size.")
            st.stop()
        sizes_value = str(single)

    elif jacket_type == "Custom / More than 2":
        sizes_value = "Read Chat"

    balance = price - received

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
        "Remarks": remarks if remarks else "-",
        "Order Entry Date": datetime.today()
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)

    st.success("Order Added Successfully!")

# =====================================================
# ALL ORDERS
# =====================================================

st.subheader("📋 All Orders")

if not df.empty:

    df_display = df.copy()

    df_display["Payment Status"] = df_display.apply(
        lambda x: payment_status_logic(x["Price"], x["Received"]), axis=1
    )

    # SAFE DATE CONVERSION (NO ERROR)
    df_display["Est Delivery"] = pd.to_datetime(
        df_display["Est Delivery"], errors="coerce"
    ).dt.strftime("%d-%m-%Y")

    df_display["Order Entry Date"] = pd.to_datetime(
        df_display["Order Entry Date"], errors="coerce"
    ).dt.strftime("%d-%m-%Y")

    df_display = df_display.fillna("-")

    df_display["Price"] = df_display["Price"].apply(format_indian)
    df_display["Received"] = df_display["Received"].apply(format_indian)
    df_display["Balance"] = df_display["Balance"].apply(format_indian)

    st.dataframe(df_display, use_container_width=True)

    idx = st.selectbox(
        "Delete Order",
        df_display.index,
        format_func=lambda x: f"{df_display.loc[x,'Name']} - {df_display.loc[x,'Est Delivery']}"
    )

    if st.button("Delete Selected Order"):
        df = df.drop(idx).reset_index(drop=True)
        df.to_csv(FILE_NAME, index=False)
        st.success("Deleted")
        st.rerun()

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
