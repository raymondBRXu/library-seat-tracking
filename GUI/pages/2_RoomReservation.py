import streamlit as st
import csv
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Cornell Libraries – Room Reservation", layout="wide")

# ---------- AUTHENTICATION FUNCTIONS ----------
def load_credentials(csv_path: str = "data/credentials.csv") -> dict:
    """
    Load credentials from CSV file.
    Returns a dictionary mapping username to password and user info.
    """
    csv_file = Path(__file__).parent.parent.parent / csv_path
    
    if not csv_file.exists():
        return {}
    
    credentials = {}
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                username = row.get('username', '').strip()
                if username:
                    credentials[username] = {
                        'password': row.get('password', '').strip(),
                        'role': row.get('role', 'student').strip(),
                        'full_name': row.get('full_name', username).strip()
                    }
    except (KeyError, ValueError, IOError) as e:
        st.error(f"Error loading credentials: {e}")
        return {}
    
    return credentials


def verify_credentials(username: str, password: str, credentials: dict) -> bool:
    """
    Verify if the provided username and password match stored credentials.
    """
    if username in credentials:
        return credentials[username]['password'] == password
    return False


def get_user_info(username: str, credentials: dict) -> dict:
    """
    Get user information for a given username.
    """
    if username in credentials:
        return credentials[username]
    return {}


def login_page(credentials: dict):
    """
    Display login form and handle authentication.
    """
    # Back button at top
    if st.button("⬅ Back to home page", key="back_from_login"):
        st.switch_page("app.py")
    
    st.markdown("## 🔐 Room Reservation Login")
    st.markdown("Please log in to access room reservation features.")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit_button = st.form_submit_button("Login", use_container_width=True)
        
        if submit_button:
            if not username or not password:
                st.error("Please enter both username and password.")
            elif verify_credentials(username, password, credentials):
                # Store authentication in session state
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["user_info"] = get_user_info(username, credentials)
                st.success(f"Welcome, {st.session_state['user_info'].get('full_name', username)}!")
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")
    
    # Display available test accounts (for development)
    with st.expander("ℹ️ Test Accounts"):
        st.markdown("""
        **Available test accounts:**
        - `admin` / `admin123` (Administrator)
        - `student1` / `student123` (Student)
        - `student2` / `password123` (Student)
        - `faculty1` / `faculty123` (Faculty)
        - `staff1` / `staff123` (Staff)
        """)


def logout():
    """
    Clear authentication and return to login page.
    """
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["user_info"] = None
    st.rerun()


# ---------- CSS ----------
st.markdown(
    """
    <style>
    .block-container {max-width: 1150px;}
    
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- INITIALIZE SESSION STATE ----------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None

# ---------- LOAD CREDENTIALS ----------
credentials = load_credentials()

# ---------- AUTHENTICATION CHECK ----------
if not st.session_state["authenticated"]:
    # Show login page
    login_page(credentials)
else:
    # User is authenticated - show main content
    user_info = st.session_state["user_info"]
    username = st.session_state["username"]
    
    # Top bar with logout
    cols_top = st.columns([1, 3, 1])
    with cols_top[0]:
        if st.button("⬅ Back to home page"):
            st.switch_page("app.py")
    with cols_top[1]:
        st.markdown("## 🏢 Room Reservation")
    with cols_top[2]:
        if st.button("🚪 Logout"):
            logout()
    
    # User info display
    st.info(f"Logged in as: **{user_info.get('full_name', username)}** ({user_info.get('role', 'user').title()})")
    
    st.write("")  # spacer
    
    # Main reservation content (placeholder for now)
    st.markdown("### Welcome to Room Reservation")
    st.markdown("Room reservation features will be implemented here.")
    
    # Display current time
    st.caption(f"Current time: {datetime.now().strftime('%I:%M:%S %p')}")

