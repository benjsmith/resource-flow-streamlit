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
        demands: List of Demand objects
        
    Returns:
        Plotly figure with the Gantt chart
    """
    if not demands:
        return go.Figure()
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            "id": demand.id,
            "project_name": demand.project_name,
            "role_required": demand.role_required,
            "start_date": demand.start_date,
            "end_date": demand.end_date,
            "status": demand.status,
            "fte_required": demand.fte_required,
            "skills_required": ", ".join(demand.skills_required) if demand.skills_required else ""
        }
        for demand in demands
    ])
    
    # Create custom y-axis label
    df["demand_label"] = df.apply(
        lambda row: f"{row['project_name']}: {row['role_required']} ({row['fte_required']} FTE)", 
        axis=1
    )
    
    # Create color mapping for status
    color_map = {
        "open": "#F44336",           # Red
        "partially_filled": "#FF9800", # Orange
        "filled": "#4CAF50",         # Green
        "cancelled": "#9E9E9E"       # Gray
    }
    
    # Create figure
    fig = px.timeline(
        df, 
        x_start="start_date", 
        x_end="end_date", 
        y="demand_label",
        color="status",
        color_discrete_map=color_map,
    )
    
    # Adjust bar width based on FTE (thicker bars for higher FTE)
    for i, demand in enumerate(df.iterrows()):
        # Normalize the width between 0.2 and 1.0 based on FTE
        # Assuming most FTEs will be between 0.1 and 2.0
        width = min(1.0, max(0.2, demand[1]["fte_required"] / 2))
        fig.data[0].marker.line.width = 0  # Remove border
        if len(fig.data) > 0 and i < len(fig.data[0].width):
            fig.data[0].width[i] = width
    
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
    
    # Improve hover information
    hover_template = (
        "<b>%{y}</b><br>" +
        "Start: %{x[0]|%b %d, %Y}<br>" +
        "End: %{x[1]|%b %d, %Y}<br>" +
        "Status: %{marker.color}<br>" +
        "<extra></extra>"
    )
    fig.update_traces(hovertemplate=hover_template)
    
    return fig

def create_allocation_gantt(allocations: List) -> go.Figure:
    """
    Create a Gantt chart for resource allocations.
    
    Args:
        allocations: List of Allocation objects
        
    Returns:
        Plotly figure with the Gantt chart
    """
    if not allocations:
        return go.Figure()
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            "id": allocation.id,
            "person_name": allocation.person_name,
            "project_name": allocation.project_name,
            "start_date": allocation.start_date,
            "end_date": allocation.end_date,
            "fte_allocated": allocation.fte_allocated,
            "notes": allocation.notes if allocation.notes else ""
        }
        for allocation in allocations
    ])
    
    # Create figure
    fig = px.timeline(
        df, 
        x_start="start_date", 
        x_end="end_date", 
        y="person_name",
        color="project_name",
        hover_data=["fte_allocated", "notes"]
    )
    
    # Adjust bar width based on FTE (thicker bars for higher FTE)
    for i, allocation in enumerate(df.iterrows()):
        # Normalize the width between 0.2 and 1.0 based on FTE
        width = min(1.0, max(0.2, allocation[1]["fte_allocated"]))
        fig.data[0].marker.line.width = 0  # Remove border
        if len(fig.data) > 0 and i < len(fig.data[0].width):
            fig.data[0].width[i] = width
    
    # Mark today's date with a vertical line
    today = date.today()
    fig.add_vline(x=today, line_width=2, line_dash="dash", line_color="red")
    
    # Customize layout
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        legend_title="Project",
        margin=dict(l=10, r=10, t=10, b=10),
    )
    
    # Improve hover information
    hover_template = (
        "<b>%{y}</b> on <b>%{customdata[3]}</b><br>" +
        "Start: %{x[0]|%b %d, %Y}<br>" +
        "End: %{x[1]|%b %d, %Y}<br>" +
        "FTE: %{customdata[0]}<br>" +
        "Notes: %{customdata[1]}<br>" +
        "<extra></extra>"
    )
    fig.update_traces(hovertemplate=hover_template)
    
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