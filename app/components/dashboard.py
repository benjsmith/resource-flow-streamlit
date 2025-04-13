import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from typing import List, Dict

from app.database import queries as db
from app.utils.date_utils import get_months_between, format_date_display
from app.utils.data_processor import classify_gap
from app.utils.plotly_utils import preprocess_dataframe_for_plotly, prepare_figure_for_streamlit

def create_project_health_chart(projects):
    """Create a donut chart showing project health distribution."""
    if not projects:
        return go.Figure()
    
    df = pd.DataFrame([{
        "status": p.status,
        "count": 1
    } for p in projects])
    
    df = df.groupby("status").sum().reset_index()
    
    # Preprocess DataFrame for Plotly
    df = preprocess_dataframe_for_plotly(df)
    
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
    """Create a stacked bar chart showing team allocations."""
    if not team_allocations:
        return go.Figure()
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        "team": ta.team_name or "No Team",
        "allocated": ta.allocation_fte,
        "free": ta.capacity_fte - ta.allocation_fte
    } for ta in team_allocations if ta.capacity_fte > 0])
    
    if df.empty:
        return go.Figure()
    
    # Preprocess DataFrame for Plotly
    df = preprocess_dataframe_for_plotly(df)
    
    # Sort by team name
    df = df.sort_values("team")
    
    # Create stacked bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df["team"],
        y=df["allocated"],
        name="Allocated",
        marker_color="rgb(55, 83, 109)"
    ))
    
    fig.add_trace(go.Bar(
        x=df["team"],
        y=df["free"],
        name="Free Capacity",
        marker_color="rgb(26, 118, 255)"
    ))
    
    fig.update_layout(
        barmode="stack",
        yaxis_title="FTE",
        margin=dict(l=0, r=0, t=20, b=0),
        height=250,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def aggregate_data_by_period(monthly_data: List[Dict], period: str = "month") -> pd.DataFrame:
    """
    Aggregate monthly data by the specified period.
    
    Args:
        monthly_data: List of monthly allocation data dictionaries
        period: Aggregation period ("month", "quarter", or "year")
        
    Returns:
        DataFrame with aggregated data
    """
    # Convert year_month strings to datetime
    df = pd.DataFrame(monthly_data)
    df["year_month"] = pd.to_datetime(df["year_month"])
    df["year"] = df["year_month"].dt.year
    df["month"] = df["year_month"].dt.month
    
    if period == "month":
        # For monthly data, we need to ensure we have all months in the range
        min_date = df["year_month"].min()
        max_date = df["year_month"].max()
        all_months = pd.date_range(start=min_date, end=max_date, freq='MS')
        
        # Create a complete DataFrame with all months
        complete_df = pd.DataFrame({"year_month": all_months})
        complete_df["year"] = complete_df["year_month"].dt.year
        complete_df["month"] = complete_df["year_month"].dt.month
        
        # Merge with original data
        df = pd.merge(complete_df, df, on=["year_month", "year", "month"], how="left")
        
        # Fill missing values with 0
        df = df.fillna(0)
        
        return df
    
    elif period == "quarter":
        df["quarter"] = df["month"].apply(lambda x: (x - 1) // 3 + 1)
        # Group by quarter and sum the values
        return df.groupby(["year", "quarter"]).agg({
            "fte_demand": "sum",
            "fte_allocated": "sum",
            "fte_gap": "sum",
            "capacity_fte": "mean"  # Use mean for capacity as it's constant
        }).reset_index()
    
    else:  # year
        # Group by year and sum the values
        return df.groupby("year").agg({
            "fte_demand": "sum",
            "fte_allocated": "sum",
            "fte_gap": "sum",
            "capacity_fte": "mean"  # Use mean for capacity as it's constant
        }).reset_index()

def create_resource_trend_chart(monthly_data: List[Dict], period: str = "month") -> go.Figure:
    """
    Create a line chart showing resource trends over time.
    
    Args:
        monthly_data: List of monthly allocation data dictionaries
        period: Time period for aggregation ("month", "quarter", or "year")
        
    Returns:
        Plotly figure object
    """
    df = aggregate_data_by_period(monthly_data, period)
    
    # Create time labels
    if period == "month":
        df["time_label"] = df.apply(lambda x: f"{x['year']}-{x['month']:02d}", axis=1)
    elif period == "quarter":
        df["time_label"] = df.apply(lambda x: f"{x['year']} Q{x['quarter']}", axis=1)
    else:
        df["time_label"] = df["year"].astype(str)
    
    # Create the figure
    fig = go.Figure()
    
    # Add demand line
    fig.add_trace(go.Scatter(
        x=df["time_label"],
        y=df["fte_demand"],
        name="Demand",
        line=dict(color="red", width=2)
    ))
    
    # Add allocation line
    fig.add_trace(go.Scatter(
        x=df["time_label"],
        y=df["fte_allocated"],
        name="Allocated",
        line=dict(color="green", width=2)
    ))
    
    # Add capacity line
    fig.add_trace(go.Scatter(
        x=df["time_label"],
        y=df["capacity_fte"],
        name="Capacity",
        line=dict(color="blue", width=2, dash="dash")
    ))
    
    # Update layout
    fig.update_layout(
        title="Resource Trends",
        xaxis_title="Time Period",
        yaxis_title="FTE",
        showlegend=True,
        height=400
    )
    
    return fig

def render_dashboard():
    """Render the dashboard view."""
    st.title("Resource Flow Dashboard")
    
    # Get date range from session state
    start_date = st.session_state.date_range[0]
    end_date = st.session_state.date_range[1]
    
    # Tab navigation for different dashboard views
    tabs = st.tabs(["Overview", "Allocations", "Projects"])
    
    with tabs[0]:  # Overview tab
        # Get data
        projects = db.get_projects()
        monthly_data = db.get_monthly_demand_allocation(start_date, end_date)
        team_allocations = db.get_team_allocations(start_date, end_date)
        
        # Create layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Project Health")
            fig_project_health = create_project_health_chart(projects)
            st.plotly_chart(fig_project_health, use_container_width=True)
        
        with col2:
            st.subheader("Team Allocation")
            fig_team_allocation = create_team_allocation_chart(team_allocations)
            st.plotly_chart(fig_team_allocation, use_container_width=True)
        
        # Resource trend over time
        st.subheader("Resource Trend")
        
        # Period selector
        period = st.radio(
            "Time Period",
            ["Month", "Quarter", "Year"],
            horizontal=True,
            key="trend_period"
        )
        
        fig_resource_trend = create_resource_trend_chart(
            monthly_data, 
            period=period.lower()
        )
        
        st.plotly_chart(fig_resource_trend, use_container_width=True)
        
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
            # Ensure date column is properly formatted
            data["formatted_date"] = [d.strftime("%b %d, %Y") if hasattr(d, "strftime") else str(d) 
                                    for d in data["date"]]
            st.dataframe(data[["formatted_date", "event"]], hide_index=True)
        else:
            st.info("No upcoming key dates found.")
    
    with tabs[1]:  # Allocations tab
        # Get allocations data
        monthly_data = db.get_monthly_demand_allocation(start_date, end_date)
        resources_by_project = db.get_allocations_by_project()
        
        st.subheader("Resource Allocation Overview")
        
        # Current month summary
        today = date.today()
        current_month_first_day = date(today.year, today.month, 1)
        try:
            current_month_data = next(
                m for m in monthly_data 
                if pd.to_datetime(m["year_month"]).date() == current_month_first_day
            )
        except StopIteration:
            current_month_data = {
                "fte_demand": 0,
                "fte_allocated": 0,
                "fte_gap": 0,
                "capacity_fte": 0
            }
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Capacity", 
                f"{current_month_data['capacity_fte']:.1f} FTE"
            )
        
        with col2:
            st.metric(
                "Allocation", 
                f"{current_month_data['fte_allocated']:.1f} FTE",
                f"{100 * current_month_data['fte_allocated'] / current_month_data['capacity_fte']:.0f}%" 
                if current_month_data['capacity_fte'] > 0 else "N/A"
            )
        
        with col3:
            st.metric(
                "Demand", 
                f"{current_month_data['fte_demand']:.1f} FTE"
            )
        
        with col4:
            gap = current_month_data['capacity_fte'] - current_month_data['fte_demand']
            gap_status = classify_gap(gap, current_month_data['capacity_fte'])
            
            st.metric(
                "Gap", 
                f"{gap:.1f} FTE",
                delta_color="normal" if gap_status == "optimal" else "inverse",
            )
        
        # Project allocation breakdown
        st.subheader("Project Allocation Breakdown")
        if resources_by_project:
            df = pd.DataFrame(resources_by_project)
            st.dataframe(
                df[["project_name", "num_people", "total_fte"]],
                column_config={
                    "project_name": "Project",
                    "num_people": "People",
                    "total_fte": "FTE"
                },
                hide_index=True
            )
        else:
            st.info("No project allocations found.")
    
    with tabs[2]:  # Projects tab
        # Get project data
        projects = db.get_projects()
        
        st.subheader("Project Overview")
        
        if projects:
            # Count projects by status
            status_counts = {}
            for p in projects:
                if p.status not in status_counts:
                    status_counts[p.status] = 0
                status_counts[p.status] += 1
            
            # Display status metrics
            status_cols = st.columns(len(status_counts))
            for i, (status, count) in enumerate(status_counts.items()):
                with status_cols[i]:
                    st.metric(
                        f"{status.title()}", 
                        count
                    )
            
            # Project timeline
            from app.visualizations.gantt_chart import create_project_gantt
            
            st.subheader("Project Timeline")
            fig_project_timeline = create_project_gantt(projects)
            st.plotly_chart(fig_project_timeline, use_container_width=True)
        else:
            st.info("No projects found. Add some projects to see the overview.")