import streamlit as st
import pandas as pd
from datetime import date

from app.database import queries as db
from app.models.data_models import Person

def render_people_view():
    """Render the people management view using a master-detail layout."""
    st.header("People Management")
    
    # Initialize state variables if they don't exist
    if "selected_person_id" not in st.session_state:
        st.session_state.selected_person_id = None
    
    if "editing_person" not in st.session_state:
        st.session_state.editing_person = False
    
    if "confirm_delete_person" not in st.session_state:
        st.session_state.confirm_delete_person = None
    
    # Create a two-column layout - list on the left, details/edit on the right
    col1, col2 = st.columns([3, 4])
    
    with col1:
        # People list section
        st.subheader("People")
        
        # Add button at the top
        if st.button("➕ Add New Person", use_container_width=True):
            st.session_state.selected_person_id = None
            st.session_state.editing_person = True
            st.rerun()
        
        # Get all people
        people = db.get_people()
        
        # Create a DataFrame for display
        if people:
            people_data = []
            for person in people:
                people_data.append({
                    "ID": person.id,
                    "Name": person.name,
                    "Role": person.role,
                    "Team": person.team_name or "No Team"
                })
            
            df = pd.DataFrame(people_data)
            
            # Display people in a clickable dataframe
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID": st.column_config.TextColumn("ID", width="small", help="Person ID"),
                }
            )
            
            # Add a selection dropdown for people
            selected_name = st.selectbox(
                "Select Person",
                options=["Select a person..."] + [p.name for p in people],
                index=0
            )
            
            if selected_name != "Select a person...":
                selected_person = next((p for p in people if p.name == selected_name), None)
                if selected_person:
                    st.session_state.selected_person_id = selected_person.id
                    st.session_state.editing_person = False
                    st.rerun()
    
    with col2:
        # Show delete confirmation if needed
        if st.session_state.confirm_delete_person:
            person_to_delete = st.session_state.confirm_delete_person
            st.warning(f"Are you sure you want to delete {person_to_delete['name']}? This action cannot be undone.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.confirm_delete_person = None
                    st.rerun()
            
            with col2:
                if st.button("Yes, Delete", type="primary", use_container_width=True):
                    success = db.delete_person(person_to_delete['id'])
                    if success:
                        st.session_state.confirm_delete_person = None
                        st.session_state.selected_person_id = None
                        st.session_state.editing_person = False
                        st.success(f"Person {person_to_delete['name']} deleted successfully")
                        st.rerun()
                    else:
                        st.error("Cannot delete a person with active allocations. Please remove allocations first.")
        
        # Show either the detail view or edit form based on state
        elif st.session_state.selected_person_id is not None or st.session_state.editing_person:
            # For edit mode of existing person
            if st.session_state.selected_person_id and st.session_state.editing_person:
                person = db.get_person(st.session_state.selected_person_id)
                if not person:
                    st.error(f"Person not found")
                    st.session_state.selected_person_id = None
                    st.session_state.editing_person = False
                    st.rerun()
                render_person_form(person, is_new=False)
            
            # For detail view of existing person
            elif st.session_state.selected_person_id:
                person = db.get_person(st.session_state.selected_person_id)
                if not person:
                    st.error(f"Person not found")
                    st.session_state.selected_person_id = None
                    st.rerun()
                render_person_details(person)
            
            # For adding a new person
            else:
                render_person_form(Person(), is_new=True)
        
        # Empty state
        else:
            st.info("Select a person from the list to view details, or click 'Add New Person' to create a new entry.")

def render_person_details(person):
    """Render the details view for a person."""
    st.subheader(f"{person.name}")
    
    # Create a clean layout with key details
    detail_col1, detail_col2 = st.columns(2)
    
    with detail_col1:
        st.markdown(f"**Role:** {person.role}")
        st.markdown(f"**Team:** {person.team_name or 'No Team'}")
    
    with detail_col2:
        st.markdown(f"**ID:** {person.id}")
    
    # Action buttons
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("✏️ Edit", use_container_width=True):
            st.session_state.editing_person = True
            st.rerun()
    
    with action_col2:
        if st.button("🗑️ Delete", use_container_width=True):
            st.session_state.confirm_delete_person = {
                'id': person.id,
                'name': person.name
            }
            st.rerun()
    
    with action_col3:
        if st.button("👥 Allocations", use_container_width=True):
            allocations = db.get_allocations(person_id=person.id)
            if allocations:
                display_allocations(person, allocations)
            else:
                st.info(f"No allocations found for {person.name}")
                # Add option to create a new allocation
                if st.button("Create allocation for this person"):
                    st.session_state.sidebar_selection = "Allocations"
                    st.session_state.allocation_tab = "Add/Edit Allocation"
                    st.session_state.new_allocation_person_id = person.id
                    st.rerun()

def render_person_form(person, is_new=False):
    """Render a form for adding/editing a person."""
    # Set the title based on whether we're adding or editing
    title = "Add New Person" if is_new else f"Edit Person: {person.name}"
    st.subheader(title)
    
    # Create the form
    with st.form("person_form", clear_on_submit=is_new):
        name = st.text_input("Name", value=person.name)
        role = st.text_input("Role", value=person.role)
        
        # Get teams for dropdown
        teams = db.get_teams()
        team_options = ["No Team"] + [team.name for team in teams]
        
        # Find current team index
        team_index = 0
        if person.team_name:
            try:
                team_index = team_options.index(person.team_name)
            except ValueError:
                team_index = 0
        
        selected_team = st.selectbox("Team", options=team_options, index=team_index)
        
        # Convert team name to team ID
        team_id = None
        if selected_team != "No Team":
            for team in teams:
                if team.name == selected_team:
                    team_id = team.id
                    break
        
        # Form buttons
        button_col1, button_col2 = st.columns(2)
        
        with button_col1:
            submit_button = st.form_submit_button("Save", use_container_width=True)
        
        with button_col2:
            cancel_button = st.form_submit_button("Cancel", use_container_width=True)
        
        # Handle form submission
        if submit_button:
            if not name:
                st.error("Name is required")
                return
            
            # Update person object
            person.name = name
            person.role = role
            person.team_id = team_id
            
            # Save to database
            person_id = db.save_person(person)
            
            if person_id:
                action = "updated" if not is_new else "added"
                st.success(f"Person {action} successfully")
                
                # Update state and reload
                st.session_state.selected_person_id = person_id
                st.session_state.editing_person = False
                st.rerun()
            else:
                st.error("Failed to save person")
        
        # Handle cancel
        if cancel_button:
            if is_new:
                st.session_state.selected_person_id = None
            st.session_state.editing_person = False
            st.rerun()

def display_allocations(person, allocations):
    """Display a person's allocations."""
    st.subheader(f"Allocations for {person.name}")
    
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
    
    # Add button to manage allocations
    if st.button("Manage Allocations"):
        st.session_state.sidebar_selection = "Allocations"
        st.rerun() 