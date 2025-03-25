import streamlit as st
import pandas as pd
from datetime import date, timedelta

from app.database import queries as db
from app.models.data_models import Allocation
from app.visualizations.gantt_chart import create_allocation_gantt

def render_allocations_view():
    """
    Render the resource allocations management view
    """
    st.header("Resource Allocations Management")
    
    # Create tabs for different actions
    tab1, tab2, tab3 = st.tabs(["Allocations List", "Add/Edit Allocation", "Allocation Timeline"])
    
    with tab1:
        render_allocations_list()
    
    with tab2:
        render_allocation_form()
    
    with tab3:
        render_allocation_timeline()

def render_allocations_list():
    """Render the list of allocations with filters and actions."""
    # Add filters for allocations view
    col1, col2 = st.columns(2)
    
    with col1:
        # Person filter
        people = db.get_people()
        person_options = [("All People", None)] + [(person.name, person.id) for person in people]
        
        selected_person_name = st.selectbox(
            "Filter by Person",
            options=[name for name, _ in person_options],
            index=0
        )
        
        # Get the selected person ID
        selected_person_id = None
        for name, id in person_options:
            if name == selected_person_name:
                selected_person_id = id
                break
    
    with col2:
        # Project filter
        projects = db.get_projects()
        project_options = [("All Projects", None)] + [(project.name, project.id) for project in projects]
        
        selected_project_name = st.selectbox(
            "Filter by Project",
            options=[name for name, _ in project_options],
            index=0
        )
        
        # Get the selected project ID
        selected_project_id = None
        for name, id in project_options:
            if name == selected_project_name:
                selected_project_id = id
                break
    
    # Get allocations based on filters
    allocations = db.get_allocations(person_id=selected_person_id, project_id=selected_project_id)
    
    if not allocations:
        st.info("No allocations found matching the selected criteria. Please add some allocations to get started.")
        return
    
    # Get people and project names for display
    person_map = {person.id: person.name for person in people}
    project_map = {project.id: project.name for project in projects}
    
    # Get demands for reference
    all_demands = db.get_demands()
    demand_map = {demand.id: f"{project_map.get(demand.project_id, 'Unknown')} - {demand.role_required}" for demand in all_demands}
    
    # Convert to DataFrame for display
    allocations_data = []
    for alloc in allocations:
        allocations_data.append({
            "ID": alloc.id,
            "Person": person_map.get(alloc.person_id, "Unknown"),
            "Project": project_map.get(alloc.project_id, "Unknown"),
            "Demand": demand_map.get(alloc.demand_id, "Direct Allocation") if alloc.demand_id else "Direct Allocation",
            "FTE": alloc.fte_allocated,
            "Start Date": alloc.start_date,
            "End Date": alloc.end_date,
            "Notes": alloc.notes
        })
    
    df = pd.DataFrame(allocations_data)
    
    # Display allocations
    st.dataframe(df, use_container_width=True)
    
    # Add actions for selected allocation
    st.subheader("Actions")
    
    cols = st.columns(2)
    with cols[0]:
        allocation_id = st.number_input("Allocation ID", min_value=1, step=1)
    
    with cols[1]:
        edit_allocation = st.button("Edit Allocation")
    
    if edit_allocation and allocation_id:
        # Store the allocation ID in session state for editing
        st.session_state.edit_allocation_id = allocation_id
        # Switch to the Add/Edit tab
        st.rerun()

def render_allocation_timeline():
    """Render the allocation timeline view."""
    # Get date range from session state
    start_date, end_date = st.session_state.date_range
    
    # Get all allocations
    allocations = db.get_allocations()
    
    if not allocations:
        st.info("No allocations found. Add some allocations to see the timeline.")
        return
    
    # Create Gantt chart
    fig = create_allocation_gantt(allocations)
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

