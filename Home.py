import streamlit as st

# --- Page Configuration ---
# We set the page config based on the login status to hide/show the sidebar.

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def configure_page():
    """Sets the page configuration based on login status."""
    if st.session_state.logged_in:
        # Show the sidebar on the dashboard page
        st.set_page_config(
            page_title="Home Automation Dashboard",
            page_icon="🚀",
            layout="centered",
            initial_sidebar_state="expanded"
        )
    else:
        # Hide the sidebar on the login page
        st.set_page_config(
            page_title="Home Automation Login",
            page_icon="🏠",
            layout="centered",
            initial_sidebar_state="collapsed"
        )

# Call the function to set the page config at the start
configure_page()


def check_login():
    """Displays a login form and returns True if the user is logged in."""
    # If not logged in, show the login form
    if not st.session_state.logged_in:
        st.title("🏠 Home Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login")

            if submitted:
                # Check for the correct username and password
                if username == "AutoB4" and password == "P@ssw0rd":
                    st.session_state.logged_in = True
                    st.rerun()  # Rerun the script to re-evaluate and show the dashboard
                else:
                    st.error("Incorrect username or password")
        return False
    
    # If already logged in, return True
    return True

# --- Main Logic ---
# If the user is successfully logged in, show the dashboard.
if check_login():
    st.title("🚀 Dashboard")
    st.header("Welcome!")
    
    st.markdown("""
        This is the central dashboard for all your home automation applications.
        
        **Please select an app from the sidebar on the left to get started.**
    """)
    
    st.info("Currently available apps:\n- Medical Bill Manager")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
