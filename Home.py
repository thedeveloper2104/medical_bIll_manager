import streamlit as st

# --- Page Configuration for Login Page ---
st.set_page_config(
    page_title="Home Automation Login",
    page_icon="🏠",
    layout="centered"
)

def check_login():
    """Displays a login form and returns True if the user is logged in."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # If not logged in, show the login form
    if not st.session_state.logged_in:
        st.title("🏠 Home Automation Universal Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login")

            if submitted:
                # Check for the correct username and password
                if username == "AutoB4" and password == "P@ssw0rd":
                    st.session_state.logged_in = True
                    st.rerun()  # Rerun the script to show the dashboard
                else:
                    st.error("Incorrect username or password")
        return False
    
    # If already logged in, return True
    return True

# --- Main Logic ---
# If the user is successfully logged in, show the dashboard.
if check_login():
    st.title("🚀 Home Automation Dashboard")
    st.header("Welcome!")
    
    st.markdown("""
        This is the central dashboard for all your home automation applications.
        
        **Please select an app from the sidebar on the left to get started.**
    """)
    
    st.info("Currently available apps:\n- Medical Bill Manager")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
