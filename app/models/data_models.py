from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any

@dataclass
class Person:
    """Person model representing an employee/resource."""
    id: Optional[int] = None
    name: str = ""
    role: str = ""
    team_id: Optional[int] = None
    team_name: Optional[str] = None

    def __init__(self, id: Optional[int] = None, name: str = "", role: str = "", 
                 team_id: Optional[int] = None, team_name: Optional[str] = None):
        self.id = id
        self.name = name
        self.role = role
        self.team_id = team_id
        self.team_name = team_name

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
    project_manager_id: Optional[int] = None
    project_manager_name: Optional[str] = None
    project_type: str = ""
    lead_team_id: Optional[int] = None
    lead_team_name: Optional[str] = None

@dataclass
class Demand:
    """Demand model representing a request for resources on a project."""
    id: Optional[int] = None
    project_id: int = 0
    project_name: Optional[str] = None
    role_required: str = ""
    fte_required: float = 0.0
    start_date: date = field(default_factory=date.today)
    end_date: date = field(default_factory=date.today)
    priority: int = 1  # 1-5, where 5 is highest
    status: str = "open"  # open, partially_filled, filled, cancelled

    def __init__(self, id: Optional[int] = None, project_id: int = 0, role_required: str = "", 
                 fte_required: float = 0.0, start_date: date = None, end_date: date = None, 
                 priority: int = 1, status: str = "open", project_name: Optional[str] = None):
        self.id = id
        self.project_id = project_id
        self.role_required = role_required
        self.fte_required = fte_required
        self.start_date = start_date or date.today()
        self.end_date = end_date or date.today()
        self.priority = priority
        self.status = status
        self.project_name = project_name

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
    capacity_fte: float = 0

@dataclass
class TeamAllocation:
    """Team allocation data including capacity and utilization."""
    team_id: int
    team_name: str
    allocation_fte: float
    capacity_fte: float 