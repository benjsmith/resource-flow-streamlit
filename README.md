# Resource Flow

A lightweight, responsive, and informative resource planning application built with Streamlit, DuckDB, and Polars.

## Features

- **Dashboard**
  - Overview of resource allocation, demand, and status
  - Project health visualization
  - Team allocation charts
  - Resource trend analysis with period selection (Month/Quarter/Year)
  - Upcoming key dates tracking

- **Projects**
  - Project management with timeline and status
  - Project health metrics
  - Project timeline visualization
  - Project allocation breakdown

- **People & Teams**
  - Team management with hierarchical structure
  - Resource capacity tracking
  - Team allocation visualization
  - Role and skill management

- **Resource Planning**
  - Demand tracking with priority and status
  - Resource allocation with FTE tracking
  - Gap analysis between demand and allocation
  - Capacity utilization monitoring

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/resource-flow.git
cd resource-flow
```

2. Create a virtual environment and activate it:
```
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the dependencies:
```
pip install -r requirements.txt
```

## Running the Application

You can run the application in one of two ways:

### Option 1: Using the run script (recommended)

```
./run.py
```

### Option 2: Using Streamlit directly

```
# Make sure you're in the project root directory
python -m streamlit run app/main.py
```

The application will open in your default web browser at http://localhost:8501.

## Data Structure

The application uses the following data models:

- **People**: Resource people with skills and team assignments
  - id, name, role, team_id, fte_capacity, active

- **Teams**: Groups of people with hierarchical structure
  - id, name, description, parent_team_id

- **Projects**: Projects with timeline and status
  - id, name, description, start_date, end_date, status, project_manager_id, project_type, lead_team_id

- **Demands**: Resource demands for projects
  - id, project_id, role_required, fte_required, start_date, end_date, priority, status

- **Allocations**: Resource allocations to projects
  - id, person_id, project_id, demand_id, fte_allocated, start_date, end_date, notes

- **Monthly Demand Allocation**: Aggregated reporting data
  - id, year_month, project_id, demand_id, person_id, fte_demand, fte_allocated, fte_gap, status, capacity_fte

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 