import streamlit as st
import pandas as pd
from datetime import date, timedelta

from app.database import queries as db
from app.models.data_models import Project
from app.visualizations.gantt_chart import create_project_gantt
from app.utils.plotly_utils import prepare_figure_for_streamlit

def render_projects_view():
    """Render the projects management view with master-detail layout."""
    st.header("Projects Management")
    
    # Initialize session state for selected project
    if "selected_project_id" not in st.session_state:
        st.session_state.selected_project_id = None
    
    # Add filter for project status at the top
    status_options = ["All", "planning", "active", "completed", "cancelled"]
    selected_status = st.selectbox("Filter by Status", status_options)
    
    # Get projects based on filter
    if selected_status == "All":
        projects = db.get_projects()
    else:
        projects = db.get_projects(status=selected_status)
    
    # Layout with two columns: master list and detail view
    col1, col2 = st.columns([1, 2])
    
    with col1:
        render_projects_list(projects)
    
    with col2:
        if st.session_state.selected_project_id:
            render_project_details()
        else:
            st.info("Select a project from the list or click 'Add New Project' to get started.")

def render_projects_list(projects):
    """Render the list of projects with selection capability."""
    # Add New Project button
    if st.button("Add New Project", key="add_new_project"):
        st.session_state.selected_project_id = "new"
        st.rerun()
    
    st.markdown("---")
    
    if projects:
        # Create a selectbox for project selection
        selected_index = 0
        if st.session_state.selected_project_id and st.session_state.selected_project_id != "new":
            selected_index = next((i for i, p in enumerate(projects) if p.id == st.session_state.selected_project_id), 0)
        
        selected_project = st.selectbox(
            "Select Project",
            options=projects,
            format_func=lambda x: x.name,
            index=selected_index,
            key="project_selector"
        )
        
        if selected_project:
            st.session_state.selected_project_id = selected_project.id
            
            # Display project summary
            st.markdown(f"**Status:** {selected_project.status}")
            st.markdown(f"**Project Manager:** {selected_project.project_manager_name or 'Not assigned'}")
            st.markdown(f"**Lead Team:** {selected_project.lead_team_name or 'Not assigned'}")
            
            # Display timeline
            st.markdown("### Project Timeline")
            fig = create_project_gantt([selected_project])
            st.plotly_chart(prepare_figure_for_streamlit(fig), use_container_width=True)
    else:
        st.info("No projects found matching the selected criteria. Click 'Add New Project' to create one.")

def render_project_details():
    """Render the details and edit form for the selected project."""
    if st.session_state.selected_project_id == "new":
        today = date.today()
        project = Project(
            name="",
            description="",
            start_date=today,
            end_date=today + timedelta(days=90),
            status="planning",
            id=None
        )
        st.subheader("New Project")
    else:
        project = db.get_project(st.session_state.selected_project_id)
        if not project:
            st.error("Selected project not found")
            return
        st.subheader(f"Project: {project.name}")
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Project Details", "Demands", "Allocations"])
    
    with tab1:
        render_project_form(project)
    
    with tab2:
        if project.id:  # Only show demands for existing projects
            render_project_demands(project)
            
            # Add demand management
            st.markdown("---")
            st.subheader("Add New Demand")
            with st.form("add_demand_form"):
                role = st.text_input("Role Required")
                fte = st.number_input("FTE Required", min_value=0.0, max_value=1.0, value=1.0, step=0.1)
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date", value=date.today())
                with col2:
                    end_date = st.date_input("End Date", value=date.today() + timedelta(days=90))
                priority = st.selectbox("Priority", options=["high", "medium", "low"])
                
                if st.form_submit_button("Add Demand"):
                    if not role:
                        st.error("Role is required")
                    elif end_date < start_date:
                        st.error("End date must be after start date")
                    else:
                        if db.save_demand(project.id, role, fte, start_date, end_date, priority):
                            st.success("Demand added successfully")
                            st.rerun()
                        else:
                            st.error("Failed to add demand")
    
    with tab3:
        if project.id:  # Only show allocations for existing projects
            render_project_allocations(project)
            
            # Add allocation management
            st.markdown("---")
            st.subheader("Add New Allocation")
            with st.form("add_allocation_form"):
                # Get available people
                people = db.get_people()
                person = st.selectbox(
                    "Person",
                    options=people,
                    format_func=lambda x: x.name
                )
                
                fte = st.number_input("FTE Allocated", min_value=0.0, max_value=1.0, value=1.0, step=0.1)
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date", value=date.today())
                with col2:
                    end_date = st.date_input("End Date", value=date.today() + timedelta(days=90))
                notes = st.text_area("Notes")
                
                if st.form_submit_button("Add Allocation"):
                    if end_date < start_date:
                        st.error("End date must be after start date")
                    else:
                        if db.save_allocation(project.id, person.id, fte, start_date, end_date, notes):
                            st.success("Allocation added successfully")
                            st.rerun()
                        else:
                            st.error("Failed to add allocation")

