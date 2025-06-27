#!/usr/bin/env python3
"""
Interview Day Scheduling Algorithm

This algorithm solves a complex scheduling problem for a hiring event where:
- 3 candidates must each attend 7 panels/activities
- Each panel has specific availability windows
- Hard constraint: gaps between consecutive sessions must be ≤ 15 minutes
- Soft constraint: prefer a specific order of panels
- Minimize order violations, then total completion time

The key insight is modeling the "follows" relationship between sessions
and enforcing the gap constraint as a hard constraint rather than soft.

Requirements: pip install ortools==9.10.4068
"""

from ortools.sat.python import cp_model

# ------------------------------------------------------------------
# Data Definition
# ------------------------------------------------------------------

CANDIDATES = range(3)  # 3 candidates to be interviewed

# Panel durations in 15-minute slots
PANELS = {
    "Director"     : 1,        # 15 minutes
    "Competencies" : 4,        # 1 hour
    "Customers"    : 4,        # 1 hour
    "HR"           : 3,        # 45 minutes
    "Lunch"        : 4,        # 1 hour
    "Team"         : 3,        # 45 minutes
    "Goodbye"      : 2,        # 30 minutes
}

# Preferred order (soft constraint)
ORDER = [
    "Director",
    "Competencies",
    "Customers",
    "Lunch",
    "Team",
    "HR",
    "Goodbye",
]

SLOTS_PER_DAY = 34  # 08:30 – 17:00 = 34×15 min slots

def t(h, m):
    """Convert clock time to slot index (08:30 = slot 0)"""
    return (h - 8) * 4 + (m - 30) // 15

# Panel availability windows (in slots)
AVAIL = {
    "Director"    : [(t(8,30),  t(10, 0))],     # Only available 08:30-10:00
    "Competencies": [(t(8,30),  t(11, 0)),      # Available 08:30-11:00,
                     (t(12,0),  t(14, 0)),      #           12:00-14:00,
                     (t(16,0),  t(17, 0))],     #           16:00-17:00
    "Customers"   : [(t(8,30),  t(14, 0))],     # Must finish by 14:00
    "HR"          : [(t(8,30),  t(17, 0))],     # Available all day
    "Team"        : [(t(8,30),  t(17, 0))],     # Available all day
    "Goodbye"     : [(t(8,30),  t(17, 0))],     # Available all day
    "Lunch"       : [(t(11,45), t(13,30))],     # Canteen window 11:45-13:30
}

# ------------------------------------------------------------------
# Constraint Programming Model
# ------------------------------------------------------------------

print("Building constraint model...")
model = cp_model.CpModel()

# Decision variables: start time of each (candidate, panel) session
start = {
    (c, p): model.NewIntVar(0, SLOTS_PER_DAY - d, f"start_{c}_{p}")
    for c in CANDIDATES for p, d in PANELS.items()
}

# Interval variables for no-overlap constraints
interval = {
    (c, p): model.NewIntervalVar(start[(c, p)], d, start[(c, p)] + d, f"interval_{c}_{p}")
    for c in CANDIDATES for p, d in PANELS.items()
}

# ------------------------------------------------------------------
# Hard Constraints
# ------------------------------------------------------------------

# 1. Each candidate cannot be in two sessions simultaneously
for c in CANDIDATES:
    model.AddNoOverlap([interval[(c, p)] for p in PANELS])

# 2. Each panel cannot see two candidates simultaneously (except Lunch)
for p in PANELS:
    if p != "Lunch":  # Multiple candidates can have lunch at the same time
        model.AddNoOverlap([interval[(c, p)] for c in CANDIDATES])

# 3. Panel availability windows
for (c, p), s in start.items():
    dur = PANELS[p]
    availability_options = []
    for (lo, hi) in AVAIL[p]:
        option = model.NewBoolVar(f"avail_{c}_{p}_{lo}")
        model.Add(s >= lo).OnlyEnforceIf(option)
        model.Add(s + dur <= hi).OnlyEnforceIf(option)
        availability_options.append(option)
    # Exactly one availability window must be chosen
    model.Add(sum(availability_options) == 1)

# 4. CRITICAL: Hard gap constraint ≤ 15 minutes between consecutive sessions
print("Adding gap constraints...")

