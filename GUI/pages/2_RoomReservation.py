import streamlit as st
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, time
from mailersend import MailerSendClient, EmailBuilder


# You'll need to replace this with your actual MailerSend API key
# For now I'll use a placeholder, please replace it with your key.
mailersend_api_key = "mlsn.2bd1267c64270d886df86fc36d96cb7f2399dcff751f5fe2f070761a3dd5278c"

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


def load_rooms(csv_path: str = "data/library_rooms.csv") -> pd.DataFrame:
    """
    Load room data from CSV file.
    """
    csv_file = Path(__file__).parent.parent.parent / csv_path
    
    if not csv_file.exists():
        st.error(f"Room data file not found at {csv_file}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(csv_file)
        return df
    except Exception as e:
        st.error(f"Error loading room data: {e}")
        return pd.DataFrame()

def generate_time_slots(selected_date):
    """
    Generate 30-minute time slots from 8:00 AM to 11:00 PM.
    If selected_date is today, start from the next hour or half hour.
    """
    now = datetime.now()
    slots = []
    
    start_time = datetime.combine(selected_date, time(8, 0))
    end_time = datetime.combine(selected_date, time(23, 0))
    
    # If today, adjust start time
    if selected_date == now.date():
        # Round up to next 30 minutes
        delta = timedelta(minutes=30)
        next_slot = now + (datetime.min - now) % delta
        if next_slot < start_time:
            current_slot = start_time
        else:
            current_slot = next_slot
    else:
        current_slot = start_time

    while current_slot <= end_time:
        if current_slot >= start_time: # Ensure we don't go before 8 AM
             slots.append(current_slot.strftime("%I:%M %p"))
        current_slot += timedelta(minutes=30)
        
    return pd.DataFrame({"Time": slots, "Select": [False]*len(slots)})


# Optimized Dialog: Single step with expander or just unconditional display
if hasattr(st, "dialog"):
    @st.dialog("Room Reservation")
    def show_room_details(room):
        st.subheader(room['Room'])
        
        # Always show details at top
        with st.expander("Room Details", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**📍 Library:** {room['Library']}")
                st.markdown(f"**🔊 Noise Level:** {room['Noise']}")
            with col2:
                st.markdown(f"**👥 Capacity:** {room['People']} people")
            
            features = []
            if room.get('Project', 0) == 1: features.append("Projector")
            if room.get('Whiteboard', 0) == 1: features.append("Whiteboard")
            if room.get('Window', 0) == 1: features.append("Window")
            
            if features:
                st.markdown(f"**✨ Features:** {', '.join(features)}")
            else:
                st.markdown("**✨ Features:** None")

        st.markdown("---")
        st.markdown("### Select Date & Time")
        
        # Date Selection
        min_date = datetime.now().date()
        max_date = min_date + timedelta(days=7)
        
        selected_date = st.date_input(
            "Select Date",
            min_value=min_date,
            max_value=max_date,
            value=min_date,
            key=f"date_input_{room['Room']}"
        )
        
        # Time Slots
        st.markdown("Select Time Slots (Max 4 slots / 2 hours):")
        
        df_slots = generate_time_slots(selected_date)
        
        if df_slots.empty:
            st.warning("No time slots available for this date.")
            edited_df = df_slots
        else:
            edited_df = st.data_editor(
                df_slots,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select time slot",
                        default=False,
                    ),
                    "Time": st.column_config.TextColumn(
                        "Time Slot",
                        disabled=True
                    )
                },
                hide_index=True,
                key=f"slot_editor_{room['Room']}_{selected_date}",
                use_container_width=True
            )
        
        # Count selected slots
        num_selected = 0
        selected_slots = []
        if not edited_df.empty:
            selected_slots = edited_df[edited_df["Select"] == True]["Time"].tolist()
            num_selected = len(selected_slots)
            
            if num_selected > 4:
                st.error(f"⚠️ You have selected {num_selected} slots. Maximum allowed is 4.")
            elif num_selected > 0:
                st.success(f"Selected {num_selected} slots: {', '.join(selected_slots)}")

        st.markdown("### Contact Information")
        email_input = st.text_input("Email Address", placeholder="netid@cornell.edu", key=f"email_{room['Room']}")
        
        st.markdown("---")
        
        # Confirm Button
        if st.button("Confirm Reservation", type="primary", key=f"confirm_{room['Room']}", disabled=(num_selected == 0 or num_selected > 4 or not email_input)):
            # Logic to record data will go here
            try:
                # Initialize MailerSend client
                ms = MailerSendClient(mailersend_api_key)

                email = (EmailBuilder()
                    .from_email("future.cornell.libs@test-xkjn41m1qx04z781.mlsender.net", "Future Cornell Libs")
                    .to_many([{"email": email_input, "name": "Student"}])
                    .subject("Confirmation on room reservation")
                    .html(f"""
                    <p>Hi there,</p>
                    <p>Your reservation for <strong>{room['Room']}</strong> on <strong>{selected_date}</strong> has been confirmed!</p>
                    <p><strong>Time Slots:</strong> {', '.join(selected_slots)}</p>
                    <br>
                    <p>Cheers</p>
                    """)
                    .text(f"Hi there, Your reservation for room {room['Room']} on {selected_date} has been confirmed! Time Slots: {', '.join(selected_slots)}. Cheers")
                    .build())

                response = ms.emails.send(email)
                # print(f"Email sent: {response.message_id}") # For debugging
                
                st.success(f"Reservation confirmed for {selected_date} at {', '.join(selected_slots)}!")
                st.info("A Confirmation Email Has Been Sent.")
            except Exception as e:
                st.error(f"Failed to send confirmation email: {e}")

