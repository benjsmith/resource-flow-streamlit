import duckdb
import os
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from app.models.data_models import (
    Person,
    Team,
    Project,
    Demand,
    Allocation,
    MonthlyDemandAllocation,
    TeamAllocation
)

# Database connection
def get_db_connection():
    """Get a connection to the DuckDB database."""
    db_path = "resource_flow.duckdb"
    conn = duckdb.connect(db_path)
    return conn

# People queries
def get_people(team_id: Optional[int] = None) -> List[Person]:
    """
    Get all people, optionally filtered by team_id.
    
    Args:
        team_id: Optional team ID to filter by
        
    Returns:
        List of Person objects
    """
    conn = get_db_connection()
    
    query = """
        SELECT 
            p.id, 
            p.name, 
            p.role, 
            p.skills, 
            p.team_id,
            t.name as team_name
        FROM people p
        LEFT JOIN teams t ON p.team_id = t.id
    """
    
    params = []
    if team_id is not None:
        query += " WHERE p.team_id = ?"
        params.append(team_id)
    
    query += " ORDER BY p.name"
    
    result = conn.execute(query, params).fetchall()
    conn.close()
    
    people = []
    for row in result:
        people.append(Person(
            id=row[0],
            name=row[1],
            role=row[2],
            skills=row[3].split(",") if row[3] else [],
            team_id=row[4],
            team_name=row[5]
        ))
    
    return people

def get_person(person_id: int) -> Optional[Person]:
    """
    Get a person by ID.
    
    Args:
        person_id: The ID of the person to retrieve
        
    Returns:
        Person object if found, None otherwise
    """
    conn = get_db_connection()
    
    query = """
        SELECT 
            p.id, 
            p.name, 
            p.role, 
            p.skills, 
            p.team_id,
            t.name as team_name
        FROM people p
        LEFT JOIN teams t ON p.team_id = t.id
        WHERE p.id = ?
    """
    
    result = conn.execute(query, [person_id]).fetchone()
    conn.close()
    
    if result:
        return Person(
            id=result[0],
            name=result[1],
            role=result[2],
            skills=result[3].split(",") if result[3] else [],
            team_id=result[4],
            team_name=result[5]
        )
    
    return None

def save_person(person: Person) -> int:
    """
    Save a person to the database.
    
    Args:
        person: The Person object to save
        
    Returns:
        The ID of the saved person
    """
    conn = get_db_connection()
    
    skills_str = ",".join(person.skills) if person.skills else ""
    
    if person.id:
        # Update existing person
        query = """
            UPDATE people
            SET name = ?, role = ?, skills = ?, team_id = ?
            WHERE id = ?
        """
        conn.execute(query, [person.name, person.role, skills_str, person.team_id, person.id])
        person_id = person.id
    else:
        # Insert new person
        query = """
            INSERT INTO people (name, role, skills, team_id)
            VALUES (?, ?, ?, ?)
            RETURNING id
        """
        result = conn.execute(query, [person.name, person.role, skills_str, person.team_id]).fetchone()
        person_id = result[0]
    
    conn.close()
    return person_id

def delete_person(person_id: int) -> bool:
    """
    Delete a person from the database.
    
    Args:
        person_id: The ID of the person to delete
        
    Returns:
        True if the person was deleted, False otherwise
    """
    conn = get_db_connection()
    
    # Check if person has allocations
    has_allocations = conn.execute(
        "SELECT COUNT(*) FROM allocations WHERE person_id = ?", 
        [person_id]
    ).fetchone()[0]
    
    if has_allocations > 0:
        conn.close()
        return False
    
    # Delete person
    conn.execute("DELETE FROM people WHERE id = ?", [person_id])
    conn.close()
    return True

def get_total_people_count() -> int:
    """
    Get the total number of people in the database.
    
    Returns:
        Total number of people
    """
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    conn.close()
    return count

