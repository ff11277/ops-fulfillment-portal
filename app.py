import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# ---------------------------------------------------------
# PERSISTENCE FILE PATHS
# ---------------------------------------------------------
DATA_FILE = "saved_export.csv"
ACK_FILE = "saved_acknowledged.json"
ACK_DATES_FILE = "saved_ack_dates.json"
RESTORED_FILE = "saved_restored.json"
NOTES_FILE = "saved_notes.json"
CC_FILE = "saved_cc.json"
VC_FILE = "saved_vc.json"

def load_persisted_state():
    if "acknowledged_pos" not in st.session_state:
        if os.path.exists(ACK_FILE):
            try:
                with open(ACK_FILE, "r") as f:
                    st.session_state["acknowledged_pos"] = set(json.load(f))
            except Exception:
                st.session_state["acknowledged_pos"] = set()
        else:
            st.session_state["acknowledged_pos"] = set()

    if "acknowledged_dates" not in st.session_state:
        if os.path.exists(ACK_DATES_FILE):
            try:
                with open(ACK_DATES_FILE, "r") as f:
                    st.session_state["acknowledged_dates"] = json.load(f)
            except Exception:
                st.session_state["acknowledged_dates"] = {}
        else:
            st.session_state["acknowledged_dates"] = {}

    if "restored_pos" not in st.session_state:
        if os.path.exists(RESTORED_FILE):
            try:
                with open(RESTORED_FILE, "r") as f:
                    st.session_state["restored_pos"] = set(json.load(f))
            except Exception:
                st.session_state["restored_pos"] = set()
        else:
            st.session_state["restored_pos"] = set()

    if "reviewer_notes" not in st.session_state:
        if os.path.exists(NOTES_FILE):
            try:
                with open(NOTES_FILE, "r") as f:
                    st.session_state["reviewer_notes"] = json.load(f)
            except Exception:
                st.session_state["reviewer_notes"] = {}
        else:
            st.session_state["reviewer_notes"] = {}

    if "cc_state" not in st.session_state:
        if os.path.exists(CC_FILE):
            try:
                with open(CC_FILE, "r") as f:
                    st.session_state["cc_state"] = json.load(f)
            except Exception:
                st.session_state["cc_state"] = {}
        else:
            st.session_state["cc_state"] = {}

    if "vc_state" not in st.session_state:
        if os.path.exists(VC_FILE):
            try:
                with open(VC_FILE, "r") as f:
                    st.session_state["vc_state"] = json.load(f)
            except Exception:
                st.session_state["vc_state"] = {}
        else:
            st.session_state["vc_state"] = {}

def save_persisted_state():
    with open(ACK_FILE, "w") as f:
        json.dump(list(st.session_state["acknowledged_pos"]), f)
    with open(ACK_DATES_FILE, "w") as f:
        json.dump(st.session_state["acknowledged_dates"], f)
    with open(RESTORED_FILE, "w") as f:
        json.dump(list(st.session_state["restored_pos"]), f)
    with open(NOTES_FILE, "w") as f:
        json.dump(st.session_state["reviewer_notes"], f)
    with open(CC_FILE, "w") as f:
        json.dump(st.session_state["cc_state"], f)
    with open(VC_FILE, "w") as f:
        json.dump(st.session_state["vc_state"], f)

def clear_all_saved_data():
    for f in [DATA_FILE, ACK_FILE, ACK_DATES_FILE, RESTORED_FILE, NOTES_FILE, CC_FILE, VC_FILE]:
        if os.path.exists(f):
            os.remove(f)
    st.session_state["acknowledged_pos"] = set()
    st.session_state["acknowledged_dates"] = {}
    st.session_state["restored_pos"] = set()
    st.session_state["reviewer_notes"] = {}
    st.session_state["cc_state"] = {}
    st.session_state["vc_state"] = {}

# ---------------------------------------------------------
# CONFIGURATION & SECURITY
# ---------------------------------------------------------
APP_PASSWORD = "11277"

