import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------
# CONFIGURATION & SECURITY
# ---------------------------------------------------------
APP_PASSWORD = "11277"

st.set_page_config(page_title="Force Fitters - Vendor Audit Portal", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------
# BACKGROUND GOOGLE SHEETS STORAGE CONNECTION
# ---------------------------------------------------------
@st.cache_resource
def get_gspread_sheet():
    if "gcp_service_account" in st.secrets and "gsheets" in st.secrets:
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=scopes
            )
            client = gspread.authorize(creds)
            sheet = client.open_by_url(st.secrets["gsheets"]["spreadsheet_url"]).sheet1
            return sheet
        except Exception:
            return None
    return None

def load_persisted_state():
    if "acknowledged_pos" not in st.session_state:
        st.session_state["acknowledged_pos"] = set()
    if "acknowledged_dates" not in st.session_state:
        st.session_state["acknowledged_dates"] = {}
    if "restored_pos" not in st.session_state:
        st.session_state["restored_pos"] = set()

    if "cust_acknowledged_orders" not in st.session_state:
        st.session_state["cust_acknowledged_orders"] = set()
    if "cust_acknowledged_dates" not in st.session_state:
        st.session_state["cust_acknowledged_dates"] = {}
    if "cust_restored_orders" not in st.session_state:
        st.session_state["cust_restored_orders"] = set()

    if "reviewer_notes" not in st.session_state:
        st.session_state["reviewer_notes"] = {}
    if "cc_state" not in st.session_state:
        st.session_state["cc_state"] = {}
    if "vc_state" not in st.session_state:
        st.session_state["vc_state"] = {}

    sheet = get_gspread_sheet()
    if sheet and "cloud_loaded" not in st.session_state:
        try:
            records = sheet.get_all_records()
            for row in records:
                key = str(row.get("key_id", "")).strip()
                if not key:
                    continue
                st.session_state["reviewer_notes"][key] = str(row.get("review_notes", ""))
                st.session_state["vc_state"][key] = str(row.get("vc", "")).upper() == "TRUE"
                st.session_state["cc_state"][key] = str(row.get("cc", "")).upper() == "TRUE"

                is_reviewed = str(row.get("is_reviewed", "")).upper() == "TRUE"
                is_cust_order = str(row.get("is_cust_order", "")).upper() == "TRUE"
                rev_date = str(row.get("reviewed_date", "")).strip()

                if is_reviewed:
                    if is_cust_order:
                        st.session_state["cust_acknowledged_orders"].add(key)
                        if rev_date:
                            st.session_state["cust_acknowledged_dates"][key] = rev_date
                    else:
                        st.session_state["acknowledged_pos"].add(key)
                        if rev_date:
                            st.session_state["acknowledged_dates"][key] = rev_date
            st.session_state["cloud_loaded"] = True
        except Exception:
            pass

def save_key_state_to_cloud(key_id, review_notes="", vc=False, cc=False, is_reviewed=False, is_cust_order=False, reviewed_date=""):
    sheet = get_gspread_sheet()
    if not sheet:
        return
    try:
        str_key = str(key_id)
        cell = sheet.find(str_key)
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row_data = [str_key, str(review_notes), bool(vc), bool(cc), bool(is_reviewed), bool(is_cust_order), str(reviewed_date or ""), now_str]
        
        if cell:
            sheet.update(f"A{cell.row}:H{cell.row}", [row_data])
        else:
            sheet.append_row(row_data)
    except Exception:
        pass

def clear_all_saved_data():
    st.session_state["acknowledged_pos"] = set()
    st.session_state["acknowledged_dates"] = {}
    st.session_state["restored_pos"] = set()
    st.session_state["cust_acknowledged_orders"] = set()
    st.session_state["cust_acknowledged_dates"] = {}
    st.session_state["cust_restored_orders"] = set()
    st.session_state["reviewer_notes"] = {}
    st.session_state["cc_state"] = {}
    st.session_state["vc_state"] = {}
    
    sheet = get_gspread_sheet()
    if sheet:
        try:
            sheet.resize(rows=1)
        except Exception:
            pass

