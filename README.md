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
pip install ortools==9.10.4068
```

### Running the Algorithm
```bash
python schedule.py
```

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