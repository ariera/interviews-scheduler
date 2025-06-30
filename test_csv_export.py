#!/usr/bin/env python3
"""
Test script for CSV export functionality
"""

from src.scheduler.schedule import InterviewScheduler

def test_csv_export():
    """Test the CSV export with a simple example."""

    # Simple example with 2 candidates and 30-minute slots
    panels = {
        "Panel 1": 2,      # 30 minutes (2 slots of 15 min each)
        "Panel 2": 2,      # 30 minutes
        "Director": 1,     # 15 minutes
        "Meet the team": 2, # 30 minutes
        "Lunch": 4,        # 1 hour
        "Presentation (45')": 3, # 45 minutes
    }

    order = ["Panel 1", "Panel 2", "Director", "Meet the team", "Lunch", "Presentation (45')"]

    availabilities = {
        "Panel 1": [(0, 20)],      # Available all day
        "Panel 2": [(0, 20)],      # Available all day
        "Director": [(0, 20)],     # Available all day
        "Meet the team": [(0, 20)], # Available all day
        "Lunch": [(8, 20)],        # Lunch window (12:00 onwards)
        "Presentation (45')": [(0, 20)], # Available all day
    }

    # Create scheduler with 30-minute slots
    scheduler = InterviewScheduler(
        num_candidates=2,  # Reduced to 2 candidates
        panels=panels,
        order=order,
        availabilities=availabilities,
        slots_per_day=20,  # 5 hours (20 slots of 15 min each)
        max_gap_minutes=30,  # Increased gap tolerance
        start_time_hour=9,  # Start at 09:00
        start_time_minute=0,
        slot_duration_minutes=15,
        # Removed position constraints to make it easier
    )

    print("Solving scheduling problem...")
    if scheduler.solve(verbose=True):
        print("\nSolution found! Exporting to CSV...")

        # Export to string
        csv_content = scheduler.export_to_csv_string()
        print("\nCSV Export:")
        print(csv_content)

        # Export to file
        filename = scheduler.export_to_csv_file("test_schedule.csv", date="2024-01-15")
        print(f"\nCSV saved to: {filename}")

    else:
        print("Failed to find a solution!")

if __name__ == "__main__":
    test_csv_export()