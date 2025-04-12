import duckdb
import os
from datetime import date

def migrate_database():
    """Migrate the database to the latest schema."""
    db_path = "resource_flow.duckdb"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    # Connect to the database
    conn = duckdb.connect(db_path)
    
    try:
        # Check if the capacity_fte column exists in monthly_demand_allocation
        has_capacity = conn.execute("""
            SELECT COUNT(*) FROM pragma_table_info('monthly_demand_allocation') 
            WHERE name = 'capacity_fte'
        """).fetchone()[0]
        
        if not has_capacity:
            print("Migrating monthly_demand_allocation table to add capacity_fte column...")
            
            # Create a backup of the current data
            conn.execute("""
                CREATE TEMP TABLE monthly_demand_allocation_backup AS
                SELECT * FROM monthly_demand_allocation
            """)
            
            # Add the capacity_fte column to the table
            conn.execute("""
                ALTER TABLE monthly_demand_allocation ADD COLUMN capacity_fte FLOAT DEFAULT 0
            """)
            
            # Update capacity values (set to people count for simplicity)
            people_count = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
            conn.execute(f"""
                UPDATE monthly_demand_allocation
                SET capacity_fte = {people_count}
            """)
            
            print(f"Added capacity_fte column with default value {people_count}")
            
            # Recompute monthly allocations
            print("Recomputing monthly allocations...")
            from app.database.init_db import compute_monthly_allocations
            compute_monthly_allocations(conn)
            
            print("Capacity migration completed successfully!")
        
        # Project fields migration
        # Check if columns exist in projects table
        columns = conn.execute("""
            SELECT name FROM pragma_table_info('projects')
        """).fetchall()
        column_names = [col[0] for col in columns]
        
        project_columns_added = False
        
        # Check if we need to convert project_manager to project_manager_id
        if "project_manager" in column_names and "project_manager_id" not in column_names:
            print("Converting project_manager from string to project_manager_id reference...")
            
            # First add the project_manager_id column
            conn.execute("ALTER TABLE projects ADD COLUMN project_manager_id INTEGER REFERENCES people(id)")
            
            # Then try to match project_manager names to people names
            # Get all projects with project_manager set
            projects_with_managers = conn.execute("""
                SELECT id, project_manager FROM projects 
                WHERE project_manager IS NOT NULL AND project_manager != ''
            """).fetchall()
            
            # Get all people for matching
            people = conn.execute("SELECT id, name FROM people").fetchall()
            people_map = {person[1]: person[0] for person in people}
            
            # Update each project's project_manager_id if we can find a match
            for project_id, manager_name in projects_with_managers:
                if manager_name in people_map:
                    person_id = people_map[manager_name]
                    conn.execute(
                        "UPDATE projects SET project_manager_id = ? WHERE id = ?",
                        [person_id, project_id]
                    )
            
            # Don't drop the old column yet - we'll do that in a future migration
            project_columns_added = True
        elif "project_manager_id" not in column_names:
            # Add project_manager_id column if it doesn't exist
            conn.execute("ALTER TABLE projects ADD COLUMN project_manager_id INTEGER REFERENCES people(id)")
            project_columns_added = True
        
        # Add project_type column if it doesn't exist
        if "project_type" not in column_names:
            conn.execute("ALTER TABLE projects ADD COLUMN project_type VARCHAR")
            project_columns_added = True
        
        # Add lead_team_id column if it doesn't exist
        if "lead_team_id" not in column_names:
            conn.execute("ALTER TABLE projects ADD COLUMN lead_team_id INTEGER REFERENCES teams(id)")
            project_columns_added = True
        
        if project_columns_added:
            print("Added new project fields: project_manager_id, project_type, and lead_team_id")
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database() 