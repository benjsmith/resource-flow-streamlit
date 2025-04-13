import streamlit as st
import pandas as pd

from app.database import queries as db
from app.models.data_models import Team

def render_teams_view():
    """Render the teams management view."""
    st.header("Teams Management")
    
    # Create tabs for different actions
    tab1, tab2 = st.tabs(["Team List", "Team Members"])
    
    with tab1:
        render_team_list()
    
    with tab2:
        render_team_members_view()

def render_team_list():
    """Render a list of teams with actions."""
    # Add a button to create a new team
    if st.button("Add New Team", key="add_team_button"):
        st.session_state.show_team_form = True
        st.session_state.editing_team = None
        st.rerun()
    
    # Get all teams for display
    teams = db.get_teams()
    
    # Display teams in a dataframe
    if teams:
        # Convert to dataframe for display
        teams_data = []
        for team in teams:
            members = db.get_people(team_id=team.id)
            parent_team = next((t for t in teams if t.id == team.parent_team_id), None)
            teams_data.append({
                "ID": team.id,
                "Name": team.name,
                "Description": team.description,
                "Parent Team": parent_team.name if parent_team else "None",
                "Members": len(members)
            })
        
        df = pd.DataFrame(teams_data)
        
        # Display in a dataframe
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Selection for editing
        selected_team_id = st.selectbox(
            "Select a team to edit:",
            options=[t.id for t in teams],
            format_func=lambda x: next((t.name for t in teams if t.id == x), ""),
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Edit Selected Team", use_container_width=True):
                st.session_state.show_team_form = True
                st.session_state.editing_team = next((t for t in teams if t.id == selected_team_id), None)
                st.rerun()
        
        with col2:
            if st.button("Delete Selected Team", use_container_width=True):
                # Confirm deletion
                st.session_state.confirm_delete_team = selected_team_id
                st.rerun()
    else:
        st.info("No teams found. Add some teams to get started.")
    
    # Handle delete confirmation
    if "confirm_delete_team" in st.session_state and st.session_state.confirm_delete_team:
        team_id = st.session_state.confirm_delete_team
        team = next((t for t in teams if t.id == team_id), None)
        
        if team:
            st.warning(f"Are you sure you want to delete the team {team.name}?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete", type="primary"):
                    if db.delete_team(team_id):
                        st.success("Team deleted successfully!")
                        st.session_state.confirm_delete_team = None
                        st.rerun()
                    else:
                        st.error("Failed to delete team.")
            
            with col2:
                if st.button("Cancel"):
                    st.session_state.confirm_delete_team = None
                    st.rerun()
    
    # Show form for adding/editing a team
    if "show_team_form" in st.session_state and st.session_state.show_team_form:
        render_team_form(st.session_state.editing_team)

def render_team_members_view():
    """Render a view of team members."""
    # Get all teams
    teams = db.get_teams()
    
    if not teams:
        st.info("No teams found. Add some teams to manage members.")
        return
    
    # Team selection
    selected_team = st.selectbox(
        "Select Team",
        options=teams,
        format_func=lambda x: x.name
    )
    
    if selected_team:
        render_team_members(selected_team)

def render_team_form(team=None):
    """Render a form for adding or editing a team."""
    is_edit = team is not None
    form_title = "Edit Team" if is_edit else "Add New Team"
    
    st.subheader(form_title)
    
    # Initialize form data
    form_data = {
        "name": team.name if is_edit else "",
        "description": team.description if is_edit else "",
        "parent_team_id": team.parent_team_id if is_edit else None
    }
    
    # Get all teams for parent team selection
    teams = db.get_teams()
    parent_team_options = [("None", None)] + [(t.name, t.id) for t in teams if not is_edit or t.id != team.id]
    
    # Find the current parent team index
    parent_team_index = 0
    if is_edit and team.parent_team_id:
        for i, (_, team_id) in enumerate(parent_team_options):
            if team_id == team.parent_team_id:
                parent_team_index = i
                break
    
    # Create the form
    with st.form(key="team_form"):
        # Form inputs
        form_data["name"] = st.text_input("Team Name", value=form_data["name"])
        form_data["description"] = st.text_area("Description", value=form_data["description"])
        
        selected_parent_team = st.selectbox(
            "Parent Team (Optional)",
            options=[name for name, _ in parent_team_options],
            index=parent_team_index
        )
        form_data["parent_team_id"] = next((id for name, id in parent_team_options if name == selected_parent_team), None)
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Save", use_container_width=True)
        with col2:
            cancel_button = st.form_submit_button("Cancel", use_container_width=True)
    
    # Handle form submission
    if submit_button:
        if not form_data["name"]:
            st.error("Team name is required")
        else:
            try:
                # Create or update team
                if is_edit:
                    team.name = form_data["name"]
                    team.description = form_data["description"]
                    team.parent_team_id = form_data["parent_team_id"]
                    team_id = db.save_team(team)
                else:
                    new_team = Team(
                        name=form_data["name"],
                        description=form_data["description"],
                        parent_team_id=form_data["parent_team_id"]
                    )
                    team_id = db.save_team(new_team)
                
                if team_id:
                    st.success("Team saved successfully!")
                    # Clear session state
                    st.session_state.show_team_form = False
                    st.session_state.editing_team = None
                    # Force a rerun to refresh the data
                    st.rerun()
                else:
                    st.error("Failed to save team")
            except Exception as e:
                st.error(f"Error saving team: {str(e)}")
    
    # Handle cancel
    if cancel_button:
        # Clear session state
        st.session_state.show_team_form = False
        st.session_state.editing_team = None
        # Force a rerun to refresh the data
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