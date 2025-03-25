import polars as pl
import pandas as pd
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union

def filter_dataframe_by_date(df: pl.DataFrame, 
                            start_date: date, 
                            end_date: date, 
                            date_column: str = 'year_month') -> pl.DataFrame:
    """
    Filter a Polars DataFrame by date range
    
    Args:
        df (pl.DataFrame): DataFrame to filter
        start_date (date): Start date for filter
        end_date (date): End date for filter
        date_column (str): Column name with date values
        
    Returns:
        pl.DataFrame: Filtered DataFrame
    """
    return df.filter(
        (pl.col(date_column) >= start_date) &
        (pl.col(date_column) <= end_date)
    )

def aggregate_by_month(df: pl.DataFrame, 
                      date_column: str = 'year_month', 
                      value_columns: List[str] = None) -> pl.DataFrame:
    """
    Aggregate a Polars DataFrame by month
    
    Args:
        df (pl.DataFrame): DataFrame to aggregate
        date_column (str): Column name with date values
        value_columns (List[str]): Columns to aggregate
        
    Returns:
        pl.DataFrame: Aggregated DataFrame
    """
    if value_columns is None:
        # Try to detect numeric columns
        value_columns = [col for col in df.columns if df[col].dtype in [pl.Float32, pl.Float64, pl.Int32, pl.Int64]]
    
    # Create month column if not using year_month
    if date_column != 'year_month':
        df = df.with_column(
            pl.col(date_column).dt.truncate('1mo').alias('year_month')
        )
        group_by = 'year_month'
    else:
        group_by = date_column
    
    # Aggregate by month
    return df.group_by(group_by).agg([
        pl.sum(col).alias(col) for col in value_columns
    ]).sort(group_by)

def pivot_data(df: pl.DataFrame, 
              index_col: str, 
              column_col: str, 
              value_col: str) -> pl.DataFrame:
    """
    Pivot a Polars DataFrame
    
    Args:
        df (pl.DataFrame): DataFrame to pivot
        index_col (str): Column to use as index
        column_col (str): Column to use as columns
        value_col (str): Column to use as values
        
    Returns:
        pl.DataFrame: Pivoted DataFrame
    """
    # Polars pivot is more basic than pandas, convert for advanced pivot
    pd_df = df.to_pandas()
    
    pivot_df = pd.pivot_table(
        pd_df,
        values=value_col,
        index=index_col,
        columns=column_col,
        aggfunc='sum',
        fill_value=0
    )
    
    # Convert back to polars
    return pl.from_pandas(pivot_df.reset_index())

def calculate_rolling_average(df: pl.DataFrame, 
                             value_column: str, 
                             window_size: int = 3, 
                             date_column: str = 'year_month') -> pl.DataFrame:
    """
    Calculate rolling average on a Polars DataFrame
    
    Args:
        df (pl.DataFrame): DataFrame to process
        value_column (str): Column to calculate rolling average
        window_size (int): Window size for rolling average
        date_column (str): Column name with date values
        
    Returns:
        pl.DataFrame: DataFrame with rolling average
    """
    # Sort by date
    sorted_df = df.sort(date_column)
    
    # Calculate rolling average
    result = sorted_df.with_column(
        pl.col(value_column).rolling_mean(window_size).alias(f"{value_column}_rolling_avg")
    )
    
    return result

def convert_dataframe_for_plotly(df: pl.DataFrame) -> pd.DataFrame:
    """
    Convert a Polars DataFrame to Pandas for Plotly
    
    Args:
        df (pl.DataFrame): Polars DataFrame
        
    Returns:
        pd.DataFrame: Pandas DataFrame
    """
    return df.to_pandas()

def format_date_column(df: pl.DataFrame, 
                      date_column: str = 'year_month',
                      format: str = '%b %Y') -> pl.DataFrame:
    """
    Format a date column in a Polars DataFrame
    
    Args:
        df (pl.DataFrame): DataFrame to process
        date_column (str): Column name with date values
        format (str): Date format string
        
    Returns:
        pl.DataFrame: DataFrame with formatted date column
    """
    return df.with_column(
        pl.col(date_column).dt.strftime(format).alias(f"{date_column}_formatted")
    )

def calculate_percentage(df: pl.DataFrame, 
                        numerator: str, 
                        denominator: str, 
                        new_column: str) -> pl.DataFrame:
    """
    Calculate percentage in a Polars DataFrame
    
    Args:
        df (pl.DataFrame): DataFrame to process
        numerator (str): Column name for numerator
        denominator (str): Column name for denominator
        new_column (str): Name for the new percentage column
        
    Returns:
        pl.DataFrame: DataFrame with percentage column
    """
    return df.with_column(
        (pl.col(numerator) / pl.col(denominator) * 100.0).alias(new_column)
    )

def merge_dataframes(left_df: pl.DataFrame, 
                    right_df: pl.DataFrame, 
                    on: Union[str, List[str]], 
                    how: str = 'inner') -> pl.DataFrame:
    """
    Merge two Polars DataFrames
    
    Args:
        left_df (pl.DataFrame): Left DataFrame
        right_df (pl.DataFrame): Right DataFrame
        on (Union[str, List[str]]): Column(s) to join on
        how (str): Join type ('inner', 'left', 'right', 'outer')
        
    Returns:
        pl.DataFrame: Merged DataFrame
    """
    return left_df.join(right_df, on=on, how=how)

def classify_gap(gap: float) -> str:
    """
    Classify a resource gap
    
    Args:
        gap (float): Resource gap value
        
    Returns:
        str: Classification ('surplus', 'balanced', 'deficit', 'critical')
    """
    if gap >= 0.5:
        return "surplus"
    elif gap >= -0.1:
        return "balanced"
    elif gap >= -0.5:
        return "deficit"
    else:
        return "critical"

def add_gap_classification(df: pl.DataFrame, gap_column: str) -> pl.DataFrame:
    """
    Add gap classification column to a Polars DataFrame
    
    Args:
        df (pl.DataFrame): DataFrame to process
        gap_column (str): Column name with gap values
        
    Returns:
        pl.DataFrame: DataFrame with gap classification
    """
    # Convert to pandas for vectorized custom function
    pd_df = df.to_pandas()
    pd_df['gap_classification'] = pd_df[gap_column].apply(classify_gap)
    
    # Convert back to polars
    return pl.from_pandas(pd_df) 