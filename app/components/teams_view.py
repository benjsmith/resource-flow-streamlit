import streamlit as st
import pandas as pd

from app.database import queries as db
from app.models.data_models import Team

def render_teams_view():
    """Render the teams management view."""
    st.header("Teams Management")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Teams List", "Add/Edit Team"])
    
    with tab1:
        render_teams_list()
    
    with tab2:
        render_teams_form()

def render_teams_list():
    """Render the list of teams with actions."""
    # Get all teams
    teams = db.get_teams()
    
    if teams:
        # Convert to DataFrame for display
        teams_data = []
        for team in teams:
            teams_data.append({
                "ID": team.id,
                "Name": team.name,
                "Description": team.description
            })
        
        df = pd.DataFrame(teams_data)
        
        # Display the data
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Add section for actions
        st.subheader("Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_team_id = st.selectbox(
                "Select Team", 
                options=[t.id for t in teams],
                format_func=lambda x: next((t.name for t in teams if t.id == x), "")
            )
        
        with col2:
            if st.button("View Team Members"):
                team = next((t for t in teams if t.id == selected_team_id), None)
                if team:
                    render_team_members(team)
        
        with col3:
            if st.button("Edit Team"):
                # Set the team ID for editing and switch to the edit tab
                st.session_state.edit_team_id = selected_team_id
                st.rerun()
    else:
        st.info("No teams found. Add some teams to get started.")

def render_team_members(team):
    """Render members of a specific team."""
    st.subheader(f"Members of {team.name}")
    
    # Get team members
    people = db.get_people(team_id=team.id)
    
    if people:
        # Convert to DataFrame for display
        members_data = []
        for person in people:
            members_data.append({
                "ID": person.id,
                "Name": person.name,
                "Role": person.role,
                "Skills": ", ".join(person.skills) if person.skills else ""
            })
        
        df = pd.DataFrame(members_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(f"No members found in team {team.name}")

def render_teams_form():
    """Render the form for adding or editing a team."""
    # Check if we're editing an existing team
    edit_mode = "edit_team_id" in st.session_state and st.session_state.edit_team_id is not None
    
    if edit_mode:
        team = db.get_team(st.session_state.edit_team_id)
        if not team:
            st.error(f"Team with ID {st.session_state.edit_team_id} not found")
            return
        st.subheader(f"Edit Team: {team.name}")
    else:
        # Create a new team object
        team = Team(
            name="",
            description="",
            id=None
        )
        st.subheader("Add New Team")
    
    # Create a form for the team details
    with st.form("team_form"):
        name = st.text_input("Team Name", value=team.name)
        description = st.text_area("Description", value=team.description, height=100)
        
        submitted = st.form_submit_button("Save Team")
        
        if submitted:
            if not name:
                st.error("Team name is required")
            else:
                # Create or update the team object
                team.name = name
                team.description = description
                
                # Save to database
                team_id = db.save_team(team)
                
                if team_id:
                    action = "updated" if edit_mode else "added"
                    st.success(f"Team {action} successfully")
                    
                    # Clear the edit team ID
                    if edit_mode:
                        st.session_state.edit_team_id = None
                        st.rerun()
                else:
                    st.error("Failed to save team") 