import duckdb
import os
from datetime import date, datetime, timedelta
from calendar import monthrange
from uuid import uuid4

def migrate_database():
    """Migrate the database schema to add new columns."""
    db_path = "resource_flow.duckdb"
    
    if not os.path.exists(db_path):
        print(f"Database does not exist at {db_path}")
        return
    
    # Create a new connection
    conn = duckdb.connect(db_path)
    
    try:
        # Check if parent_team_id column exists
        result = conn.execute("""
            SELECT COUNT(*) 
            FROM pragma_table_info('teams') 
            WHERE name = 'parent_team_id'
        """).fetchone()
        
        if result[0] == 0:
            print("Adding parent_team_id column to teams table...")
            # Add parent_team_id column
            conn.execute("""
                ALTER TABLE teams 
                ADD COLUMN parent_team_id VARCHAR
            """)
            
            # Add foreign key constraint
            conn.execute("""
                ALTER TABLE teams 
                ADD FOREIGN KEY (parent_team_id) REFERENCES teams(id)
            """)
            print("Migration completed successfully")
        else:
            print("Database is already up to date")
    
    finally:
        conn.close()

def initialize_database():
    """Initialize the DuckDB database with tables and sample data."""
    db_path = "resource_flow.duckdb"
    
    # Check if database already exists
    if os.path.exists(db_path):
        print(f"Database already exists at {db_path}")
        # Run migrations if needed
        migrate_database()
        return
    
    # Create a new connection
    conn = duckdb.connect(db_path)
    
    try:
        # Create tables
        create_tables(conn)
        
        # Add sample data
        add_sample_data(conn)
        
        # Compute monthly allocations
        compute_monthly_allocations(conn)
        
        print(f"Database initialized successfully at {db_path}")
    
    finally:
        conn.close()

def create_tables(conn):
    """Create the database tables."""
    # Create Teams table
    conn.execute("""
    CREATE TABLE teams (
        id VARCHAR PRIMARY KEY,
        name VARCHAR NOT NULL,
        description VARCHAR,
        parent_team_id VARCHAR,
        FOREIGN KEY (parent_team_id) REFERENCES teams(id)
    )
    """)
    
    # Create People table
    conn.execute("""
    CREATE TABLE people (
        id VARCHAR PRIMARY KEY,
        name VARCHAR NOT NULL,
        role VARCHAR,
        team_id VARCHAR,
        FOREIGN KEY (team_id) REFERENCES teams(id)
    )
    """)
    
    # Create Projects table
    conn.execute("""
    CREATE TABLE projects (
        id VARCHAR PRIMARY KEY,
        name VARCHAR NOT NULL,
        description VARCHAR,
        start_date DATE NOT NULL,
        end_date DATE,
        status VARCHAR DEFAULT 'planning',
        project_manager_id VARCHAR,
        project_type VARCHAR,
        lead_team_id VARCHAR,
        FOREIGN KEY (project_manager_id) REFERENCES people(id),
        FOREIGN KEY (lead_team_id) REFERENCES teams(id)
    )
    """)
    
    # Create Demands table
    conn.execute("""
    CREATE TABLE demands (
        id VARCHAR PRIMARY KEY,
        project_id VARCHAR NOT NULL,
        role_required VARCHAR,
        fte_required FLOAT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        priority INTEGER DEFAULT 1,
        status VARCHAR DEFAULT 'open',
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    """)
    
    # Create Allocations table
    conn.execute("""
    CREATE TABLE allocations (
        id VARCHAR PRIMARY KEY,
        person_id VARCHAR NOT NULL,
        project_id VARCHAR NOT NULL,
        demand_id VARCHAR,
        fte_allocated FLOAT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        notes VARCHAR,
        FOREIGN KEY (person_id) REFERENCES people(id),
        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (demand_id) REFERENCES demands(id)
    )
    """)
    
    # Create Monthly Demand Allocation table for aggregated reporting
    conn.execute("""
    CREATE TABLE monthly_demand_allocation (
        year_month DATE NOT NULL,
        demand_fte FLOAT DEFAULT 0,
        allocation_fte FLOAT DEFAULT 0,
        capacity_fte FLOAT DEFAULT 0,
        PRIMARY KEY (year_month)
    )
    """)

