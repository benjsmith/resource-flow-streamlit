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
    col1, col2 = st.columns([2, 1])
    with col1:
        team_filter = st.selectbox(
            "Filter by Team", 
            ["All Teams"] + sorted(list(set([p.team_name for p in people if p.team_name is not None]))),
            index=0
        )
    
    with col2:
        # Add a button to add a new person
        if st.button("➕ Add New Person", use_container_width=True):
            # Clear any existing editing state
            if "edit_person_id" in st.session_state:
                del st.session_state.edit_person_id
            # Switch to the Add/Edit tab
            st.session_state.people_tab = "Add/Edit Person"
            st.rerun()
    
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
        
        # Initialize selected person state if not present
        if "selected_person_id" not in st.session_state:
            st.session_state.selected_person_id = None
        
        # Display the data
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn(
                    "ID",
                    help="Person ID",
                    format="%d",
                    width="small"
                )
            }
        )
        
        # Add a selection dropdown for people
        selected_name = st.selectbox(
            "Select a person to perform actions",
            options=["Select a person..."] + [p.name for p in filtered_people],
            index=0
        )
        
        if selected_name != "Select a person...":
            selected_person = next((p for p in filtered_people if p.name == selected_name), None)
            
            if selected_person:
                # Store the selected person ID in session state
                st.session_state.selected_person_id = selected_person.id
                
                # Create columns for actions
                st.subheader(f"Actions for {selected_person.name}")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("View Allocations", use_container_width=True):
                        render_person_allocations(selected_person)
                
                with col2:
                    if st.button("Edit Person", use_container_width=True):
                        # Set the person ID for editing and switch to the edit tab
                        st.session_state.edit_person_id = selected_person.id
                        st.rerun()
                
                with col3:
                    # Add delete with confirmation
                    if st.button("Delete Person", type="primary", use_container_width=True):
                        st.session_state.confirm_delete_person_id = selected_person.id
                        st.session_state.confirm_delete_person_name = selected_person.name
            
            # Handle delete confirmation
            if "confirm_delete_person_id" in st.session_state:
                st.warning(f"Are you sure you want to delete {st.session_state.confirm_delete_person_name}? This action cannot be undone.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, Delete", type="primary", use_container_width=True):
                        # Delete the person
                        if db.delete_person(st.session_state.confirm_delete_person_id):
                            st.success(f"{st.session_state.confirm_delete_person_name} deleted successfully")
                            # Clear the state
                            del st.session_state.confirm_delete_person_id
                            del st.session_state.confirm_delete_person_name
                            st.rerun()
                        else:
                            st.error("Cannot delete a person with allocations. Please remove allocations first.")
                with col2:
                    if st.button("Cancel", use_container_width=True):
                        # Clear the state
                        del st.session_state.confirm_delete_person_id
                        del st.session_state.confirm_delete_person_name
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
        
        # Add a button to go to Allocations tab
        if st.button("Manage Allocations"):
            # Switch to allocations view
            st.session_state.sidebar_selection = "Allocations"
            st.rerun()
    else:
        st.info(f"No allocations found for {person.name}")
        # Add a button to create an allocation for this person
        if st.button("Create Allocation"):
            # Switch to allocations view and set up for new allocation
            st.session_state.sidebar_selection = "Allocations"
            st.session_state.allocation_tab = "Add/Edit Allocation"
            st.session_state.new_allocation_person_id = person.id
            st.rerun()

def render_people_form():
    """Render the form for adding or editing a person."""
    # Check if we're editing an existing person
    edit_mode = "edit_person_id" in st.session_state and st.session_state.edit_person_id is not None
    
    if edit_mode:
        person = db.get_person(st.session_state.edit_person_id)
        if not person:
            st.error(f"Person with ID {st.session_state.edit_person_id} not found")
            if st.button("Clear and Start New"):
                if "edit_person_id" in st.session_state:
                    del st.session_state.edit_person_id
                st.rerun()
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
    with st.form("person_form", clear_on_submit=not edit_mode):
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
        
        # Skills as a comma-separated list with tagging UI
        skills_input = st.text_input(
            "Skills (comma-separated)", 
            value=", ".join(person.skills) if person.skills else "",
            help="Enter skills separated by commas (e.g., Python, Java, Project Management)"
        )
        
        # Process skills
        skills = [skill.strip() for skill in skills_input.split(",")] if skills_input else []
        
        # Display the current skills as tags
        if skills:
            st.write("Current skills:")
            cols = st.columns(4)
            for i, skill in enumerate(skills):
                if skill:  # Only display non-empty skills
                    cols[i % 4].markdown(f"<span style='background-color:#f0f2f6;padding:5px;border-radius:5px;margin:2px;white-space:nowrap;display:inline-block;'>{skill}</span>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Save Person", use_container_width=True)
        
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)
        
        if submitted:
            if not name:
                st.error("Name is required")
            else:
                # Create or update the person object
                person.name = name
                person.role = role
                person.team_id = team_id
                person.skills = [s for s in skills if s]  # Remove empty skills
                
                # Save to database
                person_id = db.save_person(person)
                
                if person_id:
                    action = "updated" if edit_mode else "added"
                    st.success(f"Person {action} successfully")
                    
                    # Clear the edit person ID
                    if edit_mode:
                        del st.session_state.edit_person_id
                        # Go back to list view
                        st.session_state.people_tab = "People List"
                        st.rerun()
                else:
                    st.error("Failed to save person")
        
        elif cancelled:
            # Clear the edit state and go back to list
            if "edit_person_id" in st.session_state:
                del st.session_state.edit_person_id
            st.rerun() 