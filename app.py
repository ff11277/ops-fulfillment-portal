import streamlit as st
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# CONFIGURATION & SECURITY
# ---------------------------------------------------------
APP_PASSWORD = "Operations2026!"  # <-- Change this to your desired password

st.set_page_config(page_title="Operations Fulfillment Portal", layout="wide")

# Password Authenticator
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

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
# MAIN APPLICATION (Only visible after login)
# ---------------------------------------------------------
st.title("📦 Fulfillment & Inventory Audit Portal")
st.markdown("Upload your system CSV export file to run operational audits.")

uploaded_file = st.file_uploader("Upload CSV Export File", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    report_type = st.radio(
        "Select Analysis Type:",
        ["Weekly On Order Audit", "Decorating Work Order List"],
        horizontal=True
    )
    
    current_date = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))

    # 1. WEEKLY ON ORDER AUDIT
    if report_type == "Weekly On Order Audit":
        st.subheader("📋 On Order Audit Results")
        
        on_order_df = df[df['Status'] == 'On Order'].copy()
        
        if on_order_df.empty:
            st.warning("No records found with status 'On Order'.")
        else:
            on_order_df['Vendor Order Date Clean'] = pd.to_datetime(on_order_df['Vendor Order Date'], errors='coerce')
            on_order_df['Date Ordered Clean'] = pd.to_datetime(on_order_df['Date Ordered'], errors='coerce')
            on_order_df['Effective Date'] = on_order_df['Vendor Order Date Clean'].fillna(on_order_df['Date Ordered Clean'])
            
            po_summary = on_order_df.groupby(['Vendor', 'Vendor PO']).agg(
                Min_Vendor_Order_Date=('Effective Date', 'min'),
                Min_Customer_Order_Date=('Date Ordered Clean', 'min'),
                Total_Qty=('Qty', 'sum'),
                Customer_Orders=('Magento Order', 'nunique')
            ).reset_index()
            
            po_summary['Days_Open_Vendor'] = (current_date - po_summary['Min_Vendor_Order_Date']).dt.days
            po_summary['Days_Open_Customer'] = (current_date - po_summary['Min_Customer_Order_Date']).dt.days
            
            def check_past_due(row):
                if row['Vendor'] == 'Sanmar':
                    return row['Days_Open_Vendor'] > 7
                else:
                    return row['Days_Open_Vendor'] > 14
                    
            po_summary['Is_Past_Due'] = po_summary.apply(check_past_due, axis=1)
            past_due_df = po_summary[po_summary['Is_Past_Due']].sort_values(by='Days_Open_Vendor', ascending=False)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Units On Order", int(on_order_df['Qty'].sum()))
            col2.metric("Active Vendor POs", po_summary['Vendor PO'].nunique())
            col3.metric("Past Due Vendor POs", len(past_due_df))
            col4.metric("Past Due Units", int(past_due_df['Total_Qty'].sum()))
            
            st.markdown("---")
            st.subheader("🚨 Past Due Vendor Orders")
            
            if not past_due_df.empty:
                display_table = past_due_df.copy()
                display_table['Vendor Order Date'] = display_table['Min_Vendor_Order_Date'].dt.strftime('%m/%d/%Y')
                display_table['Customer Order Date'] = display_table['Min_Customer_Order_Date'].dt.strftime('%m/%d/%Y')
                
                output_cols = ['Vendor', 'Vendor PO', 'Vendor Order Date', 'Days_Open_Vendor', 'Customer Order Date', 'Days_Open_Customer', 'Total_Qty', 'Customer_Orders']
                rename_dict = {
                    'Days_Open_Vendor': 'Days Open (Vendor)',
                    'Days_Open_Customer': 'Days Open (Customer)',
                    'Total_Qty': 'Total Units',
                    'Customer_Orders': 'Customer Orders'
                }
                
                st.dataframe(display_table[output_cols].rename(columns=rename_dict), use_container_width=True)
                
                po_list_str = ", ".join(past_due_df['Vendor PO'].dropna().unique().tolist())
                st.text_area("Past Due Vendor POs String (Copy/Paste):", value=po_list_str, height=70)
            else:
                st.success("All 'On Order' POs are within acceptable lead-time windows!")

    # 2. DECORATING WORK ORDER LIST
    elif report_type == "Decorating Work Order List":
        st.subheader("🎨 Decorating Work Order List")
        
        decorating_df = df[df['Status'] == 'Decorating'].copy()
        
        if decorating_df.empty:
            st.warning("No records found with status 'Decorating'.")
        else:
            decorating_df['Gorilla: Date Taken Clean'] = pd.to_datetime(decorating_df['Gorilla: Date Taken'], errors='coerce')
            decorating_df['Date Ordered Clean'] = pd.to_datetime(decorating_df['Date Ordered'], errors='coerce')
            decorating_df['Days Since Ordered'] = (current_date - decorating_df['Date Ordered Clean']).dt.days
            
            wo_oldest = decorating_df.groupby('Gorilla Work Order')['Gorilla: Date Taken Clean'].min().rename('Bunch_Oldest_Date').reset_index()
            decorating_merged = decorating_df.merge(wo_oldest, on='Gorilla Work Order', how='left')
            
            decorating_sorted = decorating_merged.sort_values(
                by=['Bunch_Oldest_Date', 'Gorilla Work Order', 'Gorilla: Date Taken Clean'],
                ascending=[True, True, True]
            )
            
            decorating_sorted['Gorilla: Date Taken'] = decorating_sorted['Gorilla: Date Taken Clean'].dt.strftime('%m/%d/%Y')
            decorating_sorted['Date Ordered'] = decorating_sorted['Date Ordered Clean'].dt.strftime('%m/%d/%Y')
            
            target_cols = ['Gorilla: Date Taken', 'Gorilla Work Order', 'Group', 'Logo', 'Magento Order', 'Date Ordered', 'Days Since Ordered']
            st.dataframe(decorating_sorted[target_cols], use_container_width=True)
            
            wo_list_str = ", ".join([str(wo) for wo in decorating_sorted['Gorilla Work Order'].dropna().unique()])
            st.text_area("Decorating Work Orders String (Copy/Paste):", value=wo_list_str, height=70)