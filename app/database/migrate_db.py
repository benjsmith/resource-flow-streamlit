import duckdb
import os
from datetime import date, datetime, timedelta
from calendar import monthrange
from uuid import uuid4
from app.database.queries import get_db_connection

def migrate_database():
    """Run database migrations."""
    with get_db_connection() as conn:
        try:
            # Check if migrations table exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Get list of applied migrations
            applied_migrations = set(
                row[0] for row in conn.execute("SELECT name FROM migrations").fetchall()
            )
            
            # Define migrations
            migrations = [
                {
                    "name": "add_capacity_fte_to_monthly_demand_allocation",
                    "sql": """
                        ALTER TABLE monthly_demand_allocation 
                        ADD COLUMN IF NOT EXISTS capacity_fte FLOAT DEFAULT 8.0;
                    """
                }
            ]
            
            # Run pending migrations
            for migration in migrations:
                if migration["name"] not in applied_migrations:
                    try:
                        print(f"Applying migration: {migration['name']}...")
                        conn.execute(migration["sql"])
                        # Get next ID
                        next_id = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM migrations").fetchone()[0]
                        conn.execute(
                            "INSERT INTO migrations (id, name) VALUES (?, ?)",
                            [next_id, migration["name"]]
                        )
                        print(f"Successfully applied migration: {migration['name']}")
                    except Exception as e:
                        print(f"Error applying migration {migration['name']}: {e}")
                        raise
        except Exception as e:
            print(f"Migration error: {e}")
            raise

def check_if_using_uuid(conn):
    """Check if the database is already using UUIDs for primary keys."""
    columns = conn.execute("""
        SELECT type FROM pragma_table_info('teams') 
        WHERE name = 'id'
    """).fetchone()
    
    if columns and (columns[0].upper() == "UUID" or columns[0].upper() == "VARCHAR"):
        return True
    return False

