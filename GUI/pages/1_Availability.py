import streamlit as st
import csv
import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import sys

# Add project root to path to import from src
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.lib_configs import LIBRARIES

st.set_page_config(page_title="Cornell Libraries – Availabilities", layout="wide")

# ---------- DATA MODEL ----------
# LIBRARIES is now imported from src.lib_configs
# The structure is:
# {
#   "name": str,
#   "floors": [
#       {"floor": int, "capacity": int, "occupied": int},
#       ...
#   ]
# }

# Store original LIBRARIES as base template (with capacities)
LIBRARIES_BASE = LIBRARIES.copy()


def level_and_color(rate: float):
    if rate < 0.4:
        return "Low", "#22c55e", "green"
    if rate < 0.7:
        return "Medium", "#fbbf24", "orange"
    return "High", "#ef4444", "red"


def library_totals(lib: dict):
    cap = sum(f["capacity"] for f in lib["floors"])
    occ = sum(f["occupied"] for f in lib["floors"])
    return cap, occ, cap - occ


def get_google_maps_url(address: str) -> str:
    """
    Generate a Google Maps URL for the given address.
    
    Args:
        address: The address string
    
    Returns:
        Google Maps URL
    """
    # URL encode the address
    encoded_address = urllib.parse.quote_plus(address)
    # Google Maps search URL
    return f"https://www.google.com/maps/search/?api=1&query={encoded_address}"


def get_latest_occupancy_from_csv(csv_path: str = "data/library_occupancy.csv") -> dict:
    """
    Read the latest row from the occupancy CSV file.
    Returns a dictionary mapping column names to occupancy values, or None if file doesn't exist.
    """
    csv_file = Path(__file__).parent.parent.parent / csv_path
    
    if not csv_file.exists():
        return None
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                return None
            # Return the last row (most recent)
            return rows[-1]
    except (KeyError, ValueError, IndexError, IOError):
        return None


def update_libraries_from_csv(libraries: list, csv_data: dict) -> list:
    """
    Update the libraries data structure with occupancy values from CSV.
    
    Args:
        libraries: The LIBRARIES list with capacity data
        csv_data: Dictionary from CSV with column names as keys and occupancy as values
    
    Returns:
        Updated libraries list with occupancy values from CSV
    """
    if csv_data is None:
        return libraries
    
    # Create a copy to avoid modifying the original
    updated_libraries = []
    
    for lib in libraries:
        updated_lib = {
            "name": lib["name"],
            "floors": []
        }
        # Preserve address if it exists
        if "address" in lib:
            updated_lib["address"] = lib["address"]
        
        for floor_data in lib["floors"]:
            # Construct the column name as it appears in CSV
            col_name = f"{lib['name']} Floor {floor_data['floor']}"
            
            # Get occupancy from CSV, fall back to original if not found
            if col_name in csv_data:
                try:
                    occupied = int(csv_data[col_name])
                except (ValueError, TypeError):
                    occupied = floor_data.get("occupied", 0)
            else:
                occupied = floor_data.get("occupied", 0)
            
            updated_lib["floors"].append({
                "floor": floor_data["floor"],
                "capacity": floor_data["capacity"],
                "occupied": occupied
            })
        
        updated_libraries.append(updated_lib)
    
    return updated_libraries


