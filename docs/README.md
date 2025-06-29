# Interview Day Scheduling Algorithm

A constraint programming solution for scheduling multiple candidates across multiple interview panels on a single day, with strict gap constraints and panel availability windows.

## Problem Description

### Scenario
- **3 candidates** must each attend **7 panels/activities**
- All interviews happen on the same day (08:30 – 17:00)
- Time is divided into **15-minute slots** (34 slots total)

### Panels and Durations
| Panel | Duration | Special Constraints |
|-------|----------|-------------------|
| Director | 15 min | Only available 08:30–10:00 |
| Competencies | 60 min | Unavailable 11:00–12:00 and 14:00–16:00 |
| Customers | 60 min | Must finish by 14:00 |
| HR | 45 min | Available all day |
| Lunch | 60 min | Canteen window 11:45–13:30 |
| Team | 45 min | Available all day |
| Goodbye | 30 min | Available all day |

### Constraints

#### Hard Constraints (Must be satisfied)
1. **No double-booking**: Candidates can't be in two places at once
2. **Panel capacity**: Each panel (except Lunch) can only see one candidate at a time
3. **Availability windows**: Sessions must fit within panel availability
4. **Gap constraint**: **≤ 15 minutes** idle time between any two consecutive sessions for each candidate
5. **Day bounds**: All sessions must fit within 08:30–17:00
6. **Position constraints**: Force specific panels to be at fixed positions (first, last, or specific position)

#### Soft Constraints (Preferences)
- **Preferred order**: Director → Competencies → Customers → Lunch → HR → Team → Goodbye
- Order violations are minimized but allowed if necessary

### Objectives (in priority order)
1. **Minimize order breaks** (deviations from preferred sequence)
2. **Minimize makespan** (when the last session of the day ends)

## Solution Approach

The key insight is modeling this as a **Constraint Satisfaction Problem** using Google OR-Tools CP-SAT solver, with a novel approach to the gap constraint:

### Key Innovation: "Follows" Relationship Modeling
Instead of trying to model gaps as soft constraints (which can be violated), we:

1. **Create boolean variables** `follows[p1, p2]` for each candidate indicating if panel `p2` immediately follows panel `p1` in the final schedule
2. **Enforce hard gap constraints**: If `p2` follows `p1`, then `start[p2] ≤ start[p1] + duration[p1] + 1` (gap ≤ 15 min)
3. **Ensure sequence topology**: Each session has at most one predecessor and successor, forming a valid chain
4. **Prevent overlaps**: No other session can start between consecutive sessions

This guarantees that **all gaps are ≤ 15 minutes** rather than just minimizing violations.

## Installation and Usage

### Prerequisites
```bash
pip install -r requirements.txt
```

### Using the Class Directly (Python API)
```python
from schedule import InterviewScheduler

# Define your parameters
scheduler = InterviewScheduler(
    num_candidates=3,
    panels={"Director": 1, "HR": 3, ...},
    order=["Director", "HR", ...],
    availabilities={"Director": [(0, 6)], ...},
    max_gap_minutes=15
)

# Solve and get results
if scheduler.solve():
    scheduler.print_solution()
```

### Using the Command Line Interface
```bash
# Basic usage
python cli.py config.yaml

# With options
python cli.py config.yaml --max-time 120 --output results.json

# Validate configuration only
python cli.py config.yaml --validate-only
```

### Using the Web Interface
The scheduler includes a modern web interface for easy configuration upload and solution viewing.

#### Starting the Web Server
```bash
python app.py
```

The web interface will be available at `http://localhost:5001`

#### Features
- **Drag & Drop Upload**: Simply drag your YAML configuration file onto the interface
- **Multiple Solutions**: Automatically generates up to 3 different scheduling solutions
- **Interactive Viewing**: Tabbed interface to compare different solutions
- **Solution Summary**: Overview of key metrics (order breaks, day end time, etc.)
- **Download Results**: Export all solutions as JSON for further analysis
- **Real-time Validation**: Immediate feedback on configuration errors

#### Web Interface Workflow
1. **Upload**: Drag and drop your YAML configuration file
2. **Process**: The system automatically runs the scheduler multiple times to find different solutions
3. **View**: Browse through the solutions using the tabbed interface
4. **Compare**: See how different solutions vary in timing and order
5. **Download**: Export the results for use in other tools

#### Example Usage
1. Create a YAML configuration file (see format below)
2. Open `http://localhost:5001` in your browser
3. Drag the YAML file onto the upload area
4. Wait for processing (typically 10-30 seconds)
5. Browse the solutions and download if needed

### YAML Configuration Format
Create a `config.yaml` file with your scheduling parameters:

