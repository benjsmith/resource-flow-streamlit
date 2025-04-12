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
    
    # Create the resource trend chart
    fig_resource_trend = create_resource_trend_chart(monthly_data)
    st.plotly_chart(fig_resource_trend, use_container_width=True)
    
    # Period selector for trend chart (month, quarter, year)
    period_options = ["month", "quarter", "year"]
    period = st.selectbox("Time Resolution", period_options, index=0)
    
    # Update chart with selected period
    if period != "month":
        fig_resource_trend = create_resource_trend_chart(monthly_data, period)
        st.plotly_chart(fig_resource_trend, use_container_width=True)
    
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
    demands = db.get_demands()
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
    
    # Sort by date
    upcoming_dates.sort(key=lambda x: x["date"])
    
    # Display as table
    if upcoming_dates:
        data = pd.DataFrame(upcoming_dates)
        # Ensure date column is properly formatted without using dt accessor
        data["formatted_date"] = [d.strftime("%b %d, %Y") if hasattr(d, "strftime") else str(d) 
                                 for d in data["date"]]
        st.dataframe(data[["formatted_date", "event"]], hide_index=True)
    else:
        st.info("No upcoming key dates found.")