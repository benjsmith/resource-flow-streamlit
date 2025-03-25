import streamlit as st
from datetime import date, datetime, timedelta

def render_sidebar():
    """
    Render the sidebar for navigation and filters
    
    Returns:
        str: The current selected view
    """
    st.sidebar.title("Navigation")
    
    # Main navigation
    view_options = [
        "Dashboard",
        "People",
        "Teams",
        "Projects", 
        "Demand",
        "Allocations"
    ]
    
    current_view = st.sidebar.radio("View", view_options)
    
    # Add date filters for relevant views
    if current_view in ["Dashboard", "Demand", "Allocations"]:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Date Filters")
        
        # Get current date and set default date ranges
        today = date.today()
        current_year = today.year
        current_month = today.month
        
        # Calculate default date ranges
        if "date_range" not in st.session_state:
            # Default to current quarter
            quarter = (current_month - 1) // 3 + 1
            quarter_start_month = (quarter - 1) * 3 + 1
            
            default_start_date = date(current_year, quarter_start_month, 1)
            if quarter == 4:
                default_end_date = date(current_year, 12, 31)
            else:
                default_end_date = date(current_year, quarter_start_month + 3, 1) - timedelta(days=1)
            
            st.session_state.date_range = (default_start_date, default_end_date)
        
        # Date range options
        date_range_options = [
            "Current Month",
            "Current Quarter",
            "Current Year",
            "Next 3 Months",
            "Next 6 Months",
            "Next 12 Months",
            "Custom Range"
        ]
        
        selected_range = st.sidebar.selectbox(
            "Preset Ranges",
            date_range_options,
            index=1  # Default to Current Quarter
        )
        
        # Set date range based on selection
        if selected_range == "Current Month":
            month_start = date(today.year, today.month, 1)
            if today.month == 12:
                month_end = date(today.year, 12, 31)
            else:
                month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
            st.session_state.date_range = (month_start, month_end)
            
        elif selected_range == "Current Quarter":
            quarter = (today.month - 1) // 3 + 1
            quarter_start_month = (quarter - 1) * 3 + 1
            
            quarter_start = date(today.year, quarter_start_month, 1)
            if quarter == 4:
                quarter_end = date(today.year, 12, 31)
            else:
                quarter_end = date(today.year, quarter_start_month + 3, 1) - timedelta(days=1)
            
            st.session_state.date_range = (quarter_start, quarter_end)
            
        elif selected_range == "Current Year":
            year_start = date(today.year, 1, 1)
            year_end = date(today.year, 12, 31)
            st.session_state.date_range = (year_start, year_end)
            
        elif selected_range == "Next 3 Months":
            start_date = today
            if today.month + 3 > 12:
                end_month = (today.month + 3) % 12
                end_year = today.year + 1
            else:
                end_month = today.month + 3
                end_year = today.year
            
            end_date = date(end_year, end_month, 1) - timedelta(days=1)
            st.session_state.date_range = (start_date, end_date)
            
        elif selected_range == "Next 6 Months":
            start_date = today
            if today.month + 6 > 12:
                end_month = (today.month + 6) % 12
                end_year = today.year + 1
            else:
                end_month = today.month + 6
                end_year = today.year
            
            end_date = date(end_year, end_month, 1) - timedelta(days=1)
            st.session_state.date_range = (start_date, end_date)
            
        elif selected_range == "Next 12 Months":
            start_date = today
            end_date = date(today.year + 1, today.month, 1) - timedelta(days=1)
            st.session_state.date_range = (start_date, end_date)
            
        elif selected_range == "Custom Range":
            col1, col2 = st.sidebar.columns(2)
            with col1:
                start_date = st.date_input("Start Date", st.session_state.date_range[0])
            with col2:
                end_date = st.date_input("End Date", st.session_state.date_range[1])
            
            if start_date and end_date:
                if start_date > end_date:
                    st.sidebar.error("Start date must be before end date")
                else:
                    st.session_state.date_range = (start_date, end_date)
    
    # Add global project filter for relevant views
    if current_view in ["Dashboard", "Demand", "Allocations"]:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Project Filter")
        
        # This would typically come from the database
        # For now, we'll set a session state placeholder
        if "selected_projects" not in st.session_state:
            st.session_state.selected_projects = []
        
        if "all_projects" not in st.session_state:
            st.session_state.all_projects = []
            
            # We would populate this from the database in a real app
            # For now, let's set a default
            # This will be replaced when projects are loaded
            # if no projects exist yet
            if not st.session_state.all_projects:
                st.session_state.all_projects = ["All Projects"]
        
        selected_project = st.sidebar.selectbox(
            "Filter by Project",
            ["All Projects"] + [p for p in st.session_state.all_projects if p != "All Projects"],
            index=0
        )
        
        if selected_project != "All Projects":
            st.session_state.selected_projects = [selected_project]
        else:
            st.session_state.selected_projects = []
    
    # Add information section
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Resource Flow**
    
    A lightweight resource planning application
    
    Built with Streamlit, DuckDB, and Polars
    """)
    
    return current_view 