st.set_page_config(page_title="Force Fitters - Vendor Audit Portal", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------
# CUSTOM INJECTED CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    :root {
        --background-color: #FFFFFF !important;
        --secondary-background-color: #F4F5F7 !important;
        --text-color: #111827 !important;
    }

    .stApp {
        background-color: #F4F5F7 !important;
        color: #111827 !important;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }

    p, span, label, h1, h2, h3, h4, h5, h6, div, .stMarkdown, .stCaption, small, button {
        color: #111827 !important;
    }

    /* Tooltip styling fix (white background, dark text) */
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
        padding: 14px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #222222;
        margin: -6rem -5rem 2rem -5rem;
    }
    .ff-navbar *, .ff-brand, .ff-user {
        color: #FFFFFF !important;
    }
    .ff-brand {
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .ff-user {
        font-size: 0.9rem;
        font-weight: 500;
        color: #E5E7EB !important;
    }

    div[data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
        padding: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    section[data-testid="stFileUploaderDropzone"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #9CA3AF !important;
        border-radius: 6px !important;
    }
    section[data-testid="stFileUploaderDropzone"] * {
        background-color: #FFFFFF !important;
        color: #111827 !important;
    }

    div[data-testid="stMetric"], .ff-card {
        background-color: #FFFFFF !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
        padding: 16px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: #4B5563 !important;
        font-weight: 700 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] div {
        color: #111827 !important;
        font-weight: 800 !important;
    }

    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"], div[data-testid="stTable"], .glideDataEditor {
        background-color: #FFFFFF !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
        padding: 4px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stDataFrame"] *, div[data-testid="stDataEditor"] * {
        color: #111827 !important;
    }

    .stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
        background-color: #E5E7EB !important;
        color: #111827 !important;
        border: 1px solid #9CA3AF !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 6px 14px !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #D1D5DB !important;
        border-color: #6B7280 !important;
        color: #000000 !important;
    }

    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
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
    }
    div[data-testid="stAlert"] * {
        color: #78350F !important;
    }
</style>

<div class="ff-navbar">
    <div class="ff-brand">
        ⚡ FORCE FITTERS
    </div>
    <div class="ff-user">
        👤 Vendor Audit Portal
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
st.title("📦 Vendor Audit Portal")

col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    st.markdown("Upload a new system CSV export file, or continue working with saved audit data.")

with col_top2:
    if not st.session_state["confirm_clear"]:
        if st.button("🗑️ Clear Saved Session & Data"):
            st.session_state["confirm_clear"] = True
            st.rerun()
    else:
        st.warning("Are you sure you want to clear all data?")
        col_yes, col_no = st.columns(2)
        if col_yes.button("Yes", key="confirm_clear_yes"):
            clear_all_saved_data()
            st.session_state["confirm_clear"] = False
            st.success("Saved data cleared!")
            st.rerun()
        if col_no.button("No", key="confirm_clear_no"):
            st.session_state["confirm_clear"] = False
            st.rerun()

uploaded_file = st.file_uploader("Only upload On Order export from [here](https://admin.forcefitters.com/orders?statuses[]=9)", type=["csv"])

