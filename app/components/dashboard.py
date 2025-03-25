import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta

from app.database import queries as db
from app.utils.date_utils import get_months_between, format_date_display
from app.utils.data_processor import classify_gap

def create_project_health_chart(projects):
    """Create a donut chart showing project health distribution."""
    if not projects:
        return go.Figure()
    
    df = pd.DataFrame([{
        "status": p.status,
        "count": 1
    } for p in projects])
    
    df = df.groupby("status").sum().reset_index()
    
    fig = go.Figure(data=[go.Pie(
        labels=df["status"],
        values=df["count"],
        hole=.4,
        marker_colors=px.colors.qualitative.Set3
    )])
    
    fig.update_layout(
        showlegend=True,
        margin=dict(l=0, r=0, t=20, b=0),
        height=200
    )
    
    return fig

def create_team_allocation_chart(team_allocations):
    """Create a horizontal bar chart showing team allocation breakdown."""
    if not team_allocations:
        return go.Figure()
    
    df = pd.DataFrame([{
        "team": ta.team_name,  # TeamAllocation has team_name
        "allocated": ta.allocation_fte,
        "available": ta.capacity_fte - ta.allocation_fte
    } for ta in team_allocations])
    
    # Sort by allocated percentage (descending)
    df["allocated_pct"] = df["allocated"] / (df["allocated"] + df["available"]) * 100
    df = df.sort_values("allocated_pct", ascending=False)
    
    fig = go.Figure(data=[
        go.Bar(
            name="Allocated",
            y=df["team"],
            x=df["allocated"],
            orientation="h",
            marker_color="rgb(55, 83, 109)"
        ),
        go.Bar(
            name="Available",
            y=df["team"],
            x=df["available"],
            orientation="h",
            marker_color="rgb(26, 118, 255)"
        )
    ])
    
    fig.update_layout(
        barmode="stack",
        showlegend=True,
        margin=dict(l=0, r=0, t=20, b=0),
        height=max(200, len(df) * 25),
        yaxis=dict(autorange="reversed"),
        xaxis_title="FTE"
    )
    
    return fig

def create_skills_analysis_chart(demands, people):
    """Create a bar chart comparing skills demand vs. capacity."""
    if not demands or not people:
        return go.Figure()
    
    # Safely get skills from an object (handling both string and list formats)
    def get_skills(obj, attr_name):
        skills_attr = getattr(obj, attr_name, None)
        if not skills_attr:
            return []
        
        if isinstance(skills_attr, list):
            return skills_attr
        elif isinstance(skills_attr, str):
            return [s.strip() for s in skills_attr.split(",") if s.strip()]
        return []
    
    # Aggregate skills from demands
    demand_skills = {}
    for d in demands:
        skills_list = get_skills(d, "skills_required")
        for skill in skills_list:
            demand_skills[skill] = demand_skills.get(skill, 0) + d.fte_required
    
    # Aggregate skills from people
    capacity_skills = {}
    for p in people:
        skills_list = get_skills(p, "skills")
        for skill in skills_list:
            capacity_skills[skill] = capacity_skills.get(skill, 0) + 1
    
    # Combine data
    all_skills = sorted(set(list(demand_skills.keys()) + list(capacity_skills.keys())))
    if not all_skills:
        # If no skills found, return empty chart
        fig = go.Figure()
        fig.update_layout(
            title="No skills data available",
            height=300
        )
        return fig
    
    df = pd.DataFrame([{
        "skill": skill,
        "demand": demand_skills.get(skill, 0),
        "capacity": capacity_skills.get(skill, 0)
    } for skill in all_skills])
    
    fig = go.Figure(data=[
        go.Bar(
            name="Demand",
            x=df["skill"],
            y=df["demand"],
            marker_color="rgb(55, 83, 109)"
        ),
        go.Bar(
            name="Capacity",
            x=df["skill"],
            y=df["capacity"],
            marker_color="rgb(26, 118, 255)"
        )
    ])
    
    fig.update_layout(
        barmode="group",
        showlegend=True,
        margin=dict(l=0, r=0, t=20, b=0),
        height=300,
        xaxis_tickangle=-45,
        yaxis_title="FTE / People"
    )
    
    return fig

