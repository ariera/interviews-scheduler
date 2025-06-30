#!/usr/bin/env python3
"""
Interview Day Scheduling Algorithm - Class-based Implementation

A flexible constraint programming solution for scheduling multiple candidates
across multiple interview panels with customizable parameters.

Requirements: pip install ortools==9.10.4068
"""

from ortools.sat.python import cp_model
from typing import Dict, List, Tuple, Optional
import sys
import csv
import io


class InterviewScheduler:
    """
    A constraint programming scheduler for interview day logistics.

    Solves the problem of scheduling multiple candidates across multiple panels
    with hard gap constraints and panel availability windows.
    """

    def __init__(
        self,
        num_candidates: int,
        panels: Dict[str, int],
        order: List[str],
        availabilities: Dict[str, List[Tuple[int, int]]],
        slots_per_day: int = 34,
        max_gap_minutes: int = 15,
        start_time_hour: int = 8,
        start_time_minute: int = 30,
        slot_duration_minutes: int = 15,
        position_constraints: Optional[Dict[str, str]] = None,
        panel_conflicts: Optional[List[List[str]]] = None
    ):
        """
        Initialize the interview scheduler.

        Args:
            num_candidates: Number of candidates to schedule
            panels: Dictionary mapping panel names to durations (in slots)
            order: Preferred order of panels (soft constraint)
            availabilities: Dict mapping panel names to list of (start_slot, end_slot) tuples
            slots_per_day: Total number of time slots in the day (default 34)
            max_gap_minutes: Maximum allowed gap between consecutive sessions (default 15)
            start_time_hour: Day start hour (default 8 for 08:00)
            start_time_minute: Day start minute (default 30 for 08:30)
            slot_duration_minutes: Duration of each slot in minutes (default 15)
            position_constraints: Dict mapping panel names to positions ("first", "last", or integer)
            panel_conflicts: List of panel groups that cannot run simultaneously (shared resources)
        """
        self.num_candidates = num_candidates
        self.panels = panels
        self.order = order
        self.availabilities = availabilities
        self.slots_per_day = slots_per_day
        self.max_gap_minutes = max_gap_minutes
        self.start_time_hour = start_time_hour
        self.start_time_minute = start_time_minute
        self.slot_duration_minutes = slot_duration_minutes
        self.position_constraints = position_constraints or {}
        self.panel_conflicts = panel_conflicts or []

        # Derived parameters
        self.candidates = range(num_candidates)
        self.max_gap_slots = max_gap_minutes // slot_duration_minutes

        # Validation
        self._validate_parameters()

        # Results (populated after solve)
        self.model = None
        self.solver = None
        self.status = None
        self.start_vars = None
        self.solution_found = False

    def _validate_parameters(self):
        """Validate input parameters for consistency."""
        # Check that all panels in order exist in panels dict
        for panel in self.order:
            if panel not in self.panels:
                raise ValueError(f"Panel '{panel}' in order list not found in panels dict")

        # Check that all panels have availability windows
        for panel in self.panels:
            if panel not in self.availabilities:
                raise ValueError(f"Panel '{panel}' missing availability windows")

        # Check availability windows are valid
        for panel, windows in self.availabilities.items():
            for start, end in windows:
                if start < 0 or end > self.slots_per_day or start >= end:
                    raise ValueError(f"Invalid availability window ({start}, {end}) for panel '{panel}'")

        # Check position constraints are valid
        for panel, position in self.position_constraints.items():
            if panel not in self.panels:
                raise ValueError(f"Panel '{panel}' in position constraints not found in panels dict")

            if isinstance(position, str):
                if position not in ["first", "last"]:
                    raise ValueError(f"Invalid position '{position}' for panel '{panel}'. "
                                   "String positions must be 'first' or 'last'")
            elif isinstance(position, int):
                if not (0 <= position < len(self.panels)):
                    raise ValueError(f"Invalid position {position} for panel '{panel}'. "
                                   f"Position must be between 0 and {len(self.panels)-1}")
            else:
                raise ValueError(f"Invalid position type for panel '{panel}'. "
                               "Position must be 'first', 'last', or an integer")

        # Check panel conflicts are valid
        for i, conflict_group in enumerate(self.panel_conflicts):
            if not isinstance(conflict_group, list) or len(conflict_group) < 2:
                raise ValueError(f"Panel conflict group {i} must be a list with at least 2 panels")

            for panel in conflict_group:
                if panel not in self.panels:
                    raise ValueError(f"Panel '{panel}' in conflict group {i} not found in panels dict")

            # Check for duplicates within the group
            if len(set(conflict_group)) != len(conflict_group):
                raise ValueError(f"Panel conflict group {i} contains duplicate panels: {conflict_group}")

    def time_to_slot(self, hour: int, minute: int) -> int:
        """Convert clock time to slot index."""
        return ((hour - self.start_time_hour) * 60 + (minute - self.start_time_minute)) // self.slot_duration_minutes

    def slot_to_time(self, slot: int) -> str:
        """Convert slot index back to clock time string."""
        total_minutes = slot * self.slot_duration_minutes + self.start_time_minute
        hour = self.start_time_hour + total_minutes // 60
        minute = total_minutes % 60
        return f"{hour:02d}:{minute:02d}"

    def solve(self, max_time_seconds: int = 60, verbose: bool = True) -> bool:
        """
        Solve the scheduling problem.

        Args:
            max_time_seconds: Maximum solver time limit
            verbose: Whether to print progress messages

        Returns:
            True if a solution was found, False otherwise
        """
        if verbose:
            print("Building constraint model...")

        self.model = cp_model.CpModel()

        # Decision variables: start time of each (candidate, panel) session
        self.start_vars = {
            (c, p): self.model.NewIntVar(0, self.slots_per_day - d, f"start_{c}_{p}")
            for c in self.candidates for p, d in self.panels.items()
        }

        # Interval variables for no-overlap constraints
        interval_vars = {
            (c, p): self.model.NewIntervalVar(
                self.start_vars[(c, p)], d, self.start_vars[(c, p)] + d, f"interval_{c}_{p}"
            )
            for c in self.candidates for p, d in self.panels.items()
        }

        self._add_basic_constraints(interval_vars, verbose)
        self._add_gap_constraints(verbose)
        self._add_position_constraints(verbose)
        self._add_panel_conflict_constraints(interval_vars, verbose)
        break_vars = self._add_order_constraints(verbose)
        self._set_objective(break_vars)

        if verbose:
            print("Solving...")

        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = max_time_seconds
        self.status = self.solver.Solve(self.model)

        self.solution_found = self.status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        return self.solution_found

    def _add_basic_constraints(self, interval_vars, verbose):
        """Add basic scheduling constraints."""
        # Each candidate cannot be in two sessions simultaneously
        for c in self.candidates:
            self.model.AddNoOverlap([interval_vars[(c, p)] for p in self.panels])

        # Each panel cannot see two candidates simultaneously (except panels that allow it)
        lunch_like_panels = {"Lunch"}  # Panels that can handle multiple candidates
        for p in self.panels:
            if p not in lunch_like_panels:
                self.model.AddNoOverlap([interval_vars[(c, p)] for c in self.candidates])

        # Panel availability windows
        for (c, p), start_var in self.start_vars.items():
            duration = self.panels[p]
            availability_options = []

            for i, (start_slot, end_slot) in enumerate(self.availabilities[p]):
                option = self.model.NewBoolVar(f"avail_{c}_{p}_{i}")
                self.model.Add(start_var >= start_slot).OnlyEnforceIf(option)
                self.model.Add(start_var + duration <= end_slot).OnlyEnforceIf(option)
                availability_options.append(option)

            # Exactly one availability window must be chosen
            self.model.Add(sum(availability_options) == 1)

    def _add_gap_constraints(self, verbose):
        """Add hard gap constraints between consecutive sessions."""
        if verbose:
            print("Adding gap constraints...")

        for c in self.candidates:
            panels_list = list(self.panels.keys())

            # Boolean variables: follows[p1,p2] = True if p2 immediately follows p1
            follows = {}
            for p1 in panels_list:
                for p2 in panels_list:
                    if p1 != p2:
                        follows[(p1, p2)] = self.model.NewBoolVar(f"follows_{c}_{p1}_{p2}")

            # Constraints for each potential "follows" relationship
            for p1 in panels_list:
                for p2 in panels_list:
                    if p1 != p2:
                        follows_var = follows[(p1, p2)]
                        d1 = self.panels[p1]

                        # If p2 follows p1: p2 starts after p1 ends
                        self.model.Add(
                            self.start_vars[(c, p2)] >= self.start_vars[(c, p1)] + d1
                        ).OnlyEnforceIf(follows_var)

                        # If p2 follows p1: gap ≤ max_gap_slots (KEY CONSTRAINT)
                        self.model.Add(
                            self.start_vars[(c, p2)] <= self.start_vars[(c, p1)] + d1 + self.max_gap_slots
                        ).OnlyEnforceIf(follows_var)

                        # If p2 follows p1: no other session can start between them
                        for p3 in panels_list:
                            if p3 != p1 and p3 != p2:
                                before = self.model.NewBoolVar(f"before_{c}_{p1}_{p2}_{p3}")
                                after = self.model.NewBoolVar(f"after_{c}_{p1}_{p2}_{p3}")

                                self.model.Add(
                                    self.start_vars[(c, p3)] < self.start_vars[(c, p1)] + d1
                                ).OnlyEnforceIf([follows_var, before])
                                self.model.Add(
                                    self.start_vars[(c, p3)] >= self.start_vars[(c, p2)]
                                ).OnlyEnforceIf([follows_var, after])
                                self.model.AddBoolOr([before, after]).OnlyEnforceIf(follows_var)

            # Topology constraints: each session has at most one predecessor and successor
            for p in panels_list:
                self.model.Add(sum(follows[(p1, p)] for p1 in panels_list if p1 != p) <= 1)
                self.model.Add(sum(follows[(p, p2)] for p2 in panels_list if p2 != p) <= 1)

            # Exactly (num_panels - 1) "follows" relationships form a chain
            num_panels = len(panels_list)
            self.model.Add(
                sum(follows[(p1, p2)] for p1 in panels_list for p2 in panels_list if p1 != p2) == num_panels - 1
            )

    def _add_position_constraints(self, verbose):
        """Add hard constraints for fixed panel positions."""
        if not self.position_constraints:
            return

        if verbose:
            print("Adding position constraints...")

        for c in self.candidates:
            for panel, position in self.position_constraints.items():
                if position == "first":
                    # Panel must start before all other panels
                    for other_panel in self.panels:
                        if other_panel != panel:
                            self.model.Add(
                                self.start_vars[(c, panel)] <= self.start_vars[(c, other_panel)]
                            )

                elif position == "last":
                    # Panel must start after all other panels end
                    for other_panel in self.panels:
                        if other_panel != panel:
                            other_duration = self.panels[other_panel]
                            self.model.Add(
                                self.start_vars[(c, panel)] >=
                                self.start_vars[(c, other_panel)] + other_duration
                            )

                elif isinstance(position, int):
                    # Panel must be at specific position (0-indexed)
                    # Count how many panels start before this panel
                    panels_before = []
                    for other_panel in self.panels:
                        if other_panel != panel:
                            before_var = self.model.NewBoolVar(f"before_{c}_{other_panel}_{panel}")
                            other_duration = self.panels[other_panel]

                            # If before_var is True, other_panel ends before panel starts
                            self.model.Add(
                                self.start_vars[(c, other_panel)] + other_duration <= self.start_vars[(c, panel)]
                            ).OnlyEnforceIf(before_var)

                            # If before_var is False, panel starts before other_panel ends
                            self.model.Add(
                                self.start_vars[(c, panel)] < self.start_vars[(c, other_panel)] + other_duration
                            ).OnlyEnforceIf(before_var.Not())

                            panels_before.append(before_var)

                    # Exactly 'position' panels should come before this panel
                    self.model.Add(sum(panels_before) == position)

    def _add_order_constraints(self, verbose):
        """Add soft constraints for preferred order."""
        if verbose:
            print("Adding order preference constraints...")

        break_vars = []

        for c in self.candidates:
            for i in range(len(self.order) - 1):
                p1, p2 = self.order[i], self.order[i + 1]
                d1 = self.panels[p1]

                # break_var = True if preferred order is violated
                break_var = self.model.NewBoolVar(f"break_{c}_{p1}_{p2}")
                break_vars.append(break_var)

                # If order preserved: p1 ends before p2 starts
                self.model.Add(
                    self.start_vars[(c, p1)] + d1 <= self.start_vars[(c, p2)]
                ).OnlyEnforceIf(break_var.Not())

                # If order violated: p2 ends before p1 starts
                self.model.Add(
                    self.start_vars[(c, p2)] + self.panels[p2] <= self.start_vars[(c, p1)]
                ).OnlyEnforceIf(break_var)

        return break_vars

    def _set_objective(self, break_vars):
        """Set the hierarchical objective function."""
        num_breaks = self.model.NewIntVar(0, len(break_vars), "num_breaks")
        self.model.Add(num_breaks == sum(break_vars))

        makespan = self.model.NewIntVar(0, self.slots_per_day, "makespan")
        for c in self.candidates:
            for p, d in self.panels.items():
                self.model.Add(makespan >= self.start_vars[(c, p)] + d)

        # Hierarchical objective: minimize breaks first, then makespan
        BIG = (self.slots_per_day + 1) * 1000
        self.model.Minimize(num_breaks * BIG + makespan)

    def get_solution_summary(self) -> Dict:
        """Get a summary of the solution."""
        if not self.solution_found:
            return {"status": "No solution found"}

        # Calculate metrics
        num_breaks = sum(
            1 for c in self.candidates
            for i in range(len(self.order) - 1)
            if self._is_order_broken(c, i)
        )

        makespan = max(
            self.solver.Value(self.start_vars[(c, p)]) + self.panels[p]
            for c in self.candidates for p in self.panels
        )

        return {
            "status": self.solver.StatusName(self.status),
            "order_breaks": num_breaks,
            "day_ends_at": self.slot_to_time(makespan),
            "max_gap_enforced": f"{self.max_gap_minutes} minutes"
        }

    def _is_order_broken(self, candidate: int, order_index: int) -> bool:
        """Check if the preferred order is broken between two consecutive panels."""
        p1, p2 = self.order[order_index], self.order[order_index + 1]
        start1 = self.solver.Value(self.start_vars[(candidate, p1)])
        start2 = self.solver.Value(self.start_vars[(candidate, p2)])
        return start1 + self.panels[p1] > start2  # p1 doesn't finish before p2 starts

    def get_candidate_schedule(self, candidate_id: int) -> List[Dict]:
        """Get the schedule for a specific candidate."""
        if not self.solution_found:
            return []

        sessions = []
        for panel in self.panels:
            start_slot = self.solver.Value(self.start_vars[(candidate_id, panel)])
            end_slot = start_slot + self.panels[panel]

            sessions.append({
                "panel": panel,
                "start_time": self.slot_to_time(start_slot),
                "end_time": self.slot_to_time(end_slot),
                "start_slot": start_slot,
                "end_slot": end_slot,
                "duration_minutes": self.panels[panel] * self.slot_duration_minutes
            })

        # Sort by start time
        sessions.sort(key=lambda x: x["start_slot"])

        # Add gap information
        for i in range(1, len(sessions)):
            gap_slots = sessions[i]["start_slot"] - sessions[i-1]["end_slot"]
            gap_minutes = gap_slots * self.slot_duration_minutes
            sessions[i]["gap_before"] = gap_minutes

        return sessions

    def print_solution(self):
        """Print a formatted solution."""
        if not self.solution_found:
            print(f"\n{'='*50}")
            print(f"NO FEASIBLE SOLUTION FOUND")
            print(f"{'='*50}")
            print(f"Status: {self.solver.StatusName(self.status)}")
            print("\nThis suggests the problem is over-constrained.")
            print("Possible solutions:")
            print("- Relax availability windows")
            print("- Allow longer gaps between sessions")
            print("- Reduce number of candidates or panels")
            return

        summary = self.get_solution_summary()

        print(f"\n{'='*50}")
        print(f"SOLUTION FOUND!")
        print(f"{'='*50}")
        print(f"Order breaks: {summary['order_breaks']}")
        print(f"Status: {summary['status']}")
        print(f"✓ All gaps between consecutive sessions are ≤ {self.max_gap_minutes} minutes")
        print(f"✓ Day ends at: {summary['day_ends_at']}")
        print()

        for c in self.candidates:
            schedule = self.get_candidate_schedule(c)
            print(f"=== Candidate {c + 1} ===")

            total_idle_minutes = 0
            for session in schedule:
                gap_str = ""
                if "gap_before" in session:
                    gap = session["gap_before"]
                    total_idle_minutes += gap
                    if gap > 0:
                        gap_str = f" (gap: {gap} min)"
                    elif gap == 0:
                        gap_str = " (back-to-back)"

                print(f"  {session['panel']:<13} {session['start_time']} – {session['end_time']}{gap_str}")

            print(f"  Total idle time: {total_idle_minutes} minutes")
            print()

    def _add_panel_conflict_constraints(self, interval_vars, verbose):
        """Add constraints to prevent conflicting panels from running simultaneously."""
        if not self.panel_conflicts:
            return

        if verbose:
            print("Adding panel conflict constraints...")

        for conflict_group in self.panel_conflicts:
            # Collect all intervals for all panels in this conflict group across all candidates
            conflicting_intervals = []

            for panel in conflict_group:
                for c in self.candidates:
                    conflicting_intervals.append(interval_vars[(c, panel)])

            # All these intervals cannot overlap with each other
            self.model.AddNoOverlap(conflicting_intervals)

    def export_to_csv(self, filename: Optional[str] = None, date: str = "DATE") -> str:
        """
        Export the schedule to CSV format.

        Args:
            filename: Optional filename to save the CSV. If None, returns the CSV as a string.
            date: The date string to use in the header (default: "DATE")

        Returns:
            The CSV content as a string if filename is None, otherwise returns the filename.

        Raises:
            ValueError: If no solution has been found.
        """
        if not self.solution_found:
            raise ValueError("No solution found. Call solve() first.")

        # Create a matrix to store panel assignments for each candidate at each time slot
        schedule_matrix = {}

        # Initialize all slots as empty
        for slot in range(self.slots_per_day):
            schedule_matrix[slot] = {c: "" for c in self.candidates}

        # Fill in the panel assignments
        for c in self.candidates:
            for panel, duration in self.panels.items():
                start_slot = self.solver.Value(self.start_vars[(c, panel)])
                end_slot = start_slot + duration

                # Mark all slots for this session with the panel name
                for slot in range(start_slot, end_slot):
                    if slot < self.slots_per_day:
                        schedule_matrix[slot][c] = panel

        # Prepare CSV data
        csv_data = []

        # Header row
        header = [date] + [f"CANDIDATE {c+1}" for c in self.candidates]
        csv_data.append(header)

        # Data rows - one for each time slot
        for slot in range(self.slots_per_day):
            start_time = self.slot_to_time(slot)
            end_time = self.slot_to_time(slot + 1)
            time_range = f"{start_time}-{end_time}"

            row = [time_range]
            for c in self.candidates:
                row.append(schedule_matrix[slot][c])

            csv_data.append(row)

        # Write to file or return as string
        if filename:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(csv_data)
            return filename
        else:
            # Return as string
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerows(csv_data)
            return output.getvalue()

    def export_to_csv_string(self) -> str:
        """
        Export the schedule to CSV format and return as a string.

        Returns:
            The CSV content as a string.

        Raises:
            ValueError: If no solution has been found.
        """
        return self.export_to_csv()

    def export_to_csv_file(self, filename: str, date: str = "DATE") -> str:
        """
        Export the schedule to CSV format and save to a file.

        Args:
            filename: The filename to save the CSV to.
            date: The date string to use in the header (default: "DATE")

        Returns:
            The filename that was written to.

        Raises:
            ValueError: If no solution has been found.
        """
        return self.export_to_csv(filename=filename, date=date)


