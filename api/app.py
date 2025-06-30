#!/usr/bin/env python3
"""
API Backend for Interview Scheduler

A Flask API that provides scheduling functionality for the web frontend.
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yaml
import tempfile
import time
import uuid
from copy import deepcopy
import sys
import os

# Add the scheduler to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scheduler import create_scheduler_from_config

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Store temporary files
temp_files = {}

@app.route('/api/schedule', methods=['POST'])
def schedule():
    """Generate interview schedule from configuration."""
    try:
        data = request.get_json()
        config = data.get('config')

        if not config:
            return jsonify({'error': 'No configuration provided'}), 400

        # Create scheduler and run
        scheduler = create_scheduler_from_config(config)
        success = scheduler.solve(max_time_seconds=30, verbose=False)

        if not success:
            return jsonify({'error': 'No feasible solutions found. Try relaxing constraints.'}), 400

        # Get solution data
        summary = scheduler.get_solution_summary()
        candidate_schedules = {}

        for i in range(scheduler.num_candidates):
            candidate_schedules[f'candidate_{i+1}'] = scheduler.get_candidate_schedule(i)

        solution_data = {
            'summary': summary,
            'schedules': candidate_schedules
        }

        # Store results temporarily
        session_id = str(uuid.uuid4())
        temp_files[session_id] = {
            'solutions': [solution_data],
            'config': config,
            'timestamp': time.time()
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'solution': solution_data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule-multiple', methods=['POST'])
def schedule_multiple():
    """Generate multiple interview schedules from configuration."""
    try:
        data = request.get_json()
        config = data.get('config')
        max_solutions = data.get('max_solutions', 3)

        if not config:
            return jsonify({'error': 'No configuration provided'}), 400

        # Create scheduler and run multiple times
        scheduler = create_scheduler_from_config(config)
        solutions = []
        max_attempts = 10

        for attempt in range(max_attempts):
            if len(solutions) >= max_solutions:
                break

            # Run the scheduler
            success = scheduler.solve(max_time_seconds=30, verbose=False)

            if success:
                # Get solution data
                summary = scheduler.get_solution_summary()
                candidate_schedules = {}

                for i in range(scheduler.num_candidates):
                    candidate_schedules[f'candidate_{i+1}'] = scheduler.get_candidate_schedule(i)

                solution_data = {
                    'summary': summary,
                    'schedules': candidate_schedules,
                    'attempt': attempt + 1
                }

                # Check if this solution is different from previous ones
                is_different = True
                for existing_solution in solutions:
                    if _solutions_are_similar(solution_data, existing_solution):
                        is_different = False
                        break

                if is_different:
                    solutions.append(solution_data)

        if not solutions:
            return jsonify({'error': 'No feasible solutions found. Try relaxing constraints.'}), 400

        # Store results temporarily
        session_id = str(uuid.uuid4())
        temp_files[session_id] = {
            'solutions': solutions,
            'config': config,
            'timestamp': time.time()
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'num_solutions': len(solutions),
            'solutions': solutions,
            'summary': {
                'num_candidates': config.get('num_candidates', 0),
                'num_panels': len(config.get('panels', {})),
                'max_gap': config.get('max_gap_minutes', 15)
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_config():
    """Validate YAML configuration without running scheduler."""
    try:
        data = request.get_json()
        config = data.get('config')

        if not config:
            return jsonify({'error': 'No configuration provided'}), 400

        # Validate required fields
        required_fields = ['num_candidates', 'panels', 'order', 'availabilities']
        missing_fields = []

        for field in required_fields:
            if field not in config:
                missing_fields.append(field)

        if missing_fields:
            return jsonify({
                'valid': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Try to create scheduler (this will catch configuration errors)
        try:
            scheduler = create_scheduler_from_config(config)
            return jsonify({
                'valid': True,
                'message': 'Configuration is valid'
            })
        except Exception as e:
            return jsonify({
                'valid': False,
                'error': f'Configuration error: {str(e)}'
            }), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'interview-scheduler-api',
        'version': '1.0.0'
    })

@app.route('/api/solutions/<session_id>')
def get_solutions(session_id):
    """Get stored solutions for a session."""
    if session_id not in temp_files:
        return jsonify({'error': 'Session not found or expired'}), 404

    return jsonify(temp_files[session_id]['solutions'])

@app.route('/api/download_csv/<session_id>/<int:solution_index>')
def download_csv(session_id, solution_index):
    """Download the CSV export for a specific solution."""
    cleanup_old_sessions()

    if session_id not in temp_files:
        return jsonify({'error': 'Session not found or expired'}), 404

    solutions = temp_files[session_id]['solutions']
    config = temp_files[session_id]['config']

    if solution_index >= len(solutions):
        return jsonify({'error': 'Solution index out of range'}), 400

    solution = solutions[solution_index]

    # Generate CSV content
    csv_content = generate_csv_content(solution, config)

    # Create response
    response = Response(csv_content, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=interview_schedule_{session_id}_{solution_index}.csv'

    return response

def generate_csv_content(solution, config):
    """Generate CSV content from solution data."""
    schedules = solution['schedules']
    candidates = list(schedules.keys())

    if not candidates:
        return "Time\n"

    # Get time range
    first_candidate = candidates[0]
    first_schedule = schedules[first_candidate]

    if not first_schedule:
        return "Time\n"

    # Find start and end times
    start_time = min(session['start_time'] for session in first_schedule)
    end_time = max(session['end_time'] for session in first_schedule)

    # Create time slots (15-minute intervals)
    time_slots = []
    current_time = _parse_time_to_minutes(start_time)
    end_minutes = _parse_time_to_minutes(end_time)

    while current_time < end_minutes:
        time_slots.append(_minutes_to_time_string(current_time))
        current_time += 15

    # Generate CSV
    csv_lines = ['Time']
    csv_lines.extend([f'Candidate {i+1}' for i in range(len(candidates))])

    for time_slot in time_slots:
        row = [time_slot]
        for candidate in candidates:
            schedule = schedules[candidate]
            panel = _find_panel_at_time(schedule, time_slot)
            row.append(panel if panel else '')
        csv_lines.append(','.join(row))

    return '\n'.join(csv_lines)

def _find_panel_at_time(schedule, time_slot):
    """Find which panel is active at a given time slot."""
    for session in schedule:
        if session['start_time'] <= time_slot < session['end_time']:
            return session['panel']
    return None

def _parse_time_to_minutes(time_str):
    """Convert time string (HH:MM) to minutes since midnight."""
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes

def _minutes_to_time_string(minutes):
    """Convert minutes since midnight to time string (HH:MM)."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def _solutions_are_similar(sol1, sol2, tolerance=0.1):
    """Check if two solutions are similar (to avoid duplicates)."""
    # Simple similarity check based on total idle time
    idle1 = _calculate_total_idle_time(sol1['schedules'])
    idle2 = _calculate_total_idle_time(sol2['schedules'])

    return abs(idle1 - idle2) < tolerance

def _calculate_total_idle_time(schedules):
    """Calculate total idle time across all candidates."""
    total_idle = 0
    for candidate_schedule in schedules.values():
        if isinstance(candidate_schedule, list):
            for session in candidate_schedule:
                if 'idle_time' in session:
                    total_idle += session['idle_time']
    return total_idle

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))