# ---------- CSS ----------
st.markdown(
    """
    <style>
    .block-container {max-width: 1150px;}

    /* Target buttons inside bordered containers in the columns */
    [data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"] .stButton > button {
        width: 100%;
        text-align: left;
        padding: 0.7rem 1.1rem;
        border-radius: 999px;
        border: 1px solid #4b5563;
        background-color: #111827;
        color: #f9fafb;
        font-weight: 600;
        font-size: 0.95rem;
    }

    /* Adjust spacing for the buttons */
    [data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"] .stButton {
        width: 100%;
        margin-bottom: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- STATE ----------
if "selected_library" not in st.session_state:
    st.session_state["selected_library"] = LIBRARIES[0]["name"]
if "last_csv_timestamp" not in st.session_state:
    st.session_state["last_csv_timestamp"] = None
if "libraries_data" not in st.session_state:
    st.session_state["libraries_data"] = None

# ---------- LOAD DATA FROM CSV ----------
# Check if we need to refresh data (on first load or when refresh button is clicked)
if st.session_state["libraries_data"] is None:
    # First load - read from CSV
    csv_data = get_latest_occupancy_from_csv()
    if csv_data:
        # Update libraries with latest occupancy data
        st.session_state["libraries_data"] = update_libraries_from_csv(LIBRARIES_BASE, csv_data)
        st.session_state["last_csv_timestamp"] = csv_data.get("timestamp", None)
    else:
        # Fall back to static data if CSV doesn't exist
        st.session_state["libraries_data"] = LIBRARIES_BASE
        st.session_state["last_csv_timestamp"] = None

# Use the loaded data
LIBRARIES = st.session_state["libraries_data"]

# ---------- TOP BAR ----------
cols_top = st.columns([1, 2, 1])
with cols_top[0]:
    if st.button("⬅ Back to home page"):
        st.switch_page("app.py")
with cols_top[1]:
    st.markdown("## Availability Snapshots")
with cols_top[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        # Force refresh by reading CSV and updating from base LIBRARIES
        csv_data = get_latest_occupancy_from_csv()
        if csv_data:
            st.session_state["libraries_data"] = update_libraries_from_csv(LIBRARIES_BASE, csv_data)
            st.session_state["last_csv_timestamp"] = csv_data.get("timestamp", None)
            st.rerun()
        else:
            st.warning("CSV file not found. Using static data.")
            st.session_state["libraries_data"] = LIBRARIES_BASE
            st.session_state["last_csv_timestamp"] = None
            st.rerun()

st.write("")  # spacer

# ---------- LEFT / RIGHT LAYOUT ----------
list_col, detail_col = st.columns([2, 3], gap="large")

# ---------- LEFT: LIBRARY BUTTONS ----------
with list_col:
    # Use a scrollable container with fixed height
    with st.container(height=650):
        
        # --- Recommendation Tab/Section ---
        best_lib = max(LIBRARIES, key=lambda l: library_totals(l)[2])
        best_name = best_lib["name"]
        _, _, best_avail = library_totals(best_lib)
        
        st.caption("🌟 RECOMMENDATION")
        with st.container(border=True):
            st.markdown(f"**{best_name}**")
            st.markdown(f"Has the most space right now: <span style='color:#22c55e; font-weight:bold'>{best_avail}</span> seats.", unsafe_allow_html=True)
            
            if st.button("Go to " + best_name, key="btn_rec"):
                st.session_state["selected_library"] = best_name
                st.rerun()
                
        st.divider()
        st.caption("📚 ALL LIBRARIES")
        
        for lib in LIBRARIES:
            name = lib["name"]

            # Example summary info for the card
            total_capacity = sum(f["capacity"] for f in lib["floors"])
            total_occupied = sum(f["occupied"] for f in lib["floors"])
            available = total_capacity - total_occupied
            n_floors = len(lib["floors"])

            rate = total_occupied / total_capacity if total_capacity else 0
            lvl, _, status_color = level_and_color(rate)
            # One "card" per library
            with st.container(border=True):  # border=True if you’re on a recent Streamlit
                clicked = st.button(
                    name,
                    key=f"btn_{name}",
                    use_container_width=True,   # equal width
                )

                # Info inside the same card, under the button text
                st.caption(
                    f"{n_floors} floors · "
                    f"{total_occupied} seats used · "
                    f"{available} available · "
                    f":{status_color}[{lvl}]"
                )

            if clicked:
                st.session_state["selected_library"] = name

# ---------- RIGHT: DETAILS + FLOOR GRID ----------
with detail_col:
    sel = next(l for l in LIBRARIES if l["name"] == st.session_state["selected_library"])
    total_cap, total_occ, total_avail = library_totals(sel)

    rate = total_occ / total_cap if total_cap else 0
    lvl, _, status_color = level_and_color(rate)

    st.markdown(f"### {sel['name']}")
    
    # Display the actual timestamp from CSV if available
    if st.session_state["last_csv_timestamp"]:
        try:
            csv_time = datetime.fromisoformat(st.session_state["last_csv_timestamp"])
            st.caption(f"Last updated: {csv_time.strftime('%I:%M:%S %p')} ({csv_time.strftime('%Y-%m-%d')})")
        except (ValueError, TypeError):
            st.caption(f"Last updated: {datetime.now(ZoneInfo('America/New_York')).strftime('%I:%M:%S %p')}")
    else:
        st.caption(f"Last updated: {datetime.now(ZoneInfo('America/New_York')).strftime('%I:%M:%S %p')} (using static data)")

    # ----- table-like grid for floors (now directly under the header) -----
    rows_md = []

    # total row
    rows_md.append(
        f"**Total** | **{total_occ}** | **{total_avail}** | "
        f":{status_color}[{lvl}]"
    )

    # per-floor rows
    for f in sel["floors"]:
        floor_cap = f["capacity"]
        floor_occ = f["occupied"]
        floor_avail = floor_cap - floor_occ
        floor_rate = floor_occ / floor_cap if floor_cap else 0
        fl_lvl, _, fl_color = level_and_color(floor_rate)

        rows_md.append(
            f"{f['floor']} | {floor_occ} | {floor_avail} | "
            f":{fl_color}[{fl_lvl}]"
        )

    table_md = (
        "Floor | People | Available | Status\n"
        "---|---:|---:|---\n" + "\n".join(rows_md)
    )

    st.markdown("#### Floor occupancy")
    st.markdown(table_md)
    st.write(
        f"**Status:** "
        f":{status_color}[{lvl}] (about {int(rate*100)}% of seats are currently occupied)."
    )
    
    # Go There button - show if address is available
    if "address" in sel and sel["address"]:
        st.write("")  # spacer
        maps_url = get_google_maps_url(sel["address"])
        st.link_button("🗺️ Go There", maps_url, use_container_width=True)
        st.caption(f"📍 {sel['address']}")
    
    # line comes AFTER the table now
    st.markdown("---")
    
    
    
