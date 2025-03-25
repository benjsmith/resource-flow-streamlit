# Resource Flow

A lightweight, responsive, and informative resource planning application built with Streamlit, DuckDB, and Polars.

## Features

- Dashboard with time-resolved plots
- Team management
- Project management
- Resource demand tracking
- Resource allocation tracking
- Visualizations for resource planning

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

- People: Resource people with skills and team assignments
- Teams: Groups of people
- Projects: Projects with timeline and status
- Demands: Resource demands for projects
- Allocations: Resource allocations to projects

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 