#!/usr/bin/env python3
"""
Command-line interface for the Interview Scheduler.

Usage:
    python run_cli.py config.yaml [options]

The YAML configuration file should contain all scheduling parameters.
"""

import argparse
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any

from .schedule import InterviewScheduler


def parse_time_to_minutes(time_str: str) -> Tuple[int, int]:
    """
    Parse time string like '08:30' to (hour, minute) tuple.

    Args:
        time_str: Time in format 'HH:MM'

    Returns:
        Tuple of (hour, minute)
    """
    try:
        parts = time_str.split(':')
        if len(parts) != 2:
            raise ValueError(f"Invalid time format '{time_str}'. Expected 'HH:MM'")

        hour = int(parts[0])
        minute = int(parts[1])

        if not (0 <= hour <= 23):
            raise ValueError(f"Invalid hour {hour}. Must be 0-23")
        if not (0 <= minute <= 59):
            raise ValueError(f"Invalid minute {minute}. Must be 0-59")

        return hour, minute
    except ValueError as e:
        raise ValueError(f"Error parsing time '{time_str}': {e}")


def parse_duration(duration_str: str) -> int:
    """
    Parse duration string to minutes.

    Supports formats:
    - '15min', '30min', '45min' etc.
    - '1h', '2h' etc.
    - '1h30min', '2h15min' etc.
    - Just numbers (assumed to be minutes)

    Args:
        duration_str: Duration string

    Returns:
        Duration in minutes
    """
    duration_str = duration_str.lower().strip()

    # If it's just a number, assume minutes
    if duration_str.isdigit():
        return int(duration_str)

    total_minutes = 0

    # Handle hours
    if 'h' in duration_str:
        if 'min' in duration_str:
            # Format like '1h30min'
            parts = duration_str.split('h')
            hours = int(parts[0])
            remaining = parts[1].replace('min', '').strip()
            minutes = int(remaining) if remaining else 0
        else:
            # Format like '1h'
            hours = int(duration_str.replace('h', ''))
            minutes = 0
        total_minutes = hours * 60 + minutes
    elif 'min' in duration_str:
        # Format like '30min'
        total_minutes = int(duration_str.replace('min', ''))
    else:
        raise ValueError(f"Invalid duration format '{duration_str}'. "
                        "Expected formats: '15min', '1h', '1h30min', or just '30'")

    return total_minutes


def parse_availability_windows(
    windows: List[str],
    scheduler: InterviewScheduler
) -> List[Tuple[int, int]]:
    """
    Parse availability windows from time strings to slot indices.

    Args:
        windows: List of time ranges like ['08:30-10:00', '12:00-14:00']
        scheduler: InterviewScheduler instance for time conversion

    Returns:
        List of (start_slot, end_slot) tuples
    """
    parsed_windows = []

    for window in windows:
        if '-' not in window:
            raise ValueError(f"Invalid time window '{window}'. Expected format 'HH:MM-HH:MM'")

        start_str, end_str = window.split('-', 1)
        start_hour, start_min = parse_time_to_minutes(start_str.strip())
        end_hour, end_min = parse_time_to_minutes(end_str.strip())

        start_slot = scheduler.time_to_slot(start_hour, start_min)
        end_slot = scheduler.time_to_slot(end_hour, end_min)

        if start_slot >= end_slot:
            raise ValueError(f"Invalid time window '{window}': start time must be before end time")

        parsed_windows.append((start_slot, end_slot))

    return parsed_windows


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load and validate the YAML configuration file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file '{config_path}' not found")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file '{config_path}': {e}")

    # Validate required fields
    required_fields = ['num_candidates', 'panels', 'order', 'availabilities']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field '{field}' in configuration")

    return config


