import streamlit as st
import pandas as pd
import uuid
from datetime import date
import plotly.graph_objects as go

from app.database import queries as db
from app.models.data_models import Demand
from app.visualizations.gantt_chart import create_demand_gantt
from app.utils.plotly_utils import prepare_figure_for_streamlit

def render_demand_view():
    """
    Render the demand management view
    """
    st.header("Resource Demand Management")
    
    # Create tabs for different actions
    tab1, tab2 = st.tabs(["Demand List", "Demand Timeline"])
    
    with tab1:
        render_demand_list()
    
    with tab2:
        render_demand_timeline()

def render_demand_list():
    """
    Render a list of demands with actions.
    """
    # Add a button to create a new demand
    if st.button("Add New Demand", key="add_demand_button"):
        st.session_state.show_demand_form = True
        st.session_state.editing_demand = None
    
    # Get all demands for display
    demands = db.get_demands()
    
    # Display demands in a dataframe
    if demands:
        # Convert to dataframe for display
        demands_data = []
        for demand in demands:
            demands_data.append({
                "ID": demand.id,
                "Project": demand.project_name,
                "Role Required": demand.role_required,
                "FTE Required": demand.fte_required,
                "Start Date": demand.start_date,
                "End Date": demand.end_date,
                "Status": demand.status,
                "Priority": demand.priority
            })
        
        df = pd.DataFrame(demands_data)
        
        # Display in a dataframe
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Selection for editing
        selected_demand_id = st.selectbox(
            "Select a demand to edit:",
            options=[d.id for d in demands],
            format_func=lambda x: next((f"{d.project_name} - {d.role_required}" for d in demands if d.id == x), ""),
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Edit Selected Demand", use_container_width=True):
                st.session_state.show_demand_form = True
                st.session_state.editing_demand = next((d for d in demands if d.id == selected_demand_id), None)
                st.rerun()
        
        with col2:
            if st.button("Delete Selected Demand", use_container_width=True):
                # Confirm deletion
                st.session_state.confirm_delete_demand = selected_demand_id
                st.rerun()
    else:
        st.info("No demands found. Add some demands to get started.")
    
    # Handle delete confirmation
    if "confirm_delete_demand" in st.session_state and st.session_state.confirm_delete_demand:
        demand_id = st.session_state.confirm_delete_demand
        demand = next((d for d in demands if d.id == demand_id), None)
        
        if demand:
            st.warning(f"Are you sure you want to delete the demand for {demand.role_required} in {demand.project_name}?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete", type="primary"):
                    if db.delete_demand(demand_id):
                        st.success("Demand deleted successfully!")
                        st.session_state.confirm_delete_demand = None
                        st.rerun()
                    else:
                        st.error("Failed to delete demand.")
            
            with col2:
                if st.button("Cancel"):
                    st.session_state.confirm_delete_demand = None
                    st.rerun()
    
    # Show form for adding/editing a demand
    if "show_demand_form" in st.session_state and st.session_state.show_demand_form:
        render_demand_form(st.session_state.editing_demand)

def render_demand_timeline():
    """
    Render a timeline view of demands.
    """
    # Get date range from session state
    start_date, end_date = st.session_state.date_range
    
    # Get all demands
    demands = db.get_demands()
    
    if not demands:
        st.info("No demands found. Add some demands to see the timeline.")
        return
    
    # Filter demands by date if needed
    if start_date and end_date:
        filtered_demands = [
            d for d in demands 
            if (d.end_date and d.end_date >= start_date) and 
               (d.start_date and d.start_date <= end_date)
        ]
    else:
        filtered_demands = demands
    
    if not filtered_demands:
        st.info("No demands found in the selected date range.")
        return
    
    # Create Gantt chart
    fig = create_demand_gantt(filtered_demands)
    
    # Display the chart
    st.plotly_chart(prepare_figure_for_streamlit(fig), use_container_width=True)

def render_demand_form(demand=None):
    """
    Render a form for adding or editing a demand.
    """
    is_edit = demand is not None
    form_title = "Edit Demand" if is_edit else "Add New Demand"
    
    st.subheader(form_title)
    
    with st.form(key="demand_form"):
        # Get projects for dropdown
        projects = db.get_projects()
        project_options = [p.name for p in projects]
        
        if is_edit:
            # For editing, find the index of the current project
            project_index = project_options.index(demand.project_name) if demand.project_name in project_options else 0
            project_name = st.selectbox("Project", options=project_options, index=project_index)
        else:
            # For adding, just show the dropdown
            project_name = st.selectbox("Project", options=project_options, index=0 if project_options else None)
        
        # Get the project ID from the name
        project_id = next((p.id for p in projects if p.name == project_name), None)
        
        # Form inputs
        role_required = st.text_input("Role Required", value=demand.role_required if is_edit else "")
        fte_required = st.number_input("FTE Required", min_value=0.1, max_value=5.0, value=demand.fte_required if is_edit else 1.0, step=0.1)
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=demand.start_date if is_edit and demand.start_date else date.today())
        with col2:
            end_date = st.date_input("End Date", value=demand.end_date if is_edit and demand.end_date else date.today())
        
        status_options = ["open", "filled", "partially_filled", "cancelled"]
        status = st.selectbox(
            "Status", 
            options=status_options,
            index=status_options.index(demand.status) if is_edit else 0
        )
        
        priority_options = ["high", "medium", "low"]
        priority = st.selectbox(
            "Priority", 
            options=priority_options,
            index=priority_options.index(demand.priority) if is_edit else 0
        )
        
        notes = st.text_area("Notes", value=demand.notes if is_edit and demand.notes else "")
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Save", use_container_width=True)
        with col2:
            cancel_button = st.form_submit_button("Cancel", use_container_width=True)
        
        if submit_button:
            if not project_id:
                st.error("Please select a project.")
                return
            
            if not role_required:
                st.error("Role Required is mandatory.")
                return
            
            if start_date > end_date:
                st.error("Start date must be before end date.")
                return
            
            # Create or update demand
            if is_edit:
                demand_obj = Demand(
                    id=demand.id,
                    project_id=project_id,
                    role_required=role_required,
                    fte_required=fte_required,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    priority=priority,
                    notes=notes
                )
            else:
                demand_obj = Demand(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    role_required=role_required,
                    fte_required=fte_required,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    priority=priority,
                    notes=notes
                )
            
            # Save to database
            if db.save_demand(demand_obj):
                st.success(f"Demand {'updated' if is_edit else 'added'} successfully!")
                st.session_state.show_demand_form = False
                st.session_state.editing_demand = None
                st.rerun()
            else:
                st.error(f"Failed to {'update' if is_edit else 'add'} demand.")
        
        if cancel_button:
            st.session_state.show_demand_form = False
            st.session_state.editing_demand = None
            st.rerun() 