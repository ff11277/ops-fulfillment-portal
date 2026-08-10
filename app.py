import streamlit as st
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# CONFIGURATION & SECURITY
# ---------------------------------------------------------
APP_PASSWORD = "Operations2026!"  # Change this to your team password if desired

st.set_page_config(page_title="Operations Fulfillment Portal", layout="wide")

# Password Authenticator
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Initialize Session State for Interactive Reviewer Notes
if "reviewer_notes" not in st.session_state:
    st.session_state["reviewer_notes"] = {}

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
st.markdown("Upload your system CSV export file to run the **On Order Audit**.")

uploaded_file = st.file_uploader("Upload CSV Export File", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    current_date = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))

    # Filter for 'On Order' status
    on_order_df = df[df['Status'] == 'On Order'].copy()

    if on_order_df.empty:
        st.warning("No records found with status 'On Order'.")
    else:
        # Detect items with Work Order numbers assigned (checked in but status not updated)
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
            with st.expander("🔍 Click to view items needing ERP Status Update"):
                clean_cols = ['Magento Order', 'Vendor', 'Vendor PO', wo_col, 'Qty', 'Vendor Order Date', 'Notes']
                existing_clean_cols = [c for c in clean_cols if c in checked_in_mismatch.columns]
                st.dataframe(checked_in_mismatch[existing_clean_cols], use_container_width=True)

        st.markdown("---")

        # Parse Dates
        on_order_df['Vendor Order Date Clean'] = pd.to_datetime(on_order_df['Vendor Order Date'], errors='coerce')
        on_order_df['Date Ordered Clean'] = pd.to_datetime(on_order_df['Date Ordered'], errors='coerce')
        on_order_df['Effective Date'] = on_order_df['Vendor Order Date Clean'].fillna(on_order_df['Date Ordered Clean'])

        # Function to collect and combine all unique, non-empty CSV system notes per PO
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
            Has_WO_Any=('Has_WO', 'any'),
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

        # Format display dates and check-in status
        all_past_due_df['Vendor Order Date'] = all_past_due_df['Min_Vendor_Order_Date'].dt.strftime('%m/%d/%Y')
        all_past_due_df['Customer Order Date'] = all_past_due_df['Min_Customer_Order_Date'].dt.strftime('%m/%d/%Y')
        all_past_due_df['Check-In Status'] = all_past_due_df['Has_WO_Any'].apply(
            lambda x: "⚠️ Checked In (WO Assigned)" if x else "Pending Vendor Ship"
        )

        # Map interactive reviewer notes from session state
        all_past_due_df['Review Notes'] = all_past_due_df['Vendor PO'].apply(
            lambda po: st.session_state["reviewer_notes"].get(po, "")
        )

        # Final Column Sequence (Days Open Customer removed)
        output_cols = [
            'Vendor Order Date', 'Vendor PO', 'Vendor', 'Days_Open_Vendor',
            'Customer Order Date', 'Total_Qty', 
            'Check-In Status', 'Combined_Notes', 'Review Notes'
        ]
        
        rename_dict = {
            'Days_Open_Vendor': 'Days Open (Vendor)',
            'Total_Qty': 'Total Units',
            'Combined_Notes': 'System Notes'
        }

        # --- ACKNOWLEDGE / REVIEWED PO SELECTOR ---
        st.subheader("🚨 Past Due Vendor Orders")
        
        if not all_past_due_df.empty:
            po_options = all_past_due_df['Vendor PO'].unique().tolist()
            acknowledged_pos = st.multiselect(
                "✅ Select POs you have already reviewed / know why they are late (moves them to Secondary Table):",
                options=po_options,
                default=[]
            )

            # Split Dataframes
            active_past_due = all_past_due_df[~all_past_due_df['Vendor PO'].isin(acknowledged_pos)].copy()
            reviewed_past_due = all_past_due_df[all_past_due_df['Vendor PO'].isin(acknowledged_pos)].copy()

            # High-Level Metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Units On Order", int(on_order_df['Qty'].sum()))
            col2.metric("Active Vendor POs", po_summary['Vendor PO'].nunique())
            col3.metric("Action Required POs", len(active_past_due))
            col4.metric("Reviewed / Acknowledged POs", len(reviewed_past_due))

            st.markdown("### 📋 Action Required (Unreviewed Past Due POs)")
            st.caption("💡 Representatives can type notes directly in the 'Review Notes' column below.")

            if not active_past_due.empty:
                final_active_view = active_past_due[output_cols].rename(columns=rename_dict)
                
                # Interactive Editable Table
                edited_active_view = st.data_editor(
                    final_active_view,
                    use_container_width=True,
                    disabled=[col for col in final_active_view.columns if col != 'Review Notes'],
                    key="active_data_editor"
                )

                # Save typed reviewer notes back to Session State
                for _, row in edited_active_view.iterrows():
                    st.session_state["reviewer_notes"][row['Vendor PO']] = row['Review Notes']

                # Copy/Paste PO List String (Active only)
                po_list_str = ", ".join(active_past_due['Vendor PO'].dropna().unique().tolist())
                st.text_area("Past Due Vendor POs String for Outreach (Excludes Acknowledged):", value=po_list_str, height=70)

                # Download CSV Button (Active only, includes typed reviewer notes)
                csv_data = edited_active_view.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Action Required Report (CSV)",
                    data=csv_data,
                    file_name=f"Action_Required_Vendor_POs_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.success("All past-due POs have been acknowledged or resolved!")

            # --- SECONDARY TABLE FOR REVIEWED / ACKNOWLEDGED POS ---
            st.markdown("---")
            with st.expander(f"📁 Secondary Table: Acknowledged / Reviewed Past Due POs ({len(reviewed_past_due)})", expanded=True if not reviewed_past_due.empty else False):
                if not reviewed_past_due.empty:
                    final_reviewed_view = reviewed_past_due[output_cols].rename(columns=rename_dict)
                    
                    # Interactive Editable Table for Secondary View
                    edited_reviewed_view = st.data_editor(
                        final_reviewed_view,
                        use_container_width=True,
                        disabled=[col for col in final_reviewed_view.columns if col != 'Review Notes'],
                        key="reviewed_data_editor"
                    )

                    # Save typed reviewer notes back to Session State
                    for _, row in edited_reviewed_view.iterrows():
                        st.session_state["reviewer_notes"][row['Vendor PO']] = row['Review Notes']
                else:
                    st.info("No POs have been marked as reviewed yet. Use the multiselect box above to move items here.")
        else:
            st.success("All 'On Order' POs are within acceptable lead-time windows!")