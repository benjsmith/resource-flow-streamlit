import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
import calendar
from typing import Tuple, List, Dict

from app.database import queries as db
from app.models.data_models import MonthlyDemandAllocation
from app.utils.data_processor import convert_dataframe_for_plotly, add_gap_classification
from app.utils.date_utils import get_months_between, format_date_display, is_quarter_start

def format_date_label(dt: date) -> str:
    """
    Format a date for display in charts
    
    Args:
        dt (date): Date to format
        
    Returns:
        str: Formatted date string
    """
    return f"{calendar.month_abbr[dt.month]} {dt.year}"

def render_dashboard():
    """
    Render the main dashboard view with key metrics and visualizations.
    """
    st.header("Resource Planning Dashboard 📊")
    
    # Get date range from session state
    start_date, end_date = st.session_state.date_range
    
    # Connect to database
    conn = db.get_db_connection()
    
    # Fetch data for dashboard
    try:
        # Get monthly demand and allocation data
        monthly_data = db.get_monthly_demand_allocation(start_date, end_date)
        if not monthly_data:
            st.warning("No data available for the selected date range.")
            return
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_total_people_metric()
        with col2:
            render_active_projects_metric()
        with col3:
            render_open_demands_metric()
        with col4:
            render_allocation_rate_metric(monthly_data)
        
        st.markdown("---")
        
        # Main charts section
        tab1, tab2, tab3 = st.tabs(["Demand vs. Allocation", "Team Allocation", "Project Timeline"])
        
        with tab1:
            render_demand_vs_allocation_chart(monthly_data, start_date, end_date)
            
        with tab2:
            render_team_allocation_chart(start_date, end_date)
            
        with tab3:
            render_project_timeline()
    
    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")
    finally:
        if conn:
            conn.close()

def render_total_people_metric():
    """Render metric showing total number of people."""
    total_people = db.get_total_people_count()
    st.metric("Total People", total_people)

def render_active_projects_metric():
    """Render metric showing active projects count."""
    active_projects = db.get_active_projects_count()
    st.metric("Active Projects", active_projects)

def render_open_demands_metric():
    """Render metric showing open demand count."""
    open_demands = db.get_open_demands_count()
    st.metric("Open Demands", open_demands)

def render_allocation_rate_metric(monthly_data: List[MonthlyDemandAllocation]):
    """
    Render metric showing allocation rate (allocated FTE / demanded FTE).
    
    Args:
        monthly_data: List of monthly demand and allocation data
    """
    if not monthly_data:
        st.metric("Allocation Rate", "N/A")
        return
        
    # Calculate allocation rate for the current month
    today = date.today()
    current_month_data = next(
        (m for m in monthly_data if m.year_month.year == today.year and m.year_month.month == today.month), 
        None
    )
    
    if current_month_data and current_month_data.demand_fte > 0:
        allocation_rate = (current_month_data.allocation_fte / current_month_data.demand_fte) * 100
        delta = allocation_rate - 100 if allocation_rate <= 100 else None
        st.metric("Allocation Rate", f"{allocation_rate:.1f}%", delta=f"{delta:.1f}%" if delta else None)
    else:
        st.metric("Allocation Rate", "N/A")