def render_allocation_form():
    """Render the form for adding or editing an allocation."""
    st.subheader("Add/Edit Allocation")
    
    # Add clear button at the top of the form if in edit mode
    if "edit_allocation_id" in st.session_state and st.session_state.edit_allocation_id is not None:
        if st.button("Clear Form (Add New Allocation)"):
            st.session_state.edit_allocation_id = None
            st.rerun()
    
    # Initialize the allocation object
    if "edit_allocation_id" in st.session_state and st.session_state.edit_allocation_id:
        # Editing an existing allocation
        allocation = db.get_allocation(st.session_state.edit_allocation_id)
        if not allocation:
            st.error(f"Allocation with ID {st.session_state.edit_allocation_id} not found")
            st.session_state.edit_allocation_id = None
            st.rerun()
            return
        editing = True
    else:
        # Creating a new allocation
        today = date.today()
        allocation = Allocation(
            id=None, 
            person_id=None,
            project_id=None,
            demand_id=None,
            fte_allocated=0.5, 
            start_date=today, 
            end_date=today + timedelta(days=90),
            notes=""
        )
        editing = False
    
    # Create the form
    with st.form("allocation_form"):
        # Person selection
        people = db.get_people()
        person_options = [(person.name, person.id) for person in people]
        
        if not person_options:
            st.error("No people available. Please add a person first.")
            return
        
        # Find the current person index
        person_index = 0
        for i, (person_name, person_id) in enumerate(person_options):
            if person_id == allocation.person_id:
                person_index = i
                break
        
        selected_person = st.selectbox(
            "Person",
            options=[name for name, _ in person_options],
            index=min(person_index, len(person_options) - 1)
        )
        
        # Update the person_id based on selection
        for name, id in person_options:
            if name == selected_person:
                allocation.person_id = id
                break
        
        # Project selection
        projects = db.get_projects()
        project_options = [(project.name, project.id) for project in projects]
        
        if not project_options:
            st.error("No projects available. Please create a project first.")
            return
        
        # Find the current project index
        project_index = 0
        for i, (project_name, project_id) in enumerate(project_options):
            if project_id == allocation.project_id:
                project_index = i
                break
        
        selected_project = st.selectbox(
            "Project",
            options=[name for name, _ in project_options],
            index=min(project_index, len(project_options) - 1)
        )
        
        # Update the project_id based on selection
        selected_project_id = None
        for name, id in project_options:
            if name == selected_project:
                allocation.project_id = id
                selected_project_id = id
                break
        
        # Demand selection (optional)
        if selected_project_id:
            demands = db.get_demands(project_id=selected_project_id)
            demand_options = [("None/Direct Allocation", None)] + [
                (f"{demand.role_required} ({demand.fte_required} FTE, {demand.start_date} to {demand.end_date})", 
                 demand.id) 
                for demand in demands
            ]
            
            # Find the current demand index
            demand_index = 0
            for i, (demand_name, demand_id) in enumerate(demand_options):
                if demand_id == allocation.demand_id:
                    demand_index = i
                    break
            
            selected_demand = st.selectbox(
                "Link to Demand (Optional)",
                options=[name for name, _ in demand_options],
                index=demand_index
            )
            
            # Update the demand_id based on selection
            for name, id in demand_options:
                if name == selected_demand:
                    allocation.demand_id = id
                    break
        
        # FTE allocation
        fte_allocated = st.number_input(
            "FTE Allocated",
            min_value=0.1,
            max_value=1.0,
            value=allocation.fte_allocated,
            step=0.1
        )
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=allocation.start_date)
        with col2:
            end_date = st.date_input("End Date", value=allocation.end_date)
        
        # Notes
        notes = st.text_area("Notes", value=allocation.notes or "", height=100)
        
        submitted = st.form_submit_button("Save Allocation")
        
        if submitted:
            if not allocation.person_id:
                st.error("Person is required")
            elif not allocation.project_id:
                st.error("Project is required")
            elif end_date < start_date:
                st.error("End date must be after start date")
            else:
                # Update allocation object
                allocation.fte_allocated = fte_allocated
                allocation.start_date = start_date
                allocation.end_date = end_date
                allocation.notes = notes
                
                # Save to database
                allocation_id = db.save_allocation(allocation)
                
                if allocation_id:
                    action = "updated" if editing else "added"
                    st.success(f"Allocation {action} successfully")
                    
                    # Clear the edit allocation ID
                    if editing:
                        st.session_state.edit_allocation_id = None
                        st.rerun()
                else:
                    st.error("Failed to save allocation") 