def create_utilization_trend_chart(monthly_data):
    """Create an area chart showing resource utilization trends."""
    if not monthly_data:
        return go.Figure()
    
    df = pd.DataFrame([{
        "Month": data.year_month,
        "Utilization": (data.allocation_fte / data.capacity_fte * 100) if data.capacity_fte > 0 else 0
    } for data in monthly_data])
    
    fig = go.Figure(data=[
        go.Scatter(
            x=df["Month"],
            y=df["Utilization"],
            fill="tozeroy",
            mode="lines",
            line=dict(color="rgb(26, 118, 255)")
        )
    ])
    
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0),
        height=200,
        yaxis_title="Utilization %",
        yaxis_range=[0, 100]
    )
    
    return fig

def aggregate_data_by_period(monthly_data, period="month"):
    """
    Aggregate monthly data by specified period (month, quarter, or year).
    
    Args:
        monthly_data: List of MonthlyDemandAllocation objects
        period: Aggregation period ("month", "quarter", or "year")
        
    Returns:
        DataFrame with aggregated data
    """
    if not monthly_data:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        "year_month": data.year_month,
        "demand_fte": data.demand_fte,
        "allocation_fte": data.allocation_fte,
        "capacity_fte": data.capacity_fte
    } for data in monthly_data])
    
    # Create time period columns
    df["year"] = df["year_month"].apply(lambda d: d.year)
    df["quarter"] = df["year_month"].apply(lambda d: f"{d.year}-Q{(d.month-1)//3+1}")
    df["month"] = df["year_month"].apply(lambda d: f"{d.year}-{d.month:02d}")
    
    # Choose aggregation column based on period
    if period == "quarter":
        group_col = "quarter"
    elif period == "year":
        group_col = "year"
    else:  # Default to month
        group_col = "month"
    
    # Aggregate by period
    result = df.groupby(group_col).agg({
        "demand_fte": "mean",
        "allocation_fte": "mean",
        "capacity_fte": "mean"
    }).reset_index()
    
    result.rename(columns={group_col: "Period"}, inplace=True)
    return result

