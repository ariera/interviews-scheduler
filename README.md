# Interview Scheduler

A powerful constraint-based interview scheduling system that uses Google OR-Tools CP-SAT solver to optimize interview schedules with complex constraints.

## Features

- **Flexible Configuration**: YAML-based configuration for easy setup
- **Complex Constraints**: Support for position constraints, panel conflicts, and gap limits
- **Multiple Solutions**: Generate multiple optimal schedules
- **Web Interface**: Modern, responsive web UI with drag & drop file upload
- **CLI Tool**: Command-line interface for automation and scripting
- **Docker Support**: Production-ready Docker deployment

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd interview_scheduler
   ```

2. **Deploy with Docker:**
   ```bash
   # Development environment
   ./deploy.sh dev up

   # Production environment
   ./deploy.sh prod up
   ```

3. **Access the web interface:**
   - Development: http://localhost:5001
   - Production: http://localhost:8080

### Manual Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the web interface:**
   ```bash
   python run_web.py
   ```

3. **Or use the CLI:**
   ```bash
   python run_cli.py examples/complete-example.yaml
   ```

## Configuration

### YAML Configuration Format

```yaml
# Basic configuration
candidates: 3
panels:
  - name: "Technical"
    duration: 45
  - name: "Behavioral"
    duration: 30
  - name: "Goodbye"
    duration: 15
    position: "last"  # Fixed position constraint

# Availability windows
availability:
  - day: "Monday"
    start: "09:00"
    end: "17:00"
  - day: "Tuesday"
    start: "10:00"
    end: "16:00"

# Constraints
slots_per_day: 8
max_gap: 15
start_time: "09:00"

# Panel conflicts (cannot run in parallel)
panel_conflicts:
  - ["Team", "Goodbye"]
  - ["Technical", "Behavioral"]

# Preferred order (soft constraint)
preferred_order:
  - "Technical"
  - "Behavioral"
  - "Goodbye"
```

### Environment Variables

See `production.env.example` and `development.env.example` for available configuration options.

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

## Docker Deployment

### Development

```bash
# Start development environment
./deploy.sh dev up

# View logs
./deploy.sh dev logs

# Stop services
./deploy.sh dev down
```

### Production

```bash
# Setup production environment
cp production.env.example production.env
# Edit production.env with your settings

# Deploy
./deploy.sh prod up

# Monitor
./deploy.sh prod status
./deploy.sh prod logs
```

### Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

For detailed Docker documentation, see [docker/README.md](docker/README.md).

## Architecture

```
interview_scheduler/
├── src/
│   ├── scheduler/          # Core scheduling logic
│   │   ├── schedule.py     # InterviewScheduler class
│   │   └── cli.py         # Command-line interface
│   └── web/               # Web application
│       ├── app.py         # Flask application
│       └── templates/     # HTML templates
├── examples/              # Configuration examples
├── docker/               # Docker configuration
├── run_web.py           # Web interface entry point
├── run_cli.py           # CLI entry point
└── deploy.sh            # Deployment script
```

## Constraints Supported

- **Duration Constraints**: Each panel has a specific duration
- **Availability Windows**: Time slots when interviews can be scheduled
- **Gap Limits**: Maximum time between consecutive sessions
- **Position Constraints**: Force panels to specific positions (first, last, or specific)
- **Panel Conflicts**: Prevent certain panels from running in parallel
- **Preferred Order**: Soft constraints for panel ordering

## Examples

See the `examples/` directory for various configuration examples:

- `complete-example.yaml`: Full-featured example with all constraints
- `config.yaml`: Basic configuration
- `example-web.yaml`: Web interface example

## Development

### Project Structure

The project follows a clean architecture with separation of concerns:

- **Core Logic**: `src/scheduler/schedule.py` contains the main scheduling algorithm
- **CLI Interface**: `src/scheduler/cli.py` provides command-line access
- **Web Interface**: `src/web/app.py` serves the Flask web application
- **Configuration**: YAML files for easy configuration management

### Adding New Features

1. **Core Logic**: Extend `InterviewScheduler` class in `schedule.py`
2. **CLI**: Add new options in `cli.py`
3. **Web Interface**: Update Flask routes in `app.py`
4. **Configuration**: Update YAML schema and examples

### Testing

```bash
# Run tests (when implemented)
python -m pytest

# Manual testing
python run_cli.py examples/complete-example.yaml
python run_web.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
1. Check the examples in `examples/`
2. Review the Docker documentation in `docker/README.md`
3. Open an issue on the repository
