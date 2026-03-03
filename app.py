import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4

st.set_page_config(page_title="DressKraft Orders Dashboard", layout="wide")

# ================= DARK THEME =================

st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0f1117;
    color: #ffffff;
}
.block-container {
    padding-top: 1.5rem;
}
.stButton>button {
    background: linear-gradient(135deg, #2c2f4a, #1e2238);
    color: #ffffff;
    border-radius: 10px;
    border: 1px solid #3a3f5c;
    height: 3em;
    width: 100%;
    font-weight: 600;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #3a3f5c, #2c2f4a);
}
input, textarea {
    background-color: #1c1f26 !important;
    color: white !important;
}
div[data-baseweb="select"] > div {
    background-color: #1c1f26 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================

st.markdown("""
<div style="text-align:center;margin-bottom:15px;">
<h1 style="font-size:42px;">DressKraft</h1>
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

# ================= DATA =================

FILE_NAME = "orders.csv"

if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame(columns=[
        "Est Delivery","Name","Look","Add-on","Sizes","Count","City",
        "Production Status","Price","Received","Balance",
        "Remarks","Order Entry Date"
    ])
    # =====================================================
# ADD ORDER SECTION
# =====================================================

st.subheader("➕ Add Order")

est_delivery = st.date_input("Est Delivery", key="add_est")
name_customer = st.text_input("Customer Name", key="add_name")

# ===== LOOK (AFTER NAME) =====
look = st.selectbox(
    "Look",
    ["-- Select --","LED","Non-LED","Patch","Multiple"],
    key="add_look"
)

addon = st.selectbox(
    "Add-on",
    ["-- Select --","Pearls","Studs","Both Mix","No Add On","Read Chat"],
    key="add_addon"
)

jacket_type = st.selectbox(
    "Jacket Type",
    ["-- Select --","Couple (M + F)","Single","Custom / More than 2"],
    key="add_jacket"
)

sizes_value = "-"
male = female = single = None

# ===== DYNAMIC SIZING =====
if jacket_type == "Couple (M + F)":
    col1, col2 = st.columns(2)
    male = col1.number_input("Male Size", 30, 60, step=1, key="add_male")
    female = col2.number_input("Female Size", 30, 60, step=1, key="add_female")

elif jacket_type == "Single":
    single = st.number_input("Size", 30, 60, step=1, key="add_single")

elif jacket_type == "Custom / More than 2":
    st.info("Size will be marked as 'Read Chat'")

count = st.number_input("Count", min_value=1, step=1, key="add_count")
city = st.text_input("City", key="add_city")

production_status = st.selectbox(
    "Production Status",
    ["-- Select --","To Start","Ongoing","Pending for Payment","Paid - To Dispatch","Dispatched"],
    key="add_status"
)

price = st.number_input("Price", min_value=0.0, step=1.0, key="add_price")
received = st.number_input("Received", min_value=0.0, step=1.0, key="add_received")
remarks = st.text_area("Remarks", key="add_remarks")

if st.button("Add Order"):

    if not name_customer:
        st.error("Customer Name is required.")
        st.stop()

    if jacket_type == "Couple (M + F)" and male and female:
        sizes_value = f"{male}M | {female}F"
    elif jacket_type == "Single" and single:
        sizes_value = str(single)
    elif jacket_type == "Custom / More than 2":
        sizes_value = "Read Chat"
    else:
        sizes_value = "-"

    balance = price - received if price else 0

    new_row = {
        "Est Delivery": est_delivery if est_delivery else "-",
        "Name": name_customer,
        "Look": look if look != "-- Select --" else "-",
        "Add-on": addon if addon != "-- Select --" else "-",
        "Sizes": sizes_value,
        "Count": count if count else 1,
        "City": city if city else "-",
        "Production Status": production_status if production_status != "-- Select --" else "-",
        "Price": price if price else 0,
        "Received": received if received else 0,
        "Balance": balance,
        "Remarks": remarks if remarks else "-",
        "Order Entry Date": datetime.today()
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)

    st.success("Order Added Successfully!")

# ===== CLEAR FORM FIELDS =====
for key in list(st.session_state.keys()):
    if key.startswith("add_"):
        del st.session_state[key]

st.rerun()
    # =====================================================
# ALL ORDERS SECTION
# =====================================================

st.subheader("📋 All Orders")

if not df.empty:

    # ===== FILTER =====
    status_options = df["Production Status"].fillna("-").replace("", "-").unique().tolist()
    status_options = sorted(list(set(status_options)))

    selected_status = st.multiselect(
        "Filter Production Status",
        options=status_options,
        default=status_options
    )

    df_display = df.copy()
    df_display["Production Status"] = df_display["Production Status"].fillna("-").replace("", "-")

    if selected_status:
        df_display = df_display[df_display["Production Status"].isin(selected_status)]

    # ===== AUTO SORT ASCENDING =====
    df_display["__sort"] = pd.to_datetime(df_display["Est Delivery"], errors="coerce")
    df_display = df_display.sort_values("__sort", ascending=True)
    df_display = df_display.drop(columns=["__sort"])

    # ===== PAYMENT STATUS =====
    df_display["Payment Status"] = df_display.apply(
        lambda x: payment_status_logic(x["Price"], x["Received"]), axis=1
    )

    # ===== FORMAT DATES =====
    df_display["Est Delivery"] = pd.to_datetime(
        df_display["Est Delivery"], errors="coerce"
    ).dt.strftime("%d-%m-%Y")

    df_display["Order Entry Date"] = pd.to_datetime(
        df_display["Order Entry Date"], errors="coerce"
    ).dt.strftime("%d-%m-%Y")

    df_display = df_display.fillna("-")

    # ===== FORMAT NUMBERS =====
    df_display["Price"] = df_display["Price"].apply(format_indian)
    df_display["Received"] = df_display["Received"].apply(format_indian)
    df_display["Balance"] = df_display["Balance"].apply(format_indian)

    # ===== REORDER COLUMNS (Move Look after Name) =====
    columns = df_display.columns.tolist()

    if "Look" in columns:
        columns.remove("Look")
        name_index = columns.index("Name")
        columns.insert(name_index + 1, "Look")

    df_display = df_display[columns]

    st.dataframe(df_display, use_container_width=True)

    # =====================================================
    # EDIT SECTION
    # =====================================================

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
        if st.session_state.get("update_success"):
            st.success("Updated Successfully")
            st.session_state.update_success = False

    if "edit_row" in st.session_state:

        edit = st.session_state.edit_row

        edit_name = st.text_input(
            "Customer Name",
            value="" if edit["Name"] == "-" else edit["Name"],
            key="edit_name"
        )

        # ===== LOOK EDIT =====
        look_options = ["-- Select --","LED","Non-LED","Patch","Multiple"]

        edit_look = st.selectbox(
            "Look",
            look_options,
            index=look_options.index(edit["Look"]) if edit["Look"] in look_options else 0,
            key="edit_look"
        )

        addon_options = ["-- Select --","Pearls","Studs","Both Mix","No Add On","Read Chat"]

        edit_addon = st.selectbox(
            "Add-on",
            addon_options,
            index=addon_options.index(edit["Add-on"]) if edit["Add-on"] in addon_options else 0,
            key="edit_addon"
        )

        edit_count = st.number_input("Count", value=int(edit["Count"]), key="edit_count")
        edit_city = st.text_input("City", value="" if edit["City"] == "-" else edit["City"], key="edit_city")

        status_options_edit = ["-- Select --","To Start","Ongoing","Pending for Payment","Paid - To Dispatch","Dispatched"]

        edit_status = st.selectbox(
            "Production Status",
            status_options_edit,
            index=status_options_edit.index(edit["Production Status"]) if edit["Production Status"] in status_options_edit else 0,
            key="edit_status"
        )

        edit_price = st.number_input("Price", value=float(edit["Price"]), key="edit_price")
        edit_received = st.number_input("Received", value=float(edit["Received"]), key="edit_received")
        edit_remarks = st.text_area("Remarks", value="" if edit["Remarks"] == "-" else edit["Remarks"], key="edit_remarks")

        col_upd, col_upd_msg = st.columns([1,2])

        with col_upd:
            if st.button("Update Order"):

                df.loc[st.session_state.edit_index] = {
                    **edit,
                    "Name": edit_name,
                    "Look": edit_look if edit_look != "-- Select --" else "-",
                    "Add-on": edit_addon if edit_addon != "-- Select --" else "-",
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

    # =====================================================
    # DELETE SECTION
    # =====================================================

    st.markdown("### 🗑 Delete Order")

    idx = st.selectbox(
        "Select Order to Delete",
        df_display.index,
        format_func=lambda x: f"{df_display.loc[x,'Name']} - {df_display.loc[x,'Est Delivery']}"
    )

    if st.button("🗑 Delete Selected Order"):
        df2 = df.drop(idx).reset_index(drop=True)
        df2.to_csv(FILE_NAME, index=False)
        st.session_state.delete_success = True
        st.rerun()

    if st.session_state.get("delete_success"):
        st.success("Deleted Successfully")
        st.session_state.delete_success = False

    # =====================================================
    # CSV DOWNLOAD
    # =====================================================

    st.download_button(
        "📥 Download CSV",
        df_display.to_csv(index=False).encode(),
        "dresskraft_orders.csv"
    )

    # =====================================================
    # PDF DOWNLOAD
    # =====================================================

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