df = None
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.to_csv(DATA_FILE, index=False)
elif os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)

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
        save_persisted_state()

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

        st.markdown("---")

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

        po_summary = on_order_df.groupby(['Vendor', 'Vendor PO']).agg(
            Min_Vendor_Order_Date=('Effective Date', 'min'),
            Min_Customer_Order_Date=('Date Ordered Clean', 'min'),
            Total_Qty=('Qty', 'sum'),
            Combined_Notes=('Notes', combine_notes)
        ).reset_index()

        po_summary['Days_Open_Vendor'] = (current_date - po_summary['Min_Vendor_Order_Date']).dt.days

        def check_past_due(row):
            if row['Vendor'] == 'Sanmar':
                return row['Days_Open_Vendor'] > 10
            else:
                return row['Days_Open_Vendor'] > 14

        po_summary['Is_Past_Due'] = po_summary.apply(check_past_due, axis=1)
        all_past_due_df = po_summary[po_summary['Is_Past_Due']].sort_values(by='Days_Open_Vendor', ascending=False)

        all_past_due_df['Vendor Order Date'] = all_past_due_df['Min_Vendor_Order_Date'].dt.strftime('%m/%d/%Y')
        all_past_due_df['Customer Order Date'] = all_past_due_df['Min_Customer_Order_Date'].dt.strftime('%m/%d/%Y')

        # Flag column logic: Shows 🚩 if PO was moved back from Reviewed table
        all_past_due_df['Flag'] = all_past_due_df['Vendor PO'].apply(
            lambda po: "🚩" if po in st.session_state["restored_pos"] else ""
        )

        # Map interactive state values
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

        # High-Level Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Units On Order", int(on_order_df['Qty'].sum()))
        col2.metric("Active Vendor POs", po_summary['Vendor PO'].nunique())
        col3.metric("Action Required POs", len(active_past_due))
        col4.metric("Reviewed POs", len(reviewed_past_due))

        rename_dict = {
            'Days_Open_Vendor': 'DSVO',
            'Total_Qty': 'Units',
            'Combined_Notes': 'Item Notes'
        }

        table_column_config = {
            "Flag": st.column_config.TextColumn("Flag", width=50, help="🚩 Flagged: Re-opened from Reviewed table"),
            "Move": st.column_config.CheckboxColumn("Move", width="small", help="Check to move between tables"),
            "Vendor Order Date": st.column_config.TextColumn("Vendor Order Date", width="small"),
            "Vendor PO": st.column_config.TextColumn("Vendor PO", width="small"),
            "Vendor": st.column_config.TextColumn("Vendor", width="small"),
            "DSVO": st.column_config.NumberColumn("DSVO", width="small"),
            "Customer Order Date": st.column_config.TextColumn("Customer Order Date", width="small"),
            "Units": st.column_config.NumberColumn("Units", width="small"),
            "Item Notes": st.column_config.TextColumn("Item Notes", width="medium"),
            "VC": st.column_config.CheckboxColumn("VC", width="small", help="Vendor Contacted"),
            "CC": st.column_config.CheckboxColumn("CC", width="small", help="Customer Contacted"),
            "Review Notes": st.column_config.TextColumn("Review Notes", width="large")
        }

        # --- TABLE 1: ACTION REQUIRED ---
        st.markdown("### 📋 Action Required (Unreviewed Past Due POs)")
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
                column_config=table_column_config,
                key="active_data_editor"
            )

            state_changed = False
            for _, row in edited_active_view.iterrows():
                po = row['Vendor PO']
                if st.session_state["reviewer_notes"].get(po) != row['Review Notes']:
                    st.session_state["reviewer_notes"][po] = row['Review Notes']
                    state_changed = True
                if st.session_state["vc_state"].get(po) != row['VC']:
                    st.session_state["vc_state"][po] = row['VC']
                    state_changed = True
                if st.session_state["cc_state"].get(po) != row['CC']:
                    st.session_state["cc_state"][po] = row['CC']
                    state_changed = True
                if row['Move']:
                    st.session_state["acknowledged_pos"].add(po)
                    st.session_state["acknowledged_dates"][po] = datetime.today().strftime('%Y-%m-%d')
                    if po in st.session_state["restored_pos"]:
                        st.session_state["restored_pos"].remove(po)
                    state_changed = True

            if state_changed:
                save_persisted_state()
                st.rerun()
        else:
            st.success("All past-due POs have been moved to Reviewed or resolved!")

        # --- TABLE 2: REVIEWED ---
        st.markdown("---")
        st.markdown("### 📁 Reviewed")
        st.caption("💡 Items in Reviewed automatically move back to Action Required after 7 days.")

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
                column_config=table_column_config,
                key="reviewed_data_editor"
            )

            state_changed_rev = False
            for _, row in edited_reviewed_view.iterrows():
                po = row['Vendor PO']
                if st.session_state["reviewer_notes"].get(po) != row['Review Notes']:
                    st.session_state["reviewer_notes"][po] = row['Review Notes']
                    state_changed_rev = True
                if st.session_state["vc_state"].get(po) != row['VC']:
                    st.session_state["vc_state"][po] = row['VC']
                    state_changed_rev = True
                if st.session_state["cc_state"].get(po) != row['CC']:
                    st.session_state["cc_state"][po] = row['CC']
                    state_changed_rev = True
                if row['Move']:
                    st.session_state["acknowledged_pos"].remove(po)
                    if po in st.session_state["acknowledged_dates"]:
                        del st.session_state["acknowledged_dates"][po]
                    st.session_state["restored_pos"].add(po)
                    state_changed_rev = True

            if state_changed_rev:
                save_persisted_state()
                st.rerun()
        else:
            st.info("No POs are currently in Reviewed. Check the 'Move' box in Table 1 above to move items here.")
else:
    st.info("Please upload a CSV export file to begin.")