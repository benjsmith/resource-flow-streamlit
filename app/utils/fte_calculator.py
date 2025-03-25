from datetime import date, datetime, timedelta
from typing import Tuple, Optional, Dict, List
from calendar import monthrange
import polars as pl

def calculate_days_in_period(start_date: date, end_date: date) -> int:
    """
    Calculate the number of days in a period
    
    Args:
        start_date (date): Start date
        end_date (date): End date
        
    Returns:
        int: Number of days in the period
    """
    delta = end_date - start_date
    return delta.days + 1  # Include both start and end dates

def calculate_months_in_period(start_date: date, end_date: date) -> float:
    """
    Calculate the number of months in a period, with partial months
    
    Args:
        start_date (date): Start date
        end_date (date): End date
        
    Returns:
        float: Number of months in the period
    """
    if start_date > end_date:
        return 0.0
    
    # Calculate full months between dates
    year_diff = end_date.year - start_date.year
    month_diff = end_date.month - start_date.month
    full_months = year_diff * 12 + month_diff
    
    # Calculate partial months
    start_partial = (start_date.day - 1) / monthrange(start_date.year, start_date.month)[1]
    end_partial = end_date.day / monthrange(end_date.year, end_date.month)[1]
    
    # Adjust for partial months
    if start_date.month == end_date.month and start_date.year == end_date.year:
        # Same month
        return (end_date.day - start_date.day + 1) / monthrange(start_date.year, start_date.month)[1]
    else:
        # Different months
        return full_months - start_partial + end_partial
    
def calculate_fte_months(fte: float, start_date: date, end_date: date) -> float:
    """
    Calculate FTE-months for a given period
    
    Args:
        fte (float): FTE allocation
        start_date (date): Start date
        end_date (date): End date
        
    Returns:
        float: FTE-months
    """
    months = calculate_months_in_period(start_date, end_date)
    return fte * months

def calculate_monthly_fte_distribution(fte: float, start_date: date, end_date: date) -> Dict[str, float]:
    """
    Calculate monthly distribution of FTE over a period
    
    Args:
        fte (float): FTE allocation
        start_date (date): Start date
        end_date (date): End date
        
    Returns:
        Dict[str, float]: Dictionary with months as keys and FTE values
    """
    if start_date > end_date:
        return {}
    
    result = {}
    current_date = date(start_date.year, start_date.month, 1)
    
    while current_date <= end_date:
        # Calculate last day of current month
        _, last_day = monthrange(current_date.year, current_date.month)
        month_end = date(current_date.year, current_date.month, last_day)
        
        # Calculate overlap period
        period_start = max(start_date, current_date)
        period_end = min(end_date, month_end)
        
        # Calculate FTE for this month
        if period_start <= period_end:
            days_in_month = monthrange(current_date.year, current_date.month)[1]
            days_in_period = calculate_days_in_period(period_start, period_end)
            month_fte = fte * days_in_period / days_in_month
            
            # Format month key
            month_key = f"{current_date.year}-{current_date.month:02d}"
            result[month_key] = round(month_fte, 3)
        
        # Move to next month
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)
    
    return result

def get_current_quarter_dates() -> Tuple[date, date]:
    """
    Get the start and end dates for the current quarter
    
    Returns:
        Tuple[date, date]: (start_date, end_date)
    """
    today = date.today()
    quarter = (today.month - 1) // 3 + 1
    quarter_start_month = (quarter - 1) * 3 + 1
    
    start_date = date(today.year, quarter_start_month, 1)
    if quarter == 4:
        end_date = date(today.year, 12, 31)
    else:
        end_date = date(today.year, quarter_start_month + 3, 1) - timedelta(days=1)
    
    return (start_date, end_date)

def get_current_year_dates() -> Tuple[date, date]:
    """
    Get the start and end dates for the current year
    
    Returns:
        Tuple[date, date]: (start_date, end_date)
    """
    today = date.today()
    return (date(today.year, 1, 1), date(today.year, 12, 31))

def calculate_fte_summary(df: pl.DataFrame, start_date: date, end_date: date) -> Dict[str, float]:
    """
    Calculate FTE summary metrics from a Polars DataFrame with allocation data
    
    Args:
        df (pl.DataFrame): DataFrame with allocation data
        start_date (date): Start date for calculation
        end_date (date): End date for calculation
        
    Returns:
        Dict[str, float]: Dictionary with summary metrics
    """
    total_days = calculate_days_in_period(start_date, end_date)
    total_months = calculate_months_in_period(start_date, end_date)
    
    # Check if DataFrame has the expected columns
    if "fte_demand" in df.columns and "fte_allocated" in df.columns:
        total_demand = df["fte_demand"].sum()
        total_allocated = df["fte_allocated"].sum()
        total_gap = total_demand - total_allocated
        
        if total_demand > 0:
            fulfillment_percentage = (total_allocated / total_demand) * 100
        else:
            fulfillment_percentage = 0.0
        
        return {
            "total_days": total_days,
            "total_months": total_months,
            "total_demand": total_demand,
            "total_allocated": total_allocated,
            "total_gap": total_gap,
            "fulfillment_percentage": fulfillment_percentage
        }
    else:
        return {
            "total_days": total_days,
            "total_months": total_months,
            "total_demand": 0.0,
            "total_allocated": 0.0,
            "total_gap": 0.0,
            "fulfillment_percentage": 0.0
        } 