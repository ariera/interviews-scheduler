// Interview Scheduler - Validation Utilities
// GitHub Pages compatible namespace pattern

window.InterviewScheduler = window.InterviewScheduler || {};

window.InterviewScheduler.Validators = {
    /**
     * Validate time format (HH:MM)
     */
    validateTimeFormat(time) {
        if (!time) return false;
        const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
        return timeRegex.test(time);
    },

    /**
     * Validate duration format (e.g., "1h", "30min", "1h30min", or just numbers)
     */
    validateDuration(duration) {
        if (!duration) return false;

        // Allow pure numbers (minutes)
        if (/^\d+$/.test(duration)) return true;

        // Allow formats like "1h", "30min", "1h30min"
        const durationRegex = /^(\d+h)?(\d+min)?$/;
        return durationRegex.test(duration) && duration !== '';
    },

    /**
     * Validate availability window format (e.g., "08:30-10:00")
     */
    validateAvailabilityWindow(window) {
        if (!window) return false;
        const windowRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]-([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
        return windowRegex.test(window);
    },

    /**
     * Validate panel name (non-empty, reasonable length)
     */
    validatePanelName(name) {
        if (!name || typeof name !== 'string') return false;
        const trimmed = name.trim();
        return trimmed.length > 0 && trimmed.length <= 50;
    },

    /**
     * Validate number of candidates
     */
    validateCandidateCount(count) {
        return Number.isInteger(count) && count > 0 && count <= 20;
    },

    /**
     * Validate slot duration in minutes
     */
    validateSlotDuration(minutes) {
        return Number.isInteger(minutes) && minutes > 0 && minutes <= 480; // Max 8 hours
    },

    /**
     * Validate max gap in minutes
     */
    validateMaxGap(minutes) {
        return Number.isInteger(minutes) && minutes >= 0 && minutes <= 240; // Max 4 hours
    },

    /**
     * Validate position constraint value
     */
    validatePositionConstraint(value) {
        const validValues = ['first', 'last', '0', '1', '2', '3', '4', '5'];
        return validValues.includes(value);
    },

    /**
     * Validate complete configuration object
     */
    validateConfig(config) {
        const errors = [];

        // Basic settings validation
        if (!this.validateCandidateCount(config.num_candidates)) {
            errors.push('Invalid number of candidates');
        }

        if (!this.validateTimeFormat(config.start_time)) {
            errors.push('Invalid start time format');
        }

        if (!this.validateTimeFormat(config.end_time)) {
            errors.push('Invalid end time format');
        }

        if (!this.validateSlotDuration(config.slot_duration_minutes)) {
            errors.push('Invalid slot duration');
        }

        if (!this.validateMaxGap(config.max_gap_minutes)) {
            errors.push('Invalid max gap');
        }

        // Panel validation
        if (!config.panels || Object.keys(config.panels).length === 0) {
            errors.push('At least one panel is required');
        } else {
            Object.entries(config.panels).forEach(([name, duration]) => {
                if (!this.validatePanelName(name)) {
                    errors.push(`Invalid panel name: ${name}`);
                }
                if (!this.validateDuration(duration)) {
                    errors.push(`Invalid duration for panel ${name}: ${duration}`);
                }
            });
        }

        // Availability validation
        if (config.availabilities) {
            Object.entries(config.availabilities).forEach(([panel, availability]) => {
                const windows = Array.isArray(availability) ? availability : [availability];
                windows.forEach(window => {
                    if (!this.validateAvailabilityWindow(window)) {
                        errors.push(`Invalid availability window for ${panel}: ${window}`);
                    }
                });
            });
        }

        // Position constraints validation
        if (config.position_constraints) {
            Object.entries(config.position_constraints).forEach(([panel, constraint]) => {
                if (!this.validatePositionConstraint(constraint)) {
                    errors.push(`Invalid position constraint for ${panel}: ${constraint}`);
                }
            });
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }
};