# Teams queries
def get_teams() -> List[Team]:
    """
    Get all teams.
    
    Returns:
        List of Team objects
    """
    conn = get_db_connection()
    
    query = """
        SELECT id, name, description
        FROM teams
        ORDER BY name
    """
    
    result = conn.execute(query).fetchall()
    conn.close()
    
    teams = []
    for row in result:
        teams.append(Team(
            id=row[0],
            name=row[1],
            description=row[2]
        ))
    
    return teams

def get_team(team_id: int) -> Optional[Team]:
    """
    Get a team by ID.
    
    Args:
        team_id: The ID of the team to retrieve
        
    Returns:
        Team object if found, None otherwise
    """
    conn = get_db_connection()
    
    query = """
        SELECT id, name, description
        FROM teams
        WHERE id = ?
    """
    
    result = conn.execute(query, [team_id]).fetchone()
    conn.close()
    
    if result:
        return Team(
            id=result[0],
            name=result[1],
            description=result[2]
        )
    
    return None

def save_team(team: Team) -> int:
    """
    Save a team to the database.
    
    Args:
        team: The Team object to save
        
    Returns:
        The ID of the saved team
    """
    conn = get_db_connection()
    
    if team.id:
        # Update existing team
        query = """
            UPDATE teams
            SET name = ?, description = ?
            WHERE id = ?
        """
        conn.execute(query, [team.name, team.description, team.id])
        team_id = team.id
    else:
        # Insert new team
        query = """
            INSERT INTO teams (name, description)
            VALUES (?, ?)
            RETURNING id
        """
        result = conn.execute(query, [team.name, team.description]).fetchone()
        team_id = result[0]
    
    conn.close()
    return team_id

def delete_team(team_id: int) -> bool:
    """
    Delete a team from the database.
    
    Args:
        team_id: The ID of the team to delete
        
    Returns:
        True if the team was deleted, False otherwise
    """
    conn = get_db_connection()
    
    # Check if team has members
    has_members = conn.execute(
        "SELECT COUNT(*) FROM people WHERE team_id = ?", 
        [team_id]
    ).fetchone()[0]
    
    if has_members > 0:
        conn.close()
        return False
    
    # Delete team
    conn.execute("DELETE FROM teams WHERE id = ?", [team_id])
    conn.close()
    return True

def get_team_allocations(start_date: date, end_date: date) -> List[TeamAllocation]:
    """
    Get team allocations for the specified date range.
    
    Args:
        start_date: Start date for allocations
        end_date: End date for allocations
        
    Returns:
        List of TeamAllocation objects
    """
    conn = get_db_connection()
    
    query = """
    WITH team_capacity AS (
        SELECT 
            t.id AS team_id,
            t.name AS team_name,
            COUNT(p.id) AS num_people,
            COUNT(p.id) AS capacity_fte
        FROM teams t
        LEFT JOIN people p ON t.id = p.team_id
        GROUP BY t.id, t.name
    ),
    team_allocation AS (
        SELECT 
            t.id AS team_id,
            t.name AS team_name,
            SUM(a.fte_allocated) AS allocation_fte
        FROM teams t
        JOIN people p ON t.id = p.team_id
        JOIN allocations a ON p.id = a.person_id
        WHERE a.start_date <= ? AND a.end_date >= ?
        GROUP BY t.id, t.name
    )
    SELECT 
        tc.team_id,
        tc.team_name,
        COALESCE(ta.allocation_fte, 0) AS allocation_fte,
        tc.capacity_fte
    FROM team_capacity tc
    LEFT JOIN team_allocation ta ON tc.team_id = ta.team_id
    ORDER BY tc.team_name
    """
    
    result = conn.execute(query, [end_date, start_date]).fetchall()
    conn.close()
    
    team_allocations = []
    for row in result:
        team_allocations.append(TeamAllocation(
            team_id=row[0],
            team_name=row[1],
            allocation_fte=row[2],
            capacity_fte=row[3]
        ))
    
    return team_allocations