def migrate_to_uuid(conn):
    """Migrate the database tables from integer IDs to UUIDs."""
    # We need to recreate all tables and migrate the data
    # First check for and drop any leftover _uuid tables from previous migration attempts
    for table in ["allocations_uuid", "demands_uuid", "projects_uuid", "people_uuid", "teams_uuid"]:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    
    # Create mapping tables to keep track of old IDs to new UUIDs
    conn.execute("DROP TABLE IF EXISTS team_id_map")
    conn.execute("DROP TABLE IF EXISTS person_id_map")
    conn.execute("DROP TABLE IF EXISTS project_id_map")
    conn.execute("DROP TABLE IF EXISTS demand_id_map")
    conn.execute("DROP TABLE IF EXISTS allocation_id_map")
    
    # Create Teams table with UUID
    conn.execute("""
    CREATE TABLE teams_uuid (
        id VARCHAR PRIMARY KEY,
        name VARCHAR NOT NULL,
        description VARCHAR
    )
    """)
    
    # Create People table with UUID
    conn.execute("""
    CREATE TABLE people_uuid (
        id VARCHAR PRIMARY KEY,
        name VARCHAR NOT NULL,
        role VARCHAR,
        team_id VARCHAR,
        FOREIGN KEY (team_id) REFERENCES teams_uuid(id)
    )
    """)
    
    # Create Projects table with UUID
    conn.execute("""
    CREATE TABLE projects_uuid (
        id VARCHAR PRIMARY KEY,
        name VARCHAR NOT NULL,
        description VARCHAR,
        start_date DATE NOT NULL,
        end_date DATE,
        status VARCHAR DEFAULT 'planning',
        project_manager_id VARCHAR,
        project_type VARCHAR,
        lead_team_id VARCHAR,
        FOREIGN KEY (project_manager_id) REFERENCES people_uuid(id),
        FOREIGN KEY (lead_team_id) REFERENCES teams_uuid(id)
    )
    """)
    
    # Create Demands table with UUID
    conn.execute("""
    CREATE TABLE demands_uuid (
        id VARCHAR PRIMARY KEY,
        project_id VARCHAR NOT NULL,
        role_required VARCHAR,
        fte_required FLOAT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        priority INTEGER DEFAULT 1,
        status VARCHAR DEFAULT 'open',
        FOREIGN KEY (project_id) REFERENCES projects_uuid(id)
    )
    """)
    
    # Create Allocations table with UUID
    conn.execute("""
    CREATE TABLE allocations_uuid (
        id VARCHAR PRIMARY KEY,
        person_id VARCHAR NOT NULL,
        project_id VARCHAR NOT NULL,
        demand_id VARCHAR,
        fte_allocated FLOAT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        notes VARCHAR,
        FOREIGN KEY (person_id) REFERENCES people_uuid(id),
        FOREIGN KEY (project_id) REFERENCES projects_uuid(id),
        FOREIGN KEY (demand_id) REFERENCES demands_uuid(id)
    )
    """)
    
    # Create mapping tables to keep track of old IDs to new UUIDs
    conn.execute("CREATE TABLE team_id_map (old_id INTEGER, new_id VARCHAR)")
    conn.execute("CREATE TABLE person_id_map (old_id INTEGER, new_id VARCHAR)")
    conn.execute("CREATE TABLE project_id_map (old_id INTEGER, new_id VARCHAR)")
    conn.execute("CREATE TABLE demand_id_map (old_id INTEGER, new_id VARCHAR)")
    conn.execute("CREATE TABLE allocation_id_map (old_id INTEGER, new_id VARCHAR)")
    
    # Migrate Teams
    teams = conn.execute("SELECT id, name, description FROM teams").fetchall()
    for team in teams:
        old_id, name, description = team
        new_id = str(uuid4())
        conn.execute("INSERT INTO teams_uuid VALUES (?, ?, ?)", 
                     [new_id, name, description])
        conn.execute("INSERT INTO team_id_map VALUES (?, ?)", 
                     [old_id, new_id])
    
    # Migrate People
    people = conn.execute("""
        SELECT p.id, p.name, p.role, p.team_id, m.new_id 
        FROM people p
        LEFT JOIN team_id_map m ON p.team_id = m.old_id
    """).fetchall()
    
    for person in people:
        old_id, name, role, old_team_id, new_team_id = person
        new_id = str(uuid4())
        conn.execute("INSERT INTO people_uuid VALUES (?, ?, ?, ?)", 
                    [new_id, name, role, new_team_id])
        conn.execute("INSERT INTO person_id_map VALUES (?, ?)", 
                    [old_id, new_id])
    
    # Migrate Projects
    projects = conn.execute("""
        SELECT p.id, p.name, p.description, p.start_date, p.end_date, p.status,
               p.project_manager_id, pm.new_id as new_manager_id,
               p.lead_team_id, tm.new_id as new_team_id,
               p.project_type
        FROM projects p
        LEFT JOIN person_id_map pm ON p.project_manager_id = pm.old_id
        LEFT JOIN team_id_map tm ON p.lead_team_id = tm.old_id
    """).fetchall()
    
    for project in projects:
        old_id = project[0]
        name = project[1]
        description = project[2]
        start_date = project[3]
        end_date = project[4]
        status = project[5]
        new_manager_id = project[7] # Using mapped manager id
        project_type = project[10]
        new_team_id = project[9] # Using mapped team id
        
        new_id = str(uuid4())
        conn.execute("""
            INSERT INTO projects_uuid 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [new_id, name, description, start_date, end_date, status, 
              new_manager_id, project_type, new_team_id])
        conn.execute("INSERT INTO project_id_map VALUES (?, ?)", 
                    [old_id, new_id])
    
    # Migrate Demands
    demands = conn.execute("""
        SELECT d.id, d.project_id, pm.new_id as new_project_id,
               d.role_required, d.fte_required, d.start_date, d.end_date,
               d.priority, d.status
        FROM demands d
        LEFT JOIN project_id_map pm ON d.project_id = pm.old_id
    """).fetchall()
    
    for demand in demands:
        old_id = demand[0]
        new_project_id = demand[2]
        role_required = demand[3]
        fte_required = demand[4]
        start_date = demand[5]
        end_date = demand[6]
        priority = demand[7]
        status = demand[8]
        
        new_id = str(uuid4())
        conn.execute("""
            INSERT INTO demands_uuid 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [new_id, new_project_id, role_required, fte_required, 
              start_date, end_date, priority, status])
        conn.execute("INSERT INTO demand_id_map VALUES (?, ?)", 
                    [old_id, new_id])
    
    # Migrate Allocations
    allocations = conn.execute("""
        SELECT a.id, a.person_id, pm.new_id as new_person_id,
               a.project_id, pjm.new_id as new_project_id,
               a.demand_id, dm.new_id as new_demand_id,
               a.fte_allocated, a.start_date, a.end_date, a.notes
        FROM allocations a
        LEFT JOIN person_id_map pm ON a.person_id = pm.old_id
        LEFT JOIN project_id_map pjm ON a.project_id = pjm.old_id
        LEFT JOIN demand_id_map dm ON a.demand_id = dm.old_id
    """).fetchall()
    
    for allocation in allocations:
        old_id = allocation[0]
        new_person_id = allocation[2]
        new_project_id = allocation[4]
        new_demand_id = allocation[6]
        fte_allocated = allocation[7]
        start_date = allocation[8]
        end_date = allocation[9]
        notes = allocation[10]
        
        new_id = str(uuid4())
        conn.execute("""
            INSERT INTO allocations_uuid 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [new_id, new_person_id, new_project_id, new_demand_id, 
              fte_allocated, start_date, end_date, notes])
        conn.execute("INSERT INTO allocation_id_map VALUES (?, ?)", 
                    [old_id, new_id])
    
    # Replace old tables with new ones - need to handle dependencies correctly
    # First drop tables with foreign key dependencies in reverse order
    conn.execute("DROP TABLE IF EXISTS allocations")
    conn.execute("DROP TABLE IF EXISTS demands")
    conn.execute("DROP TABLE IF EXISTS projects")
    conn.execute("DROP TABLE IF EXISTS people")
    conn.execute("DROP TABLE IF EXISTS teams")
    
    # Now rename the new tables
    conn.execute("ALTER TABLE teams_uuid RENAME TO teams")
    conn.execute("ALTER TABLE people_uuid RENAME TO people")
    conn.execute("ALTER TABLE projects_uuid RENAME TO projects") 
    conn.execute("ALTER TABLE demands_uuid RENAME TO demands")
    conn.execute("ALTER TABLE allocations_uuid RENAME TO allocations")
    
    # Cleanup mapping tables if desired
    # conn.execute("DROP TABLE team_id_map")
    # conn.execute("DROP TABLE person_id_map")
    # conn.execute("DROP TABLE project_id_map")
    # conn.execute("DROP TABLE demand_id_map")
    # conn.execute("DROP TABLE allocation_id_map")

if __name__ == "__main__":
    migrate_database() 