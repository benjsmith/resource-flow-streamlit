import streamlit as st
import pandas as pd

from app.database import queries as db
from app.models.data_models import Team

def render_teams_view():
    """Render the teams management view."""
    st.header("Teams Management")
    
    # Get all teams
    teams = db.get_teams()
    
    # Display teams in a table
    if teams:
        teams_data = []
        for team in teams:
            members = db.get_people(team_id=team.id)
            teams_data.append({
                "ID": team.id,
                "Name": team.name,
                "Description": team.description,
                "Members": len(members)
            })
        
        df = pd.DataFrame(teams_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Add actions section
        st.subheader("Actions")
        
        # Create a selectbox for team selection
        selected_team = st.selectbox(
            "Select Team",
            options=teams,
            format_func=lambda x: x.name,
            key="team_selector"
        )
        
        # Add buttons for actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Edit Team"):
                st.session_state.edit_team_id = selected_team.id
                st.rerun()
        with col2:
            if st.button("View Members"):
                render_team_members(selected_team)
    else:
        st.info("No teams found. Add a team to get started.")
    
    # Add New Team button
    if st.button("Add New Team"):
        st.session_state.edit_team_id = "new"
        st.rerun()
    
    # Show edit form if in edit mode
    if "edit_team_id" in st.session_state and st.session_state.edit_team_id:
        render_team_form()

def render_team_form():
    """Render the form for adding or editing a team."""
    # Add clear button at the top of the form if in edit mode
    if st.session_state.edit_team_id != "new":
        if st.button("Clear Form (Add New Team)"):
            st.session_state.edit_team_id = "new"
            st.rerun()
    
    # Initialize the team object
    if st.session_state.edit_team_id == "new":
        team = Team(name="", description="", id=None)
        st.subheader("New Team")
    else:
        team = db.get_team(st.session_state.edit_team_id)
        if not team:
            st.error(f"Team with ID {st.session_state.edit_team_id} not found")
            st.session_state.edit_team_id = None
            st.rerun()
            return
        st.subheader(f"Edit Team: {team.name}")
    
    # Create the form
    with st.form("team_form"):
        name = st.text_input("Team Name", value=team.name)
        description = st.text_area("Description", value=team.description or "", height=100)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button("Save Team")
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state.edit_team_id = None
                st.rerun()
        
        if submitted:
            if not name:
                st.error("Team name is required")
            else:
                # Update team object
                team.name = name
                team.description = description
                
                # Save to database
                team_id = db.save_team(team)
                
                if team_id:
                    st.success("Team saved successfully")
                    st.session_state.edit_team_id = None
                    st.rerun()
                else:
                    st.error("Failed to save team")

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