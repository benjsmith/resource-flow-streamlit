import streamlit as st
import os
import sys
from datetime import date, timedelta

# Add the parent directory to the Python path so 'app' can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.components.people_view import render_people_view
from app.components.teams_view import render_teams_view
from app.components.projects_view import render_projects_view
from app.components.demand_view import render_demand_view
from app.components.allocations_view import render_allocations_view
from app.components.dashboard import render_dashboard
from app.database.init_db import initialize_database
from app.database.migrate_db import migrate_database

def check_database_initialization():
    """Check if the database is initialized and initialize if it doesn't exist."""
    if not os.path.exists("resource_flow.duckdb"):
        initialize_database()
    
    # Run database migrations
    migrate_database()

def setup_session_state():
    """Initialize session state variables."""
    # Default date range for filters (6 months)
    if "date_range" not in st.session_state:
        today = date.today()
        start_date = date(today.year, today.month, 1)  # First day of current month
        end_date = date(today.year + 1 if today.month == 12 else today.year,
                        1 if today.month == 12 else today.month + 6,
                        1) - timedelta(days=1)  # Last day of 6 months from now
        st.session_state.date_range = (start_date, end_date)
    
    # Default sidebar selection
    if "sidebar_selection" not in st.session_state:
        st.session_state.sidebar_selection = "Dashboard"

def create_sidebar():
    """Create the sidebar navigation menu."""
    with st.sidebar:
        st.title("Resource Flow")
        
        # Date range selector
        st.header("Date Range")
        start_date = st.date_input("Start Date", value=st.session_state.date_range[0])
        end_date = st.date_input("End Date", value=st.session_state.date_range[1])
        
        # Update date range in session state
        if start_date > end_date:
            st.error("Start date must be before end date")
        else:
            st.session_state.date_range = (start_date, end_date)
        
        # Navigation menu
        st.header("Navigation")
        options = ["Dashboard", "Projects", "People", "Teams", "Demands", "Allocations"]
        
        # Define a callback function to update the selection only
        def on_nav_change():
            st.session_state.sidebar_selection = st.session_state.sidebar_nav
        
        # Use the radio button with the callback
        selection = st.radio(
            "Go to", 
            options, 
            key="sidebar_nav", 
            index=options.index(st.session_state.sidebar_selection),
            on_change=on_nav_change
        )
        
        # Check if navigation has changed and trigger a rerun at the top level
        if st.session_state.sidebar_selection != selection:
            st.session_state.sidebar_selection = selection
            st.rerun()
        
        # App info
        st.sidebar.markdown("---")
        st.sidebar.info("Resource Flow: A resource planning and management application.")
        
        # About/Help button
        if st.sidebar.button("Help & Documentation"):
            st.session_state.show_help = True

def main():
    """Main function to run the Streamlit app."""
    # Check if the database exists and initialize if needed
    check_database_initialization()
    
    # Set up the session state
    setup_session_state()
    
    # Set page configuration
    st.set_page_config(
        page_title="Resource Flow",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Create the sidebar
    create_sidebar()
    
    # Show help dialog if requested
    if st.session_state.get("show_help", False):
        with st.expander("Help & Documentation", expanded=True):
            st.markdown("""
            # Resource Flow Help
            
            ## Overview
            Resource Flow is a tool for planning and managing resources across projects.
            
            ## Features and Usage
            
            ### Dashboard
            - View an overview of resource allocation, demand, and status
            - Analyze resource trends by selecting different time periods (Month/Quarter/Year)
            - Monitor project health and team allocations
            - Track upcoming key dates
            
            ### Projects
            - **View Projects**: See a list of all projects with their status and timeline
            - **Add Project**: Click "Add New Project" to create a new project
            - **Edit Project**: Select a project and click "Edit Selected Project"
            - **Delete Project**: Select a project and click "Delete Selected Project"
            - Required fields: Name, Start Date, End Date, Status
            
            ### People
            - **View People**: See a list of all team members with their roles and teams
            - **Add Person**: Click "Add New Person" to create a new team member
            - **Edit Person**: Select a person and click "Edit Selected Person"
            - **Delete Person**: Select a person and click "Delete Selected Person"
            - Required fields: Name, Role
            - Note: Cannot delete people with active allocations
            
            ### Teams
            - **View Teams**: See a list of all teams with their hierarchy and member count
            - **Add Team**: Click "Add New Team" to create a new team
            - **Edit Team**: Select a team and click "Edit Selected Team"
            - **Delete Team**: Select a team and click "Delete Selected Team"
            - Required fields: Name
            - Optional: Description, Parent Team
            
            ### Demands
            - **View Demands**: See a list of all resource demands with their status and priority
            - **Add Demand**: Click "Add New Demand" to create a new resource demand
            - **Edit Demand**: Select a demand and click "Edit Selected Demand"
            - **Delete Demand**: Select a demand and click "Delete Selected Demand"
            - Required fields: Project, Role Required, FTE Required, Start Date, End Date
            - Note: Deleting a demand with allocations will prompt for confirmation
            
            ### Allocations
            - **View Allocations**: See a list of all resource allocations
            - **Add Allocation**: Click "Add New Allocation" to assign a person to a project
            - **Edit Allocation**: Select an allocation and click "Edit Selected Allocation"
            - **Delete Allocation**: Select an allocation and click "Delete Selected Allocation"
            - Required fields: Person, Project, FTE Allocated, Start Date, End Date
            - Use filters to view allocations by person or project
            
            ## Tips
            - Use the date range selector to filter data by time period
            - Click on items in tables to select them for actions
            - Add new items using the "Add" buttons or tabs
            - Use the sidebar navigation to switch between different views
            - Check the status indicators for project and demand health
            - Monitor capacity utilization in the dashboard
            """)
            if st.button("Close Help"):
                st.session_state.show_help = False
                st.rerun()
    
    # Render the selected view
    if st.session_state.sidebar_selection == "Dashboard":
        render_dashboard()
    elif st.session_state.sidebar_selection == "Projects":
        render_projects_view()
    elif st.session_state.sidebar_selection == "People":
        render_people_view()
    elif st.session_state.sidebar_selection == "Teams":
        render_teams_view()
    elif st.session_state.sidebar_selection == "Demands":
        render_demand_view()
    elif st.session_state.sidebar_selection == "Allocations":
        render_allocations_view()

if __name__ == "__main__":
    main() 