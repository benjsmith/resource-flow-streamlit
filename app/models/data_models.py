from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any

@dataclass
class Person:
    """Person model representing an employee/resource."""
    name: str
    role: str
    skills: List[str] = field(default_factory=list)
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    id: Optional[int] = None

@dataclass
class Team:
    """Team model representing a group of people."""
    name: str
    description: str = ""
    id: Optional[int] = None

@dataclass
class Project:
    """Project model representing a project with timeline and status."""
    name: str
    description: str = ""
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None
    status: str = "planning"  # planning, active, completed, cancelled
    id: Optional[int] = None

@dataclass
class Demand:
    """Demand model representing a request for resources on a project."""
    project_id: int
    role_required: str
    fte_required: float
    start_date: date
    end_date: date
    priority: int = 1  # 1-5, where 5 is highest
    status: str = "open"  # open, partially_filled, filled, cancelled
    skills_required: List[str] = field(default_factory=list)
    project_name: Optional[str] = None
    id: Optional[int] = None

@dataclass
class Allocation:
    """Allocation model representing the assignment of a person to a project/demand."""
    person_id: int
    project_id: int
    fte_allocated: float
    start_date: date
    end_date: date
    notes: str = ""
    demand_id: Optional[int] = None
    person_name: Optional[str] = None
    project_name: Optional[str] = None
    id: Optional[int] = None

@dataclass
class MonthlyDemandAllocation:
    """Monthly aggregated demand and allocation data for reporting."""
    year_month: date  # First day of month
    demand_fte: float
    allocation_fte: float

@dataclass
class TeamAllocation:
    """Team allocation data including capacity and utilization."""
    team_id: int
    team_name: str
    allocation_fte: float
    capacity_fte: float 