# ---------------------------------------------------------
# CUSTOM INJECTED CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    :root {
        --background-color: #F3F4F6 !important;
        --secondary-background-color: #FFFFFF !important;
        --text-color: #111827 !important;
    }

    header[data-testid="stHeader"], [data-testid="stHeader"] {
        display: none !important;
    }

    .block-container {
        padding-top: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }

    .stApp {
        background-color: #F4F5F7 !important;
        color: #111827 !important;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
    }

    p, span, label, h1, h2, h3, h4, h5, h6, div, .stMarkdown, .stCaption, small, button {
        color: #111827 !important;
    }

    div[data-baseweb="tooltip"], div[role="tooltip"], .stTooltipContent {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    div[data-baseweb="tooltip"] *, div[role="tooltip"] * {
        background-color: #FFFFFF !important;
        color: #111827 !important;
    }

    .ff-navbar {
        background-color: #111111 !important;
        padding: 14px 28px !important;
        display: flex !important;
        align-items: center !important;
        border-bottom: 1px solid #222222 !important;
        margin-left: -2rem !important;
        margin-right: -2rem !important;
        margin-top: 0rem !important;
        margin-bottom: 1.2rem !important;
    }
    .ff-brand {
        color: #FFFFFF !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
    }

    div[data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
        padding: 4px 10px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    section[data-testid="stFileUploaderDropzone"] {
        background-color: #FFFFFF !important;
        border: 1px dashed #9CA3AF !important;
        border-radius: 6px !important;
        padding: 4px 8px !important;
        min-height: 48px !important;
    }
    section[data-testid="stFileUploaderDropzone"] > div {
        padding-top: 2px !important;
        padding-bottom: 2px !important;
    }
    section[data-testid="stFileUploaderDropzone"] * {
        background-color: #FFFFFF !important;
        color: #111827 !important;
    }

    div[data-testid="stMetric"], .ff-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 6px !important;
        padding: 10px 14px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: #4B5563 !important;
        font-weight: 700 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] div {
        color: #111827 !important;
        font-weight: 800 !important;
    }

    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"], div[data-testid="stTable"], .glideDataEditor {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 6px !important;
        padding: 2px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }
    
    div[data-testid="stDataFrame"] header, 
    div[data-testid="stDataEditor"] header, 
    .glideDataEditor .gdg-header-cell {
        background-color: #F9FAFB !important;
        color: #111827 !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        border-bottom: 1px solid #E5E7EB !important;
    }

    div[data-testid="stDataFrame"] *, div[data-testid="stDataEditor"] * {
        color: #111827 !important;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
    }

    .stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
        background-color: #E5E7EB !important;
        color: #111827 !important;
        border: 1px solid #9CA3AF !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 4px 12px !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #D1D5DB !important;
        border-color: #6B7280 !important;
        color: #000000 !important;
    }

    div[data-testid="stExpander"], 
    div[data-testid="stExpander"] details, 
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] details[open] summary {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
    }
    div[data-testid="stExpander"] summary:hover, 
    div[data-testid="stExpander"] summary:focus, 
    div[data-testid="stExpander"] summary:active,
    div[data-testid="stExpander"] details[open] summary:hover,
    div[data-testid="stExpander"] details[open] summary:focus {
        background-color: #F3F4F6 !important;
        color: #111827 !important;
    }
    div[data-testid="stExpander"] summary * {
        color: #111827 !important;
        fill: #111827 !important;
    }

    .stTextInput input, .stTextArea textarea {
        background-color: #FFFFFF !important;
        border: 1px solid #9CA3AF !important;
        border-radius: 6px !important;
        color: #111827 !important;
    }

    div[data-testid="stAlert"] {
        background-color: #FEF3C7 !important;
        border: 1px solid #F59E0B !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
    }
    div[data-testid="stAlert"] * {
        color: #78350F !important;
    }
</style>

<div class="ff-navbar">
    <div class="ff-brand">
        FORCE FITTERS <span style="color: #6B7280; margin: 0 8px;">|</span> Vendor Audit Portal
    </div>
</div>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "confirm_clear" not in st.session_state:
    st.session_state["confirm_clear"] = False

load_persisted_state()

if not st.session_state["authenticated"]:
    st.title("🔒 Security Check")
    with st.form("login_form"):
        user_input = st.text_input("Enter Access Key:", type="password")
        login_submitted = st.form_submit_button("Login")
        if login_submitted:
            if user_input == APP_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect access key. Please try again.")
    st.stop()

# ---------------------------------------------------------
# MAIN APPLICATION
# ---------------------------------------------------------
_, col_clear_btn = st.columns([3, 1])