```yaml
# Interview Scheduler Configuration
# ================================

# Basic scheduling parameters
num_candidates: 3

# Day configuration
start_time: "08:30"      # When the interview day starts
end_time: "17:00"        # When the interview day ends
slot_duration_minutes: 15  # Duration of each time slot
max_gap_minutes: 15      # Maximum allowed gap between consecutive sessions

# Panel definitions with durations
# Supported formats: '15min', '1h', '1h30min', or just numbers (minutes)
panels:
  Director: "15min"      # 15 minutes
  Competencies: "1h"     # 60 minutes
  Customers: "1h"        # 60 minutes
  HR: "45min"           # 45 minutes
  Lunch: "1h"           # 60 minutes
  Team: "45min"         # 45 minutes
  Goodbye: "30min"      # 30 minutes

# Preferred order of panels (soft constraint)
# The algorithm will try to follow this order but may deviate if necessary
order:
  - Director
  - Competencies
  - Customers
  - Lunch
  - Team
  - HR
  - Goodbye

# Availability windows for each panel
# Format: "HH:MM-HH:MM" or list of time ranges
availabilities:
  Director: "08:30-10:00"                    # Only available morning

  Competencies:                              # Multiple windows
    - "08:30-11:00"                         # Morning slot
    - "12:00-14:00"                         # Early afternoon
    - "16:00-17:00"                         # Late afternoon

  Customers: "08:30-14:00"                   # Must finish by 2 PM

  HR: "08:30-17:00"                         # Available all day

  Team: "08:30-17:00"                       # Available all day

  Goodbye: "08:30-17:00"                    # Available all day

  Lunch: "11:45-13:30"                      # Canteen serving window

# Position constraints (optional, hard constraints)
# Force specific panels to be at fixed positions in the schedule
position_constraints:
  Goodbye: "last"                           # Goodbye must always be the last panel
  # Director: "first"                       # Uncomment to force Director to be first
  # Lunch: 3                               # Uncomment to force Lunch to be 4th panel (0-indexed)

# Panel conflicts (optional, hard constraints)
# Prevent certain panels from running simultaneously due to shared resources
panel_conflicts:
  - [Team, Goodbye]                         # Team and Goodbye share people, cannot run simultaneously
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--max-time N` | Maximum solver time in seconds (default: 60) |
| `--quiet, -q` | Suppress progress messages |
| `--output FILE, -o FILE` | Save results to JSON file |
| `--validate-only` | Only validate configuration without solving |

### Expected Output
```
Building constraint model...
Adding gap constraints...
Adding order preference constraints...
Solving...

==================================================
SOLUTION FOUND!
==================================================
Order breaks: 3
Status: OPTIMAL
✓ All gaps between consecutive sessions are ≤ 15 minutes
✓ Day ends at: 14:45

=== Candidate 1 ===
  Director      08:30 – 08:45
  Competencies  08:45 – 09:45 (back-to-back)
  Customers     09:45 – 10:45 (back-to-back)
  HR            10:45 – 11:30 (back-to-back)
  Lunch         11:45 – 12:45 (gap: 15 min)
  Team          12:45 – 13:30 (back-to-back)
  Goodbye       13:30 – 14:00 (back-to-back)
  Total idle time: 15 minutes

... (similar for other candidates)
```

## Algorithm Details

### Variables
- `start[c, p]`: Start time (in slots) for candidate `c` at panel `p`
- `follows[c, p1, p2]`: Boolean indicating if `p2` immediately follows `p1` for candidate `c`
- `break_var[c, i]`: Boolean indicating if preferred order is violated between positions `i` and `i+1`

### Constraint Categories

1. **Basic Scheduling**
   - No-overlap constraints for candidates and panels
   - Availability window constraints

2. **Gap Enforcement**
   - Follows-relationship constraints
   - Hard gap limits (≤ 1 slot = 15 minutes)
   - Sequence topology constraints

3. **Order Preferences**
   - Soft constraints penalizing order violations
   - Hierarchical objective function

### Performance
- Typical solve time: < 5 seconds
- Guaranteed optimal solution for this problem size
- Scalable to larger instances with more candidates/panels

## Validation

The solution guarantees:
- ✅ All gaps between consecutive sessions are ≤ 15 minutes
- ✅ All panel availability windows are respected
- ✅ No scheduling conflicts
- ✅ Minimized order violations
- ✅ Compact schedule (early completion)

## Extensions

The algorithm can be easily extended for:
- Different gap constraints (e.g., ≤ 30 minutes)
- Additional panels or candidates
- Different availability windows
- Multiple days
- Priority candidates
- Panel capacity > 1

## Technical Notes

- **Time complexity**: Polynomial in practice for reasonable problem sizes
- **Space complexity**: O(candidates × panels²) for follows variables
- **Solver**: Google OR-Tools CP-SAT (state-of-the-art constraint solver)
- **Modeling paradigm**: Constraint Programming with Boolean satisfiability