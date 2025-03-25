import duckdb
import os
from datetime import date, datetime, timedelta
from calendar import monthrange

def initialize_database():
    """Initialize the DuckDB database with tables and sample data."""
    db_path = "resource_flow.duckdb"
    
    # Check if database already exists
    if os.path.exists(db_path):
        print(f"Database already exists at {db_path}")
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
        id INTEGER PRIMARY KEY,
        name VARCHAR NOT NULL,
        description VARCHAR
    )
    """)
    
    # Create People table
    conn.execute("""
    CREATE TABLE people (
        id INTEGER PRIMARY KEY,
        name VARCHAR NOT NULL,
        role VARCHAR,
        skills VARCHAR,
        team_id INTEGER,
        FOREIGN KEY (team_id) REFERENCES teams(id)
    )
    """)
    
    # Create Projects table
    conn.execute("""
    CREATE TABLE projects (
        id INTEGER PRIMARY KEY,
        name VARCHAR NOT NULL,
        description VARCHAR,
        start_date DATE NOT NULL,
        end_date DATE,
        status VARCHAR DEFAULT 'planning'
    )
    """)
    
    # Create Demands table
    conn.execute("""
    CREATE TABLE demands (
        id INTEGER PRIMARY KEY,
        project_id INTEGER NOT NULL,
        role_required VARCHAR,
        skills_required VARCHAR,
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
        id INTEGER PRIMARY KEY,
        person_id INTEGER NOT NULL,
        project_id INTEGER NOT NULL,
        demand_id INTEGER,
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
    teams = [
        (1, "Engineering", "Software development team"),
        (2, "Design", "UX and UI design team"),
        (3, "Product", "Product management team"),
        (4, "Data Science", "Data analysis and ML team")
    ]
    
    conn.executemany("""
    INSERT INTO teams (id, name, description)
    VALUES (?, ?, ?)
    """, teams)
    
    # Add People
    people = [
        (1, "John Smith", "Software Engineer", "Python,JavaScript,React", 1),
        (2, "Jane Doe", "Senior Developer", "Java,Kubernetes,Docker", 1),
        (3, "Bob Johnson", "UX Designer", "Figma,Sketch,UI Design", 2),
        (4, "Alice Brown", "Product Manager", "Agile,Roadmapping,User Research", 3),
        (5, "Charlie Davis", "Data Scientist", "Python,R,Machine Learning,SQL", 4),
        (6, "Eva Wilson", "Backend Developer", "Java,Spring,Databases", 1),
        (7, "Frank Miller", "Frontend Developer", "JavaScript,React,CSS,HTML", 1),
        (8, "Grace Lee", "UI Designer", "Illustrator,Photoshop,Wireframing", 2)
    ]
    
    conn.executemany("""
    INSERT INTO people (id, name, role, skills, team_id)
    VALUES (?, ?, ?, ?, ?)
    """, people)
    
    # Add Projects
    today = date.today()
    projects = [
        (1, "Website Redesign", "Redesign company website with new branding", today - timedelta(days=30), today + timedelta(days=90), "active"),
        (2, "Mobile App Development", "Create new mobile app for customers", today - timedelta(days=15), today + timedelta(days=120), "active"),
        (3, "Data Platform", "Build new data analytics platform", today + timedelta(days=15), today + timedelta(days=180), "planning"),
        (4, "CRM Integration", "Integrate with new CRM system", today + timedelta(days=45), today + timedelta(days=90), "planning")
    ]
    
    conn.executemany("""
    INSERT INTO projects (id, name, description, start_date, end_date, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, projects)
    
    # Add Demands
    demands = [
        (1, 1, "Frontend Developer", "React,JavaScript,HTML,CSS", 1.0, today - timedelta(days=30), today + timedelta(days=90), 3, "partially_filled"),
        (2, 1, "UX Designer", "Figma,Sketch,User Research", 0.5, today - timedelta(days=30), today + timedelta(days=45), 2, "filled"),
        (3, 2, "Mobile Developer", "Swift,Kotlin,React Native", 2.0, today - timedelta(days=15), today + timedelta(days=120), 4, "partially_filled"),
        (4, 3, "Data Engineer", "Python,SQL,ETL,Spark", 1.0, today + timedelta(days=15), today + timedelta(days=180), 3, "open"),
        (5, 3, "Machine Learning Engineer", "Python,ML,TensorFlow", 0.5, today + timedelta(days=45), today + timedelta(days=180), 2, "open"),
        (6, 4, "Backend Developer", "Java,Spring,API Design", 1.0, today + timedelta(days=45), today + timedelta(days=90), 3, "open")
    ]
    
    conn.executemany("""
    INSERT INTO demands (id, project_id, role_required, skills_required, fte_required, start_date, end_date, priority, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, demands)
    
    # Add Allocations
    allocations = [
        (1, 7, 1, 1, 0.8, today - timedelta(days=30), today + timedelta(days=90), "Frontend work for website redesign"),
        (2, 3, 1, 2, 0.5, today - timedelta(days=30), today + timedelta(days=45), "UX design for website"),
        (3, 6, 2, 3, 0.5, today - timedelta(days=15), today + timedelta(days=120), "Backend support for mobile app"),
        (4, 7, 2, 3, 0.5, today - timedelta(days=15), today + timedelta(days=60), "Frontend components for mobile app")
    ]
    
    conn.executemany("""
    INSERT INTO allocations (id, person_id, project_id, demand_id, fte_allocated, start_date, end_date, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, allocations)

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