def render_demand_vs_allocation_chart(monthly_data: List[MonthlyDemandAllocation], 
                                     start_date: date, 
                                     end_date: date):
    """
    Render a chart comparing demand vs allocation over time.
    
    Args:
        monthly_data: List of monthly demand and allocation data
        start_date: Start date for the chart
        end_date: End date for the chart
    """
    st.subheader("Demand vs. Allocation Over Time")
    
    # Convert to Polars DataFrame
    data = {
        "year_month": [m.year_month for m in monthly_data],
        "demand_fte": [m.demand_fte for m in monthly_data],
        "allocation_fte": [m.allocation_fte for m in monthly_data],
        "gap_fte": [m.allocation_fte - m.demand_fte for m in monthly_data]
    }
    
    df = pl.DataFrame(data)
    
    # Add gap classification
    df = add_gap_classification(df, "gap_fte")
    
    # Format date for display
    df = df.with_columns([
        pl.col("year_month").map_elements(lambda d: format_date_display(d, "month_year")).alias("month_display"),
        pl.col("year_month").map_elements(lambda d: is_quarter_start(d)).alias("is_quarter_start")
    ])
    
    # Convert to pandas for plotly
    pdf = convert_dataframe_for_plotly(df)
    
    # Create figure
    fig = go.Figure()
    
    # Add demand line
    fig.add_trace(go.Scatter(
        x=pdf['month_display'],
        y=pdf['demand_fte'],
        mode='lines+markers',
        name='Demand',
        line=dict(color='#FF9800', width=3),
        marker=dict(size=8)
    ))
    
    # Add allocation line
    fig.add_trace(go.Scatter(
        x=pdf['month_display'],
        y=pdf['allocation_fte'],
        mode='lines+markers',
        name='Allocation',
        line=dict(color='#2196F3', width=3),
        marker=dict(size=8)
    ))
    
    # Add gap bars
    colors = pdf['gap_classification'].map({
        'surplus': '#4CAF50',
        'balanced': '#8BC34A',
        'deficit': '#FF9800',
        'critical': '#F44336'
    })
    
    fig.add_trace(go.Bar(
        x=pdf['month_display'],
        y=pdf['gap_fte'],
        name='Gap',
        marker_color=colors,
        opacity=0.7
    ))
    
    # Add vertical lines for quarter starts
    for i, row in pdf[pdf['is_quarter_start']].iterrows():
        fig.add_shape(
            type="line",
            x0=row['month_display'],
            y0=0,
            x1=row['month_display'],
            y1=max(pdf['demand_fte'].max(), pdf['allocation_fte'].max()) * 1.1,
            line=dict(color="rgba(0,0,0,0.3)", width=1, dash="dash")
        )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="FTE",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=40, b=80),
        hovermode="x unified"
    )
    
    # Create custom hover template
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{y:.2f} FTE<extra></extra>"
    )
    
    # Show the figure
    st.plotly_chart(fig, use_container_width=True)
    
    # Add color legend for gap classification
    cols = st.columns(4)
    with cols[0]:
        st.markdown("**Gap Legend:**")
    with cols[1]:
        st.markdown("🟢 Surplus (>0.5 FTE)")
    with cols[2]:
        st.markdown("🟡 Deficit (<-0.5 FTE)")
    with cols[3]:
        st.markdown("🔴 Critical (<-1 FTE)")

def render_team_allocation_chart(start_date: date, end_date: date):
    """
    Render a chart showing allocation by team.
    
    Args:
        start_date: Start date for the chart
        end_date: End date for the chart
    """
    st.subheader("Team Allocation")
    
    # Get team allocation data
    team_allocations = db.get_team_allocations(start_date, end_date)
    
    if not team_allocations:
        st.info("No team allocation data available.")
        return
    
    # Create DataFrame
    df = pl.DataFrame({
        "team_name": [ta.team_name for ta in team_allocations],
        "allocation_fte": [ta.allocation_fte for ta in team_allocations],
        "capacity_fte": [ta.capacity_fte for ta in team_allocations]
    })
    
    # Calculate utilization percentage
    df = df.with_columns([
        (pl.col("allocation_fte") / pl.col("capacity_fte") * 100).alias("utilization")
    ])
    
    # Convert to pandas for plotly
    pdf = convert_dataframe_for_plotly(df)
    
    # Create figure
    fig = go.Figure()
    
    # Add bars for allocation
    fig.add_trace(go.Bar(
        x=pdf['team_name'],
        y=pdf['allocation_fte'],
        name='Allocated FTE',
        marker_color='#2196F3'
    ))
    
    # Add line for capacity
    fig.add_trace(go.Scatter(
        x=pdf['team_name'],
        y=pdf['capacity_fte'],
        mode='markers',
        name='Capacity FTE',
        marker=dict(size=12, color='#FF5722', symbol='line-ns', line=dict(width=3, color='#FF5722'), 
                    line_width=4)
    ))
    
    # Update layout
    fig.update_layout(
        xaxis_title="Team",
        yaxis_title="FTE",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=40, b=80)
    )
    
    # Show the figure
    st.plotly_chart(fig, use_container_width=True)
    
    # Show utilization table
    st.subheader("Team Utilization")
    
    # Format table data
    table_data = pdf[['team_name', 'allocation_fte', 'capacity_fte', 'utilization']].copy()
    table_data['utilization'] = table_data['utilization'].round(1).astype(str) + '%'
    table_data.columns = ['Team', 'Allocated FTE', 'Capacity FTE', 'Utilization']
    
    # Display table
    st.dataframe(table_data, use_container_width=True, hide_index=True)

def render_project_timeline():
    """Render a timeline of projects."""
    from app.visualizations.gantt_chart import create_project_gantt
    
    st.subheader("Project Timeline")
    
    # Get projects
    projects = db.get_projects()
    
    if not projects:
        st.info("No project data available.")
        return
    
    # Create project gantt chart
    fig = create_project_gantt(projects)
    
    # Show the figure
    st.plotly_chart(fig, use_container_width=True)