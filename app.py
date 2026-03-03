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

# ================= DARK THEME =================

st.markdown("""
<style>

html, body, [class*="css"] {
    background-color: #0e1117;
    color: #ffffff;
}

.logo-container {
    margin-top: 45px;
    margin-bottom: 25px;
    text-align: center;
}

.logo-text {
    font-size: 34px;
    font-weight: 700;
    color: white;
    letter-spacing: 1px;
}

.logo-bow {
    font-size: 28px;
    margin-right: 6px;
}

.logo-sparkle {
    font-size: 22px;
    margin-left: 6px;
}

div[data-baseweb="select"] > div {
    background-color: #1f2937 !important;
}

input, textarea {
    background-color: #1f2937 !important;
    color: white !important;
}

.stButton>button {
    background-color: #ec4899;
    color: white;
    border-radius: 6px;
    border: none;
}

.stButton>button:hover {
    background-color: #db2777;
}

</style>

<div class="logo-container">
    <span class="logo-bow">🎀</span>
    <span class="logo-text">DressKraft</span>
    <span class="logo-sparkle">✨</span>
</div>
""", unsafe_allow_html=True)

# ================= HELPERS =================

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

# ================= 24 HOUR PERSISTENT LOGIN =================

USERS = ["srinath", "diksha", "megha"]
PASSWORD = "Diksha@1999"

cookie_manager = stx.CookieManager()

if not cookie_manager.ready():
    st.stop()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

cookie = cookie_manager.get("dresskraft_login")

if cookie:
    try:
        user, expiry_str = cookie.split("|")
        expiry = datetime.fromisoformat(expiry_str)

        if datetime.now() < expiry:
            st.session_state.logged_in = True
            st.session_state.username = user
        else:
            cookie_manager.delete("dresskraft_login")
    except:
        cookie_manager.delete("dresskraft_login")

if not st.session_state.logged_in:

    st.title("Login")

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

st.sidebar.markdown(f"### Welcome {st.session_state.username}")

if st.sidebar.button("Logout"):
    cookie_manager.delete("dresskraft_login")
    st.session_state.logged_in = False
    st.rerun()

# ================= DATA =================

FILE_NAME = "orders.csv"

if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame(columns=[
        "Est Delivery","Name","Add-on","Sizes","Count","City",
        "Production Status","Price","Received","Balance",
        "Remarks","Order Entry Date"
    ])
    # ================= ADD ORDER SECTION =================

st.markdown("## ➕ Add Order")

est_delivery = st.date_input("Est Delivery", key="add_est")
name_customer = st.text_input("Customer Name", key="add_name")

addon_options = ["-- Select --","Pearls","Studs","Both Mix","No Add On","Read Chat"]
addon = st.selectbox("Add-on", addon_options, key="add_addon")

jacket_options = ["-- Select --","Couple (M + F)","Single","Custom / More than 2"]
jacket_type = st.selectbox("Jacket Type", jacket_options, key="add_jacket")

sizes_value = "-"
male = female = single = None

if jacket_type == "Couple (M + F)":
    col1, col2 = st.columns(2)
    male = col1.number_input("Male Size", 30, 60, key="add_male")
    female = col2.number_input("Female Size", 30, 60, key="add_female")

elif jacket_type == "Single":
    single = st.number_input("Size", 30, 60, key="add_single")

elif jacket_type == "Custom / More than 2":
    st.info("Size will be marked as 'Read Chat'")

count = st.number_input("Count", min_value=1, key="add_count")
city = st.text_input("City", key="add_city")

status_options = ["-- Select --","To Start","Ongoing","Pending for Payment","Paid - To Dispatch","Dispatched"]
production_status = st.selectbox("Production Status", status_options, key="add_status")

price = st.number_input("Price", min_value=0.0, key="add_price")
received = st.number_input("Received", min_value=0.0, key="add_received")
remarks = st.text_area("Remarks", key="add_remarks")

if st.button("Add Order"):

    if not name_customer:
        st.error("Customer Name is required.")
        st.stop()

    if jacket_type == "Couple (M + F)":
        sizes_value = f"{male}M | {female}F"
    elif jacket_type == "Single":
        sizes_value = str(single)
    elif jacket_type == "Custom / More than 2":
        sizes_value = "Read Chat"

    balance = price - received if price else 0

    new_row = {
        "Est Delivery": est_delivery,
        "Name": name_customer,
        "Add-on": addon if addon != "-- Select --" else "-",
        "Sizes": sizes_value,
        "Count": count,
        "City": city if city else "-",
        "Production Status": production_status if production_status != "-- Select --" else "-",
        "Price": price,
        "Received": received,
        "Balance": balance,
        "Remarks": remarks if remarks else "-",
        "Order Entry Date": datetime.today()
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)
    st.success("Order Added Successfully!")

# ================= ALL ORDERS SECTION =================