def add_sample_data(conn):
    """Add sample data to the database."""
    # Add Teams
    team_ids = []
    teams = [
        ("Engineering", "Software development team"),
        ("Design", "UX and UI design team"),
        ("Product", "Product management team"),
        ("Data Science", "Data analysis and ML team")
    ]
    
    for team_name, team_desc in teams:
        team_id = str(uuid4())
        conn.execute("""
        INSERT INTO teams (id, name, description)
        VALUES (?, ?, ?)
        """, [team_id, team_name, team_desc])
        team_ids.append(team_id)
    
    # Add sub-teams with parent relationships
    sub_teams = [
        ("Frontend", "Frontend development team", team_ids[0]),  # Under Engineering
        ("Backend", "Backend development team", team_ids[0]),    # Under Engineering
        ("UX", "User experience team", team_ids[1]),            # Under Design
        ("UI", "User interface team", team_ids[1]),             # Under Design
        ("Product Strategy", "Product strategy team", team_ids[2]),  # Under Product
        ("Product Operations", "Product operations team", team_ids[2]),  # Under Product
        ("Machine Learning", "ML team", team_ids[3]),           # Under Data Science
        ("Data Engineering", "Data engineering team", team_ids[3])  # Under Data Science
    ]
    
    for team_name, team_desc, parent_id in sub_teams:
        team_id = str(uuid4())
        conn.execute("""
        INSERT INTO teams (id, name, description, parent_team_id)
        VALUES (?, ?, ?, ?)
        """, [team_id, team_name, team_desc, parent_id])
        team_ids.append(team_id)
    
    # Add People
    people_ids = []
    people = [
        ("John Smith", "Software Engineer", team_ids[4]),  # Frontend team
        ("Jane Doe", "Senior Developer", team_ids[5]),     # Backend team
        ("Bob Johnson", "UX Designer", team_ids[6]),       # UX team
        ("Alice Brown", "Product Manager", team_ids[9]),   # Product Strategy team
        ("Charlie Davis", "Data Scientist", team_ids[10]), # ML team
        ("Eva Wilson", "Backend Developer", team_ids[5]),  # Backend team
        ("Frank Miller", "Frontend Developer", team_ids[4]), # Frontend team
        ("Grace Lee", "UI Designer", team_ids[7])          # UI team
    ]
    
    for person_name, person_role, team_id in people:
        person_id = str(uuid4())
        conn.execute("""
        INSERT INTO people (id, name, role, team_id)
        VALUES (?, ?, ?, ?)
        """, [person_id, person_name, person_role, team_id])
        people_ids.append(person_id)
    
    # Add Projects
    today = date.today()
    project_ids = []
    projects = [
        ("Website Redesign", "Redesign company website with new branding", today - timedelta(days=30), today + timedelta(days=90), "active", people_ids[3], "Marketing", team_ids[1]),
        ("Mobile App Development", "Create new mobile app for customers", today - timedelta(days=15), today + timedelta(days=120), "active", people_ids[0], "Development", team_ids[0]),
        ("Data Platform", "Build new data analytics platform", today + timedelta(days=15), today + timedelta(days=180), "planning", people_ids[4], "Infrastructure", team_ids[3]),
        ("CRM Integration", "Integrate with new CRM system", today + timedelta(days=45), today + timedelta(days=90), "planning", people_ids[5], "Integration", team_ids[2])
    ]
    
    for proj_name, proj_desc, start_date, end_date, status, manager_id, proj_type, team_id in projects:
        project_id = str(uuid4())
        conn.execute("""
        INSERT INTO projects (id, name, description, start_date, end_date, status, 
                             project_manager_id, project_type, lead_team_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [project_id, proj_name, proj_desc, start_date, end_date, status, manager_id, proj_type, team_id])
        project_ids.append(project_id)
    
    # Add Demands
    demand_ids = []
    demands = [
        (project_ids[0], "Frontend Developer", 1.0, today - timedelta(days=30), today + timedelta(days=90), 3, "partially_filled"),
        (project_ids[0], "UX Designer", 0.5, today - timedelta(days=30), today + timedelta(days=45), 2, "filled"),
        (project_ids[1], "Mobile Developer", 2.0, today - timedelta(days=15), today + timedelta(days=120), 4, "partially_filled"),
        (project_ids[2], "Data Engineer", 1.0, today + timedelta(days=15), today + timedelta(days=180), 3, "open"),
        (project_ids[2], "Machine Learning Engineer", 0.5, today + timedelta(days=45), today + timedelta(days=180), 2, "open"),
        (project_ids[3], "Backend Developer", 1.0, today + timedelta(days=45), today + timedelta(days=90), 3, "open")
    ]
    
    for proj_id, role, fte, start_date, end_date, priority, status in demands:
        demand_id = str(uuid4())
        conn.execute("""
        INSERT INTO demands (id, project_id, role_required, fte_required, start_date, end_date, priority, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [demand_id, proj_id, role, fte, start_date, end_date, priority, status])
        demand_ids.append(demand_id)
    
    # Add Allocations
    allocations = [
        (people_ids[6], project_ids[0], demand_ids[0], 0.8, today - timedelta(days=30), today + timedelta(days=90), "Frontend work for website redesign"),
        (people_ids[2], project_ids[0], demand_ids[1], 0.5, today - timedelta(days=30), today + timedelta(days=45), "UX design for website"),
        (people_ids[5], project_ids[1], demand_ids[2], 0.5, today - timedelta(days=15), today + timedelta(days=120), "Backend support for mobile app"),
        (people_ids[6], project_ids[1], demand_ids[2], 0.5, today - timedelta(days=15), today + timedelta(days=60), "Frontend components for mobile app")
    ]
    
    for person_id, proj_id, demand_id, fte, start_date, end_date, notes in allocations:
        allocation_id = str(uuid4())
        conn.execute("""
        INSERT INTO allocations (id, person_id, project_id, demand_id, fte_allocated, start_date, end_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [allocation_id, person_id, proj_id, demand_id, fte, start_date, end_date, notes])

def compute_monthly_allocations(conn=None):
    """
    Compute monthly demand and allocation data for visualization.
    
    Args:
        conn: Optional database connection. If not provided, a new connection will be created.
    """
    should_close_conn = False
    if conn is None:
        conn = duckdb.connect("resource_flow.duckdb")
        should_close_conn = True
    
    try:
        # Clear the existing data
        conn.execute("DELETE FROM monthly_demand_allocation")
        
        # Get the date range for all demands and allocations
        date_range = conn.execute("""
            SELECT 
                MIN(start_date) as min_date,
                MAX(end_date) as max_date
            FROM (
                SELECT start_date, end_date FROM demands
                UNION ALL
                SELECT start_date, end_date FROM allocations
            )
        """).fetchone()
        
        if not date_range[0] or not date_range[1]:
            return
        
        start_date = date_range[0]
        end_date = date_range[1]
        
        # Generate a series of months
        current_date = date(start_date.year, start_date.month, 1)
        end_month = date(end_date.year, end_date.month, 1)
        
        # Get people count for capacity calculation
        people_count = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        
        while current_date <= end_month:
            # Calculate days in the month
            _, days_in_month = monthrange(current_date.year, current_date.month)
            month_end = date(current_date.year, current_date.month, days_in_month)
            
            # Calculate demand FTE for the month
            demand_fte = conn.execute("""
                SELECT COALESCE(SUM(
                    fte_required * (
                        CAST(
                            (LEAST(end_date, ?) - GREATEST(start_date, ?))
                            AS INTEGER) + 1
                    ) / CAST(? AS INTEGER)
                ), 0) as monthly_fte
                FROM demands
                WHERE start_date <= ? AND end_date >= ?
            """, [month_end, current_date, days_in_month, month_end, current_date]).fetchone()[0]
            
            # Calculate allocation FTE for the month
            allocation_fte = conn.execute("""
                SELECT COALESCE(SUM(
                    fte_allocated * (
                        CAST(
                            (LEAST(end_date, ?) - GREATEST(start_date, ?))
                            AS INTEGER) + 1
                    ) / CAST(? AS INTEGER)
                ), 0) as monthly_fte
                FROM allocations
                WHERE start_date <= ? AND end_date >= ?
            """, [month_end, current_date, days_in_month, month_end, current_date]).fetchone()[0]
            
            # Check if capacity_fte column exists in the table
            has_capacity = conn.execute("""
                SELECT COUNT(*) FROM pragma_table_info('monthly_demand_allocation') 
                WHERE name = 'capacity_fte'
            """).fetchone()[0]
            
            if has_capacity:
                # Insert with capacity_fte
                conn.execute("""
                    INSERT INTO monthly_demand_allocation 
                    (year_month, demand_fte, allocation_fte, capacity_fte)
                    VALUES (?, ?, ?, ?)
                """, [current_date, demand_fte, allocation_fte, people_count])
            else:
                # Insert without capacity_fte (older schema)
                conn.execute("""
                    INSERT INTO monthly_demand_allocation 
                    (year_month, demand_fte, allocation_fte)
                    VALUES (?, ?, ?)
                """, [current_date, demand_fte, allocation_fte])
            
            # Move to next month
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
    
    finally:
        if should_close_conn:
            conn.close() 