else:
    # Fallback for older streamlit versions (Simplified without wizard flow for now)
    def show_room_details(room):
        with st.expander(f"Details: {room['Room']}", expanded=True):
            st.markdown(f"**Library:** {room['Library']} | **Noise:** {room['Noise']} | **Capacity:** {room['People']}")
            features = []
            if room.get('Project', 0) == 1: features.append("Projector")
            if room.get('Whiteboard', 0) == 1: features.append("Whiteboard")
            if room.get('Window', 0) == 1: features.append("Window")
            st.markdown(f"**Features:** {', '.join(features) if features else 'None'}")
            st.button("Reserve (Update Streamlit for full feature)", key=f"reserve_{room['Room']}")


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
    
    div[data-testid="stButton"] button {
        min_height: 60px;
        height: 100%;
        white-space: normal;
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
    
    # Main reservation content
    st.markdown("### Select a Room")
    
    # Load room data
    df_rooms = load_rooms()
    
    if not df_rooms.empty:
        # Layout: Filters (1/3) and Rooms (2/3)
        col_filters, col_rooms = st.columns([1, 2])
        
        with col_filters:
            st.subheader("Filters")
            
            # Library Filter
            libraries = sorted(df_rooms['Library'].unique().tolist())
            selected_libraries = st.multiselect("Library", options=libraries, default=libraries)
            
            # Noise Filter
            noise_levels = sorted(df_rooms['Noise'].unique().tolist())
            selected_noise = st.multiselect("Noise Level", options=noise_levels, default=noise_levels)
            
            # Features Filter
            st.markdown("**Features**")
            filter_projector = st.checkbox("Projector")
            filter_whiteboard = st.checkbox("Whiteboard")
            filter_window = st.checkbox("Window")
            
            # Max People Filter (Slider 4-10)
            st.markdown("**Number of People**")
            min_people = st.slider("Minimum Capacity", min_value=4, max_value=10, value=4)
            
        # Apply Filters
        filtered_df = df_rooms.copy()
        
        if selected_libraries:
            filtered_df = filtered_df[filtered_df['Library'].isin(selected_libraries)]
            
        if selected_noise:
            filtered_df = filtered_df[filtered_df['Noise'].isin(selected_noise)]
            
        if filter_projector:
            filtered_df = filtered_df[filtered_df['Project'] == 1]
        if filter_whiteboard:
            filtered_df = filtered_df[filtered_df['Whiteboard'] == 1]
        if filter_window:
            filtered_df = filtered_df[filtered_df['Window'] == 1]
            
        # Filter by Capacity
        filtered_df = filtered_df[filtered_df['People'] >= min_people]
        
        # Display Rooms
        with col_rooms:
            st.subheader(f"Available Rooms ({len(filtered_df)})")
            
            # Convert to list of dicts for easier iteration
            rooms_list = filtered_df.to_dict('records')
            
            if not rooms_list:
                st.warning("No rooms match your criteria.")
            else:
                # Create a grid of buttons
                # We'll iterate in chunks of 3 for a 3-column grid
                cols_per_row = 3
                for i in range(0, len(rooms_list), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j in range(cols_per_row):
                        if i + j < len(rooms_list):
                            room = rooms_list[i + j]
                            with cols[j]:
                                # Button for each room
                                if st.button(
                                    f"{room['Room']}", 
                                    key=f"btn_{room['Room']}_{i}_{j}", 
                                    use_container_width=True
                                ):
                                    # Reset reservation step before opening
                                    st.session_state["reservation_step"] = "details"
                                    show_room_details(room)
    else:
        st.error("No room data available.")

    # Display current time at bottom
    st.write("")
    st.caption(f"Current time: {datetime.now().strftime('%I:%M:%S %p')}")