def create_resource_trend_chart(monthly_data, period="month"):
    """
    Create a line chart showing capacity vs allocation vs demand over time.
    
    Args:
        monthly_data: List of MonthlyDemandAllocation objects
        period: Time resolution ("month", "quarter", or "year")
        
    Returns:
        Plotly figure with the chart
    """
    if not monthly_data:
        return go.Figure()
    
    # Aggregate data by selected period
    df = aggregate_data_by_period(monthly_data, period)
    
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(go.Scatter(
        x=df["Period"],
        y=df["capacity_fte"],
        name="Capacity",
        line=dict(color="rgb(26, 118, 255)", width=2),
        mode="lines+markers"
    ))
    
    fig.add_trace(go.Scatter(
        x=df["Period"],
        y=df["allocation_fte"],
        name="Allocation",
        line=dict(color="rgb(55, 83, 109)", width=2),
        mode="lines+markers"
    ))
    
    fig.add_trace(go.Scatter(
        x=df["Period"],
        y=df["demand_fte"],
        name="Demand",
        line=dict(color="rgb(244, 67, 54)", width=2),
        mode="lines+markers"
    ))
    
    fig.update_layout(
        showlegend=True,
        margin=dict(l=0, r=0, t=20, b=0),
        height=300,
        yaxis_title="FTE",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def render_dashboard():
    """Render the main dashboard view."""
    st.header("Resource Management Dashboard")
    
    # Get current date range from session state
    start_date, end_date = st.session_state.date_range
    
    # Create metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_people = db.get_total_people_count()
        st.metric("Total People", total_people)
    
    with col2:
        active_projects = db.get_active_projects_count()
        st.metric("Active Projects", active_projects)
    
    with col3:
        open_demands = db.get_open_demands_count()
        st.metric("Open Demands", open_demands)
    
    with col4:
        # Calculate total allocation percentage
        team_allocations = db.get_team_allocations(start_date, end_date)
        if team_allocations:
            total_allocation = sum(ta.allocation_fte for ta in team_allocations)
            total_capacity = sum(ta.capacity_fte for ta in team_allocations)
            allocation_percentage = round((total_allocation / total_capacity * 100) if total_capacity > 0 else 0, 1)
            st.metric("Overall Allocation", f"{allocation_percentage}%")
        else:
            st.metric("Overall Allocation", "0%")
    
    # Project Health Overview
    st.subheader("Project Health Overview")
    projects = db.get_projects()
    fig_project_health = create_project_health_chart(projects)
    st.plotly_chart(fig_project_health, use_container_width=True)
    
    # Team Allocation Breakdown
    st.subheader("Team Allocation Breakdown")
    fig_team_allocation = create_team_allocation_chart(team_allocations)
    st.plotly_chart(fig_team_allocation, use_container_width=True)
    
    # Resource Trends
    st.subheader("Resource Trends")
    monthly_data = db.get_monthly_demand_allocation(start_date, end_date)
    
    # Time resolution selector
    time_resolution = st.radio(
        "Time Resolution",
        ["Monthly", "Quarterly", "Annual"],
        horizontal=True,
        key="time_resolution"
    )
    
    # Map selection to period
    period_map = {
        "Monthly": "month",
        "Quarterly": "quarter",
        "Annual": "year"
    }
    selected_period = period_map.get(time_resolution, "month")
    
    # Create chart with selected resolution
    fig_resource_trend = create_resource_trend_chart(monthly_data, period=selected_period)
    st.plotly_chart(fig_resource_trend, use_container_width=True)
    
    # Create table of aggregated data
    if monthly_data:
        df_agg = aggregate_data_by_period(monthly_data, period=selected_period)
        if not df_agg.empty:
            df_display = pd.DataFrame({
                "Period": df_agg["Period"],
                "Demand": df_agg["demand_fte"].round(1),
                "Allocation": df_agg["allocation_fte"].round(1),
                "Capacity": df_agg["capacity_fte"].round(1),
                "Utilization %": ((df_agg["allocation_fte"] / df_agg["capacity_fte"]) * 100).round(1),
                "Gap": (df_agg["allocation_fte"] - df_agg["demand_fte"]).round(1)
            })
            
            # Add status column
            df_display["Status"] = df_display["Gap"].apply(classify_gap)
            
            # Display as styled dataframe
            st.dataframe(
                df_display.style.apply(lambda x: [
                    "background-color: #ffcdd2" if v == "critical" else
                    "background-color: #ffe0b2" if v == "deficit" else
                    "background-color: #c8e6c9" if v == "balanced" else
                    "background-color: #b3e5fc" if v == "surplus" else ""
                    for v in x
                ], subset=["Status"]),
                use_container_width=True
            )
    
    # Skills Analysis
    st.subheader("Skills Demand vs. Capacity")
    demands = db.get_demands()
    people = db.get_people()
    fig_skills = create_skills_analysis_chart(demands, people)
    st.plotly_chart(fig_skills, use_container_width=True)
    
    # Resource Utilization Trends
    st.subheader("Resource Utilization Trend")
    fig_utilization = create_utilization_trend_chart(monthly_data)
    st.plotly_chart(fig_utilization, use_container_width=True)
    
    # Upcoming Key Dates
    st.subheader("Upcoming Key Dates")
    upcoming_dates = []
    
    # Add project start/end dates
    for project in projects:
        if project.start_date and project.start_date >= date.today():
            upcoming_dates.append({
                "date": project.start_date,
                "event": f"Project Start: {project.name}",
                "type": "project_start"
            })
        if project.end_date and project.end_date >= date.today():
            upcoming_dates.append({
                "date": project.end_date,
                "event": f"Project End: {project.name}",
                "type": "project_end"
            })
    
    # Add demand start/end dates
    for demand in demands:
        if demand.start_date and demand.start_date >= date.today():
            upcoming_dates.append({
                "date": demand.start_date,
                "event": f"Demand Start: {demand.role_required} for {demand.project_name}",
                "type": "demand_start"
            })
        if demand.end_date and demand.end_date >= date.today():
            upcoming_dates.append({
                "date": demand.end_date,
                "event": f"Demand End: {demand.role_required} for {demand.project_name}",
                "type": "demand_end"
            })
    
    if upcoming_dates:
        df_dates = pd.DataFrame(upcoming_dates)
        df_dates = df_dates.sort_values("date").head(10)  # Show next 10 events
        
        for _, row in df_dates.iterrows():
            days_until = (row["date"] - date.today()).days
            st.info(f"{row['date'].strftime('%b %d, %Y')} ({days_until} days) - {row['event']}")
    else:
        st.info("No upcoming key dates found.")