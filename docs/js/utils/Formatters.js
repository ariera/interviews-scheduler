// Interview Scheduler - Data Formatting Utilities
// GitHub Pages compatible namespace pattern

window.InterviewScheduler = window.InterviewScheduler || {};

window.InterviewScheduler.Formatters = {
    /**
     * Convert duration string to minutes
     * Supports: "1h", "30min", "1h30min", or plain numbers
     */
    durationToMinutes(duration) {
        if (!duration) return 0;

        // If it's already a number, return it
        if (/^\d+$/.test(duration)) {
            return parseInt(duration);
        }

        let totalMinutes = 0;

        // Extract hours
        const hoursMatch = duration.match(/(\d+)h/);
        if (hoursMatch) {
            totalMinutes += parseInt(hoursMatch[1]) * 60;
        }

        // Extract minutes
        const minutesMatch = duration.match(/(\d+)min/);
        if (minutesMatch) {
            totalMinutes += parseInt(minutesMatch[1]);
        }

        return totalMinutes;
    },

    /**
     * Convert minutes to human-readable duration
     */
    minutesToDuration(minutes) {
        if (!minutes || minutes === 0) return '0min';

        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;

        if (hours === 0) {
            return `${remainingMinutes}min`;
        } else if (remainingMinutes === 0) {
            return `${hours}h`;
        } else {
            return `${hours}h${remainingMinutes}min`;
        }
    },

    /**
     * Format availability data for display in textarea
     */
    formatAvailabilityForDisplay(availability) {
        if (!availability) return '';
        return Array.isArray(availability) ? availability.join('\n') : availability;
    },

    /**
     * Parse availability from textarea input
     */
    parseAvailabilityFromInput(input) {
        if (!input || !input.trim()) return null;

        const windows = input.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);

        return windows.length === 1 ? windows[0] : windows;
    },

    /**
     * Format time for display (ensure HH:MM format)
     */
    formatTime(time) {
        if (!time) return '';

        // If already in HH:MM format, return as is
        if (/^\d{2}:\d{2}$/.test(time)) return time;

        // If in H:MM format, pad with zero
        if (/^\d:\d{2}$/.test(time)) return `0${time}`;

        return time;
    },

    /**
     * Convert panel conflicts array to display format
     */
    formatConflictsForDisplay(conflicts) {
        if (!conflicts || !Array.isArray(conflicts)) return [];

        return conflicts.map(conflict => ({
            panel1: conflict[0] || '',
            panel2: conflict[1] || ''
        }));
    },

    /**
     * Convert display format conflicts back to array format
     */
    parseConflictsFromDisplay(conflictEntries) {
        if (!conflictEntries || !Array.isArray(conflictEntries)) return [];

        return conflictEntries
            .filter(entry => entry.panel1 && entry.panel2)
            .map(entry => [entry.panel1, entry.panel2]);
    },

    /**
     * Format position constraints for display
     */
    formatConstraintsForDisplay(constraints) {
        if (!constraints || typeof constraints !== 'object') return [];

        return Object.entries(constraints).map(([panel, value]) => ({
            panel: panel,
            value: value
        }));
    },

    /**
     * Parse position constraints from display format
     */
    parseConstraintsFromDisplay(constraintEntries) {
        if (!constraintEntries || !Array.isArray(constraintEntries)) return {};

        const constraints = {};
        constraintEntries.forEach(entry => {
            if (entry.panel && entry.value) {
                constraints[entry.panel] = entry.value;
            }
        });

        return constraints;
    },

    /**
     * Clean and normalize panel name
     */
    normalizePanelName(name) {
        if (!name || typeof name !== 'string') return '';
        return name.trim();
    },

    /**
     * Generate default panel name
     */
    generateDefaultPanelName(index) {
        return `Panel ${index + 1}`;
    },

    /**
     * Format configuration for YAML export
     */
    formatConfigForExport(config) {
        // Create a clean copy with normalized data
        const cleanConfig = {
            num_candidates: config.num_candidates,
            start_time: this.formatTime(config.start_time),
            end_time: this.formatTime(config.end_time),
            slot_duration_minutes: config.slot_duration_minutes,
            max_gap_minutes: config.max_gap_minutes,
            panels: {},
            order: [...(config.order || [])],
            availabilities: {},
            position_constraints: {},
            panel_conflicts: [...(config.panel_conflicts || [])]
        };

        // Clean panels
        Object.entries(config.panels || {}).forEach(([name, duration]) => {
            const cleanName = this.normalizePanelName(name);
            if (cleanName) {
                cleanConfig.panels[cleanName] = duration;
            }
        });

        // Clean availabilities
        Object.entries(config.availabilities || {}).forEach(([panel, availability]) => {
            const cleanName = this.normalizePanelName(panel);
            if (cleanName && availability) {
                cleanConfig.availabilities[cleanName] = availability;
            }
        });

        // Clean position constraints
        Object.entries(config.position_constraints || {}).forEach(([panel, constraint]) => {
            const cleanName = this.normalizePanelName(panel);
            if (cleanName && constraint) {
                cleanConfig.position_constraints[cleanName] = constraint;
            }
        });

        return cleanConfig;
    }
};