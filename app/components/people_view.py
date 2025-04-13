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
    """Render the people management view."""
    st.header("People Management")
    
    # Create tabs for different actions
    tab1, tab2 = st.tabs(["People List", "Team Assignments"])
    
    with tab1:
        render_people_list()
    
    with tab2:
        render_team_assignments()

def render_people_list():
    """Render a list of people with actions."""
    # Add a button to create a new person
    if st.button("Add New Person", key="add_person_button"):
        st.session_state.show_person_form = True
        st.session_state.editing_person = None
    
    # Get all people for display
    people = db.get_people()
    
    # Display people in a dataframe
    if people:
        # Convert to dataframe for display
        people_data = []
        for person in people:
            people_data.append({
                "ID": person.id,
                "Name": person.name,
                "Role": person.role,
                "Team": person.team_name or "No Team"
            })
        
        df = pd.DataFrame(people_data)
        
        # Display in a dataframe
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Selection for editing
        selected_person_id = st.selectbox(
            "Select a person to edit:",
            options=[p.id for p in people],
            format_func=lambda x: next((p.name for p in people if p.id == x), ""),
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Edit Selected Person", use_container_width=True):
                st.session_state.show_person_form = True
                st.session_state.editing_person = next((p for p in people if p.id == selected_person_id), None)
                st.rerun()
        
        with col2:
            if st.button("Delete Selected Person", use_container_width=True):
                # Confirm deletion
                st.session_state.confirm_delete_person = selected_person_id
                st.rerun()
    else:
        st.info("No people found. Add some people to get started.")
    
    # Handle delete confirmation
    if "confirm_delete_person" in st.session_state and st.session_state.confirm_delete_person:
        person_id = st.session_state.confirm_delete_person
        person = next((p for p in people if p.id == person_id), None)
        
        if person:
            st.warning(f"Are you sure you want to delete {person.name}?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete", type="primary"):
                    if db.delete_person(person_id):
                        st.success("Person deleted successfully!")
                        st.session_state.confirm_delete_person = None
                        st.rerun()
                    else:
                        st.error("Cannot delete a person with active allocations. Please remove allocations first.")
            
            with col2:
                if st.button("Cancel"):
                    st.session_state.confirm_delete_person = None
                    st.rerun()
    
    # Show form for adding/editing a person
    if "show_person_form" in st.session_state and st.session_state.show_person_form:
        render_person_form(st.session_state.editing_person)

def render_team_assignments():
    """Render a view of team assignments."""
    # Get all teams
    teams = db.get_teams()
    
    if not teams:
        st.info("No teams found. Add some teams to manage assignments.")
        return
    
    # Team selection
    selected_team = st.selectbox(
        "Select Team",
        options=teams,
        format_func=lambda x: x.name
    )
    
    if selected_team:
        render_team_members(selected_team)

def render_person_form(person=None):
    """Render a form for adding or editing a person."""
    is_edit = person is not None
    form_title = "Edit Person" if is_edit else "Add New Person"
    
    st.subheader(form_title)
    
    with st.form(key="person_form"):
        # Form inputs
        name = st.text_input("Name", value=person.name if is_edit else "")
        role = st.text_input("Role", value=person.role if is_edit else "")
        
        # Get teams for selection
        teams = db.get_teams()
        team_options = [(None, "No Team")] + [(team.id, team.name) for team in teams]
        
        # Team dropdown
        selected_team_index = 0
        if is_edit:
            for i, (team_id, _) in enumerate(team_options):
                if person.team_id == team_id:
                    selected_team_index = i
                    break
        
        team = st.selectbox(
            "Team",
            options=range(len(team_options)),
            format_func=lambda i: team_options[i][1],
            index=selected_team_index
        )
        team_id = team_options[team][0] if team is not None else None
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Save", use_container_width=True)
        with col2:
            cancel_button = st.form_submit_button("Cancel", use_container_width=True)
        
        if submit_button:
            if not name:
                st.error("Name is required")
            else:
                # Create or update person
                if is_edit:
                    person.name = name
                    person.role = role
                    person.team_id = team_id
                    person_id = db.save_person(person)
                else:
                    new_person = Person(
                        name=name,
                        role=role,
                        team_id=team_id
                    )
                    person_id = db.save_person(new_person)
                
                if person_id:
                    st.success("Person saved successfully!")
                    st.session_state.show_person_form = False
                    st.rerun()
                else:
                    st.error("Failed to save person")
        
        if cancel_button:
            st.session_state.show_person_form = False
            st.rerun()

def render_team_members(team):
    """Render the list of team members with management options."""
    st.subheader(f"Members of {team.name}")
    
    members = db.get_people(team_id=team.id)
    
    if members:
        members_data = []
        for member in members:
            members_data.append({
                "Name": member.name,
                "Role": member.role,
                "Actions": "Remove" if st.button(f"Remove {member.name}", key=f"remove_{member.id}") else ""
            })
            
            if members_data[-1]["Actions"] == "Remove":
                if db.update_person_team(member.id, None):
                    st.success(f"Removed {member.name} from the team")
                    st.rerun()
                else:
                    st.error(f"Failed to remove {member.name} from the team")
        
        df = pd.DataFrame(members_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Add member management
        st.markdown("---")
        st.subheader("Add Team Member")
        
        # Get available people not in the team
        all_people = db.get_people()
        team_members = db.get_people(team_id=team.id)
        available_people = [p for p in all_people if p not in team_members]
        
        if available_people:
            with st.form("add_member_form"):
                person = st.selectbox(
                    "Add Team Member",
                    options=available_people,
                    format_func=lambda x: x.name
                )
                
                if st.form_submit_button("Add to Team"):
                    if db.update_person_team(person.id, team.id):
                        st.success(f"Added {person.name} to the team")
                        st.rerun()
                    else:
                        st.error("Failed to add team member")
    else:
        st.info("No team members yet") 