def create_scheduler_from_config(config: Dict[str, Any]) -> InterviewScheduler:
    """
    Create an InterviewScheduler instance from configuration.

    Args:
        config: Configuration dictionary from YAML

    Returns:
        Configured InterviewScheduler instance
    """
    # Parse basic parameters
    num_candidates = config['num_candidates']

    # Parse panels with durations
    panels = {}
    for panel_name, duration_str in config['panels'].items():
        duration_minutes = parse_duration(str(duration_str))
        # Convert to slots (assuming 15-minute slots by default)
        slot_duration = config.get('slot_duration_minutes', 15)
        duration_slots = duration_minutes // slot_duration
        if duration_minutes % slot_duration != 0:
            raise ValueError(f"Panel '{panel_name}' duration {duration_minutes} minutes "
                           f"is not divisible by slot duration {slot_duration} minutes")
        panels[panel_name] = duration_slots

    # Parse order
    order = config['order']

    # Parse timing parameters
    start_time = config.get('start_time', '08:30')
    start_hour, start_minute = parse_time_to_minutes(start_time)

    end_time = config.get('end_time', '17:00')
    end_hour, end_minute = parse_time_to_minutes(end_time)

    slot_duration_minutes = config.get('slot_duration_minutes', 15)
    total_minutes = (end_hour - start_hour) * 60 + (end_minute - start_minute)
    slots_per_day = total_minutes // slot_duration_minutes

    max_gap_minutes = config.get('max_gap_minutes', 15)

    # Create a temporary scheduler just for time conversion utilities
    # We'll use a minimal scheduler that bypasses validation
    class TempScheduler:
        def __init__(self, start_hour, start_minute, slot_duration):
            self.start_time_hour = start_hour
            self.start_time_minute = start_minute
            self.slot_duration_minutes = slot_duration

        def time_to_slot(self, hour: int, minute: int) -> int:
            return ((hour - self.start_time_hour) * 60 + (minute - self.start_time_minute)) // self.slot_duration_minutes

    temp_scheduler = TempScheduler(start_hour, start_minute, slot_duration_minutes)

    # Parse availabilities
    availabilities = {}
    for panel_name, windows in config['availabilities'].items():
        if isinstance(windows, str):
            # Single window as string
            windows = [windows]

        parsed_windows = parse_availability_windows(windows, temp_scheduler)
        availabilities[panel_name] = parsed_windows

    # Parse optional constraints
    position_constraints = config.get('position_constraints', {})
    panel_conflicts = config.get('panel_conflicts', [])

    # Create and return the scheduler
    return InterviewScheduler(
        num_candidates=num_candidates,
        panels=panels,
        order=order,
        availabilities=availabilities,
        slots_per_day=slots_per_day,
        max_gap_minutes=max_gap_minutes,
        start_time_hour=start_hour,
        start_time_minute=start_minute,
        slot_duration_minutes=slot_duration_minutes,
        position_constraints=position_constraints,
        panel_conflicts=panel_conflicts
    )


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Interview Scheduler - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_cli.py examples/config.yaml
  python run_cli.py examples/config.yaml --max-time 120 --output results.json
  python run_cli.py examples/config.yaml --validate-only
        """
    )

    parser.add_argument(
        'config_file',
        help='Path to YAML configuration file'
    )

    parser.add_argument(
        '--max-time', '-t',
        type=int,
        default=60,
        help='Maximum solver time in seconds (default: 60)'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress messages'
    )

    parser.add_argument(
        '--output', '-o',
        help='Save results to JSON file'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate configuration without solving'
    )

    args = parser.parse_args()

    try:
        # Load and validate configuration
        config = load_config(args.config_file)

        if args.validate_only:
            print("✅ Configuration is valid!")
            print(f"  - {config['num_candidates']} candidates")
            print(f"  - {len(config['panels'])} panels")
            print(f"  - Max gap: {config.get('max_gap_minutes', 15)} minutes")
            return

        # Create scheduler
        scheduler = create_scheduler_from_config(config)

        # Solve
        success = scheduler.solve(max_time_seconds=args.max_time, verbose=not args.quiet)

        if success:
            if args.output:
                # Save to JSON file
                import json
                results = {
                    'summary': scheduler.get_solution_summary(),
                    'schedules': {
                        f'candidate_{i+1}': scheduler.get_candidate_schedule(i)
                        for i in range(scheduler.num_candidates)
                    }
                }

                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)

                print(f"✅ Results saved to {args.output}")
            else:
                # Print to console
                scheduler.print_solution()
        else:
            print("❌ Failed to find a solution!")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()