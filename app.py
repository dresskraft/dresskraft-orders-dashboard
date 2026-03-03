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
        "Est Delivery","Name","Look","Add-on","Jacket Type","Sizes","Count","City",
        "Production Status","Price","Received","Balance",
        "Remarks","Order Entry Date"
    ])
    # =====================================================
# ADD ORDER SECTION
# =====================================================

st.subheader("➕ Add Order")

est_delivery = st.date_input("Est Delivery", key="add_est")
name_customer = st.text_input("Customer Name", key="add_name")

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

if jacket_type == "Couple (M + F)":
    col1, col2 = st.columns(2)
    male = col1.number_input("Male Size", 30, 60, step=1, key="add_male")
    female = col2.number_input("Female Size", 30, 60, step=1, key="add_female")
    sizes_value = f"{male}M | {female}F"

elif jacket_type == "Single":
    single = st.number_input("Size", 30, 60, step=1, key="add_single")
    sizes_value = str(single)

elif jacket_type == "Custom / More than 2":
    st.info("Size will be marked as 'Read Chat'")
    sizes_value = "Read Chat"

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

    balance = price - received if price else 0

    new_row = {
        "Est Delivery": est_delivery,
        "Name": name_customer,
        "Look": look if look != "-- Select --" else "-",
        "Add-on": addon if addon != "-- Select --" else "-",
        "Jacket Type": jacket_type if jacket_type != "-- Select --" else "-",
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
    st.rerun()
    # =====================================================
# ALL ORDERS SECTION
# =====================================================

st.subheader("📋 All Orders")

if not df.empty:

    df_display = df.copy()

    df_display["__sort"] = pd.to_datetime(df_display["Est Delivery"], errors="coerce")
    df_display = df_display.sort_values("__sort", ascending=True)
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

    df_display["Price"] = df_display["Price"].apply(format_indian)
    df_display["Received"] = df_display["Received"].apply(format_indian)
    df_display["Balance"] = df_display["Balance"].apply(format_indian)

    st.dataframe(df_display, use_container_width=True)

    # ================= EDIT =================

    st.markdown("### ✏️ Edit Order")

    edit_idx = st.selectbox(
        "Select Order to Edit",
        df.index,
        format_func=lambda x: f"{df.loc[x,'Name']}"
    )

    if st.button("Load for Edit"):
        st.session_state.edit_row = df.loc[edit_idx].to_dict()
        st.session_state.edit_index = edit_idx

    if "edit_row" in st.session_state:

        edit = st.session_state.edit_row

        edit_name = st.text_input("Customer Name", value=edit["Name"])
        edit_look = st.selectbox("Look", ["LED","Non-LED","Patch","Multiple"],
                                 index=["LED","Non-LED","Patch","Multiple"].index(edit["Look"])
                                 if edit["Look"] in ["LED","Non-LED","Patch","Multiple"] else 0)

        edit_addon = st.selectbox("Add-on",
                                  ["Pearls","Studs","Both Mix","No Add On","Read Chat"],
                                  index=["Pearls","Studs","Both Mix","No Add On","Read Chat"].index(edit["Add-on"])
                                  if edit["Add-on"] in ["Pearls","Studs","Both Mix","No Add On","Read Chat"] else 0)

        # ===== DYNAMIC JACKET EDIT =====

        jacket_options = ["Couple (M + F)","Single","Custom / More than 2"]
        detected_type = edit["Jacket Type"] if edit["Jacket Type"] in jacket_options else jacket_options[0]

        edit_jacket = st.selectbox("Jacket Type", jacket_options,
                                   index=jacket_options.index(detected_type))

        size_val = str(edit["Sizes"])
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

        else:
            edit_sizes_value = "Read Chat"

        if st.button("Update Order"):
            df.loc[st.session_state.edit_index] = {
                **edit,
                "Name": edit_name,
                "Look": edit_look,
                "Add-on": edit_addon,
                "Jacket Type": edit_jacket,
                "Sizes": edit_sizes_value
            }
            df.to_csv(FILE_NAME, index=False)
            st.success("Updated Successfully")
            del st.session_state.edit_row
            st.rerun()

    # ================= DELETE =================

    st.markdown("### 🗑 Delete Order")

    delete_idx = st.selectbox("Select Order to Delete", df.index)

    if st.button("🗑 Delete Selected Order"):
        df = df.drop(delete_idx).reset_index(drop=True)
        df.to_csv(FILE_NAME, index=False)
        st.success("Deleted Successfully")
        st.rerun()

    # ================= DOWNLOADS =================

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

else:
    st.info("No orders yet.")
