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
NOTES_FILE = "saved_notes.json"

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

    if "reviewer_notes" not in st.session_state:
        if os.path.exists(NOTES_FILE):
            try:
                with open(NOTES_FILE, "r") as f:
                    st.session_state["reviewer_notes"] = json.load(f)
            except Exception:
                st.session_state["reviewer_notes"] = {}
        else:
            st.session_state["reviewer_notes"] = {}

def save_persisted_state():
    with open(ACK_FILE, "w") as f:
        json.dump(list(st.session_state["acknowledged_pos"]), f)
    with open(NOTES_FILE, "w") as f:
        json.dump(st.session_state["reviewer_notes"], f)

def clear_all_saved_data():
    for f in [DATA_FILE, ACK_FILE, NOTES_FILE]:
        if os.path.exists(f):
            os.remove(f)
    st.session_state["acknowledged_pos"] = set()
    st.session_state["reviewer_notes"] = {}

# ---------------------------------------------------------
# CONFIGURATION & SECURITY
# ---------------------------------------------------------
APP_PASSWORD = "11277"

st.set_page_config(page_title="Force Fitters - Fulfillment Portal", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------
# CUSTOM INJECTED CSS (FORCE FITTERS BRANDING)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* App background */
    .stApp {
        background-color: #F4F5F7;
        color: #111827;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }

    /* Top Nav Bar Styling */
    .ff-navbar {
        background-color: #111111;
        color: #FFFFFF;
        padding: 12px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #222222;
        margin: -6rem -5rem 2rem -5rem;
    }
    .ff-brand {
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .ff-user {
        font-size: 0.9rem;
        font-weight: 500;
        color: #D1D5DB;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Card Containers */
    div[data-testid="stMetric"], .ff-card {
        background-color: #EBECEF;
        border: 1px solid #D5D8DC;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Buttons styling */
    .stButton > button, .stDownloadButton > button {
        background-color: #E2E5EA !important;
        color: #1F2937 !important;
        border: 1px solid #C4C8D0 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 6px 14px !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background-color: #D1D5DB !important;
        border-color: #9CA3AF !important;
        color: #000000 !important;
    }

    /* Metric Header Fixes */
    div[data-testid="stMetricLabel"] {
        color: #4B5563 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        color: #111827 !important;
        font-weight: 700 !important;
    }

    /* Expander styling */
    div[data-testid="stExpander"] {
        background-color: #EBECEF;
        border: 1px solid #D5D8DC;
        border-radius: 8px;
    }

    /* Input text boxes */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #FFFFFF !important;
        border: 1px solid #C4C8D0 !important;
        border-radius: 6px !important;
        color: #111827 !important;
    }
</style>

<!-- Custom Header Bar -->
<div class="ff-navbar">
    <div class="ff-brand">
        ⚡ FORCE FITTERS
    </div>
    <div class="ff-user">
        👤 Internal Operations Portal
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
    user_input = st.text_input("Enter Access Key:", type="password")
    if st.button("Login"):
        if user_input == APP_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect access key. Please try again.")
    st.stop()

# ---------------------------------------------------------
# MAIN APPLICATION
# ---------------------------------------------------------
st.title("📦 Fulfillment & Inventory Audit Portal")

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

uploaded_file = st.file_uploader("Upload CSV Export File", type=["csv"])

# Handle Data Loading (Uploaded File vs Saved File)
df = None
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.to_csv(DATA_FILE, index=False)
elif os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    st.info("ℹ️ Showing previously saved audit data. Upload a new CSV above at any time to overwrite.")

if df is not None:
    current_date = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))

    # Filter for 'On Order' status
    on_order_df = df[df['Status'] == 'On Order'].copy()

    if on_order_df.empty:
        st.warning("No records found with status 'On Order'.")
    else:
        # Detect items with Work Order numbers assigned
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

        # --- DATA CLEAN-UP ALERT BANNER ---
        checked_in_mismatch = on_order_df[on_order_df['Has_WO']].copy()
        if not checked_in_mismatch.empty:
            st.warning(
                f"⚠️ **Data Clean-Up Alert:** Found **{len(checked_in_mismatch)} line item(s)** marked 'On Order' "
                f"that already have a Work Order number assigned. These items were likely checked in and need their status updated to 'Decorating'."
            )
            with st.expander("Review Item Statuses"):
                clean_cols = ['Magento Order', 'Vendor', 'Vendor PO', wo_col, 'Qty', 'Vendor Order Date', 'Notes']
                existing_clean_cols = [c for c in clean_cols if c in checked_in_mismatch.columns]
                st.dataframe(checked_in_mismatch[existing_clean_cols], use_container_width=True)

        st.markdown("---")

        # Parse Dates
        on_order_df['Vendor Order Date Clean'] = pd.to_datetime(on_order_df['Vendor Order Date'], errors='coerce')
        on_order_df['Date Ordered Clean'] = pd.to_datetime(on_order_df['Date Ordered'], errors='coerce')
        on_order_df['Effective Date'] = on_order_df['Vendor Order Date Clean'].fillna(on_order_df['Date Ordered Clean'])

        # Collect and combine all unique, non-empty CSV item notes per PO
        def combine_notes(series):
            unique_notes = []
            for item in series.dropna().unique():
                clean_item = str(item).strip()
                if clean_item and clean_item.lower() != 'nan' and clean_item not in unique_notes:
                    unique_notes.append(clean_item)
            return " | ".join(unique_notes) if unique_notes else "-"

        # Aggregate by Vendor & Vendor PO
        po_summary = on_order_df.groupby(['Vendor', 'Vendor PO']).agg(
            Min_Vendor_Order_Date=('Effective Date', 'min'),
            Min_Customer_Order_Date=('Date Ordered Clean', 'min'),
            Total_Qty=('Qty', 'sum'),
            Combined_Notes=('Notes', combine_notes)
        ).reset_index()

        po_summary['Days_Open_Vendor'] = (current_date - po_summary['Min_Vendor_Order_Date']).dt.days

        # Lead Time Rules: Sanmar > 10 days, All other vendors > 14 days
        def check_past_due(row):
            if row['Vendor'] == 'Sanmar':
                return row['Days_Open_Vendor'] > 10
            else:
                return row['Days_Open_Vendor'] > 14

        po_summary['Is_Past_Due'] = po_summary.apply(check_past_due, axis=1)
        all_past_due_df = po_summary[po_summary['Is_Past_Due']].sort_values(by='Days_Open_Vendor', ascending=False)

        # Format display dates
        all_past_due_df['Vendor Order Date'] = all_past_due_df['Min_Vendor_Order_Date'].dt.strftime('%m/%d/%Y')
        all_past_due_df['Customer Order Date'] = all_past_due_df['Min_Customer_Order_Date'].dt.strftime('%m/%d/%Y')

        # Map interactive reviewer notes from session state
        all_past_due_df['Review Notes'] = all_past_due_df['Vendor PO'].apply(
            lambda po: st.session_state["reviewer_notes"].get(po, "")
        )

        # Split Dataframes based on acknowledged session state
        active_past_due = all_past_due_df[~all_past_due_df['Vendor PO'].isin(st.session_state["acknowledged_pos"])].copy()
        reviewed_past_due = all_past_due_df[all_past_due_df['Vendor PO'].isin(st.session_state["acknowledged_pos"])].copy()

        # High-Level Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Units On Order", int(on_order_df['Qty'].sum()))
        col2.metric("Active Vendor POs", po_summary['Vendor PO'].nunique())
        col3.metric("Action Required POs", len(active_past_due))
        col4.metric("Reviewed / Secondary POs", len(reviewed_past_due))

        st.subheader("🚨 Past Due Vendor Orders")

        rename_dict = {
            'Days_Open_Vendor': 'DOV',
            'Total_Qty': 'Units',
            'Combined_Notes': 'Item Notes'
        }

        # Shared Column Configurations for compact width & expanded Review Notes
        table_column_config = {
            "Move": st.column_config.CheckboxColumn("Move", width="small", help="Check to move between tables"),
            "Vendor Order Date": st.column_config.TextColumn("Vendor Order Date", width="small"),
            "Vendor PO": st.column_config.TextColumn("Vendor PO", width="small"),
            "Vendor": st.column_config.TextColumn("Vendor", width="small"),
            "DOV": st.column_config.NumberColumn("DOV", width="small"),
            "Customer Order Date": st.column_config.TextColumn("Customer Order Date", width="small"),
            "Units": st.column_config.NumberColumn("Units", width="small"),
            "Item Notes": st.column_config.TextColumn("Item Notes", width="medium"),
            "Review Notes": st.column_config.TextColumn("Review Notes", width="large")
        }

        # --- TABLE 1: ACTION REQUIRED ---
        st.markdown("### 📋 Action Required (Unreviewed Past Due POs)")
        st.caption("💡 Click the **Move** box in Column 1 to shift a PO to the secondary table.")

        if not active_past_due.empty:
            active_past_due.insert(0, 'Move', False)

            output_cols_active = [
                'Move', 'Vendor Order Date', 'Vendor PO', 'Vendor', 'Days_Open_Vendor',
                'Customer Order Date', 'Total_Qty', 'Combined_Notes', 'Review Notes'
            ]

            final_active_view = active_past_due[output_cols_active].rename(columns=rename_dict)

            edited_active_view = st.data_editor(
                final_active_view,
                use_container_width=True,
                disabled=[col for col in final_active_view.columns if col not in ['Move', 'Review Notes']],
                column_config=table_column_config,
                key="active_data_editor"
            )

            # Process state updates for active table
            state_changed = False
            for _, row in edited_active_view.iterrows():
                po = row['Vendor PO']
                if st.session_state["reviewer_notes"].get(po) != row['Review Notes']:
                    st.session_state["reviewer_notes"][po] = row['Review Notes']
                    state_changed = True
                if row['Move']:
                    st.session_state["acknowledged_pos"].add(po)
                    state_changed = True

            if state_changed:
                save_persisted_state()
                st.rerun()

            # Copy/Paste PO List String (Active only)
            po_list_str = ", ".join(active_past_due['Vendor PO'].dropna().unique().tolist())
            st.text_area("Past Due Vendor POs String for Outreach (Excludes Secondary):", value=po_list_str, height=70)

            # Download CSV Button (Active only)
            csv_data = edited_active_view.drop(columns=['Move']).to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Action Required Report (CSV)",
                data=csv_data,
                file_name=f"Action_Required_Vendor_POs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.success("All past-due POs have been moved to Secondary or resolved!")

        # --- TABLE 2: SECONDARY TABLE ---
        st.markdown("---")
        with st.expander(f"📁 Secondary Table: Acknowledged / Reviewed Past Due POs ({len(reviewed_past_due)})", expanded=True if not reviewed_past_due.empty else False):
            if not reviewed_past_due.empty:
                reviewed_past_due.insert(0, 'Move', False)

                output_cols_reviewed = [
                    'Move', 'Vendor Order Date', 'Vendor PO', 'Vendor', 'Days_Open_Vendor',
                    'Customer Order Date', 'Total_Qty', 'Combined_Notes', 'Review Notes'
                ]

                final_reviewed_view = reviewed_past_due[output_cols_reviewed].rename(columns=rename_dict)

                edited_reviewed_view = st.data_editor(
                    final_reviewed_view,
                    use_container_width=True,
                    disabled=[col for col in final_reviewed_view.columns if col not in ['Move', 'Review Notes']],
                    column_config=table_column_config,
                    key="reviewed_data_editor"
                )

                # Process state updates for secondary table
                state_changed_rev = False
                for _, row in edited_reviewed_view.iterrows():
                    po = row['Vendor PO']
                    if st.session_state["reviewer_notes"].get(po) != row['Review Notes']:
                        st.session_state["reviewer_notes"][po] = row['Review Notes']
                        state_changed_rev = True
                    if row['Move']:
                        st.session_state["acknowledged_pos"].remove(po)
                        state_changed_rev = True

                if state_changed_rev:
                    save_persisted_state()
                    st.rerun()
            else:
                st.info("No POs have been moved to the secondary table yet. Check the 'Move' box in Table 1 above to move items here.")
else:
    st.info("Please upload a CSV export file to begin.")