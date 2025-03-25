import streamlit as st
import pandas as pd
from datetime import date, timedelta

from app.database.queries import DatabaseQueries
from app.database.models import Project
from app.visualizations.gantt_chart import create_project_gantt

def render_projects_view():
    """
    Render the projects management view
    """
    # Set up database connection
    db_path = "resource_flow.duckdb"
    db = DatabaseQueries(db_path)
    
    st.header("Projects Management")
    
    # Create tabs for different actions
    tab1, tab2, tab3 = st.tabs(["Projects List", "Add/Edit Project", "Project Timeline"])
    
    with tab1:
        # Add filter for project status
        status_options = ["All", "planning", "active", "completed", "on_hold"]
        selected_status = st.selectbox("Filter by Status", status_options)
        
        # Get projects based on filter
        status_filter = None if selected_status == "All" else selected_status
        projects = db.get_projects(status_filter=status_filter)
        
        # Get people for owner lookup
        people = db.get_people()
        person_map = {person.id: person.name for person in people}
        person_map[None] = "None"
        
        # Convert to DataFrame for display
        if projects:
            projects_data = []
            for project in projects:
                projects_data.append({
                    "ID": project.id,
                    "Name": project.name,
                    "Status": project.status,
                    "Priority": project.priority,
                    "Owner": person_map.get(project.owner_id, "None"),
                    "Start Date": project.start_date,
                    "End Date": project.end_date,
                    "Description": project.description
                })
            
            df = pd.DataFrame(projects_data)
            
            # Display projects
            st.dataframe(df, use_container_width=True)
            
            # Add actions for selected project
            st.subheader("Actions")
            
            cols = st.columns(4)
            with cols[0]:
                project_id = st.number_input("Project ID", min_value=1, step=1)
            
            with cols[1]:
                view_demands = st.button("View Demands")
            
            with cols[2]:
                view_allocations = st.button("View Allocations")
            
            with cols[3]:
                edit_project = st.button("Edit Project")
            
            if view_demands and project_id:
                # Get the project
                project = db.get_project(project_id)
                if project:
                    st.subheader(f"Demands for {project.name}")
                    
                    # Get demands for the project
                    demands = db.get_demands(project_id=project_id)
                    
                    if demands:
                        # Convert to DataFrame for display
                        demands_data = []
                        for demand in demands:
                            demands_data.append({
                                "ID": demand.id,
                                "Role Required": demand.role_required,
                                "Skills Required": demand.skills_required,
                                "FTE Required": demand.fte_required,
                                "Start Date": demand.start_date,
                                "End Date": demand.end_date,
                                "Status": demand.status,
                                "Priority": demand.priority
                            })
                        
                        df_demands = pd.DataFrame(demands_data)
                        st.dataframe(df_demands, use_container_width=True)
                    else:
                        st.info(f"No demands found for {project.name}")
                else:
                    st.error("Project not found")
            
            if view_allocations and project_id:
                # Get the project
                project = db.get_project(project_id)
                if project:
                    st.subheader(f"Allocations for {project.name}")
                    
                    # Get allocations for the project
                    allocations = db.get_allocations(project_id=project_id)
                    
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
                        st.info(f"No allocations found for {project.name}")
                else:
                    st.error("Project not found")
            
            if edit_project and project_id:
                # Store the project ID in session state for editing
                st.session_state.edit_project_id = project_id
                # Switch to the Add/Edit tab
                st.rerun()
        else:
            st.info("No projects found matching the selected criteria. Please add some projects to get started.")
    
    with tab2:
        st.subheader("Add/Edit Project")
        
        # Initialize the project object
        if "edit_project_id" in st.session_state:
            # Editing an existing project
            project = db.get_project(st.session_state.edit_project_id)
            if not project:
                st.error("Project not found")
                return
            editing = True
        else:
            # Creating a new project
            today = date.today()
            project = Project(
                id=None, 
                name="", 
                description="", 
                priority="medium", 
                status="planning", 
                start_date=today, 
                end_date=today + timedelta(days=90), 
                owner_id=None
            )
            editing = False
        
        # Create the form
        with st.form("project_form"):
            name = st.text_input("Project Name", value=project.name)
            description = st.text_area("Description", value=project.description or "", height=100)
            
            col1, col2 = st.columns(2)
            with col1:
                priority = st.selectbox(
                    "Priority",
                    options=["high", "medium", "low"],
                    index=["high", "medium", "low"].index(project.priority or "medium")
                )
            
            with col2:
                status = st.selectbox(
                    "Status",
                    options=["planning", "active", "completed", "on_hold"],
                    index=["planning", "active", "completed", "on_hold"].index(project.status or "planning")
                )
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=project.start_date or date.today())
            
            with col2:
                end_date = st.date_input("End Date", value=project.end_date or (date.today() + timedelta(days=90)))
            
            # Get people for owner dropdown
            people = db.get_people()
            owner_options = [("None", None)] + [(person.name, person.id) for person in people]
            
            # Find the current owner index
            owner_index = 0
            for i, (owner_name, owner_id) in enumerate(owner_options):
                if owner_id == project.owner_id:
                    owner_index = i
                    break
            
            owner_name, owner_id = owner_options[owner_index]
            selected_owner = st.selectbox(
                "Project Owner",
                options=[name for name, _ in owner_options],
                index=owner_index
            )
            
            # Update the owner_id based on selection
            for name, id in owner_options:
                if name == selected_owner:
                    owner_id = id
                    break
            
            if editing:
                submit_label = "Update Project"
            else:
                submit_label = "Add Project"
            
            submitted = st.form_submit_button(submit_label)
            
            if submitted:
                # Validate dates
                if end_date < start_date:
                    st.error("End date must be after start date")
                else:
                    # Update project object
                    project.name = name
                    project.description = description
                    project.priority = priority
                    project.status = status
                    project.start_date = start_date
                    project.end_date = end_date
                    project.owner_id = owner_id
                    
                    # Save to database
                    saved_project = db.save_project(project)
                    
                    if saved_project:
                        if editing:
                            st.success(f"Project '{name}' updated successfully")
                        else:
                            st.success(f"Project '{name}' added successfully")
                        
                        # Clear the edit project ID
                        if "edit_project_id" in st.session_state:
                            del st.session_state.edit_project_id
                    else:
                        st.error("Error saving project")
    
    with tab3:
        st.subheader("Project Timeline")
        
        # Get projects for Gantt chart
        projects = db.get_projects()
        
        if projects:
            # Convert to DataFrame for Gantt chart
            projects_data = []
            for project in projects:
                projects_data.append({
                    "id": project.id,
                    "name": project.name,
                    "start_date": project.start_date,
                    "end_date": project.end_date,
                    "status": project.status,
                    "priority": project.priority,
                    "description": project.description or ""
                })
            
            df_projects = pd.DataFrame(projects_data)
            
            # Create Gantt chart
            if not df_projects.empty and "start_date" in df_projects.columns and "end_date" in df_projects.columns:
                fig = create_project_gantt(df_projects)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Project data is incomplete. Please ensure all projects have start and end dates.")
        else:
            st.info("No projects found. Please add some projects to see the timeline.") 