from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any

@dataclass
class Person:
    """Person model representing an employee/resource."""
    id: Optional[str] = None
    name: str = ""
    role: str = ""
    team_id: Optional[str] = None
    team_name: Optional[str] = None

@dataclass
class Team:
    """Team model representing a group of people."""
    name: str
    description: str = ""
    id: Optional[str] = None

@dataclass
class Project:
    """Project model representing a project with timeline and status."""
    name: str
    description: str = ""
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None
    status: str = "planning"  # planning, active, completed, cancelled
    id: Optional[str] = None
    project_manager_id: Optional[str] = None
    project_manager_name: Optional[str] = None
    project_type: str = ""
    lead_team_id: Optional[str] = None
    lead_team_name: Optional[str] = None

@dataclass
class Demand:
    """Demand model representing a request for resources on a project."""
    id: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    role_required: str = ""
    fte_required: float = 0.0
    start_date: date = field(default_factory=date.today)
    end_date: date = field(default_factory=date.today)
    priority: int = 1  # 1-5, where 5 is highest
    status: str = "open"  # open, partially_filled, filled, cancelled

@dataclass
class Allocation:
    """Allocation model representing the assignment of a person to a project/demand."""
    person_id: str
    project_id: str
    fte_allocated: float
    start_date: date
    end_date: date
    notes: str = ""
    demand_id: Optional[str] = None
    person_name: Optional[str] = None
    project_name: Optional[str] = None
    id: Optional[str] = None

@dataclass
class MonthlyDemandAllocation:
    """Monthly aggregated demand and allocation data for reporting."""
    year_month: date  # First day of month
    demand_fte: float
    allocation_fte: float
    capacity_fte: float = 0

@dataclass
class TeamAllocation:
    """Team allocation data including capacity and utilization."""
    team_id: str
    team_name: str
    allocation_fte: float
    capacity_fte: float 