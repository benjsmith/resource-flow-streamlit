import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta

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

def aggregate_data_by_period(monthly_data, period="month"):
    """Aggregate data by period (month, quarter, or year)."""
    df = pd.DataFrame([{
        "month": m.year_month.month,
        "year": m.year_month.year,
        "month_name": m.year_month.strftime("%b"),
        "quarter": f"Q{(m.year_month.month-1)//3+1} {m.year_month.year}",
        "year_str": str(m.year_month.year),
        "capacity_fte": m.capacity_fte,
        "allocation_fte": m.allocation_fte,
        "demand_fte": m.demand_fte,
        "gap_fte": m.capacity_fte - m.demand_fte
    } for m in monthly_data])
    
    if df.empty:
        return pd.DataFrame(columns=["Period", "capacity_fte", "allocation_fte", "demand_fte", "gap_fte"])
    
    # Group by period and aggregate
    group_by = ""
    if period == "month":
        df["Period"] = df["month_name"] + " " + df["year"].astype(str)
        group_by = "Period"
    elif period == "quarter":
        df["Period"] = df["quarter"]
        group_by = "Period"
    else:  # year
        df["Period"] = df["year_str"]
        group_by = "Period"
    
    # Aggregate by period
    result = df.groupby(group_by).agg({
        "capacity_fte": "mean",
        "allocation_fte": "mean",
        "demand_fte": "mean",
        "gap_fte": "mean"
    }).reset_index()
    
    # Sort by year and month
    if period == "month":
        # Create a sortable column (year*100 + month)
        df["sort_key"] = df["year"] * 100 + df["month"]
        sort_order = df.sort_values("sort_key")["Period"].unique()
        result["Period"] = pd.Categorical(
            result["Period"],
            categories=sort_order,
            ordered=True
        )
        result = result.sort_values("Period")
    elif period == "quarter":
        # Create a sortable column based on year and quarter
        df["sort_key"] = df["year"] * 10 + (df["month"] - 1) // 3 + 1
        # Get unique quarters in order
        quarters = df.sort_values("sort_key")["quarter"].unique()
        result["Period"] = pd.Categorical(
            result["Period"],
            categories=quarters,
            ordered=True
        )
        result = result.sort_values("Period")
    else:  # year
        result = result.sort_values("Period")
    
    # Preprocess DataFrame for Plotly
    result = preprocess_dataframe_for_plotly(result)
    
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
    st.title("Resource Flow Dashboard")
    
    # Get date range from session state
    start_date, end_date = st.session_state.date_range
    
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
            st.plotly_chart(prepare_figure_for_streamlit(fig_project_health), use_container_width=True)
        
        with col2:
            st.subheader("Team Allocation")
            fig_team_allocation = create_team_allocation_chart(team_allocations)
            st.plotly_chart(prepare_figure_for_streamlit(fig_team_allocation), use_container_width=True)
        
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
        
        st.plotly_chart(prepare_figure_for_streamlit(fig_resource_trend), use_container_width=True)
        
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
    
    with tabs[1]:  # Allocations tab
        # Get allocations data
        monthly_data = db.get_monthly_demand_allocation(start_date, end_date)
        resources_by_project = db.get_allocations_by_project()
        
        st.subheader("Resource Allocation Overview")
        
        # Current month summary
        today = date.today()
        current_month_first_day = date(today.year, today.month, 1)
        current_month_data = next(
            (m for m in monthly_data if m.year_month == current_month_first_day), 
            None
        )
        
        if current_month_data:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Capacity", 
                    f"{current_month_data.capacity_fte:.1f} FTE",
                )
            
            with col2:
                st.metric(
                    "Allocation", 
                    f"{current_month_data.allocation_fte:.1f} FTE",
                    f"{100 * current_month_data.allocation_fte / current_month_data.capacity_fte:.0f}%" 
                    if current_month_data.capacity_fte > 0 else "N/A"
                )
            
            with col3:
                st.metric(
                    "Demand", 
                    f"{current_month_data.demand_fte:.1f} FTE",
                )
            
            with col4:
                gap = current_month_data.capacity_fte - current_month_data.demand_fte
                gap_status = classify_gap(gap, current_month_data.capacity_fte)
                
                st.metric(
                    "Gap", 
                    f"{gap:.1f} FTE",
                    delta_color="normal" if gap_status == "optimal" else "inverse",
                )
    
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
                        count,
                    )
            
            # Project timeline
            from app.visualizations.gantt_chart import create_project_gantt
            
            st.subheader("Project Timeline")
            fig_project_timeline = create_project_gantt(projects)
            st.plotly_chart(prepare_figure_for_streamlit(fig_project_timeline), use_container_width=True)
        else:
            st.info("No projects found. Add some projects to see the overview.")