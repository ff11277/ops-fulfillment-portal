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
APP_PASSWORD = "Operations2026!"

st.set_page_config(page_title="Operations Fulfillment Portal", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

load_persisted_state()

if not st.session_state["authenticated"]:
    st.title("🔒 Internal Operations Portal")
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
    st.markdown("Upload a new system CSV export file, or continue working with saved data.")
with col_top2:
    if st.button("🗑️ Clear Saved Session & Data"):
        clear_all_saved_data()
        st.success("Saved data cleared!")
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
            'Days_Open_Vendor': 'Days Open (Vendor)',
            'Total_Qty': 'Total Units',
            'Combined_Notes': 'Item Notes'
        }

        # --- TABLE 1: ACTION REQUIRED ---
        st.markdown("### 📋 Action Required (Unreviewed Past Due POs)")
        st.caption("💡 Click the **Move to Secondary** box in Column 1 to move a PO to the secondary table.")

        if not active_past_due.empty:
            active_past_due.insert(0, 'Move to Secondary', False)

            output_cols_active = [
                'Move to Secondary', 'Vendor Order Date', 'Vendor PO', 'Vendor', 'Days_Open_Vendor',
                'Customer Order Date', 'Total_Qty', 'Combined_Notes', 'Review Notes'
            ]

            final_active_view = active_past_due[output_cols_active].rename(columns=rename_dict)

            edited_active_view = st.data_editor(
                final_active_view,
                use_container_width=True,
                disabled=[col for col in final_active_view.columns if col not in ['Move to Secondary', 'Review Notes']],
                column_config={
                    "Move to Secondary": st.column_config.CheckboxColumn("Move to Secondary", help="Check to move to Secondary Table")
                },
                key="active_data_editor"
            )

            # Process state updates for active table
            state_changed = False
            for _, row in edited_active_view.iterrows():
                po = row['Vendor PO']
                if st.session_state["reviewer_notes"].get(po) != row['Review Notes']:
                    st.session_state["reviewer_notes"][po] = row['Review Notes']
                    state_changed = True
                if row['Move to Secondary']:
                    st.session_state["acknowledged_pos"].add(po)
                    state_changed = True

            if state_changed:
                save_persisted_state()
                st.rerun()

            # Copy/Paste PO List String (Active only)
            po_list_str = ", ".join(active_past_due['Vendor PO'].dropna().unique().tolist())
            st.text_area("Past Due Vendor POs String for Outreach (Excludes Secondary):", value=po_list_str, height=70)

            # Download CSV Button (Active only)
            csv_data = edited_active_view.drop(columns=['Move to Secondary']).to_csv(index=False).encode('utf-8')
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
                reviewed_past_due.insert(0, 'Restore to Main', False)

                output_cols_reviewed = [
                    'Restore to Main', 'Vendor Order Date', 'Vendor PO', 'Vendor', 'Days_Open_Vendor',
                    'Customer Order Date', 'Total_Qty', 'Combined_Notes', 'Review Notes'
                ]

                final_reviewed_view = reviewed_past_due[output_cols_reviewed].rename(columns=rename_dict)

                edited_reviewed_view = st.data_editor(
                    final_reviewed_view,
                    use_container_width=True,
                    disabled=[col for col in final_reviewed_view.columns if col not in ['Restore to Main', 'Review Notes']],
                    column_config={
                        "Restore to Main": st.column_config.CheckboxColumn("Restore to Main", help="Check to move back to Main Table")
                    },
                    key="reviewed_data_editor"
                )

                # Process state updates for secondary table
                state_changed_rev = False
                for _, row in edited_reviewed_view.iterrows():
                    po = row['Vendor PO']
                    if st.session_state["reviewer_notes"].get(po) != row['Review Notes']:
                        st.session_state["reviewer_notes"][po] = row['Review Notes']
                        state_changed_rev = True
                    if row['Restore to Main']:
                        st.session_state["acknowledged_pos"].remove(po)
                        state_changed_rev = True

                if state_changed_rev:
                    save_persisted_state()
                    st.rerun()
            else:
                st.info("No POs have been moved to the secondary table yet. Check the 'Move to Secondary' box in Table 1 above to move items here.")
else:
    st.info("Please upload a CSV export file to begin.")