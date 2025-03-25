from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, List, Dict, Any

@dataclass
class Person:
    id: int
    name: str
    email: Optional[str] = None
    role: Optional[str] = None
    skills: Optional[str] = None
    team_id: Optional[int] = None
    fte_capacity: float = 1.0
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Person':
        return cls(**data)


@dataclass
class Team:
    id: int
    name: str
    description: Optional[str] = None
    manager_id: Optional[int] = None
    department: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Team':
        return cls(**data)


@dataclass
class Project:
    id: int
    name: str
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    owner_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        # Convert string dates to date objects if present
        if 'start_date' in data and data['start_date'] and isinstance(data['start_date'], str):
            data['start_date'] = date.fromisoformat(data['start_date'])
        if 'end_date' in data and data['end_date'] and isinstance(data['end_date'], str):
            data['end_date'] = date.fromisoformat(data['end_date'])
        return cls(**data)


@dataclass
class Demand:
    id: int
    project_id: int
    role_required: Optional[str] = None
    skills_required: Optional[str] = None
    fte_required: float = 0.0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    priority: Optional[str] = None
    status: str = 'unfilled'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Demand':
        # Convert string dates to date objects if present
        if 'start_date' in data and data['start_date'] and isinstance(data['start_date'], str):
            data['start_date'] = date.fromisoformat(data['start_date'])
        if 'end_date' in data and data['end_date'] and isinstance(data['end_date'], str):
            data['end_date'] = date.fromisoformat(data['end_date'])
        return cls(**data)


@dataclass
class Allocation:
    id: int
    person_id: int
    project_id: int
    fte_allocated: float
    start_date: date
    end_date: date
    demand_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Allocation':
        # Convert string dates to date objects if present
        if 'start_date' in data and data['start_date'] and isinstance(data['start_date'], str):
            data['start_date'] = date.fromisoformat(data['start_date'])
        if 'end_date' in data and data['end_date'] and isinstance(data['end_date'], str):
            data['end_date'] = date.fromisoformat(data['end_date'])
        return cls(**data)


@dataclass
class MonthlyDemandAllocation:
    id: int
    year_month: date
    project_id: int
    fte_demand: float = 0.0
    fte_allocated: float = 0.0
    fte_gap: float = 0.0
    demand_id: Optional[int] = None
    person_id: Optional[int] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Additional fields for joined data
    project_name: Optional[str] = None
    person_name: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonthlyDemandAllocation':
        # Convert string dates to date objects if present
        if 'year_month' in data and data['year_month'] and isinstance(data['year_month'], str):
            data['year_month'] = date.fromisoformat(data['year_month'])
        return cls(**data) 