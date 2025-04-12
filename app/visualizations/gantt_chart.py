import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

def create_project_gantt(projects: List) -> go.Figure:
    """
    Create a Gantt chart for projects.
    
    Args:
        projects: List of Project objects
        
    Returns:
        Plotly figure with the Gantt chart
    """
    if not projects:
        return go.Figure()
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            "id": project.id,
            "name": project.name,
            "start_date": project.start_date,
            "end_date": project.end_date,
            "status": project.status,
            "description": project.description
        }
        for project in projects
    ])
    
    # Create color mapping for status
    color_map = {
        "planning": "#64B5F6",  # Light Blue
        "active": "#4CAF50",    # Green
        "completed": "#9E9E9E", # Gray
        "cancelled": "#F44336"  # Red
    }
    
    # Create figure
    fig = px.timeline(
        df, 
        x_start="start_date", 
        x_end="end_date", 
        y="name",
        color="status",
        color_discrete_map=color_map,
        hover_data=["description"]
    )
    
    # Mark today's date with a vertical line
    today = date.today()
    fig.add_vline(x=today, line_width=2, line_dash="dash", line_color="red")
    
    # Customize layout
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        legend_title="Status",
        margin=dict(l=10, r=10, t=10, b=10),
    )
    
    # Add hover template
    fig.update_traces(
        hovertemplate=
        "<b>%{y}</b><br>" +
        "Start: %{x[0]|%b %d, %Y}<br>" +
        "End: %{x[1]|%b %d, %Y}<br>" +
        "Status: %{customdata[0]}<br>" +
        "<extra></extra>"
    )
    
    return fig

def create_demand_gantt(demands: List) -> go.Figure:
    """
    Create a Gantt chart for resource demands.
    
    Args:
        demands: List of Demand objects or DataFrame
        
    Returns:
        Plotly figure with the Gantt chart
    """
    # Handle empty input
    if isinstance(demands, pd.DataFrame):
        if demands.empty:
            return go.Figure()
        df = demands
    elif not demands:
        return go.Figure()
    else:
        # Convert list of objects to DataFrame
        df = pd.DataFrame([{
            "id": demand.id,
            "project_name": demand.project_name,
            "role_required": demand.role_required,
            "fte_required": demand.fte_required,
            "start_date": demand.start_date,
            "end_date": demand.end_date,
            "status": demand.status,
            "priority": demand.priority
        } for demand in demands])
    
    # Status-based color mapping
    color_map = {
        "unfilled": "rgb(239, 85, 59)",    # Red for unfilled
        "open": "rgb(239, 85, 59)",        # Red for open
        "partially_filled": "rgb(255, 161, 90)",  # Orange for partially filled
        "filled": "rgb(99, 110, 250)",     # Blue for filled
        "cancelled": "rgb(155, 155, 155)"  # Gray for cancelled
    }
    
    # Create figure using px.timeline which handles dates better
    fig = px.timeline(
        df, 
        x_start="start_date", 
        x_end="end_date", 
        y="project_name",
        color="status",
        color_discrete_map=color_map,
        hover_data=["role_required", "fte_required"],
    )
    
    # Customize traces
    for trace in fig.data:
        trace.marker.line.width = 0
        # Set uniform thickness for all bars
        trace.width = 0.6
    
    # Mark today's date with a vertical line
    today = date.today()
    fig.add_vline(x=today, line_width=2, line_dash="dash", line_color="red")
    
    # Customize layout
    fig.update_layout(
        title="",
        xaxis=dict(
            title="",
            tickformat='%b %Y',
        ),
        yaxis=dict(
            title="",
            autorange="reversed",  # Reverse to match the typical gantt chart ordering
            tickfont=dict(size=12),
        ),
        bargap=0.3,  # Gap between bars for different categories
        height=max(400, len(df.project_name.unique()) * 50),  # Adjust height based on number of projects
        margin=dict(l=10, r=10, t=20, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title=""
        )
    )
    
    # Improve hover information
    hover_template = (
        "Project: <b>%{y}</b><br>" +
        "Role: <b>%{customdata[0]}</b><br>" +
        "FTE: %{customdata[1]:.1f}<br>" +
        "Start: %{base|%b %d, %Y}<br>" +
        "End: %{x|%b %d, %Y}<br>" +
        "Status: <b>%{fullData.name}</b><br>" +
        "<extra></extra>"
    )
    fig.update_traces(hovertemplate=hover_template)
    
    # Remove duplicate entry for legend if there is one
    fig.for_each_trace(lambda trace: trace.update(showlegend=False) 
                      if trace.name == "return fig" else None)
    
    return fig