def render_project_form(project):
    """Render the form for adding or editing a project."""
    with st.form("project_form"):
        name = st.text_input("Project Name", value=project.name)
        description = st.text_area("Description", value=project.description or "", height=100)
        
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
            
            project_type = st.text_input("Project Type", value=project.project_type or "")
            
            # Team dropdown
            selected_team_index = 0
            for i, (team_id, _) in enumerate(team_options):
                if team_id == project.lead_team_id:
                    selected_team_index = i
                    break
            
            lead_team = st.selectbox(
                "Lead Team",
                options=range(len(team_options)),
                format_func=lambda i: team_options[i][1],
                index=selected_team_index
            )
            lead_team_id = team_options[lead_team][0] if lead_team is not None else None
            
            start_date = st.date_input("Start Date", value=project.start_date)
        
        with col2:
            end_date = st.date_input("End Date", value=project.end_date)
            
            status = st.selectbox(
                "Status",
                options=["planning", "active", "completed", "cancelled"],
                index=["planning", "active", "completed", "cancelled"].index(project.status) if project.status else 0
            )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button("Save Project")
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state.selected_project_id = None
                st.rerun()
        
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
                project.project_manager_id = project_manager_id
                project.project_type = project_type
                project.lead_team_id = lead_team_id
                
                # Save to database
                project_id = db.save_project(project)
                
                if project_id:
                    st.success("Project saved successfully")
                    if project.id is None:  # New project
                        st.session_state.selected_project_id = project_id
                        st.rerun()
                else:
                    st.error("Failed to save project")

def render_project_demands(project):
    """Render demands for a specific project."""
    demands = db.get_demands(project_id=project.id)
    
    if demands:
        demands_data = []
        for demand in demands:
            demands_data.append({
                "Role Required": demand.role_required,
                "FTE Required": demand.fte_required,
                "Start Date": demand.start_date,
                "End Date": demand.end_date,
                "Status": demand.status,
                "Priority": demand.priority,
                "Actions": "Delete" if st.button(f"Delete {demand.role_required}", key=f"delete_demand_{demand.id}") else ""
            })
            
            if demands_data[-1]["Actions"] == "Delete":
                if db.delete_demand(demand.id):
                    st.success(f"Deleted demand for {demand.role_required}")
                    st.rerun()
                else:
                    st.error(f"Failed to delete demand for {demand.role_required}")
        
        df = pd.DataFrame(demands_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No demands found for this project")

def render_project_allocations(project):
    """Render allocations for a specific project."""
    allocations = db.get_allocations(project_id=project.id)
    
    if allocations:
        allocations_data = []
        for allocation in allocations:
            allocations_data.append({
                "Person": allocation.person_name,
                "FTE": allocation.fte_allocated,
                "Start Date": allocation.start_date,
                "End Date": allocation.end_date,
                "Notes": allocation.notes,
                "Actions": "Delete" if st.button(f"Delete {allocation.person_name}", key=f"delete_allocation_{allocation.id}") else ""
            })
            
            if allocations_data[-1]["Actions"] == "Delete":
                if db.delete_allocation(allocation.id):
                    st.success(f"Deleted allocation for {allocation.person_name}")
                    st.rerun()
                else:
                    st.error(f"Failed to delete allocation for {allocation.person_name}")
        
        df = pd.DataFrame(allocations_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No allocations found for this project") 