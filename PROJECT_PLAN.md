# Resource Flow: Resource Planning Application

## Project Overview

Resource Flow is a lightweight, responsive resource planning application built with Streamlit. It provides intuitive interfaces for managing resource allocation and demand tracking with time-resolved visualizations.

## Technologies

- **Frontend**: Streamlit (web interface)
- **Backend**: Python
- **Database**: DuckDB
- **Data Processing**: Polars
- **Package Management**: uv
- **Visualization**: Plotly, Altair

## Data Model

### Core Tables

1. **People**
   - id (primary key)
   - name
   - email
   - role
   - skills
   - team_id (foreign key to Teams)
   - fte_capacity (default 1.0)
   - active (boolean)

2. **Teams**
   - id (primary key)
   - name
   - description
   - manager_id (foreign key to People)
   - department

3. **Projects**
   - id (primary key)
   - name
   - description
   - priority (high, medium, low)
   - status (planning, active, completed, on_hold)
   - start_date
   - end_date
   - owner_id (foreign key to People)

4. **Demand**
   - id (primary key)
   - project_id (foreign key to Projects)
   - role_required
   - skills_required
   - fte_required
   - start_date
   - end_date
   - priority
   - status (unfilled, partially_filled, filled)

5. **Allocations**
   - id (primary key)
   - person_id (foreign key to People)
   - project_id (foreign key to Projects)
   - demand_id (foreign key to Demand, nullable)
   - fte_allocated
   - start_date
   - end_date
   - notes

### Computed Tables

6. **MonthlyDemandAllocation**
   - id (primary key)
   - year_month
   - project_id (foreign key to Projects)
   - demand_id (foreign key to Demand)
   - person_id (foreign key to People, nullable)
   - fte_demand
   - fte_allocated
   - fte_gap
   - status (unfilled, partially_filled, filled, over_allocated)

## Application Structure

```
resource-flow/
├── .venv/                    # Virtual environment
├── .git/                     # Git repository
├── .gitignore                # Git ignore file
├── requirements.txt          # Project dependencies
├── README.md                 # Project documentation
├── app/
│   ├── main.py               # Main application entry point
│   ├── database/
│   │   ├── init_db.py        # Database initialization script
│   │   ├── models.py         # Data models
│   │   └── queries.py        # Database queries
│   ├── utils/
│   │   ├── date_utils.py     # Date handling utilities
│   │   ├── fte_calculator.py # FTE calculation logic 
│   │   └── data_processor.py # Data processing utilities
│   ├── components/
│   │   ├── sidebar.py        # Sidebar component
│   │   ├── dashboard.py      # Dashboard component
│   │   ├── people_view.py    # People management view
│   │   ├── teams_view.py     # Teams management view
│   │   ├── projects_view.py  # Projects management view
│   │   ├── demand_view.py    # Demand management view
│   │   └── allocations_view.py # Allocations management view
│   └── visualizations/
│       ├── gantt_chart.py    # Gantt chart for time-based visualization
│       ├── fte_heatmap.py    # Heatmap for FTE allocation
│       ├── demand_vs_supply.py # Demand vs. supply comparison
│       └── team_allocation.py # Team allocation breakdown
└── tests/                    # Test directory
    ├── test_database.py      # Database tests
    ├── test_calculations.py  # Calculation tests
    └── test_views.py         # View tests
```

## Implementation Plan

### Phase 1: Setup and Foundation (1-2 days)

1. ✅ Set up development environment with uv
2. ✅ Initialize git repository
3. Create basic application structure
4. Implement database schema and initialization scripts
5. Create core data models

### Phase 2: Core Functionality (3-5 days)

1. Implement People and Teams management
2. Implement Projects management
3. Implement Demand tracking functionality
4. Implement Allocations management
5. Create monthly aggregation logic for time-based analysis

### Phase 3: Visualization and Dashboard (2-3 days)

1. Implement Gantt chart for resource allocations
2. Create demand fulfillment visualizations
3. Build FTE utilization dashboard
4. Implement time period filtering (quarterly, annual)
5. Create team-based allocation views

### Phase 4: Polishing and Enhancement (2-3 days)

1. Implement data import/export functionality
2. Add data validation and error handling
3. Improve UI/UX with consistent styling
4. Create user documentation
5. Implement basic user preferences (view settings, etc.)

## Key Features

1. **Dashboard View**: Overview of resource allocation, demand, and fulfillment
2. **Time-Based Visualization**: Gantt-like charts showing allocation and demand over time
3. **FTE Analysis**: Track Full-Time Equivalent metrics by month, quarter, and year
4. **Demand Management**: Create and track resource demands for projects
5. **Allocation Tracking**: Assign people to projects with specific FTE commitments
6. **Gap Analysis**: Identify resource shortfalls or overallocations
7. **Flexible Time Periods**: View data at different time resolutions (monthly, quarterly, annual)

## Future Enhancements

1. User authentication and role-based access
2. Notifications for overallocations or approaching deadlines
3. Resource forecasting and scenario planning
4. Integration with external calendars or project management tools
5. Enhanced filtering and search capabilities
6. Version history and change tracking
7. Mobile optimization for on-the-go access
8. Additional data models for skills, locations, and costs

## Maintenance Plan

1. Use git for version control and feature tracking
2. Maintain a clean database schema for easy extension
3. Create clear documentation for data models and calculations
4. Use automated tests to ensure data integrity
5. Implement modular components for easy extension and maintenance 