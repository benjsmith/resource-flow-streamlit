import streamlit as st
import pandas as pd
from datetime import date, timedelta

from app.database import queries as db
from app.models.data_models import Project
from app.visualizations.gantt_chart import create_project_gantt

def render_projects_view():
    """
    Render the projects management view
    """
    st.header("Projects Management")
    
    # Create tabs for different actions
    tab1, tab2, tab3 = st.tabs(["Projects List", "Add/Edit Project", "Project Timeline"])
    
    with tab1:
        # Add filter for project status
        status_options = ["All", "planning", "active", "completed", "cancelled"]
        selected_status = st.selectbox("Filter by Status", status_options)
        
        # Get projects based on filter
        if selected_status == "All":
            projects = db.get_projects()
        else:
            projects = db.get_projects(status=selected_status)
        
        # Convert to DataFrame for display
        if projects:
            projects_data = []
            for project in projects:
                projects_data.append({
                    "ID": project.id,
                    "Name": project.name,
                    "Status": project.status,
                    "Start Date": project.start_date,
                    "End Date": project.end_date,
                    "Description": project.description
                })
            
            df = pd.DataFrame(projects_data)
            
            # Display projects
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Add actions for selected project
            st.subheader("Actions")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                selected_project_id = st.selectbox(
                    "Select Project", 
                    options=[p.id for p in projects],
                    format_func=lambda x: next((p.name for p in projects if p.id == x), "")
                )
            
            with col2:
                if st.button("View Demands"):
                    project = next((p for p in projects if p.id == selected_project_id), None)
                    if project:
                        render_project_demands(project)
            
            with col3:
                if st.button("View Allocations"):
                    project = next((p for p in projects if p.id == selected_project_id), None)
                    if project:
                        render_project_allocations(project)
            
            with col4:
                if st.button("Edit Project"):
                    # Set the project ID for editing and switch to the edit tab
                    st.session_state.edit_project_id = selected_project_id
                    st.rerun()
        else:
            st.info("No projects found matching the selected criteria. Please add some projects to get started.")
    
    with tab2:
        render_project_form()
    
    with tab3:
        render_project_timeline()

def render_project_demands(project):
    """Render demands for a specific project."""
    st.subheader(f"Demands for {project.name}")
    
    # Get demands for the project
    demands = db.get_demands(project_id=project.id)
    
    if demands:
        # Convert to DataFrame for display
        demands_data = []
        for demand in demands:
            demands_data.append({
                "ID": demand.id,
                "Role Required": demand.role_required,
                "FTE Required": demand.fte_required,
                "Start Date": demand.start_date,
                "End Date": demand.end_date,
                "Status": demand.status,
                "Priority": demand.priority,
                "Skills": ", ".join(demand.skills_required) if demand.skills_required else ""
            })
        
        df = pd.DataFrame(demands_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(f"No demands found for {project.name}")

def render_project_allocations(project):
    """Render allocations for a specific project."""
    st.subheader(f"Allocations for {project.name}")
    
    # Get allocations for the project
    allocations = db.get_allocations(project_id=project.id)
    
    if allocations:
        # Convert to DataFrame for display
        allocations_data = []
        for allocation in allocations:
            allocations_data.append({
                "ID": allocation.id,
                "Person": allocation.person_name,
                "FTE": allocation.fte_allocated,
                "Start Date": allocation.start_date,
                "End Date": allocation.end_date,
                "Notes": allocation.notes
            })
        
        df = pd.DataFrame(allocations_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(f"No allocations found for {project.name}")

def render_project_form():
    """Render the form for adding or editing a project."""
    # Check if we're editing an existing project
    edit_mode = "edit_project_id" in st.session_state and st.session_state.edit_project_id is not None
    
    if edit_mode:
        project = db.get_project(st.session_state.edit_project_id)
        if not project:
            st.error(f"Project with ID {st.session_state.edit_project_id} not found")
            return
        st.subheader(f"Edit Project: {project.name}")
    else:
        # Create a new project object
        today = date.today()
        project = Project(
            name="",
            description="",
            start_date=today,
            end_date=today + timedelta(days=90),
            status="planning",
            id=None
        )
        st.subheader("Add New Project")
    
    # Create a form for the project details
    with st.form("project_form"):
        name = st.text_input("Project Name", value=project.name)
        description = st.text_area("Description", value=project.description or "", height=100)
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=project.start_date)
        with col2:
            end_date = st.date_input("End Date", value=project.end_date)
        
        status = st.selectbox(
            "Status",
            options=["planning", "active", "completed", "cancelled"],
            index=["planning", "active", "completed", "cancelled"].index(project.status) if project.status else 0
        )
        
        submitted = st.form_submit_button("Save Project")
        
        if submitted:
            if not name:
                st.error("Project name is required")
            elif end_date < start_date:
                st.error("End date must be after start date")
            else:
                # Create or update the project object
                project.name = name
                project.description = description
                project.start_date = start_date
                project.end_date = end_date
                project.status = status
                
                # Save to database
                project_id = db.save_project(project)
                
                if project_id:
                    action = "updated" if edit_mode else "added"
                    st.success(f"Project {action} successfully")
                    
                    # Clear the edit project ID
                    if edit_mode:
                        st.session_state.edit_project_id = None
                        st.rerun()
                else:
                    st.error("Failed to save project")

def render_project_timeline():
    """Render a timeline of projects using a Gantt chart."""
    st.subheader("Project Timeline")
    
    # Get projects
    projects = db.get_projects()
    
    if projects:
        # Create Gantt chart
        fig = create_project_gantt(projects)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No projects found to display in the timeline.") 