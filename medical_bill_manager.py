# Medical Bill Manager - Streamlit Version
# To run this app:
# 1. Install the required libraries:
#    pip install streamlit supabase pandas requests fpdf2
# 2. Save this code as a Python file (e.g., app.py).
# 3. Run from your terminal:
#    streamlit run app.py

import streamlit as st
import pandas as pd
from supabase import create_client, Client
import requests
import base64
from io import BytesIO
from fpdf import FPDF
import datetime
import uuid

# --- Page Configuration ---
st.set_page_config(
    page_title="Medical Bill Manager",
    page_icon="🧾",
    layout="wide"
)

# --- Supabase Connection ---
# IMPORTANT: Replace with your Supabase project's URL and anon key.
# You can store these as Streamlit secrets for better security.
try:
    SUPABASE_URL = st.secrets["supabase_url"]
    SUPABASE_KEY = st.secrets["supabase_key"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except (KeyError, FileNotFoundError):
    st.error("Supabase credentials are not set. Please add `supabase_url` and `supabase_key` to your Streamlit secrets.")
    st.stop()
    
# --- Gemini API Configuration ---
# Store your Gemini API key in Streamlit secrets for security.
try:
    GEMINI_API_KEY = st.secrets["gemini_api_key"]
except (KeyError, FileNotFoundError):
    st.warning("Gemini API key not found. Bill scanning feature will be disabled.")
    GEMINI_API_KEY = None


# --- Data Models & Functions ---

@st.cache_data(ttl=300) # Cache data for 5 minutes
def fetch_doctors():
    """Fetches the list of doctors from Supabase."""
    try:
        response = supabase.table('doctors').select('id, name').order('name').execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching doctors: {e}")
        return []

@st.cache_data(ttl=60) # Cache bills for 1 minute
def fetch_bills():
    """Fetches the list of bills from Supabase."""
    try:
        response = supabase.table('bills').select('*').order('bill_date', desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching bills: {e}")
        return []

def generate_pdf(dataframe):
    """Generates a PDF from a Pandas DataFrame."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Medical Bills Report", ln=True, align='C')
    
    # Table Header
    pdf.set_font("Arial", 'B', 10)
    col_widths = [15, 50, 30, 30, 30, 35] # Column widths
    headers = ['S.No', 'Vendor', 'Bill No.', 'Bill Date', 'Amount', 'Doctor']
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1)
    pdf.ln()

    # Table Rows
    pdf.set_font("Arial", '', 10)
    for index, row in dataframe.iterrows():
        st.print(f"Processing row {index + 1}: {row.to_dict()}")  # Debugging output
        # Ensure data is string before passing to cell
        s_no = str(index + 1)
        vendor = str(row.get('vendor_name', ''))
        bill_no = str(row.get('bill_no', ''))
        bill_date = str(row.get('bill_date', ''))
        amount = f"${row.get('bill_amount', 0.0):.2f}"
        doctor = str(row.get('doctor_name', ''))

        pdf.cell(col_widths[0], 10, s_no, border=1)
        pdf.cell(col_widths[1], 10, vendor, border=1)
        pdf.cell(col_widths[2], 10, bill_no, border=1)
        pdf.cell(col_widths[3], 10, bill_date, border=1)
        pdf.cell(col_widths[4], 10, amount, border=1)
        pdf.cell(col_widths[5], 10, doctor, border=1)
        pdf.ln()
        
    # The output method returns bytes, no encoding is needed.
    return pdf.output()

def extract_bill_details_with_gemini(image_bytes):
    """Uses Gemini API to extract details from a bill image."""
    if not GEMINI_API_KEY:
        st.error("Gemini API key is not configured.")
        return None

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={GEMINI_API_KEY}"
    
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "From the attached bill image, extract the vendor name (as vendorName), total amount (as a number, billAmount), and bill date (in YYYY-MM-DD format, billDate). Respond with only a single, clean JSON object. If a value cannot be found, use null."},
                {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}}
            ]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        # Clean up the response to get the JSON part
        json_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        clean_json = json_text.strip().replace('```json', '').replace('```', '')
        return pd.read_json(BytesIO(clean_json.encode()), lines=True).iloc[0].to_dict()
        
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
    except (KeyError, IndexError, Exception) as e:
        st.error(f"Failed to parse AI response: {e}")
        
    return None


# --- UI Layout ---

st.title("🧾 Medical Bill Manager")
st.markdown("An application to scan, track, and manage your medical bills using AI.")

# --- Sidebar for Navigation and Doctor Management ---
with st.sidebar:
    st.header("👨‍⚕️ Manage Doctors")
    
    doctors = fetch_doctors()
    doctor_names = [doc['name'] for doc in doctors]
    
    with st.form("add_doctor_form", clear_on_submit=True):
        new_doctor_name = st.text_input("Add a new doctor:")
        submitted = st.form_submit_button("Add Doctor")
        if submitted and new_doctor_name:
            if new_doctor_name in doctor_names:
                st.warning("This doctor already exists.")
            else:
                try:
                    supabase.table('doctors').insert({'name': new_doctor_name}).execute()
                    st.success(f"Added Dr. {new_doctor_name}")
                    st.cache_data.clear() # Clear cache to refetch
                except Exception as e:
                    st.error(f"Failed to add doctor: {e}")

    st.subheader("Existing Doctors")
    if doctors:
        for doctor in doctors:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.write(doctor['name'])
            with col2:
                if st.button("🗑️", key=f"del_{doctor['id']}"):
                    try:
                        supabase.table('doctors').delete().eq('id', doctor['id']).execute()
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Failed to delete.")
    else:
        st.write("No doctors added yet.")

# --- Main App Area ---

# Initialize session state for form inputs
if 'form_data' not in st.session_state:
    st.session_state.form_data = {'vendor_name': '', 'bill_no': '', 'bill_date': datetime.date.today(), 'bill_amount': 0.0, 'doctor_name': None}

st.header("➕ Add or Update a Bill")

col1, col2 = st.columns(2)

# Column 1: AI Bill Scanner
with col1:
    st.subheader("Scan a Bill")
    uploaded_file = st.file_uploader("Upload a bill image (JPG, PNG)", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        if st.button("🤖 Scan & Extract Details"):
            with st.spinner("AI is reading your bill..."):
                image_bytes = uploaded_file.getvalue()
                extracted_data = extract_bill_details_with_gemini(image_bytes)
                if extracted_data:
                    st.session_state.form_data['vendor_name'] = extracted_data.get('vendorName', '')
                    st.session_state.form_data['bill_amount'] = float(extracted_data.get('billAmount', 0.0))
                    try:
                        bill_date_str = extracted_data.get('billDate')
                        if bill_date_str:
                             st.session_state.form_data['bill_date'] = datetime.datetime.strptime(bill_date_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        st.warning("Could not parse date from AI. Please set manually.")
                    st.success("Details extracted! Please review and save.")
                    st.rerun() # Rerun to update the form with new data

# Column 2: Bill Details Form
with col2:
    st.subheader("Bill Details")
    with st.form("bill_form"):
        vendor_name = st.text_input("Name of Vendor", value=st.session_state.form_data['vendor_name'])
        bill_no = st.text_input("Bill No.", value=st.session_state.form_data['bill_no'])
        bill_date = st.date_input("Bill Date", value=st.session_state.form_data['bill_date'])
        bill_amount = st.number_input("Bill Amount", min_value=0.0, format="%.2f", value=st.session_state.form_data['bill_amount'])
        
        doctor_options = [""] + doctor_names
        selected_doctor = st.selectbox("Doctor", options=doctor_options)

        form_col1, form_col2 = st.columns(2)
        with form_col1:
            save_submitted = st.form_submit_button("💾 Save Bill", use_container_width=True)
        with form_col2:
            if st.form_submit_button("🔄 Clear Form", use_container_width=True):
                 st.session_state.form_data = {'vendor_name': '', 'bill_no': '', 'bill_date': datetime.date.today(), 'bill_amount': 0.0, 'doctor_name': None}
                 st.rerun()

        if save_submitted:
            if not vendor_name or not bill_date:
                st.warning("Vendor Name and Bill Date are required.")
            else:
                bill_data = {
                    'vendor_name': vendor_name,
                    'bill_no': bill_no,
                    'bill_date': str(bill_date),
                    'bill_amount': bill_amount,
                    'doctor_name': selected_doctor
                }
                try:
                    supabase.table('bills').insert(bill_data).execute()
                    st.success("Bill saved successfully!")
                    st.cache_data.clear() # Clear cache to refetch bills
                    # Clear form state after saving
                    st.session_state.form_data = {'vendor_name': '', 'bill_no': '', 'bill_date': datetime.date.today(), 'bill_amount': 0.0, 'doctor_name': None}
                except Exception as e:
                    st.error(f"Failed to save bill: {e}")


st.divider()

# --- Display Bills Table ---
st.header("📋 My Bills")

bills = fetch_bills()

if not bills:
    st.info("No bills found. Add your first bill to get started!")
else:
    df = pd.DataFrame(bills)
    df_display = df[['vendor_name', 'bill_no', 'bill_date', 'bill_amount', 'doctor_name']]

    # --- Filtering and Exporting ---
    st.subheader("Filter and Export")
    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 2])
    
    with filter_col1:
        start_date = st.date_input("From", value=datetime.date.today() - datetime.timedelta(days=30))
    
    with filter_col2:
        end_date = st.date_input("To", value=datetime.date.today())

    if start_date > end_date:
        st.error("Error: Start date must be before end date.")
    else:
        # Filter the dataframe
        mask = (df['bill_date'] >= str(start_date)) & (df['bill_date'] <= str(end_date))
        filtered_df = df.loc[mask]

        with filter_col3:
            st.write("") # Spacer
            st.write("") # Spacer
            # This button will now trigger the PDF generation.
            generate_button = st.button("Generate PDF Report")

    # Only generate and offer download if the button is clicked and data is available
    if 'generate_button' in locals() and generate_button:
        if not filtered_df.empty:
            with st.spinner("Generating PDF..."):
                pdf_data = generate_pdf(filtered_df.reset_index(drop=True))
                st.download_button(
                    label="⬇️ Download as PDF",
                    data=pdf_data,
                    file_name=f"Medical_Bills_{start_date}_to_{end_date}.pdf",
                    mime="application/pdf",
                )
        else:
            st.warning("No bills in the selected date range to generate a report.")


    st.dataframe(df_display, use_container_width=True)
    
    # --- Delete Functionality ---
    st.subheader("Delete a Bill")
    bill_to_delete_id = st.selectbox(
        "Select a bill to delete (by Vendor and Date)",
        options=[(f"{b['vendor_name']} - {b['bill_date']}", b['id']) for b in bills],
        format_func=lambda x: x[0],
        index=None,
        placeholder="Choose a bill..."
    )

    if bill_to_delete_id:
        if st.button("❌ Delete Selected Bill", type="primary"):
            try:
                supabase.table('bills').delete().eq('id', bill_to_delete_id[1]).execute()
                st.success("Bill deleted.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to delete bill: {e}")
