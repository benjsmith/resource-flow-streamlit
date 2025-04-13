import streamlit as st
import pandas as pd
from datetime import date, timedelta

from app.database import queries as db
from app.models.data_models import Allocation
from app.visualizations.gantt_chart import create_allocation_gantt
from app.utils.plotly_utils import prepare_figure_for_streamlit

def render_allocations_view():
    """Render the resource allocations management view."""
    st.header("Resource Allocations Management")
    
    # Create tabs for different actions
    tab1, tab2 = st.tabs(["Allocations List", "Allocation Timeline"])
    
    with tab1:
        render_allocations_list()
    
    with tab2:
        render_allocation_timeline()

def render_allocations_list():
    """Render a list of allocations with actions."""
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
    
    # Add a button to create a new allocation
    if st.button("Add New Allocation", key="add_allocation_button"):
        st.session_state.show_allocation_form = True
        st.session_state.editing_allocation = None
    
    # Get allocations based on filters
    allocations = db.get_allocations(person_id=selected_person_id, project_id=selected_project_id)
    
    # Display allocations in a dataframe
    if allocations:
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
        
        # Display in a dataframe
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Selection for editing
        selected_allocation_id = st.selectbox(
            "Select an allocation to edit:",
            options=[a.id for a in allocations],
            format_func=lambda x: next((f"{a.person_name} - {a.project_name}" for a in allocations if a.id == x), ""),
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Edit Selected Allocation", use_container_width=True):
                st.session_state.show_allocation_form = True
                st.session_state.editing_allocation = next((a for a in allocations if a.id == selected_allocation_id), None)
                st.rerun()
        
        with col2:
            if st.button("Delete Selected Allocation", use_container_width=True):
                # Confirm deletion
                st.session_state.confirm_delete_allocation = selected_allocation_id
                st.rerun()
    else:
        st.info("No allocations found matching the selected criteria. Add some allocations to get started.")
    
    # Handle delete confirmation
    if "confirm_delete_allocation" in st.session_state and st.session_state.confirm_delete_allocation:
        allocation_id = st.session_state.confirm_delete_allocation
        allocation = next((a for a in allocations if a.id == allocation_id), None)
        
        if allocation:
            st.warning(f"Are you sure you want to delete the allocation for {allocation.person_name} in {allocation.project_name}?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete", type="primary"):
                    if db.delete_allocation(allocation_id):
                        st.success("Allocation deleted successfully!")
                        st.session_state.confirm_delete_allocation = None
                        st.rerun()
                    else:
                        st.error("Failed to delete allocation.")
            
            with col2:
                if st.button("Cancel"):
                    st.session_state.confirm_delete_allocation = None
                    st.rerun()
    
    # Show form for adding/editing an allocation
    if "show_allocation_form" in st.session_state and st.session_state.show_allocation_form:
        render_allocation_form(st.session_state.editing_allocation)

def render_allocation_timeline():
    """Render a timeline view of allocations."""
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
    st.plotly_chart(prepare_figure_for_streamlit(fig), use_container_width=True)

def render_allocation_form(allocation=None):
    """Render a form for adding or editing an allocation."""
    is_edit = allocation is not None
    form_title = "Edit Allocation" if is_edit else "Add New Allocation"
    
    st.subheader(form_title)
    
    with st.form(key="allocation_form"):
        # Person selection
        people = db.get_people()
        person_options = [(person.name, person.id) for person in people]
        
        if not person_options:
            st.error("No people available. Please add a person first.")
            return
        
        # Find the current person index
        person_index = 0
        if is_edit:
            for i, (person_name, person_id) in enumerate(person_options):
                if person_id == allocation.person_id:
                    person_index = i
                    break
        
        selected_person = st.selectbox(
            "Person",
            options=[name for name, _ in person_options],
            index=min(person_index, len(person_options) - 1)
        )
        person_id = next((id for name, id in person_options if name == selected_person), None)
        
        # Project selection
        projects = db.get_projects()
        project_options = [(project.name, project.id) for project in projects]
        
        if not project_options:
            st.error("No projects available. Please add a project first.")
            return
        
        # Find the current project index
        project_index = 0
        if is_edit:
            for i, (project_name, project_id) in enumerate(project_options):
                if project_id == allocation.project_id:
                    project_index = i
                    break
        
        selected_project = st.selectbox(
            "Project",
            options=[name for name, _ in project_options],
            index=min(project_index, len(project_options) - 1)
        )
        project_id = next((id for name, id in project_options if name == selected_project), None)
        
        # Demand selection (optional)
        demands = db.get_demands(project_id=project_id)
        demand_options = [(None, "Direct Allocation")] + [(demand.id, f"{demand.role_required} ({demand.fte_required} FTE)") for demand in demands]
        
        # Find the current demand index
        demand_index = 0
        if is_edit:
            for i, (demand_id, _) in enumerate(demand_options):
                if demand_id == allocation.demand_id:
                    demand_index = i
                    break
        
        selected_demand = st.selectbox(
            "Demand (Optional)",
            options=[name for _, name in demand_options],
            index=min(demand_index, len(demand_options) - 1)
        )
        demand_id = next((id for id, name in demand_options if name == selected_demand), None)
        
        # FTE and dates
        col1, col2 = st.columns(2)
        with col1:
            fte = st.number_input(
                "FTE Allocated",
                min_value=0.0,
                max_value=1.0,
                value=allocation.fte_allocated if is_edit else 0.5,
                step=0.1
            )
            
            start_date = st.date_input(
                "Start Date",
                value=allocation.start_date if is_edit else date.today()
            )
        
        with col2:
            notes = st.text_area(
                "Notes",
                value=allocation.notes if is_edit else ""
            )
            
            end_date = st.date_input(
                "End Date",
                value=allocation.end_date if is_edit else date.today() + timedelta(days=90)
            )
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Save", use_container_width=True)
        with col2:
            cancel_button = st.form_submit_button("Cancel", use_container_width=True)
        
        if submit_button:
            if end_date < start_date:
                st.error("End date must be after start date")
            else:
                # Create or update allocation
                if is_edit:
                    allocation.person_id = person_id
                    allocation.project_id = project_id
                    allocation.demand_id = demand_id
                    allocation.fte_allocated = fte
                    allocation.start_date = start_date
                    allocation.end_date = end_date
                    allocation.notes = notes
                    allocation_id = db.save_allocation(allocation)
                else:
                    new_allocation = Allocation(
                        person_id=person_id,
                        project_id=project_id,
                        demand_id=demand_id,
                        fte_allocated=fte,
                        start_date=start_date,
                        end_date=end_date,
                        notes=notes
                    )
                    allocation_id = db.save_allocation(new_allocation)
                
                if allocation_id:
                    st.success("Allocation saved successfully!")
                    st.session_state.show_allocation_form = False
                    st.rerun()
                else:
                    st.error("Failed to save allocation")
        
        if cancel_button:
            st.session_state.show_allocation_form = False
            st.rerun() 