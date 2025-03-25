# Resource Flow

A lightweight, responsive resource planning application that helps teams manage resource allocation and track demand fulfillment with intuitive visualizations.

## Features

- **Resource Management**: Track people, teams, and their allocations
- **Project Planning**: Manage projects and their resource demands
- **Time-Based Visualization**: View allocations and demand fulfillment over time
- **FTE Analysis**: Calculate and visualize Full-Time Equivalent metrics
- **Responsive Dashboard**: Get quick insights into resource utilization

## Tech Stack

- **Frontend**: Streamlit
- **Database**: DuckDB
- **Data Processing**: Polars
- **Package Management**: uv
- **Visualization**: Plotly, Altair

## Getting Started

### Prerequisites

- Python 3.9+
- uv package manager

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd resource-flow
   ```

2. Create and activate the virtual environment:
   ```
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```

4. Run the application:
   ```
   streamlit run app/main.py
   ```

## Development

See the [PROJECT_PLAN.md](PROJECT_PLAN.md) file for a detailed development plan and application structure.

## Data Model

The application uses the following data model:

- **People**: Resource information and capacity
- **Teams**: Organizational structure
- **Projects**: Work initiatives requiring resources
- **Demand**: Resource requirements for projects
- **Allocations**: Assignment of people to projects

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 