st.markdown("## 📋 All Orders")

if not df.empty:

    # -------- FILTER --------
    df["Production Status"] = df["Production Status"].fillna("-").replace("", "-")
    filter_options = sorted(df["Production Status"].unique().tolist())

    selected_status = st.multiselect(
        "Filter Production Status",
        options=filter_options,
        default=filter_options
    )

    df_display = df.copy()

    if selected_status:
        df_display = df_display[df_display["Production Status"].isin(selected_status)]

    # -------- AUTO SORT (Oldest → Latest ALWAYS) --------
    df_display["__sort"] = pd.to_datetime(df_display["Est Delivery"], errors="coerce")
    df_display = df_display.sort_values("__sort", ascending=True)
    df_display = df_display.drop(columns=["__sort"])

    # -------- PAYMENT STATUS --------
    df_display["Payment Status"] = df_display.apply(
        lambda x: payment_status_logic(x["Price"], x["Received"]), axis=1
    )

    # -------- DATE FORMAT --------
    df_display["Est Delivery"] = pd.to_datetime(
        df_display["Est Delivery"], errors="coerce"
    ).dt.strftime("%d-%m-%Y")

    df_display["Order Entry Date"] = pd.to_datetime(
        df_display["Order Entry Date"], errors="coerce"
    ).dt.strftime("%d-%m-%Y")

    df_display = df_display.fillna("-")

    # -------- NUMBER FORMAT --------
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

    if st.button("Load for Edit"):
        st.session_state.edit_row = df.loc[edit_idx].to_dict()
        st.session_state.edit_index = edit_idx

    if "edit_row" in st.session_state:

        edit = st.session_state.edit_row

        edit_name = st.text_input("Customer Name",
                                  value="" if edit["Name"] == "-" else edit["Name"])

        edit_addon = st.selectbox(
            "Add-on",
            addon_options,
            index=addon_options.index(edit["Add-on"]) if edit["Add-on"] in addon_options else 0
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

        edit_jacket = st.selectbox(
            "Jacket Type",
            jacket_options,
            index=jacket_options.index(detected_type)
        )

        edit_sizes_value = "-"

        if edit_jacket == "Couple (M + F)":
            try:
                m, f = size_val.replace("M","").replace("F","").split("|")
                m = int(m.strip())
                f = int(f.strip())
            except:
                m, f = 40, 36

            col1, col2 = st.columns(2)
            m_edit = col1.number_input("Male Size", 30, 60, value=m)
            f_edit = col2.number_input("Female Size", 30, 60, value=f)
            edit_sizes_value = f"{m_edit}M | {f_edit}F"

        elif edit_jacket == "Single":
            try:
                s = int(size_val)
            except:
                s = 40
            s_edit = st.number_input("Size", 30, 60, value=s)
            edit_sizes_value = str(s_edit)

        elif edit_jacket == "Custom / More than 2":
            st.info("Size will be marked as 'Read Chat'")
            edit_sizes_value = "Read Chat"

        edit_count = st.number_input("Count", value=int(edit["Count"]))
        edit_city = st.text_input("City",
                                  value="" if edit["City"] == "-" else edit["City"])

        edit_status = st.selectbox(
            "Production Status",
            status_options,
            index=status_options.index(edit["Production Status"]) if edit["Production Status"] in status_options else 0
        )

        edit_price = st.number_input("Price", value=float(edit["Price"]))
        edit_received = st.number_input("Received", value=float(edit["Received"]))
        edit_remarks = st.text_area("Remarks",
                                    value="" if edit["Remarks"] == "-" else edit["Remarks"])

        col_up_btn, col_up_msg = st.columns([1,2])

        with col_up_btn:
            update_click = st.button("Update Order")

        with col_up_msg:
            if st.session_state.get("update_success", False):
                st.success("Updated Successfully")

        if update_click:
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
            st.rerun()

    # ================= DELETE =================

    st.markdown("### 🗑 Delete Order")

    delete_idx = st.selectbox(
        "Select Order to Delete",
        df_display.index,
        format_func=lambda x: f"{df_display.loc[x,'Name']} - {df_display.loc[x,'Est Delivery']}"
    )

    col_del_btn, col_del_msg = st.columns([1,2])

    with col_del_btn:
        delete_click = st.button("Delete Selected Order")

    with col_del_msg:
        if st.session_state.get("delete_success", False):
            st.success("Deleted Successfully")

    if delete_click:
        df = df.drop(delete_idx).reset_index(drop=True)
        df.to_csv(FILE_NAME, index=False)
        st.session_state.delete_success = True
        st.rerun()

    # ================= CSV =================

    st.download_button(
        "📥 Download CSV",
        df_display.to_csv(index=False).encode(),
        "dresskraft_orders.csv"
    )

    # ================= PDF =================

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

else:
    st.info("No orders yet.")