# Projects queries
def get_projects(status: Optional[str] = None) -> List[Project]:
    """
    Get all projects, optionally filtered by status.
    
    Args:
        status: Optional status to filter by
        
    Returns:
        List of Project objects
    """
    conn = get_db_connection()
    
    query = """
        SELECT id, name, description, start_date, end_date, status
        FROM projects
    """
    
    params = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    
    query += " ORDER BY start_date DESC"
    
    result = conn.execute(query, params).fetchall()
    conn.close()
    
    projects = []
    for row in result:
        projects.append(Project(
            id=row[0],
            name=row[1],
            description=row[2],
            start_date=row[3],
            end_date=row[4],
            status=row[5]
        ))
    
    return projects

def get_project(project_id: int) -> Optional[Project]:
    """
    Get a project by ID.
    
    Args:
        project_id: The ID of the project to retrieve
        
    Returns:
        Project object if found, None otherwise
    """
    conn = get_db_connection()
    
    query = """
        SELECT id, name, description, start_date, end_date, status
        FROM projects
        WHERE id = ?
    """
    
    result = conn.execute(query, [project_id]).fetchone()
    conn.close()
    
    if result:
        return Project(
            id=result[0],
            name=result[1],
            description=result[2],
            start_date=result[3],
            end_date=result[4],
            status=result[5]
        )
    
    return None

def save_project(project: Project) -> int:
    """
    Save a project to the database.
    
    Args:
        project: The Project object to save
        
    Returns:
        The ID of the saved project
    """
    conn = get_db_connection()
    
    if project.id:
        # Update existing project
        query = """
            UPDATE projects
            SET name = ?, description = ?, start_date = ?, end_date = ?, status = ?
            WHERE id = ?
        """
        conn.execute(query, [
            project.name, 
            project.description, 
            project.start_date, 
            project.end_date,
            project.status,
            project.id
        ])
        project_id = project.id
    else:
        # Insert new project
        query = """
            INSERT INTO projects (name, description, start_date, end_date, status)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id
        """
        result = conn.execute(query, [
            project.name, 
            project.description, 
            project.start_date, 
            project.end_date,
            project.status
        ]).fetchone()
        project_id = result[0]
    
    conn.close()
    return project_id

def delete_project(project_id: int) -> bool:
    """
    Delete a project from the database.
    
    Args:
        project_id: The ID of the project to delete
        
    Returns:
        True if the project was deleted, False otherwise
    """
    conn = get_db_connection()
    
    # Check if project has demands or allocations
    has_dependencies = conn.execute("""
        SELECT 
            (SELECT COUNT(*) FROM demands WHERE project_id = ?) +
            (SELECT COUNT(*) FROM allocations WHERE project_id = ?)
    """, [project_id, project_id]).fetchone()[0]
    
    if has_dependencies > 0:
        conn.close()
        return False
    
    # Delete project
    conn.execute("DELETE FROM projects WHERE id = ?", [project_id])
    conn.close()
    return True

def get_active_projects_count() -> int:
    """
    Get the count of active projects.
    
    Returns:
        Count of active projects
    """
    conn = get_db_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM projects WHERE status IN ('active', 'planning')"
    ).fetchone()[0]
    conn.close()
    return count

