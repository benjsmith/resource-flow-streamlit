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
        
        # Get people and project names for display
        person_map = {person.id: person.name for person in people}
        project_map = {project.id: project.name for project in projects}
        
        # Get demands for reference
        all_demands = db.get_demands()
        demand_map = {demand.id: f"{project_map.get(demand.project_id, 'Unknown')} - {demand.role_required}" for demand in all_demands}
        
        # Convert to DataFrame for display
        if allocations:
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
        else:
            st.info("No allocations found matching the selected criteria. Please add some allocations to get started.")
    
    with tab2:
        st.subheader("Add/Edit Allocation")
        
        # Initialize the allocation object
        if "edit_allocation_id" in st.session_state:
            # Editing an existing allocation
            allocation = db.get_allocation(st.session_state.edit_allocation_id)
            if not allocation:
                st.error("Allocation not found")
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
                    "Link to Demand (optional)",
                    options=[name for name, _ in demand_options],
                    index=min(demand_index, len(demand_options) - 1)
                )
                
                # Update the demand_id based on selection
                for name, id in demand_options:
                    if name == selected_demand:
                        allocation.demand_id = id
                        break
            
            fte_allocated = st.number_input("FTE Allocated", min_value=0.1, max_value=1.0, value=allocation.fte_allocated, step=0.1)
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=allocation.start_date or date.today())
            
            with col2:
                end_date = st.date_input("End Date", value=allocation.end_date or (date.today() + timedelta(days=90)))
            
            notes = st.text_area("Notes", value=allocation.notes or "", height=100)
            
            if editing:
                submit_label = "Update Allocation"
            else:
                submit_label = "Add Allocation"
            
            submitted = st.form_submit_button(submit_label)
            
            if submitted:
                # Validate dates
                if end_date < start_date:
                    st.error("End date must be after start date")
                elif not allocation.person_id:
                    st.error("Please select a person")
                elif not allocation.project_id:
                    st.error("Please select a project")
                else:
                    # Update allocation object
                    allocation.fte_allocated = fte_allocated
                    allocation.start_date = start_date
                    allocation.end_date = end_date
                    allocation.notes = notes
                    
                    # Save to database
                    saved_allocation = db.save_allocation(allocation)
                    
                    if saved_allocation:
                        # Update demand status if allocated to a demand
                        if allocation.demand_id:
                            # Get the demand
                            demand = db.get_demand(allocation.demand_id)
                            
                            # Get all allocations for this demand
                            demand_allocations = db.get_allocations(demand_id=allocation.demand_id)
                            
                            if demand and demand_allocations:
                                # Calculate total allocated FTE
                                total_allocated = sum(a.fte_allocated for a in demand_allocations)
                                
                                # Update demand status based on allocation
                                if total_allocated >= demand.fte_required * 0.9:
                                    # Consider filled if at least 90% allocated
                                    demand.status = "filled"
                                elif total_allocated > 0:
                                    demand.status = "partially_filled"
                                else:
                                    demand.status = "unfilled"
                                
                                # Save updated demand
                                db.save_demand(demand)
                        
                        # Update the monthly demand allocation table
                        db.update_monthly_allocations()
                        
                        if editing:
                            st.success(f"Allocation updated successfully")
                        else:
                            st.success(f"Allocation added successfully")
                        
                        # Clear the edit allocation ID
                        if "edit_allocation_id" in st.session_state:
                            del st.session_state.edit_allocation_id
                    else:
                        st.error("Error saving allocation")
    
    with tab3:
        st.subheader("Allocation Timeline")
        
        # Get date range from session state
        start_date, end_date = st.session_state.date_range
        
        # Get allocations for Gantt chart in the date range
        allocations = db.get_allocations()
        
        if allocations:
            # Get people and project names
            people = db.get_people()
            projects = db.get_projects()
            
            person_map = {person.id: person.name for person in people}
            project_map = {project.id: project.name for project in projects}
            
            # Convert to DataFrame for Gantt chart
            allocations_data = []
            for alloc in allocations:
                # Only include allocations that overlap with the date range
                if not (alloc.end_date < start_date or alloc.start_date > end_date):
                    allocations_data.append({
                        "id": alloc.id,
                        "person_id": alloc.person_id,
                        "person_name": person_map.get(alloc.person_id, "Unknown"),
                        "project_id": alloc.project_id,
                        "project_name": project_map.get(alloc.project_id, "Unknown"),
                        "fte_allocated": alloc.fte_allocated,
                        "start_date": max(alloc.start_date, start_date),  # Clip to date range
                        "end_date": min(alloc.end_date, end_date),        # Clip to date range
                        "notes": alloc.notes or ""
                    })
            
            df_allocations = pd.DataFrame(allocations_data)
            
            # Create Gantt chart
            if not df_allocations.empty and "start_date" in df_allocations.columns and "end_date" in df_allocations.columns:
                fig = create_allocation_gantt(df_allocations)
                st.plotly_chart(fig, use_container_width=True)
                
                # Add legend explanation
                st.markdown("""
                **Note:**
                - Bar width represents FTE allocation amount
                - Colors represent different projects
                - Red vertical line represents today's date
                """)
            else:
                st.info("Allocation data is incomplete. Please ensure all allocations have start and end dates.")
        else:
            st.info("No allocations found. Please add some allocations to see the timeline.") 