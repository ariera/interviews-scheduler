# Interview Scheduler

> **Disclaimer**: This repository has been entirely vibe-coded. While functional and feature-complete, it represents a rapid development approach focused on getting things working rather than following traditional software engineering practices. It's been a fun experiment! Use at your own discretion.

A powerful constraint-based interview scheduling system that uses Google OR-Tools CP-SAT solver to optimize interview schedules with complex constraints.

## Features

- **Flexible Configuration**: YAML-based configuration for easy setup
- **Complex Constraints**: Support for position constraints, panel conflicts, and gap limits
- **Multiple Solutions**: Generate multiple optimal schedules
- **Web Interface**: Modern, responsive web UI with drag & drop file upload
- **CLI Tool**: Command-line interface for automation and scripting

## Quick Start

### Option 1: Command Line Interface (CLI)

The fastest way to get started:

```bash
# Install dependencies
pip install -r requirements.txt

# Run with example configuration
python run_cli.py examples/config-Thu-c=3.yaml

# Try different examples
python run_cli.py examples/complete-example.yaml
python run_cli.py examples/config-Tue-c=2.yaml
```

### Option 2: Web Interface (Local)

For a visual interface with drag & drop configuration:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the web interface
python run_web_local.py
```

Then open http://localhost:8000 in your browser and upload a YAML configuration file.

### What You'll See

The scheduler will generate optimal interview schedules with:
- ✅ All candidates assigned to all required panels
- ✅ Panels scheduled within their availability windows
- ✅ Proper ordering and position constraints respected
- ✅ Panel conflicts avoided (e.g., Team and Goodbye panels)
- ✅ Minimal gaps between consecutive sessions


## Configuration

### YAML Configuration Format

```yaml
# Basic configuration
num_candidates: 3
panels:
  Director: "30min"
  Competencies: "1h"
  Customers: "1h"
  HR: "45min"
  Lunch: "1h"
  Team: "45min"
  Goodbye: "30min"

# Preferred order of panels (soft constraint)
order:
  - Director
  - Competencies
  - Customers
  - Lunch
  - Team
  - HR
  - Goodbye

# Availability windows for each panel
availabilities:
  Director: "8:30-10:00"
  Competencies:
    - "8:30-11:00"
    - "12:00-14:00"
  Customers: "8:30-14:00"
  HR: "8:30-17:00"
  Team: "8:30-17:00"
  Goodbye: "8:30-17:00"
  Lunch: "11:45-13:30"

# Position constraints (hard constraints)
position_constraints:
  Goodbye: "last"

# Panel conflicts (cannot run in parallel)
panel_conflicts:
  - ["Team", "Goodbye"]
```

## Usage

### Web Interface

1. Upload a YAML configuration file
2. Click "Generate Schedule" to create multiple solutions
3. View results in tabs with detailed schedules
4. Download results as JSON

### CLI Tool

```bash
# Basic usage
python run_cli.py config.yaml

# With options
python run_cli.py config.yaml --max-time 300 --quiet --output results.json

# Validate configuration
python run_cli.py config.yaml --validate
```

### Programmatic Usage

```python
from src.scheduler.schedule import InterviewScheduler

scheduler = InterviewScheduler(
    candidates=3,
    panels=[
        {"name": "Technical", "duration": 45},
        {"name": "Behavioral", "duration": 30}
    ],
    availability=[
        {"day": "Monday", "start": "09:00", "end": "17:00"}
    ],
    slots_per_day=8,
    max_gap=15
)

solutions = scheduler.solve(max_solutions=5, max_time=300)
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI
python run_cli.py examples/complete-example.yaml

# Run API locally (for testing)
cd api
python app.py
```

## Architecture

The project uses a clean separation of concerns:

- **Core Logic** (`src/scheduler/`): Pure Python scheduling algorithms
- **CLI Interface** (`run_cli.py`): Command-line tool
- **API Backend** (`api/`): Flask server for web interface
- **Web Frontend** (`docs/`): Static HTML/JS for local development

## Examples

See the `examples/` directory for various configuration examples:

- `complete-example.yaml` - Full-featured example
- `config-Thu-c=2.yaml` - Thursday schedule with 2 candidates
- `config-Tue-c=2.yaml` - Tuesday schedule with 2 candidates