# Demand queries
def get_demands(project_id: Optional[int] = None, status: Optional[str] = None) -> List[Demand]:
    """
    Get all demands, optionally filtered by project_id and status.
    
    Args:
        project_id: Optional project ID to filter by
        status: Optional status to filter by
        
    Returns:
        List of Demand objects
    """
    conn = get_db_connection()
    
    query = """
        SELECT 
            d.id, 
            d.project_id, 
            p.name as project_name,
            d.role_required, 
            d.skills_required, 
            d.fte_required, 
            d.start_date, 
            d.end_date, 
            d.priority,
            d.status
        FROM demands d
        JOIN projects p ON d.project_id = p.id
    """
    
    conditions = []
    params = []
    
    if project_id is not None:
        conditions.append("d.project_id = ?")
        params.append(project_id)
    
    if status:
        conditions.append("d.status = ?")
        params.append(status)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY d.priority DESC, d.start_date"
    
    result = conn.execute(query, params).fetchall()
    conn.close()
    
    demands = []
    for row in result:
        demands.append(Demand(
            id=row[0],
            project_id=row[1],
            project_name=row[2],
            role_required=row[3],
            skills_required=row[4].split(",") if row[4] else [],
            fte_required=row[5],
            start_date=row[6],
            end_date=row[7],
            priority=row[8],
            status=row[9]
        ))
    
    return demands

def get_demand(demand_id: int) -> Optional[Demand]:
    """
    Get a demand by ID.
    
    Args:
        demand_id: The ID of the demand to retrieve
        
    Returns:
        Demand object if found, None otherwise
    """
    conn = get_db_connection()
    
    query = """
        SELECT 
            d.id, 
            d.project_id, 
            p.name as project_name,
            d.role_required, 
            d.skills_required, 
            d.fte_required, 
            d.start_date, 
            d.end_date, 
            d.priority,
            d.status
        FROM demands d
        JOIN projects p ON d.project_id = p.id
        WHERE d.id = ?
    """
    
    result = conn.execute(query, [demand_id]).fetchone()
    conn.close()
    
    if result:
        return Demand(
            id=result[0],
            project_id=result[1],
            project_name=result[2],
            role_required=result[3],
            skills_required=result[4].split(",") if result[4] else [],
            fte_required=result[5],
            start_date=result[6],
            end_date=result[7],
            priority=result[8],
            status=result[9]
        )
    
    return None

def save_demand(demand: Demand) -> int:
    """
    Save a demand to the database.
    
    Args:
        demand: The Demand object to save
        
    Returns:
        The ID of the saved demand
    """
    conn = get_db_connection()
    
    skills_str = ",".join(demand.skills_required) if demand.skills_required else ""
    
    if demand.id:
        # Update existing demand
        query = """
            UPDATE demands
            SET project_id = ?, role_required = ?, skills_required = ?, 
                fte_required = ?, start_date = ?, end_date = ?, 
                priority = ?, status = ?
            WHERE id = ?
        """
        conn.execute(query, [
            demand.project_id, 
            demand.role_required, 
            skills_str, 
            demand.fte_required,
            demand.start_date,
            demand.end_date,
            demand.priority,
            demand.status,
            demand.id
        ])
        demand_id = demand.id
    else:
        # Insert new demand
        query = """
            INSERT INTO demands (
                project_id, role_required, skills_required, fte_required, 
                start_date, end_date, priority, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
        """
        result = conn.execute(query, [
            demand.project_id, 
            demand.role_required, 
            skills_str, 
            demand.fte_required,
            demand.start_date,
            demand.end_date,
            demand.priority,
            demand.status
        ]).fetchone()
        demand_id = result[0]
    
    # Update monthly allocations
    update_monthly_allocations()
    
    conn.close()
    return demand_id

def delete_demand(demand_id: int) -> bool:
    """
    Delete a demand from the database.
    
    Args:
        demand_id: The ID of the demand to delete
        
    Returns:
        True if the demand was deleted, False otherwise
    """
    conn = get_db_connection()
    
    # Check if demand has allocations
    has_allocations = conn.execute(
        "SELECT COUNT(*) FROM allocations WHERE demand_id = ?", 
        [demand_id]
    ).fetchone()[0]
    
    if has_allocations > 0:
        conn.close()
        return False
    
    # Delete demand
    conn.execute("DELETE FROM demands WHERE id = ?", [demand_id])
    
    # Update monthly allocations
    update_monthly_allocations()
    
    conn.close()
    return True

