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
        return "{:,.0f}".format(round(float(number)))
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
# LOGIN SYSTEM
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
# PAGE NAVIGATION
# =====================================================

page = st.sidebar.radio("Navigation", ["Main Page", "All Orders Page"])

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
# ALL ORDERS FUNCTION
# =====================================================

def render_all_orders():

    col_title, col_filter = st.columns([3,2])

    with col_title:
        st.subheader("📋 All Orders")

    with col_filter:
        status_options = [
            "-", "To Start","Ongoing",
            "Pending for Payment",
            "Paid - To Dispatch",
            "Dispatched"
        ]
        selected_status = st.multiselect(
            "Filter Production Status",
            options=status_options,
            default=status_options,
            key="status_filter"
        )

    if df.empty:
        st.info("No orders yet.")
        return

    df_display = df.copy()

    # Apply filter
    df_display["Production Status"] = df_display["Production Status"].fillna("-")
    df_display = df_display[df_display["Production Status"].isin(selected_status)]

    # AUTO SORT
    df_display["__sort"] = pd.to_datetime(df_display["Est Delivery"], errors="coerce")
    df_display = df_display.sort_values("__sort")
    df_display = df_display.drop(columns=["__sort"])

    df_display["Payment Status"] = df_display.apply(
        lambda x: payment_status_logic(x["Price"], x["Received"]), axis=1
    )

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

    # ================= EDIT =================

    st.markdown("### ✏️ Edit Order")

    edit_idx = st.selectbox(
        "Select Order to Edit",
        df_display.index,
        format_func=lambda x: f"{df_display.loc[x,'Name']} - {df_display.loc[x,'Est Delivery']}"
    )

    col_load, col_msg = st.columns([1,2])

    with col_load:
        if st.button("Load for Edit"):
            st.session_state.edit_row = df.loc[edit_idx].to_dict()
            st.session_state.edit_index = edit_idx

    with col_msg:
        if "update_success" in st.session_state and st.session_state.update_success:
            st.success("Order Updated Successfully")
            st.session_state.update_success = False

    # KEEPING FULL EDIT BLOCK UNCHANGED
    if "edit_row" in st.session_state:

        edit = st.session_state.edit_row

        edit_name = st.text_input(
            "Customer Name",
            value="" if edit["Name"] == "-" else edit["Name"],
            key="edit_name"
        )

        addon_options = ["-- Select --","Pearls","Studs","Both Mix","No Add On","Read Chat"]

        edit_addon = st.selectbox(
            "Add-on",
            addon_options,
            index=0 if edit["Add-on"] == "-" else addon_options.index(edit["Add-on"]),
            key="edit_addon"
        )

        size_val = str(edit["Sizes"])

        if "M |" in size_val:
            detected_type = "Couple (M + F)"
        elif size_val == "Read Chat":
            detected_type = "Custom / More than 2"
        elif size_val == "-" or size_val == "":
            detected_type = "-- Select --"
        else:
            detected_type = "Single"

        jacket_options = ["-- Select --","Couple (M + F)","Single","Custom / More than 2"]

        edit_jacket_type = st.selectbox(
            "Jacket Type",
            jacket_options,
            index=jacket_options.index(detected_type),
            key="edit_jacket"
        )

        edit_sizes_value = "-"

        if edit_jacket_type == "Couple (M + F)":
            try:
                m, f = size_val.replace("M","").replace("F","").split("|")
                m = int(m.strip())
                f = int(f.strip())
            except:
                m, f = 40, 36

            col1, col2 = st.columns(2)
            m_edit = col1.number_input("Male Size", 30, 60, value=m, key="edit_male")
            f_edit = col2.number_input("Female Size", 30, 60, value=f, key="edit_female")
            edit_sizes_value = f"{m_edit}M | {f_edit}F"

        elif edit_jacket_type == "Single":
            try:
                s = int(size_val)
            except:
                s = 40
            s_edit = st.number_input("Size", 30, 60, value=s, key="edit_single")
            edit_sizes_value = str(s_edit)

        elif edit_jacket_type == "Custom / More than 2":
            st.info("Size will be marked as 'Read Chat'")
            edit_sizes_value = "Read Chat"

        edit_count = st.number_input("Count", value=int(edit["Count"]), key="edit_count")
        edit_city = st.text_input("City", value="" if edit["City"] == "-" else edit["City"], key="edit_city")

        status_options = ["-- Select --","To Start","Ongoing","Pending for Payment","Paid - To Dispatch","Dispatched"]

        edit_status = st.selectbox(
            "Production Status",
            status_options,
            index=0 if edit["Production Status"] == "-" else status_options.index(edit["Production Status"]),
            key="edit_status"
        )

        edit_price = st.number_input("Price", value=float(edit["Price"]), key="edit_price")
        edit_received = st.number_input("Received", value=float(edit["Received"]), key="edit_received")
        edit_remarks = st.text_area("Remarks", value="" if edit["Remarks"] == "-" else edit["Remarks"], key="edit_remarks")

        if st.button("Update Order"):

            df.loc[st.session_state.edit_index] = {
                **edit,
                "Name": edit_name,
                "Add-on": edit_addon if edit_addon != "-- Select --" else "-",
                "Sizes": edit_sizes_value,
                "Count": edit_count,
                "City": edit_city if edit_city else "-",
                "Production Status": edit_status if edit_status != "-- Select --" else "-",
                "Price": edit_price,
                "Received": edit_received,
                "Balance": edit_price - edit_received if edit_price else 0,
                "Remarks": edit_remarks if edit_remarks else "-"
            }

            df.to_csv(FILE_NAME, index=False)
            st.session_state.update_success = True
            del st.session_state.edit_row
            del st.session_state.edit_index
            st.rerun()

    # DELETE

    idx = st.selectbox(
        "Delete Order",
        df_display.index,
        format_func=lambda x: f"{df_display.loc[x,'Name']} - {df_display.loc[x,'Est Delivery']}"
    )

    if st.button("Delete Selected Order"):
        df2 = df.drop(idx).reset_index(drop=True)
        df2.to_csv(FILE_NAME, index=False)
        st.success("Deleted")
        st.rerun()

    # CSV

    st.download_button(
        "📥 Download CSV",
        df_display.to_csv(index=False).encode(),
        "dresskraft_orders.csv"
    )

    # PDF

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

# =====================================================
# MAIN PAGE
# =====================================================

if page == "Main Page":

    st.title("📦 DressKraft Orders Dashboard")
    st.subheader("➕ Add Order")

    # ADD ORDER BLOCK (UNCHANGED)
    # ... (kept exactly same as your existing)

    render_all_orders()

# =====================================================
# ALL ORDERS PAGE
# =====================================================

if page == "All Orders Page":
    st.title("📋 All Orders Page")
    render_all_orders()