with col_clear_btn:
    if not st.session_state["confirm_clear"]:
        if st.button("🗑️ Clear Saved Session & Data"):
            st.session_state["confirm_clear"] = True
            st.rerun()
    else:
        st.warning("Clear all data?")
        col_yes, col_no = st.columns(2)
        if col_yes.button("Yes", key="confirm_clear_yes"):
            clear_all_saved_data()
            st.session_state["confirm_clear"] = False
            st.success("Cleared!")
            st.rerun()
        if col_no.button("No", key="confirm_clear_no"):
            st.session_state["confirm_clear"] = False
            st.rerun()

uploaded_file = st.file_uploader("Only upload On Order export from [here](https://admin.forcefitters.com/orders?statuses[]=9)", type=["csv"])

df = None
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.session_state["latest_df"] = df
elif "latest_df" in st.session_state:
    df = st.session_state["latest_df"]

if df is not None:
    current_date = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))
    current_today = datetime.today().date()

    # --- 7-DAY EXPIRATION AUTOMATION FOR REVIEWED POS ---
    expired_pos = []
    for po in list(st.session_state["acknowledged_pos"]):
        ack_date_str = st.session_state["acknowledged_dates"].get(po)
        if ack_date_str:
            try:
                ack_date = datetime.strptime(ack_date_str, '%Y-%m-%d').date()
                if (current_today - ack_date).days > 7:
                    expired_pos.append(po)
            except ValueError:
                pass

    if expired_pos:
        for po in expired_pos:
            st.session_state["acknowledged_pos"].remove(po)
            if po in st.session_state["acknowledged_dates"]:
                del st.session_state["acknowledged_dates"][po]
            st.session_state["restored_pos"].add(po)

    # --- 7-DAY EXPIRATION AUTOMATION FOR REVIEWED CUSTOMER ORDERS ---
    expired_cust_orders = []
    for key in list(st.session_state["cust_acknowledged_orders"]):
        ack_date_str = st.session_state["cust_acknowledged_dates"].get(key)
        if ack_date_str:
            try:
                ack_date = datetime.strptime(ack_date_str, '%Y-%m-%d').date()
                if (current_today - ack_date).days > 7:
                    expired_cust_orders.append(key)
            except ValueError:
                pass

    if expired_cust_orders:
        for key in expired_cust_orders:
            st.session_state["cust_acknowledged_orders"].remove(key)
            if key in st.session_state["cust_acknowledged_dates"]:
                del st.session_state["cust_acknowledged_dates"][key]
            st.session_state["cust_restored_orders"].add(key)

    # Filter for 'On Order' status
    on_order_df = df[df['Status'] == 'On Order'].copy()

    if on_order_df.empty:
        st.warning("No records found with status 'On Order'.")
    else:
        wo_col = 'Gorilla Work Order'
        if wo_col in on_order_df.columns:
            on_order_df['Has_WO'] = (
                on_order_df[wo_col].notna() & 
                (on_order_df[wo_col].astype(str).str.strip() != '') & 
                (on_order_df[wo_col].astype(str).str.strip() != '0') & 
                (on_order_df[wo_col].astype(str).str.lower() != 'nan')
            )
        else:
            on_order_df['Has_WO'] = False

        checked_in_mismatch = on_order_df[on_order_df['Has_WO']].copy()
        if not checked_in_mismatch.empty:
            with st.expander("⚠️ Review Item Statuses"):
                clean_cols = ['Magento Order', 'Vendor', 'Vendor PO', wo_col, 'Qty', 'Vendor Order Date', 'Notes']
                existing_clean_cols = [c for c in clean_cols if c in checked_in_mismatch.columns]
                st.dataframe(checked_in_mismatch[existing_clean_cols], use_container_width=True, hide_index=True)

        on_order_df['Vendor PO Clean'] = on_order_df['Vendor PO'].fillna('Unassigned PO')
        on_order_df['Vendor Order Date Clean'] = pd.to_datetime(on_order_df['Vendor Order Date'], errors='coerce')
        on_order_df['Date Ordered Clean'] = pd.to_datetime(on_order_df['Date Ordered'], errors='coerce')
        on_order_df['Effective Date'] = on_order_df['Vendor Order Date Clean'].fillna(on_order_df['Date Ordered Clean'])

        def combine_notes(series):
            unique_notes = []
            for item in series.dropna().unique():
                clean_item = str(item).strip()
                if clean_item and clean_item.lower() != 'nan' and clean_item not in unique_notes:
                    unique_notes.append(clean_item)
            return " | ".join(unique_notes) if unique_notes else "-"

        # ---------------------------------------------------------
        # SECTION 1: VENDOR PO CALCULATIONS
        # ---------------------------------------------------------
        po_summary = on_order_df.groupby(['Vendor', 'Vendor PO Clean'], dropna=False).agg(
            Min_Vendor_Order_Date=('Effective Date', 'min'),
            Min_Customer_Order_Date=('Date Ordered Clean', 'min'),
            Total_Qty=('Qty', 'sum'),
            Combined_Notes=('Notes', combine_notes)
        ).reset_index().rename(columns={'Vendor PO Clean': 'Vendor PO'})

        po_summary['Days_Open_Vendor'] = (current_date - po_summary['Min_Vendor_Order_Date']).dt.days

        def check_past_due(row):
            if row['Vendor'] == 'Sanmar':
                return row['Days_Open_Vendor'] > 10
            else:
                return row['Days_Open_Vendor'] > 14

        po_summary['Is_Past_Due'] = po_summary.apply(check_past_due, axis=1)
        all_past_due_df = po_summary[po_summary['Is_Past_Due']].sort_values(by='Days_Open_Vendor', ascending=False)
        all_past_due_po_set = set(all_past_due_df['Vendor PO'])

        all_past_due_df['Vendor Order Date'] = all_past_due_df['Min_Vendor_Order_Date'].dt.strftime('%m/%d/%Y')
        all_past_due_df['Customer Order Date'] = all_past_due_df['Min_Customer_Order_Date'].dt.strftime('%m/%d/%Y')

        all_past_due_df['Flag'] = all_past_due_df['Vendor PO'].apply(
            lambda po: "🚩" if po in st.session_state["restored_pos"] else ""
        )
        all_past_due_df['VC'] = all_past_due_df['Vendor PO'].apply(
            lambda po: st.session_state["vc_state"].get(po, False)
        )
        all_past_due_df['CC'] = all_past_due_df['Vendor PO'].apply(
            lambda po: st.session_state["cc_state"].get(po, False)
        )
        all_past_due_df['Review Notes'] = all_past_due_df['Vendor PO'].apply(
            lambda po: st.session_state["reviewer_notes"].get(po, "")
        )

        active_past_due = all_past_due_df[~all_past_due_df['Vendor PO'].isin(st.session_state["acknowledged_pos"])].copy()
        reviewed_past_due = all_past_due_df[all_past_due_df['Vendor PO'].isin(st.session_state["acknowledged_pos"])].copy()

        # ---------------------------------------------------------
        # SECTION 2: AGED CUSTOMER ORDERS (>21 DAYS)
        # ---------------------------------------------------------
        on_order_df['DSVO'] = (current_date - on_order_df['Vendor Order Date Clean']).dt.days
        on_order_df['DSCO'] = (current_date - on_order_df['Date Ordered Clean']).dt.days

        aged_cust_df = on_order_df[(on_order_df['DSCO'] > 21) & (~on_order_df['Vendor PO Clean'].isin(all_past_due_po_set))].copy()

        cust_orders_summary = aged_cust_df.groupby(['Magento Order', 'Vendor', 'Vendor PO Clean'], dropna=False).agg(
            Min_Customer_Order_Date=('Date Ordered Clean', 'min'),
            Min_Vendor_Order_Date=('Effective Date', 'min'),
            DSCO=('DSCO', 'max'),
            DSVO=('DSVO', 'min'),
            Total_Qty=('Qty', 'sum'),
            Combined_Notes=('Notes', combine_notes)
        ).reset_index().rename(columns={'Vendor PO Clean': 'Vendor PO'})

        cust_orders_summary = cust_orders_summary.sort_values(by='DSCO', ascending=False)
        cust_orders_summary['Customer Order Date'] = cust_orders_summary['Min_Customer_Order_Date'].dt.strftime('%m/%d/%Y')
        cust_orders_summary['Vendor Order Date'] = cust_orders_summary['Min_Vendor_Order_Date'].dt.strftime('%m/%d/%Y')

        cust_orders_summary['Order_Key'] = cust_orders_summary['Magento Order'].astype(str) + "_" + cust_orders_summary['Vendor PO'].astype(str)

        cust_orders_summary['Flag'] = cust_orders_summary['Order_Key'].apply(
            lambda key: "🚩" if key in st.session_state["cust_restored_orders"] else ""
        )
        cust_orders_summary['VC'] = cust_orders_summary['Order_Key'].apply(
            lambda key: st.session_state["vc_state"].get(key, False)
        )
        cust_orders_summary['CC'] = cust_orders_summary['Order_Key'].apply(
            lambda key: st.session_state["cc_state"].get(key, False)
        )
        cust_orders_summary['Review Notes'] = cust_orders_summary['Order_Key'].apply(
            lambda key: st.session_state["reviewer_notes"].get(key, "")
        )

        active_aged_cust = cust_orders_summary[~cust_orders_summary['Order_Key'].isin(st.session_state["cust_acknowledged_orders"])].copy()
        reviewed_aged_cust = cust_orders_summary[cust_orders_summary['Order_Key'].isin(st.session_state["cust_acknowledged_orders"])].copy()

        # ---------------------------------------------------------
        # HIGH-LEVEL METRICS
        # ---------------------------------------------------------
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Units On Order", int(on_order_df['Qty'].sum()))
        col2.metric("Active Vendor POs", po_summary['Vendor PO'].nunique())
        col3.metric("Action Required POs", len(active_past_due))
        col4.metric("Aged Customer Orders", len(active_aged_cust))

        rename_dict = {
            'Days_Open_Vendor': 'DSVO',
            'Total_Qty': 'Units',
            'Combined_Notes': 'Item Notes'
        }

        # Shared Column Configurations
        po_table_column_config = {
            "Flag": st.column_config.TextColumn("Flag", width=50, help="🚩 Flagged: Re-opened from Reviewed table"),
            "Move": st.column_config.CheckboxColumn("Move", width="small", help="Check to move between tables"),
            "Vendor Order Date": st.column_config.TextColumn("Vendor Order Date", width="small"),
            "Vendor PO": st.column_config.TextColumn("Vendor PO", width="small"),
            "Vendor": st.column_config.TextColumn("Vendor", width="small"),
            "DSVO": st.column_config.NumberColumn("DSVO", width="small", help="Days Since Vendor Order"),
            "Customer Order Date": st.column_config.TextColumn("Customer Order Date", width="small"),
            "Units": st.column_config.NumberColumn("Units", width="small"),
            "Item Notes": st.column_config.TextColumn("Item Notes", width="medium"),
            "VC": st.column_config.CheckboxColumn("VC", width="small", help="Vendor Contacted"),
            "CC": st.column_config.CheckboxColumn("CC", width="small", help="Customer Contacted"),
            "Review Notes": st.column_config.TextColumn("Review Notes", width="large")
        }

        cust_table_column_config = {
            "Flag": st.column_config.TextColumn("Flag", width=50, help="🚩 Flagged: Re-opened from Reviewed table"),
            "Move": st.column_config.CheckboxColumn("Move", width="small", help="Check to move between tables"),
            "Magento Order": st.column_config.TextColumn("Order #", width="small"),
            "Customer Order Date": st.column_config.TextColumn("Customer Order Date", width="small"),
            "DSCO": st.column_config.NumberColumn("DSCO", width="small", help="Days Since Customer Order"),
            "Vendor": st.column_config.TextColumn("Vendor", width="small"),
            "Vendor PO": st.column_config.TextColumn("Vendor PO", width="small"),
            "Vendor Order Date": st.column_config.TextColumn("Vendor Order Date", width="small"),
            "DSVO": st.column_config.NumberColumn("DSVO", width="small", help="Days Since Vendor Order"),
            "Units": st.column_config.NumberColumn("Units", width="small"),
            "Item Notes": st.column_config.TextColumn("Item Notes", width="medium"),
            "VC": st.column_config.CheckboxColumn("VC", width="small", help="Vendor Contacted"),
            "CC": st.column_config.CheckboxColumn("CC", width="small", help="Customer Contacted"),
            "Review Notes": st.column_config.TextColumn("Review Notes", width="large")
        }

        # ---------------------------------------------------------
        # DISPLAY SECTION 1: PAST DUE VENDOR ORDERS
        # ---------------------------------------------------------
        st.markdown("---")
        st.markdown("### 🚨 Past Due Vendor Orders")
        st.caption("💡 Click the **Move** box to shift a PO to the Reviewed table. 🚩 indicates PO to review again.")

        if not active_past_due.empty:
            active_past_due.insert(1, 'Move', False)

            output_cols_active = [
                'Flag', 'Move', 'Vendor Order Date', 'Vendor PO', 'Vendor', 'Days_Open_Vendor',
                'Customer Order Date', 'Total_Qty', 'Combined_Notes', 'VC', 'CC', 'Review Notes'
            ]

            final_active_view = active_past_due[output_cols_active].rename(columns=rename_dict)

            edited_active_view = st.data_editor(
                final_active_view,
                use_container_width=True,
                hide_index=True,
                disabled=[col for col in final_active_view.columns if col not in ['Move', 'VC', 'CC', 'Review Notes']],
                column_config=po_table_column_config,
                key="active_data_editor"
            )

            state_changed = False
            for _, row in edited_active_view.iterrows():
                po = row['Vendor PO']
                note = row['Review Notes']
                vc = row['VC']
                cc = row['CC']
                
                if (st.session_state["reviewer_notes"].get(po) != note or 
                    st.session_state["vc_state"].get(po) != vc or 
                    st.session_state["cc_state"].get(po) != cc or 
                    row['Move']):
                    
                    st.session_state["reviewer_notes"][po] = note
                    st.session_state["vc_state"][po] = vc
                    st.session_state["cc_state"][po] = cc
                    
                    is_reviewed = row['Move']
                    if row['Move']:
                        st.session_state["acknowledged_pos"].add(po)
                        rev_date = datetime.today().strftime('%Y-%m-%d')
                        st.session_state["acknowledged_dates"][po] = rev_date
                    else:
                        rev_date = st.session_state["acknowledged_dates"].get(po)
                        
                    save_key_state_to_cloud(po, review_notes=note, vc=vc, cc=cc, is_reviewed=is_reviewed, is_cust_order=False, reviewed_date=rev_date)
                    state_changed = True

            if state_changed:
                st.rerun()
        else:
            st.success("All past-due POs have been moved to Reviewed or resolved!")

        # --- REVIEWED VENDOR POS TABLE ---
        st.markdown("#### 📁 Reviewed Vendor POs")
        if not reviewed_past_due.empty:
            reviewed_past_due.insert(1, 'Move', False)

            output_cols_reviewed = [
                'Flag', 'Move', 'Vendor Order Date', 'Vendor PO', 'Vendor', 'Days_Open_Vendor',
                'Customer Order Date', 'Total_Qty', 'Combined_Notes', 'VC', 'CC', 'Review Notes'
            ]

            final_reviewed_view = reviewed_past_due[output_cols_reviewed].rename(columns=rename_dict)

            edited_reviewed_view = st.data_editor(
                final_reviewed_view,
                use_container_width=True,
                hide_index=True,
                disabled=[col for col in final_reviewed_view.columns if col not in ['Move', 'VC', 'CC', 'Review Notes']],
                column_config=po_table_column_config,
                key="reviewed_data_editor"
            )

            state_changed_rev = False
            for _, row in edited_reviewed_view.iterrows():
                po = row['Vendor PO']
                note = row['Review Notes']
                vc = row['VC']
                cc = row['CC']
                
                if (st.session_state["reviewer_notes"].get(po) != note or 
                    st.session_state["vc_state"].get(po) != vc or 
                    st.session_state["cc_state"].get(po) != cc or 
                    row['Move']):
                    
                    st.session_state["reviewer_notes"][po] = note
                    st.session_state["vc_state"][po] = vc
                    st.session_state["cc_state"][po] = cc
                    
                    is_reviewed = not row['Move']
                    if row['Move']:
                        st.session_state["acknowledged_pos"].remove(po)
                        st.session_state["restored_pos"].add(po)
                        
                    save_key_state_to_cloud(po, review_notes=note, vc=vc, cc=cc, is_reviewed=is_reviewed, is_cust_order=False)
                    state_changed_rev = True

            if state_changed_rev:
                st.rerun()
        else:
            st.info("No Vendor POs are currently in Reviewed.")

        # ---------------------------------------------------------
        # DISPLAY SECTION 2: AGED CUSTOMER ORDERS (>21 DAYS)
        # ---------------------------------------------------------
        st.markdown("---")
        st.markdown("### ⏳ Aged Customer Orders (Customer Wait > 21 Days)")
        st.caption("💡 Line items with customer order age > 21 days that are **not** already monitored in Past Due Vendor POs above.")

        if not active_aged_cust.empty:
            active_aged_cust.insert(1, 'Move', False)

            output_cols_cust = [
                'Flag', 'Move', 'Magento Order', 'Customer Order Date', 'DSCO', 
                'Vendor', 'Vendor PO', 'Vendor Order Date', 'DSVO', 'Total_Qty', 'Combined_Notes', 
                'VC', 'CC', 'Review Notes'
            ]

            final_cust_view = active_aged_cust[output_cols_cust].rename(columns={'Total_Qty': 'Units', 'Combined_Notes': 'Item Notes'})

            edited_cust_view = st.data_editor(
                final_cust_view,
                use_container_width=True,
                hide_index=True,
                disabled=[col for col in final_cust_view.columns if col not in ['Move', 'VC', 'CC', 'Review Notes']],
                column_config=cust_table_column_config,
                key="active_cust_data_editor"
            )

            state_changed_cust = False
            for idx, row in edited_cust_view.iterrows():
                key = str(row['Magento Order']) + "_" + str(row['Vendor PO'])
                note = row['Review Notes']
                vc = row['VC']
                cc = row['CC']
                
                if (st.session_state["reviewer_notes"].get(key) != note or 
                    st.session_state["vc_state"].get(key) != vc or 
                    st.session_state["cc_state"].get(key) != cc or 
                    row['Move']):
                    
                    st.session_state["reviewer_notes"][key] = note
                    st.session_state["vc_state"][key] = vc
                    st.session_state["cc_state"][key] = cc
                    
                    is_reviewed = row['Move']
                    if row['Move']:
                        st.session_state["cust_acknowledged_orders"].add(key)
                        rev_date = datetime.today().strftime('%Y-%m-%d')
                        st.session_state["cust_acknowledged_dates"][key] = rev_date
                    else:
                        rev_date = st.session_state["cust_acknowledged_dates"].get(key)
                        
                    save_key_state_to_cloud(key, review_notes=note, vc=vc, cc=cc, is_reviewed=is_reviewed, is_cust_order=True, reviewed_date=rev_date)
                    state_changed_cust = True

            if state_changed_cust:
                st.rerun()
        else:
            st.success("All aged customer orders are covered by Past Due Vendor POs or moved to Reviewed!")

        # --- REVIEWED AGED CUSTOMER ORDERS TABLE ---
        st.markdown("#### 📁 Reviewed Aged Customer Orders")
        if not reviewed_aged_cust.empty:
            reviewed_aged_cust.insert(1, 'Move', False)

            output_cols_cust_rev = [
                'Flag', 'Move', 'Magento Order', 'Customer Order Date', 'DSCO', 
                'Vendor', 'Vendor PO', 'Vendor Order Date', 'DSVO', 'Total_Qty', 'Combined_Notes', 
                'VC', 'CC', 'Review Notes'
            ]

            final_cust_rev_view = reviewed_aged_cust[output_cols_cust_rev].rename(columns={'Total_Qty': 'Units', 'Combined_Notes': 'Item Notes'})

            edited_cust_rev_view = st.data_editor(
                final_cust_rev_view,
                use_container_width=True,
                hide_index=True,
                disabled=[col for col in final_cust_rev_view.columns if col not in ['Move', 'VC', 'CC', 'Review Notes']],
                column_config=cust_table_column_config,
                key="reviewed_cust_data_editor"
            )

            state_changed_cust_rev = False
            for idx, row in edited_cust_rev_view.iterrows():
                key = str(row['Magento Order']) + "_" + str(row['Vendor PO'])
                note = row['Review Notes']
                vc = row['VC']
                cc = row['CC']
                
                if (st.session_state["reviewer_notes"].get(key) != note or 
                    st.session_state["vc_state"].get(key) != vc or 
                    st.session_state["cc_state"].get(key) != cc or 
                    row['Move']):
                    
                    st.session_state["reviewer_notes"][key] = note
                    st.session_state["vc_state"][key] = vc
                    st.session_state["cc_state"][key] = cc
                    
                    is_reviewed = not row['Move']
                    if row['Move']:
                        st.session_state["cust_acknowledged_orders"].remove(key)
                        st.session_state["cust_restored_orders"].add(key)
                        
                    save_key_state_to_cloud(key, review_notes=note, vc=vc, cc=cc, is_reviewed=is_reviewed, is_cust_order=True)
                    state_changed_cust_rev = True

            if state_changed_cust_rev:
                st.rerun()
        else:
            st.info("No Customer Orders are currently in Reviewed.")
else:
    st.info("Please upload a CSV export file to begin.")