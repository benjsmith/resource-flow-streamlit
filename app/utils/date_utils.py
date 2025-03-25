from datetime import date, datetime, timedelta
from typing import Tuple, List, Dict, Optional
import calendar

def get_month_start_end(year: int, month: int) -> Tuple[date, date]:
    """
    Get the start and end dates for a given month
    
    Args:
        year (int): Year
        month (int): Month (1-12)
        
    Returns:
        Tuple[date, date]: (start_date, end_date)
    """
    start_date = date(year, month, 1)
    
    # Calculate last day of month
    if month == 12:
        end_date = date(year, 12, 31)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    return (start_date, end_date)

def get_quarter_start_end(year: int, quarter: int) -> Tuple[date, date]:
    """
    Get the start and end dates for a given quarter
    
    Args:
        year (int): Year
        quarter (int): Quarter (1-4)
        
    Returns:
        Tuple[date, date]: (start_date, end_date)
    """
    if quarter < 1 or quarter > 4:
        raise ValueError("Quarter must be between 1 and 4")
    
    quarter_month = (quarter - 1) * 3 + 1
    
    start_date = date(year, quarter_month, 1)
    
    if quarter == 4:
        end_date = date(year, 12, 31)
    else:
        end_date = date(year, quarter_month + 3, 1) - timedelta(days=1)
    
    return (start_date, end_date)

def get_year_start_end(year: int) -> Tuple[date, date]:
    """
    Get the start and end dates for a given year
    
    Args:
        year (int): Year
        
    Returns:
        Tuple[date, date]: (start_date, end_date)
    """
    return (date(year, 1, 1), date(year, 12, 31))

def get_months_between(start_date: date, end_date: date) -> List[date]:
    """
    Get a list of month start dates between two dates
    
    Args:
        start_date (date): Start date
        end_date (date): End date
        
    Returns:
        List[date]: List of month start dates
    """
    months = []
    current_date = date(start_date.year, start_date.month, 1)
    
    while current_date <= end_date:
        months.append(current_date)
        
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)
    
    return months

def format_date_display(dt: date, format_type: str = 'short') -> str:
    """
    Format a date for display
    
    Args:
        dt (date): Date to format
        format_type (str): Format type ('short', 'medium', 'long')
        
    Returns:
        str: Formatted date string
    """
    if format_type == 'short':
        return dt.strftime('%m/%d/%Y')
    elif format_type == 'medium':
        return dt.strftime('%b %d, %Y')
    elif format_type == 'long':
        return dt.strftime('%B %d, %Y')
    elif format_type == 'month':
        return dt.strftime('%b %Y')
    elif format_type == 'month_year':
        return f"{calendar.month_name[dt.month]} {dt.year}"
    else:
        return str(dt)

def date_range_to_text(start_date: date, end_date: date) -> str:
    """
    Convert a date range to a descriptive text
    
    Args:
        start_date (date): Start date
        end_date (date): End date
        
    Returns:
        str: Descriptive text of the date range
    """
    # Check if it's the same day
    if start_date == end_date:
        return format_date_display(start_date, 'medium')
    
    # Check if it's the same month
    if start_date.month == end_date.month and start_date.year == end_date.year:
        return f"{start_date.day}-{end_date.day} {calendar.month_name[start_date.month]} {start_date.year}"
    
    # Check if it's the same year
    if start_date.year == end_date.year:
        return f"{format_date_display(start_date, 'medium')} - {format_date_display(end_date, 'medium')}"
    
    # Different years
    return f"{format_date_display(start_date, 'medium')} - {format_date_display(end_date, 'medium')}"

def is_quarter_start(dt: date) -> bool:
    """
    Check if a date is the start of a quarter
    
    Args:
        dt (date): Date to check
        
    Returns:
        bool: True if date is start of quarter
    """
    return dt.day == 1 and dt.month in [1, 4, 7, 10]

def is_quarter_end(dt: date) -> bool:
    """
    Check if a date is the end of a quarter
    
    Args:
        dt (date): Date to check
        
    Returns:
        bool: True if date is end of quarter
    """
    return (dt.month in [3, 6, 9] and dt.day == 31) or (dt.month == 12 and dt.day == 31)

def get_current_quarter() -> int:
    """
    Get the current quarter (1-4)
    
    Returns:
        int: Current quarter
    """
    today = date.today()
    return (today.month - 1) // 3 + 1 