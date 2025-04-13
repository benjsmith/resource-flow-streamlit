"""
Utilities for working with Plotly charts in the Resource Flow application.
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, datetime, timedelta

def preprocess_dataframe_for_plotly(df):
    """
    Preprocess a DataFrame to ensure all data is JSON serializable *before*
    it's used to create a Plotly figure. Converts dates, timedeltas, and numpy types.
    """
    if df is None or df.empty:
        return pd.DataFrame()
        
    df = df.copy()
    
    for col in df.columns:
        # Handle numpy types
        if pd.api.types.is_integer_dtype(df[col]):
            df[col] = df[col].astype('int64')
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].astype('float64')
        elif pd.api.types.is_bool_dtype(df[col]):
            df[col] = df[col].astype('bool')
        
        # Handle object columns with numpy types
        if df[col].dtype == np.dtype('object'):
            df[col] = df[col].apply(lambda x: (
                int(x) if isinstance(x, np.integer) else
                float(x) if isinstance(x, np.floating) else
                bool(x) if isinstance(x, np.bool_) else
                x
            ))
            
        # Handle datetime types
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        elif df[col].apply(lambda x: isinstance(x, (date, datetime))).any():
            df[col] = df[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, (date, datetime)) else x)

        # Handle timedelta types
        if pd.api.types.is_timedelta64_dtype(df[col]):
            df[col] = df[col].apply(lambda x: x.total_seconds() if pd.notna(x) else None)
        elif df[col].apply(lambda x: isinstance(x, timedelta)).any():
            df[col] = df[col].apply(lambda x: x.total_seconds() if isinstance(x, timedelta) else x)
            
        # Replace any remaining non-serializable objects with None
        df[col] = df[col].apply(lambda x: None if not isinstance(x, (str, int, float, bool, type(None))) else x)
            
    return df

def prepare_figure_for_streamlit(fig):
    """
    Prepare a Plotly figure for use with Streamlit.
    Ensures proper handling of the figure object and its data.
    Returns the figure directly or an empty figure if None.
    """
    if fig is None:
        return go.Figure()
    
    # Ensure the figure is a proper Plotly figure object
    if not isinstance(fig, go.Figure):
        try:
            fig = go.Figure(fig)
        except Exception:
            return go.Figure()
    
    # Convert all data to JSON-serializable format
    for trace in fig.data:
        # Handle x and y data
        if hasattr(trace, 'x') and trace.x is not None:
            trace.x = _convert_to_serializable(trace.x)
        if hasattr(trace, 'y') and trace.y is not None:
            trace.y = _convert_to_serializable(trace.y)
        
        # Handle customdata
        if hasattr(trace, 'customdata') and trace.customdata is not None:
            trace.customdata = _convert_to_serializable(trace.customdata)
    
    return fig

def _convert_to_serializable(data):
    """Helper function to convert data to JSON-serializable format."""
    if isinstance(data, (pd.Series, pd.DataFrame)):
        return data.to_numpy().tolist()
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, (date, datetime)):
        return data.isoformat()
    elif isinstance(data, timedelta):
        return data.total_seconds()
    elif isinstance(data, (list, tuple)):
        return [_convert_to_serializable(item) for item in data]
    elif isinstance(data, dict):
        return {k: _convert_to_serializable(v) for k, v in data.items()}
    return data 