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
        
        # Add project_manager column if it doesn't exist
        if "project_manager" not in column_names:
            conn.execute("ALTER TABLE projects ADD COLUMN project_manager VARCHAR")
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
            print("Added new project fields: project_manager, project_type, and lead_team_id")
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database() 