def create_allocation_gantt(allocations: List) -> go.Figure:
    """
    Create a Gantt chart for resource allocations.
    
    Args:
        allocations: List of Allocation objects or DataFrame
        
    Returns:
        Plotly figure with the Gantt chart
    """
    # Handle empty input
    if isinstance(allocations, pd.DataFrame):
        if allocations.empty:
            return go.Figure()
        df = allocations
    elif not allocations:
        return go.Figure()
    else:
        # Convert list of objects to DataFrame
        df = pd.DataFrame([{
            "id": allocation.id,
            "person_name": allocation.person_name,
            "project_name": allocation.project_name,
            "start_date": allocation.start_date,
            "end_date": allocation.end_date,
            "fte_allocated": allocation.fte_allocated,
            "notes": allocation.notes if allocation.notes else ""
        } for allocation in allocations])
    
    # Create figure using px.timeline which handles dates better
    fig = px.timeline(
        df, 
        x_start="start_date", 
        x_end="end_date", 
        y="person_name",
        color="project_name",
        hover_data=["fte_allocated", "notes"],
    )
    
    # Adjust bar width for each trace
    for trace in fig.data:
        trace.width = 0.6
        trace.marker.line.width = 0
    
    # Mark today's date with a vertical line
    today = date.today()
    fig.add_vline(x=today, line_width=2, line_dash="dash", line_color="red")
    
    # Customize layout
    fig.update_layout(
        title="",
        xaxis=dict(
            title="",
            tickformat='%b %Y',
        ),
        yaxis=dict(
            title="",
            autorange="reversed",  # Reverse to match the typical gantt chart ordering
            tickfont=dict(size=12),
        ),
        bargap=0.3,  # Gap between bars for different persons
        height=max(400, len(df.person_name.unique()) * 50),  # Adjust height based on number of people
        margin=dict(l=10, r=10, t=20, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title=""
        )
    )
    
    # Improve hover information
    hover_template = (
        "<b>%{y}</b><br>" +
        "Project: <b>%{fullData.name}</b><br>" +
        "Start: %{base|%b %d, %Y}<br>" +
        "End: %{x|%b %d, %Y}<br>" +
        "FTE: %{customdata[0]:.1f}<br>" +
        "%{customdata[1]}<br>" +  # Notes (only shown if present)
        "<extra></extra>"
    )
    fig.update_traces(hovertemplate=hover_template)
    
    # Remove any duplicate legend entries
    fig.for_each_trace(lambda trace: trace.update(showlegend=False) 
                      if trace.name == "return fig" else None)
    
    # Remove the duplicate legend line at the end of the file
    if len(fig.data) > 0 and fig.data[-1].name == "return fig":
        fig.data = fig.data[:-1]
    
    return fig

def create_heatmap(df: pd.DataFrame, x_col: str, y_col: str, value_col: str, title: str) -> go.Figure:
    """
    Create a heatmap for resource allocation or demand
    
    Args:
        df (pd.DataFrame): DataFrame with data
        x_col (str): Column name for x-axis
        y_col (str): Column name for y-axis
        value_col (str): Column name for values
        title (str): Chart title
        
    Returns:
        go.Figure: Plotly figure with heatmap
    """
    # Pivot data for heatmap
    pivot_df = df.pivot_table(
        values=value_col,
        index=y_col,
        columns=x_col,
        aggfunc='sum',
        fill_value=0
    )
    
    # Create heatmap
    fig = px.imshow(
        pivot_df,
        labels=dict(x=x_col, y=y_col, color=value_col),
        x=pivot_df.columns,
        y=pivot_df.index,
        color_continuous_scale="Viridis",
        aspect="auto"
    )
    
    fig.update_layout(
        title=title,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    
    return fig 
    return fig 