def main():
    """Example usage with the original problem parameters."""

    # Helper function for time conversion
    def t(h, m):
        return ((h - 8) * 60 + (m - 30)) // 15

    # Original problem parameters
    panels = {
        "Director": 1,       # 15 minutes
        "Competencies": 4,   # 1 hour
        "Customers": 4,      # 1 hour
        "HR": 3,            # 45 minutes
        "Lunch": 4,         # 1 hour
        "Team": 3,          # 45 minutes
        "Goodbye": 2,       # 30 minutes
    }

    order = [
        "Director",
        "Competencies",
        "Customers",
        "Lunch",
        "Team",
        "HR",
        "Goodbye",
    ]

    availabilities = {
        "Director": [(t(8,30), t(10, 0))],     # Only available 08:30-10:00
        "Competencies": [(t(8,30), t(11, 0)),  # Available 08:30-11:00,
                         (t(12,0), t(14, 0)),  #           12:00-14:00,
                         (t(16,0), t(17, 0))], #           16:00-17:00
        "Customers": [(t(8,30), t(14, 0))],    # Must finish by 14:00
        "HR": [(t(8,30), t(17, 0))],          # Available all day
        "Team": [(t(8,30), t(17, 0))],        # Available all day
        "Goodbye": [(t(8,30), t(17, 0))],     # Available all day
        "Lunch": [(t(11,45), t(13,30))],      # Canteen window 11:45-13:30
    }

    # Create and solve
    scheduler = InterviewScheduler(
        num_candidates=3,
        panels=panels,
        order=order,
        availabilities=availabilities,
        slots_per_day=34,
        max_gap_minutes=15,
        position_constraints={"Goodbye": "last"},  # Force Goodbye to be last
        panel_conflicts=[["Team", "Goodbye"]]      # Team and Goodbye share people, cannot run simultaneously
    )

    if scheduler.solve(verbose=True):
        scheduler.print_solution()

        # Demonstrate CSV export
        print("\n" + "="*50)
        print("CSV EXPORT DEMONSTRATION")
        print("="*50)

        # Export to string and print
        csv_content = scheduler.export_to_csv_string()
        print("CSV Export (first 10 lines):")
        print(csv_content.split('\n')[:10])
        print("...")

        # Export to file
        filename = scheduler.export_to_csv_file("interview_schedule.csv", date="2024-01-15")
        print(f"\nCSV saved to: {filename}")

    else:
        print("Failed to find a solution!")


if __name__ == "__main__":
    main()
