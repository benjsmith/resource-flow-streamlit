import streamlit as st
import pandas as pd
from datetime import date

from app.database import queries as db
from app.models.data_models import Person

# Callback functions for state management
def select_person(person_id):
    st.session_state.selected_person_id = person_id
    st.session_state.editing_person = False
    
def clear_selection():
    st.session_state.selected_person_id = None
    st.session_state.editing_person = False
    
def start_editing():
    st.session_state.editing_person = True
    
def show_delete_confirmation(person):
    st.session_state.confirm_delete_person = {
        'id': person.id,
        'name': person.name
    }
    
def clear_delete_confirmation():
    st.session_state.confirm_delete_person = None
    
def delete_person(person_id, person_name):
    success = db.delete_person(person_id)
    if success:
        st.session_state.confirm_delete_person = None
        st.session_state.selected_person_id = None
        st.session_state.editing_person = False
        st.session_state.show_success_message = f"Person {person_name} deleted successfully"
    else:
        st.session_state.show_error_message = "Cannot delete a person with active allocations. Please remove allocations first."
        
def on_person_selected():
    if st.session_state.person_selector != "Select a person...":
        # Fetch all people again to find the selected one
        people = db.get_people()
        selected_person = next((p for p in people if p.name == st.session_state.person_selector), None)
        if selected_person:
            st.session_state.selected_person_id = selected_person.id
            st.session_state.editing_person = False

def save_person(person, name, role, team_id, is_new):
    if not name:
        st.session_state.show_error_message = "Name is required"
        return
    
    # Update person object
    person.name = name
    person.role = role
    person.team_id = team_id
    
    # Save to database
    person_id = db.save_person(person)
    
    if person_id:
        st.session_state.selected_person_id = person_id
        st.session_state.editing_person = False
        if is_new:
            st.session_state.show_success_message = f"Person {name} created successfully"
        else:
            st.session_state.show_success_message = f"Person {name} updated successfully"
    else:
        st.session_state.show_error_message = "Failed to save person"

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
        
    if "show_success_message" not in st.session_state:
        st.session_state.show_success_message = None
        
    if "show_error_message" not in st.session_state:
        st.session_state.show_error_message = None
    
    # Display success/error messages if they exist
    if st.session_state.show_success_message:
        st.success(st.session_state.show_success_message)
        st.session_state.show_success_message = None
        
    if st.session_state.show_error_message:
        st.error(st.session_state.show_error_message)
        st.session_state.show_error_message = None
    
    # Create a two-column layout - list on the left, details/edit on the right
    col1, col2 = st.columns([3, 4])
    
    with col1:
        # People list section
        st.subheader("People")
        
        # Get all people
        people = db.get_people()
        
        # Create a DataFrame for display
        if people:
            # Add a selection dropdown for people
            options = ["Select a person..."] + [p.name for p in people]
            index = 0
            
            # If there's a selected person, make sure it's selected in the dropdown
            if st.session_state.selected_person_id:
                selected_person = db.get_person(st.session_state.selected_person_id)
                if selected_person:
                    try:
                        index = options.index(selected_person.name)
                    except ValueError:
                        index = 0
            
            st.selectbox(
                "Select a Person to View/Edit",
                options=options,
                index=index,
                key="person_selector",
                on_change=on_person_selected
            )
            
            # Create a simple table to display all people
            people_data = []
            for person in people:
                people_data.append({
                    "Name": person.name,
                    "Role": person.role,
                    "Team": person.team_name or "No Team"
                })
            
            df = pd.DataFrame(people_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Add new person button
            st.button(
                "➕ Add New Person", 
                use_container_width=True, 
                key="add_new_person_btn",
                on_click=lambda: (clear_selection(), start_editing())
            )
    
    with col2:
        # Show delete confirmation if needed
        if st.session_state.confirm_delete_person:
            person_to_delete = st.session_state.confirm_delete_person
            st.warning(f"Are you sure you want to delete {person_to_delete['name']}? This action cannot be undone.")
            
            col1, col2 = st.columns(2)
            with col1:
                st.button(
                    "Cancel", 
                    use_container_width=True, 
                    key="cancel_delete_btn",
                    on_click=clear_delete_confirmation
                )
            
            with col2:
                st.button(
                    "Yes, Delete", 
                    type="primary", 
                    use_container_width=True, 
                    key="confirm_delete_btn",
                    on_click=delete_person,
                    args=(person_to_delete['id'], person_to_delete['name'])
                )
        
        # Show either the detail view or edit form based on state
        elif st.session_state.selected_person_id is not None or st.session_state.editing_person:
            # For edit mode of existing person
            if st.session_state.selected_person_id and st.session_state.editing_person:
                person = db.get_person(st.session_state.selected_person_id)
                if not person:
                    st.error(f"Person not found")
                    clear_selection()
                else:
                    render_person_form(person, is_new=False)
            
            # For detail view of existing person
            elif st.session_state.selected_person_id:
                person = db.get_person(st.session_state.selected_person_id)
                if not person:
                    st.error(f"Person not found")
                    clear_selection()
                else:
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
    st.markdown(f"**Role:** {person.role}")
    st.markdown(f"**Team:** {person.team_name or 'No Team'}")
    st.markdown(f"**ID:** {person.id}")
    
    # Show allocations if they exist
    allocations = db.get_allocations(person_id=person.id)
    if allocations:
        st.subheader("Allocations")
        allocations_data = []
        for allocation in allocations:
            allocations_data.append({
                "Project": allocation.project_name,
                "FTE": allocation.fte_allocated,
                "Start Date": allocation.start_date,
                "End Date": allocation.end_date
            })
        
        df = pd.DataFrame(allocations_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.button(
            "Edit", 
            use_container_width=True, 
            key="edit_person_btn",
            on_click=start_editing
        )
    
    with col2:
        st.button(
            "Delete", 
            use_container_width=True, 
            key="delete_person_btn",
            on_click=show_delete_confirmation,
            args=(person,)
        )
    
    with col3:
        st.button(
            "Manage Allocations", 
            use_container_width=True, 
            key="manage_allocations_btn",
            on_click=lambda: setattr(st.session_state, "sidebar_selection", "Allocations")
        )

def render_person_form(person, is_new=False):
    """Render a form for adding/editing a person."""
    # Set the title based on whether we're adding or editing
    title = "Add New Person" if is_new else f"Edit: {person.name}"
    st.subheader(title)
    
    # Create simple inputs instead of a form
    name = st.text_input("Name", value=person.name, key=f"person_name_{is_new}")
    role = st.text_input("Role", value=person.role, key=f"person_role_{is_new}")
    
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
    
    selected_team = st.selectbox(
        "Team", 
        options=team_options, 
        index=team_index,
        key=f"person_team_{is_new}"
    )
    
    # Convert team name to team ID
    team_id = None
    if selected_team != "No Team":
        for team in teams:
            if team.name == selected_team:
                team_id = team.id
                break
    
    # Form buttons
    col1, col2 = st.columns(2)
    
    with col1:
        st.button(
            "Save", 
            use_container_width=True,
            key=f"save_person_btn_{is_new}",
            on_click=save_person,
            args=(person, name, role, team_id, is_new)
        )
    
    with col2:
        st.button(
            "Cancel", 
            use_container_width=True,
            key=f"cancel_edit_btn_{is_new}",
            on_click=lambda: clear_selection() if is_new else setattr(st.session_state, "editing_person", False)
        ) 