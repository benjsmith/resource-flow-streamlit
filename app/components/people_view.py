import streamlit as st
import pandas as pd
from datetime import date

from app.database import queries as db
from app.models.data_models import Person

def render_people_view():
    """Render the people management view."""
    st.header("People Management")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["People List", "Add/Edit Person"])
    
    with tab1:
        render_people_list()
    
    with tab2:
        render_people_form()

def render_people_list():
    """Render the list of people with filtering and actions."""
    # Get all people and teams
    people = db.get_people()
    
    # Add filters if needed
    team_filter = st.selectbox(
        "Filter by Team", 
        ["All Teams"] + [p.team_name for p in people if p.team_name is not None],
        index=0
    )
    
    # Filter people by team if selected
    if team_filter != "All Teams":
        filtered_people = [p for p in people if p.team_name == team_filter]
    else:
        filtered_people = people
    
    if filtered_people:
        # Convert to DataFrame for display
        people_data = []
        for person in filtered_people:
            people_data.append({
                "ID": person.id,
                "Name": person.name,
                "Role": person.role,
                "Team": person.team_name or "No Team",
                "Skills": ", ".join(person.skills) if person.skills else ""
            })
        
        df = pd.DataFrame(people_data)
        
        # Display the data
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Add section for actions
        st.subheader("Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_person_id = st.selectbox(
                "Select Person", 
                options=[p.id for p in filtered_people],
                format_func=lambda x: next((p.name for p in filtered_people if p.id == x), "")
            )
        
        with col2:
            if st.button("View Allocations"):
                person = next((p for p in filtered_people if p.id == selected_person_id), None)
                if person:
                    render_person_allocations(person)
        
        with col3:
            if st.button("Edit Person"):
                # Set the person ID for editing and switch to the edit tab
                st.session_state.edit_person_id = selected_person_id
                st.rerun()
    else:
        st.info("No people found. Add some people to get started.")

def render_person_allocations(person):
    """Render allocations for a specific person."""
    st.subheader(f"Allocations for {person.name}")
    
    # Get allocations for the person
    allocations = db.get_allocations(person_id=person.id)
    
    if allocations:
        # Convert to DataFrame for display
        allocations_data = []
        for allocation in allocations:
            allocations_data.append({
                "ID": allocation.id,
                "Project": allocation.project_name,
                "FTE": allocation.fte_allocated,
                "Start Date": allocation.start_date,
                "End Date": allocation.end_date,
                "Notes": allocation.notes
            })
        
        df = pd.DataFrame(allocations_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(f"No allocations found for {person.name}")

def render_people_form():
    """Render the form for adding or editing a person."""
    # Check if we're editing an existing person
    edit_mode = "edit_person_id" in st.session_state and st.session_state.edit_person_id is not None
    
    if edit_mode:
        person = db.get_person(st.session_state.edit_person_id)
        if not person:
            st.error(f"Person with ID {st.session_state.edit_person_id} not found")
            return
        st.subheader(f"Edit Person: {person.name}")
    else:
        # Create a new person object
        person = Person(
            name="",
            role="",
            skills=[],
            team_id=None,
            team_name=None,
            id=None
        )
        st.subheader("Add New Person")
    
    # Create a form for the person details
    with st.form("person_form"):
        name = st.text_input("Name", value=person.name)
        role = st.text_input("Role", value=person.role)
        
        # Get teams for dropdown
        teams = db.get_teams()
        team_options = ["No Team"] + [team.name for team in teams]
        
        # Find current team index
        if person.team_name:
            try:
                team_index = team_options.index(person.team_name)
            except ValueError:
                team_index = 0
        else:
            team_index = 0
        
        selected_team = st.selectbox("Team", options=team_options, index=team_index)
        
        # Convert team name to team ID
        team_id = None
        if selected_team != "No Team":
            for team in teams:
                if team.name == selected_team:
                    team_id = team.id
                    break
        
        # Skills as a comma-separated list
        skills_input = st.text_input(
            "Skills (comma-separated)", 
            value=", ".join(person.skills) if person.skills else ""
        )
        
        # Process skills
        skills = [skill.strip() for skill in skills_input.split(",")] if skills_input else []
        
        submitted = st.form_submit_button("Save Person")
        
        if submitted:
            if not name:
                st.error("Name is required")
            else:
                # Create or update the person object
                person.name = name
                person.role = role
                person.team_id = team_id
                person.skills = skills
                
                # Save to database
                person_id = db.save_person(person)
                
                if person_id:
                    action = "updated" if edit_mode else "added"
                    st.success(f"Person {action} successfully")
                    
                    # Clear the edit person ID
                    if edit_mode:
                        st.session_state.edit_person_id = None
                        st.rerun()
                else:
                    st.error("Failed to save person") 