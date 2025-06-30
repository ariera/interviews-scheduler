// Interview Scheduler - Default Configuration
// GitHub Pages compatible namespace pattern

window.InterviewScheduler = window.InterviewScheduler || {};

window.InterviewScheduler.Defaults = {
    /**
     * Default interview configuration
     */
    config: {
        num_candidates: 3,
        start_time: '08:30',
        end_time: '17:00',
        slot_duration_minutes: 15,
        max_gap_minutes: 15,
        panels: {
            Director: '15min',
            Competencies: '1h',
            Customers: '1h',
            HR: '45min',
            Lunch: '1h',
            Team: '45min',
            Goodbye: '30min'
        },
        order: ['Director', 'Competencies', 'Customers', 'Lunch', 'Team', 'HR', 'Goodbye'],
        availabilities: {
            Director: '08:30-10:00',
            Competencies: ['08:30-11:00', '12:00-14:00', '16:00-17:00'],
            Customers: '08:30-14:00',
            HR: '08:30-17:00',
            Team: '08:30-17:00',
            Goodbye: '08:30-17:00',
            Lunch: '12:00-13:30'
        },
        position_constraints: {
            Goodbye: 'last'
        },
        panel_conflicts: [
            ['Team', 'Goodbye']
        ]
    },

    /**
     * UI Configuration
     */
    ui: {
        maxCandidates: 20,
        maxPanels: 10,
        maxSlotDuration: 480, // 8 hours in minutes
        maxGap: 240, // 4 hours in minutes
        maxPanelNameLength: 50,
        debounceDelay: 300 // ms
    },

    /**
     * Position constraint options
     */
    positionConstraints: [
        { value: 'first', label: 'First' },
        { value: 'last', label: 'Last' },
        { value: '0', label: 'Position 0' },
        { value: '1', label: 'Position 1' },
        { value: '2', label: 'Position 2' },
        { value: '3', label: 'Position 3' },
        { value: '4', label: 'Position 4' },
        { value: '5', label: 'Position 5' }
    ],

    /**
     * API Configuration
     */
    api: {
        endpoints: {
            health: '/api/health',
            validate: '/api/validate',
            schedule: '/api/schedule-multiple'
        },
        timeout: 30000, // 30 seconds
        maxSolutions: 3
    },

    /**
     * File handling
     */
    files: {
        allowedExtensions: ['.yaml', '.yml'],
        maxFileSize: 1024 * 1024, // 1MB
        defaultFileName: 'interview_config.yaml'
    },

    /**
     * Error messages
     */
    errorMessages: {
        invalidFile: 'Please select a valid YAML file',
        fileTooLarge: 'File size exceeds the maximum limit of 1MB',
        invalidYAML: 'Invalid YAML format. Please check your file.',
        networkError: 'Network error. Please check your connection.',
        validationError: 'Configuration validation failed',
        apiNotAvailable: 'API service is not available',
        unknownError: 'An unexpected error occurred'
    },

    /**
     * Success messages
     */
    successMessages: {
        configValid: 'Configuration is valid',
        fileUploaded: 'File uploaded successfully',
        scheduleGenerated: 'Schedule generated successfully',
        yamlDownloaded: 'Configuration downloaded as YAML'
    },

    /**
     * Get a deep copy of the default configuration
     */
    getDefaultConfig() {
        return JSON.parse(JSON.stringify(this.config));
    },

    /**
     * Get API URL based on environment
     */
    getApiUrl() {
        const isLocalhost = window.location.hostname === 'localhost' ||
                           window.location.hostname === '127.0.0.1';
        return isLocalhost ?
            'http://localhost:5001' :
            'https://interviews-scheduler-90wh.onrender.com';
    },

    /**
     * Get environment info
     */
    getEnvironmentInfo() {
        const isLocalhost = window.location.hostname === 'localhost' ||
                           window.location.hostname === '127.0.0.1';
        return {
            isLocal: isLocalhost,
            apiUrl: this.getApiUrl(),
            environment: isLocalhost ? 'Local Development' : 'Production'
        };
    }
};