def get_open_demands_count() -> int:
    """
    Get the count of open demands.
    
    Returns:
        Count of open demands
    """
    conn = get_db_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM demands WHERE status IN ('open', 'partially_filled')"
    ).fetchone()[0]
    conn.close()
    return count

# Allocation queries
def get_allocations(person_id: Optional[int] = None, project_id: Optional[int] = None, demand_id: Optional[int] = None) -> List[Allocation]:
    """
    Get all allocations, optionally filtered by person_id, project_id, or demand_id.
    
    Args:
        person_id: Optional person ID to filter by
        project_id: Optional project ID to filter by
        demand_id: Optional demand ID to filter by
        
    Returns:
        List of Allocation objects
    """
    conn = get_db_connection()
    
    query = """
        SELECT 
            a.id, 
            a.person_id, 
            p.name as person_name,
            a.project_id, 
            pr.name as project_name,
            a.demand_id,
            a.fte_allocated, 
            a.start_date, 
            a.end_date, 
            a.notes
        FROM allocations a
        JOIN people p ON a.person_id = p.id
        JOIN projects pr ON a.project_id = pr.id
        LEFT JOIN demands d ON a.demand_id = d.id
    """
    
    conditions = []
    params = []
    
    if person_id is not None:
        conditions.append("a.person_id = ?")
        params.append(person_id)
    
    if project_id is not None:
        conditions.append("a.project_id = ?")
        params.append(project_id)
    
    if demand_id is not None:
        conditions.append("a.demand_id = ?")
        params.append(demand_id)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY a.start_date"
    
    result = conn.execute(query, params).fetchall()
    conn.close()
    
    allocations = []
    for row in result:
        allocations.append(Allocation(
            id=row[0],
            person_id=row[1],
            person_name=row[2],
            project_id=row[3],
            project_name=row[4],
            demand_id=row[5],
            fte_allocated=row[6],
            start_date=row[7],
            end_date=row[8],
            notes=row[9]
        ))
    
    return allocations

def get_allocation(allocation_id: int) -> Optional[Allocation]:
    """
    Get an allocation by ID.
    
    Args:
        allocation_id: The ID of the allocation to retrieve
        
    Returns:
        Allocation object if found, None otherwise
    """
    conn = get_db_connection()
    
    query = """
        SELECT 
            a.id, 
            a.person_id, 
            p.name as person_name,
            a.project_id, 
            pr.name as project_name,
            a.demand_id,
            a.fte_allocated, 
            a.start_date, 
            a.end_date, 
            a.notes
        FROM allocations a
        JOIN people p ON a.person_id = p.id
        JOIN projects pr ON a.project_id = pr.id
        LEFT JOIN demands d ON a.demand_id = d.id
        WHERE a.id = ?
    """
    
    result = conn.execute(query, [allocation_id]).fetchone()
    conn.close()
    
    if result:
        return Allocation(
            id=result[0],
            person_id=result[1],
            person_name=result[2],
            project_id=result[3],
            project_name=result[4],
            demand_id=result[5],
            fte_allocated=result[6],
            start_date=result[7],
            end_date=result[8],
            notes=result[9]
        )
    
    return None

