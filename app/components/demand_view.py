import streamlit as st
import pandas as pd
from datetime import date, timedelta

from app.database import queries as db
from app.models.data_models import Demand
from app.visualizations.gantt_chart import create_demand_gantt

def render_demand_view():
    """
    Render the demand management view
    """
    st.header("Resource Demand Management")
    
    # Create tabs for different actions
    tab1, tab2, tab3 = st.tabs(["Demand List", "Add/Edit Demand", "Demand Timeline"])
    
    with tab1:
        # Add filters for demand view
        col1, col2 = st.columns(2)
        
        with col1:
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
        
        with col2:
            # Status filter
            status_options = ["All", "unfilled", "partially_filled", "filled"]
            selected_status = st.selectbox("Filter by Status", status_options)
            status_filter = None if selected_status == "All" else selected_status
        
        # Get demands based on filters
        demands = db.get_demands(project_id=selected_project_id, status_filter=status_filter)
        
        # Get project names for display
        project_map = {project.id: project.name for project in projects}
        
        # Convert to DataFrame for display
        if demands:
            demands_data = []
            for demand in demands:
                demands_data.append({
                    "ID": demand.id,
                    "Project": project_map.get(demand.project_id, "Unknown"),
                    "Role Required": demand.role_required,
                    "Skills Required": demand.skills_required,
                    "FTE Required": demand.fte_required,
                    "Start Date": demand.start_date,
                    "End Date": demand.end_date,
                    "Status": demand.status,
                    "Priority": demand.priority
                })
            
            df = pd.DataFrame(demands_data)
            
            # Display demands
            st.dataframe(df, use_container_width=True)
            
            # Add actions for selected demand
            st.subheader("Actions")
            
            cols = st.columns(3)
            with cols[0]:
                demand_id = st.number_input("Demand ID", min_value=1, step=1)
            
            with cols[1]:
                view_allocations = st.button("View Allocations")
            
            with cols[2]:
                edit_demand = st.button("Edit Demand")
            
            if view_allocations and demand_id:
                # Get the demand
                demand = db.get_demand(demand_id)
                if demand:
                    st.subheader(f"Allocations for Demand #{demand_id}")
                    
                    # Get allocations for the demand
                    allocations = db.get_allocations(demand_id=demand_id)
                    
                    if allocations:
                        # Get people information
                        people = db.get_people()
                        person_map = {p.id: p.name for p in people}
                        
                        # Convert to DataFrame for display
                        alloc_data = []
                        for alloc in allocations:
                            alloc_data.append({
                                "ID": alloc.id,
                                "Person": person_map.get(alloc.person_id, "Unknown"),
                                "FTE": alloc.fte_allocated,
                                "Start Date": alloc.start_date,
                                "End Date": alloc.end_date,
                                "Notes": alloc.notes
                            })
                        
                        df_alloc = pd.DataFrame(alloc_data)
                        st.dataframe(df_alloc, use_container_width=True)
                    else:
                        st.info(f"No allocations found for this demand")
                else:
                    st.error("Demand not found")
            
            if edit_demand and demand_id:
                # Store the demand ID in session state for editing
                st.session_state.edit_demand_id = demand_id
                # Switch to the Add/Edit tab
                st.rerun()
        else:
            st.info("No demands found matching the selected criteria. Please add some demands to get started.")
    
    with tab2:
        st.subheader("Add/Edit Demand")
        
        # Initialize the demand object
        if "edit_demand_id" in st.session_state:
            # Editing an existing demand
            demand = db.get_demand(st.session_state.edit_demand_id)
            if not demand:
                st.error("Demand not found")
                return
            editing = True
        else:
            # Creating a new demand
            today = date.today()
            demand = Demand(
                id=None, 
                project_id=None,
                role_required="", 
                skills_required="", 
                fte_required=1.0, 
                start_date=today, 
                end_date=today + timedelta(days=90), 
                priority="medium",
                status="unfilled"
            )
            editing = False
        
        # Create the form
        with st.form("demand_form"):
            # Project selection
            projects = db.get_projects()
            project_options = [(project.name, project.id) for project in projects]
            
            if not project_options:
                st.error("No projects available. Please create a project first.")
                return
            
            # Find the current project index
            project_index = 0
            for i, (project_name, project_id) in enumerate(project_options):
                if project_id == demand.project_id:
                    project_index = i
                    break
            
            if project_options:
                selected_project = st.selectbox(
                    "Project",
                    options=[name for name, _ in project_options],
                    index=min(project_index, len(project_options) - 1)
                )
                
                # Update the project_id based on selection
                for name, id in project_options:
                    if name == selected_project:
                        demand.project_id = id
                        break
            
            role_required = st.text_input("Role Required", value=demand.role_required or "")
            skills_required = st.text_area("Skills Required", value=demand.skills_required or "", height=100)
            fte_required = st.number_input("FTE Required", min_value=0.1, max_value=10.0, value=demand.fte_required or 1.0, step=0.1)
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=demand.start_date or date.today())
            
            with col2:
                end_date = st.date_input("End Date", value=demand.end_date or (date.today() + timedelta(days=90)))
            
            col1, col2 = st.columns(2)
            with col1:
                priority = st.selectbox(
                    "Priority",
                    options=["high", "medium", "low"],
                    index=["high", "medium", "low"].index(demand.priority or "medium")
                )
            
            with col2:
                status = st.selectbox(
                    "Status",
                    options=["unfilled", "partially_filled", "filled"],
                    index=["unfilled", "partially_filled", "filled"].index(demand.status or "unfilled")
                )
            
            if editing:
                submit_label = "Update Demand"
            else:
                submit_label = "Add Demand"
            
            submitted = st.form_submit_button(submit_label)
            
            if submitted:
                # Validate dates
                if end_date < start_date:
                    st.error("End date must be after start date")
                elif not demand.project_id:
                    st.error("Please select a project")
                else:
                    # Update demand object
                    demand.role_required = role_required
                    demand.skills_required = skills_required
                    demand.fte_required = fte_required
                    demand.start_date = start_date
                    demand.end_date = end_date
                    demand.priority = priority
                    demand.status = status
                    
                    # Save to database
                    saved_demand = db.save_demand(demand)
                    
                    if saved_demand:
                        # Update the monthly demand allocation table
                        db.update_monthly_allocations()
                        
                        if editing:
                            st.success(f"Demand updated successfully")
                        else:
                            st.success(f"Demand added successfully")
                        
                        # Clear the edit demand ID
                        if "edit_demand_id" in st.session_state:
                            del st.session_state.edit_demand_id
                    else:
                        st.error("Error saving demand")
    
    with tab3:
        st.subheader("Demand Timeline")
        
        # Get demands for Gantt chart
        demands = db.get_demands()
        
        if demands:
            # Get project names
            projects = db.get_projects()
            project_map = {project.id: project.name for project in projects}
            
            # Convert to DataFrame for Gantt chart
            demands_data = []
            for demand in demands:
                demands_data.append({
                    "id": demand.id,
                    "project_id": demand.project_id,
                    "project_name": project_map.get(demand.project_id, "Unknown"),
                    "role_required": demand.role_required or "Unspecified Role",
                    "skills_required": demand.skills_required or "",
                    "fte_required": demand.fte_required,
                    "start_date": demand.start_date,
                    "end_date": demand.end_date,
                    "status": demand.status,
                    "priority": demand.priority
                })
            
            df_demands = pd.DataFrame(demands_data)
            
            # Create Gantt chart
            if not df_demands.empty and "start_date" in df_demands.columns and "end_date" in df_demands.columns:
                fig = create_demand_gantt(df_demands)
                st.plotly_chart(fig, use_container_width=True)
                
                # Add legend explanation
                st.markdown("""
                **Legend:**
                - **Red**: Unfilled demand
                - **Orange**: Partially filled demand
                - **Green**: Filled demand
                
                *Bar width represents FTE amount*
                """)
            else:
                st.info("Demand data is incomplete. Please ensure all demands have start and end dates.")
        else:
            st.info("No demands found. Please add some demands to see the timeline.") 