import streamlit as st
import pandas as pd
from datetime import date, timedelta

from app.database import queries as db
from app.models.data_models import Project
from app.visualizations.gantt_chart import create_project_gantt
from app.utils.plotly_utils import prepare_figure_for_streamlit

def render_projects_view():
    """Render the projects management view."""
    st.header("Projects Management")
    
    # Create tabs for different actions
    tab1, tab2 = st.tabs(["Project List", "Project Timeline"])
    
    with tab1:
        render_project_list()
    
    with tab2:
        render_project_timeline()

def render_project_list():
    """Render a list of projects with actions."""
    # Add filter for project status at the top
    status_options = ["All", "planning", "active", "completed", "cancelled"]
    selected_status = st.selectbox("Filter by Status", status_options)
    
    # Get projects based on filter
    if selected_status == "All":
        projects = db.get_projects()
    else:
        projects = db.get_projects(status=selected_status)
    
    # Add a button to create a new project
    if st.button("Add New Project", key="add_project_button"):
        st.session_state.show_project_form = True
        st.session_state.editing_project = None
    
    # Display projects in a dataframe
    if projects:
        # Convert to dataframe for display
        projects_data = []
        for project in projects:
            projects_data.append({
                "ID": project.id,
                "Name": project.name,
                "Status": project.status,
                "Project Manager": project.project_manager_name or "-",
                "Lead Team": project.lead_team_name or "-",
                "Start Date": project.start_date,
                "End Date": project.end_date
            })
        
        df = pd.DataFrame(projects_data)
        
        # Display in a dataframe
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Selection for editing
        selected_project_id = st.selectbox(
            "Select a project to edit:",
            options=[p.id for p in projects],
            format_func=lambda x: next((p.name for p in projects if p.id == x), ""),
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Edit Selected Project", use_container_width=True):
                st.session_state.show_project_form = True
                st.session_state.editing_project = next((p for p in projects if p.id == selected_project_id), None)
                st.rerun()
        
        with col2:
            if st.button("Delete Selected Project", use_container_width=True):
                # Confirm deletion
                st.session_state.confirm_delete_project = selected_project_id
                st.rerun()
    else:
        st.info("No projects found. Add some projects to get started.")
    
    # Handle delete confirmation
    if "confirm_delete_project" in st.session_state and st.session_state.confirm_delete_project:
        project_id = st.session_state.confirm_delete_project
        project = next((p for p in projects if p.id == project_id), None)
        
        if project:
            st.warning(f"Are you sure you want to delete the project {project.name}?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete", type="primary"):
                    if db.delete_project(project_id):
                        st.success("Project deleted successfully!")
                        st.session_state.confirm_delete_project = None
                        st.rerun()
                    else:
                        st.error("Failed to delete project.")
            
            with col2:
                if st.button("Cancel"):
                    st.session_state.confirm_delete_project = None
                    st.rerun()
    
    # Show form for adding/editing a project
    if "show_project_form" in st.session_state and st.session_state.show_project_form:
        render_project_form(st.session_state.editing_project)

def render_project_timeline():
    """Render a timeline view of projects."""
    # Get date range from session state
    start_date, end_date = st.session_state.date_range
    
    # Get all projects
    projects = db.get_projects()
    
    if not projects:
        st.info("No projects found. Add some projects to see the timeline.")
        return
    
    # Filter projects by date if needed
    if start_date and end_date:
        filtered_projects = [
            p for p in projects 
            if (p.end_date and p.end_date >= start_date) and 
               (p.start_date and p.start_date <= end_date)
        ]
    else:
        filtered_projects = projects
    
    if not filtered_projects:
        st.info("No projects found in the selected date range.")
        return
    
    # Create Gantt chart
    fig = create_project_gantt(filtered_projects)
    
    # Display the chart
    st.plotly_chart(prepare_figure_for_streamlit(fig), use_container_width=True)

def render_project_form(project=None):
    """Render a form for adding or editing a project."""
    is_edit = project is not None
    form_title = "Edit Project" if is_edit else "Add New Project"
    
    st.subheader(form_title)
    
    with st.form(key="project_form"):
        # Form inputs
        name = st.text_input("Project Name", value=project.name if is_edit else "")
        description = st.text_area("Description", value=project.description if is_edit else "")
        
        # Get teams for selection
        teams = db.get_teams()
        team_options = [(None, "-")] + [(team.id, team.name) for team in teams]
        
        # Get people for project manager selection
        people = db.get_people()
        manager_options = [(None, "-")] + [(person.id, person.name) for person in people]
        
        col1, col2 = st.columns(2)
        with col1:
            # Project Manager dropdown
            selected_manager_index = 0
            if is_edit:
                for i, (person_id, _) in enumerate(manager_options):
                    if project.project_manager_id == person_id:
                        selected_manager_index = i
                        break
            
            project_manager = st.selectbox(
                "Project Manager",
                options=range(len(manager_options)),
                format_func=lambda i: manager_options[i][1],
                index=selected_manager_index
            )
            project_manager_id = manager_options[project_manager][0] if project_manager is not None else None
            
            project_type = st.text_input("Project Type", value=project.project_type if is_edit else "")
            
            # Team dropdown
            selected_team_index = 0
            if is_edit:
                for i, (team_id, _) in enumerate(team_options):
                    if project.lead_team_id == team_id:
                        selected_team_index = i
                        break
            
            lead_team = st.selectbox(
                "Lead Team",
                options=range(len(team_options)),
                format_func=lambda i: team_options[i][1],
                index=selected_team_index
            )
            lead_team_id = team_options[lead_team][0] if lead_team is not None else None
        
        with col2:
            # Status dropdown
            status_options = ["planning", "active", "completed", "cancelled"]
            status = st.selectbox(
                "Status",
                options=status_options,
                index=status_options.index(project.status) if is_edit else 0
            )
            
            # Date inputs
            start_date = st.date_input(
                "Start Date",
                value=project.start_date if is_edit else date.today()
            )
            end_date = st.date_input(
                "End Date",
                value=project.end_date if is_edit else date.today() + timedelta(days=90)
            )
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Save", use_container_width=True)
        with col2:
            cancel_button = st.form_submit_button("Cancel", use_container_width=True)
        
        if submit_button:
            if not name:
                st.error("Project name is required")
            elif end_date < start_date:
                st.error("End date must be after start date")
            else:
                # Create or update project
                if is_edit:
                    project.name = name
                    project.description = description
                    project.project_manager_id = project_manager_id
                    project.project_type = project_type
                    project.lead_team_id = lead_team_id
                    project.status = status
                    project.start_date = start_date
                    project.end_date = end_date
                    project_id = db.save_project(project)
                else:
                    new_project = Project(
                        name=name,
                        description=description,
                        project_manager_id=project_manager_id,
                        project_type=project_type,
                        lead_team_id=lead_team_id,
                        status=status,
                        start_date=start_date,
                        end_date=end_date
                    )
                    project_id = db.save_project(new_project)
                
                if project_id:
                    st.success("Project saved successfully!")
                    st.session_state.show_project_form = False
                    st.rerun()
                else:
                    st.error("Failed to save project")
        
        if cancel_button:
            st.session_state.show_project_form = False
            st.rerun() 