def save_allocation(allocation: Allocation) -> int:
    """
    Save an allocation to the database.
    
    Args:
        allocation: The Allocation object to save
        
    Returns:
        The ID of the saved allocation
    """
    conn = get_db_connection()
    
    if allocation.id:
        # Update existing allocation
        query = """
            UPDATE allocations
            SET person_id = ?, project_id = ?, demand_id = ?, 
                fte_allocated = ?, start_date = ?, end_date = ?, notes = ?
            WHERE id = ?
        """
        conn.execute(query, [
            allocation.person_id, 
            allocation.project_id, 
            allocation.demand_id, 
            allocation.fte_allocated,
            allocation.start_date,
            allocation.end_date,
            allocation.notes,
            allocation.id
        ])
        allocation_id = allocation.id
    else:
        # Insert new allocation
        query = """
            INSERT INTO allocations (
                person_id, project_id, demand_id, fte_allocated, 
                start_date, end_date, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING id
        """
        result = conn.execute(query, [
            allocation.person_id, 
            allocation.project_id, 
            allocation.demand_id, 
            allocation.fte_allocated,
            allocation.start_date,
            allocation.end_date,
            allocation.notes
        ]).fetchone()
        allocation_id = result[0]
    
    # If allocation is linked to a demand, update the demand status
    if allocation.demand_id:
        update_demand_status(allocation.demand_id)
    
    # Update monthly allocations
    update_monthly_allocations()
    
    conn.close()
    return allocation_id

def delete_allocation(allocation_id: int) -> bool:
    """
    Delete an allocation from the database.
    
    Args:
        allocation_id: The ID of the allocation to delete
        
    Returns:
        True if the allocation was deleted, False otherwise
    """
    conn = get_db_connection()
    
    # Get the demand_id before deleting
    demand_id = conn.execute(
        "SELECT demand_id FROM allocations WHERE id = ?", 
        [allocation_id]
    ).fetchone()
    
    if demand_id and demand_id[0]:
        demand_id = demand_id[0]
    else:
        demand_id = None
    
    # Delete allocation
    conn.execute("DELETE FROM allocations WHERE id = ?", [allocation_id])
    
    # If allocation was linked to a demand, update the demand status
    if demand_id:
        update_demand_status(demand_id)
    
    # Update monthly allocations
    update_monthly_allocations()
    
    conn.close()
    return True

def update_demand_status(demand_id: int) -> None:
    """
    Update the status of a demand based on its allocations.
    
    Args:
        demand_id: The ID of the demand to update
    """
    conn = get_db_connection()
    
    # Get the demand
    demand = get_demand(demand_id)
    if not demand:
        conn.close()
        return
    
    # Get all allocations for this demand
    allocations = get_allocations(demand_id=demand_id)
    
    # Calculate total allocated FTE
    total_allocated = 0
    for allocation in allocations:
        total_allocated += allocation.fte_allocated
    
    # Update demand status based on allocated FTE
    new_status = demand.status
    if total_allocated == 0:
        new_status = 'open'
    elif total_allocated < demand.fte_required:
        new_status = 'partially_filled'
    else:
        new_status = 'filled'
    
    # Update the demand
    conn.execute(
        "UPDATE demands SET status = ? WHERE id = ?",
        [new_status, demand_id]
    )
    
    conn.close()

# Monthly demand and allocation queries
def get_monthly_demand_allocation(start_date: date, end_date: date) -> List[MonthlyDemandAllocation]:
    """
    Get monthly demand and allocation data for the specified date range.
    
    Args:
        start_date: Start date for data
        end_date: End date for data
        
    Returns:
        List of MonthlyDemandAllocation objects
    """
    conn = get_db_connection()
    
    query = """
        SELECT 
            year_month,
            demand_fte,
            allocation_fte
        FROM monthly_demand_allocation
        WHERE year_month >= ? AND year_month <= ?
        ORDER BY year_month
    """
    
    # Convert to first day of month for comparison
    start_month = date(start_date.year, start_date.month, 1)
    end_month = date(end_date.year, end_date.month, 1)
    
    result = conn.execute(query, [start_month, end_month]).fetchall()
    conn.close()
    
    monthly_data = []
    for row in result:
        monthly_data.append(MonthlyDemandAllocation(
            year_month=row[0],
            demand_fte=row[1],
            allocation_fte=row[2]
        ))
    
    return monthly_data

def update_monthly_allocations() -> None:
    """Update the monthly_demand_allocation table with current data."""
    # This function will be implemented in the init_db.py file
    # and will be called whenever demand or allocation data changes
    from app.database.init_db import compute_monthly_allocations 