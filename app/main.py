import streamlit as st
import os
import sys

# Add the parent directory to the Python path so 'app' can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta

from app.components.people_view import render_people_view
from app.components.teams_view import render_teams_view
from app.components.projects_view import render_projects_view
from app.components.demand_view import render_demand_view
from app.components.allocations_view import render_allocations_view
from app.components.dashboard import render_dashboard
from app.database.init_db import initialize_database

# Set page config
st.set_page_config(
    page_title="Resource Flow",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'selected_view' not in st.session_state:
    st.session_state.selected_view = 'Dashboard'
if 'edit_person_id' not in st.session_state:
    st.session_state.edit_person_id = None
if 'edit_team_id' not in st.session_state:
    st.session_state.edit_team_id = None
if 'edit_project_id' not in st.session_state:
    st.session_state.edit_project_id = None
if 'edit_demand_id' not in st.session_state:
    st.session_state.edit_demand_id = None
if 'edit_allocation_id' not in st.session_state:
    st.session_state.edit_allocation_id = None
if 'date_range' not in st.session_state:
    # Default to current month plus 11 months (1 year view)
    today = date.today()
    start_date = date(today.year, today.month, 1)
    
    # Calculate end date by adding 11 months
    if today.month <= 1:  # January
        end_year = today.year
        end_month = 12
    else:
        end_year = today.year + (today.month + 10) // 12
        end_month = (today.month + 10) % 12 + 1
    
    end_date = date(end_year, end_month, 1) - timedelta(days=1)
    st.session_state.date_range = (start_date, end_date)

# Main function
def main():
    # Initialize database if it doesn't exist
    db_path = "resource_flow.duckdb"
    if not os.path.exists(db_path):
        initialize_database()
    
    # Sidebar
    with st.sidebar:
        st.title("Resource Flow")
        st.markdown("---")
        
        # Navigation menu
        options = ["Dashboard", "People", "Teams", "Projects", "Demand", "Allocations"]
        selected = st.radio("Navigation", options, index=options.index(st.session_state.selected_view))
        st.session_state.selected_view = selected
        
        st.markdown("---")
        
        # Date range selector in sidebar
        st.subheader("Date Range")
        start_date, end_date = st.session_state.date_range
        
        col1, col2 = st.columns(2)
        with col1:
            new_start_date = st.date_input("Start Date", start_date)
        with col2:
            new_end_date = st.date_input("End Date", end_date)
        
        if new_start_date and new_end_date and new_start_date <= new_end_date:
            st.session_state.date_range = (new_start_date, new_end_date)
        
        st.markdown("---")
        st.caption("Resource Flow v1.0.0")
    
    # Main content based on selected view
    if st.session_state.selected_view == "Dashboard":
        render_dashboard()
    elif st.session_state.selected_view == "People":
        render_people_view()
    elif st.session_state.selected_view == "Teams":
        render_teams_view()
    elif st.session_state.selected_view == "Projects":
        render_projects_view()
    elif st.session_state.selected_view == "Demand":
        render_demand_view()
    elif st.session_state.selected_view == "Allocations":
        render_allocations_view()

if __name__ == "__main__":
    main() 