for c in CANDIDATES:
    panels_list = list(PANELS.keys())

    # Boolean variables: follows[p1,p2] = True if p2 immediately follows p1 in schedule
    follows = {}
    for p1 in panels_list:
        for p2 in panels_list:
            if p1 != p2:
                follows[(p1, p2)] = model.NewBoolVar(f"follows_{c}_{p1}_{p2}")

    # Constraints for each potential "follows" relationship
    for p1 in panels_list:
        for p2 in panels_list:
            if p1 != p2:
                follows_var = follows[(p1, p2)]
                d1 = PANELS[p1]

                # If p2 follows p1: p2 starts after p1 ends
                model.Add(start[(c, p2)] >= start[(c, p1)] + d1).OnlyEnforceIf(follows_var)

                # If p2 follows p1: gap ≤ 1 slot (15 minutes) - THIS IS THE KEY CONSTRAINT
                model.Add(start[(c, p2)] <= start[(c, p1)] + d1 + 1).OnlyEnforceIf(follows_var)

                # If p2 follows p1: no other session can start between them
                for p3 in panels_list:
                    if p3 != p1 and p3 != p2:
                        # p3 must either end before p1 ends, or start after p2 starts
                        before = model.NewBoolVar(f"before_{c}_{p1}_{p2}_{p3}")
                        after = model.NewBoolVar(f"after_{c}_{p1}_{p2}_{p3}")

                        model.Add(start[(c, p3)] < start[(c, p1)] + d1).OnlyEnforceIf([follows_var, before])
                        model.Add(start[(c, p3)] >= start[(c, p2)]).OnlyEnforceIf([follows_var, after])
                        model.AddBoolOr([before, after]).OnlyEnforceIf(follows_var)

    # Topology constraints: each session has at most one predecessor and successor
    for p in panels_list:
        model.Add(sum(follows[(p1, p)] for p1 in panels_list if p1 != p) <= 1)
        model.Add(sum(follows[(p, p2)] for p2 in panels_list if p2 != p) <= 1)

    # Exactly 6 "follows" relationships form a chain of 7 sessions
    model.Add(sum(follows[(p1, p2)] for p1 in panels_list for p2 in panels_list if p1 != p2) == 6)

# ------------------------------------------------------------------
# Soft Constraints (Order Preference)
# ------------------------------------------------------------------

print("Adding order preference constraints...")
break_vars = []

for c in CANDIDATES:
    for i in range(len(ORDER) - 1):
        p1, p2 = ORDER[i], ORDER[i + 1]
        d1 = PANELS[p1]

        # break_var = True if preferred order is violated
        break_var = model.NewBoolVar(f"break_{c}_{p1}_{p2}")
        break_vars.append(break_var)

        # If order preserved: p1 ends before p2 starts
        model.Add(start[(c, p1)] + d1 <= start[(c, p2)]).OnlyEnforceIf(break_var.Not())
        # If order violated: p2 ends before p1 starts
        model.Add(start[(c, p2)] + PANELS[p2] <= start[(c, p1)]).OnlyEnforceIf(break_var)

# ------------------------------------------------------------------
# Objective Function
# ------------------------------------------------------------------

num_breaks = model.NewIntVar(0, len(break_vars), "num_breaks")
model.Add(num_breaks == sum(break_vars))

makespan = model.NewIntVar(0, SLOTS_PER_DAY, "makespan")
for c in CANDIDATES:
    for p, d in PANELS.items():
        model.Add(makespan >= start[(c, p)] + d)

# Hierarchical objective: minimize breaks first, then makespan
BIG = (SLOTS_PER_DAY + 1) * 1000
model.Minimize(num_breaks * BIG + makespan)

# ------------------------------------------------------------------
# Solve and Display Results
# ------------------------------------------------------------------

print("Solving...")
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60
status = solver.Solve(model)

def slot_to_time(s):
    """Convert slot index back to clock time"""
    h = 8 + s // 4
    m = 30 + 15 * (s % 4)
    if m >= 60:
        h += 1
        m -= 60
    return f"{h:02d}:{m:02d}"

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"\n{'='*50}")
    print(f"SOLUTION FOUND!")
    print(f"{'='*50}")
    print(f"Order breaks: {solver.Value(num_breaks)}")
    print(f"Status: {solver.StatusName(status)}")
    print("✓ All gaps between consecutive sessions are ≤ 15 minutes")
    print(f"✓ Day ends at: {slot_to_time(solver.Value(makespan))}")
    print()

    for c in CANDIDATES:
        sessions = sorted(
            ((solver.Value(start[(c, p)]), p) for p in PANELS),
            key=lambda x: x[0]
        )

        print(f"=== Candidate {c + 1} ===")
        prev_end = None
        total_gaps = 0

        for i, (s, p) in enumerate(sessions):
            e = s + PANELS[p]
            gap_str = ""

            if prev_end is not None:
                gap = s - prev_end
                total_gaps += gap
                if gap > 0:
                    gap_str = f" (gap: {gap * 15} min)"
                elif gap == 0:
                    gap_str = " (back-to-back)"

            print(f"  {p:<13} {slot_to_time(s)} – {slot_to_time(e)}{gap_str}")
            prev_end = e

        print(f"  Total idle time: {total_gaps * 15} minutes")
        print()

else:
    print(f"\n{'='*50}")
    print(f"NO FEASIBLE SOLUTION FOUND")
    print(f"{'='*50}")
    print(f"Status: {solver.StatusName(status)}")
    print("\nThis suggests the problem is over-constrained.")
    print("Possible solutions:")
    print("- Relax availability windows")
    print("- Allow longer gaps between sessions")
    print("- Reduce number of candidates or panels")
