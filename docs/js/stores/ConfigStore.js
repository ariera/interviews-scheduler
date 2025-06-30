// Interview Scheduler - Configuration Store
// GitHub Pages compatible namespace pattern

window.InterviewScheduler = window.InterviewScheduler || {};

window.InterviewScheduler.ConfigStore = {
    /**
     * Initialize the store with Vue reactivity
     */
    init() {
        const { reactive, ref } = Vue;
        const defaults = window.InterviewScheduler.Defaults;

        // Main configuration object
        this.config = reactive(defaults.getDefaultConfig());

        // UI state for panels
        this.panelNames = ref(Object.keys(this.config.panels));
        this.panelDurations = ref(Object.values(this.config.panels));
        this.panelOrderPositions = ref({});

        // UI state for other sections
        this.availabilityEntries = ref([]);
        this.positionConstraintEntries = ref([]);
        this.conflictEntries = ref([]);

        // Initialize derived state
        this.initializeDerivedState();

        console.log('✅ ConfigStore initialized with default configuration');

        return this;
    },

    /**
     * Initialize derived state from main config
     */
    initializeDerivedState() {
        const formatters = window.InterviewScheduler.Formatters;

        // Initialize panel order positions
        this.panelOrderPositions.value = {};
        Object.keys(this.config.panels).forEach(panel => {
            const orderIndex = this.config.order.indexOf(panel);
            this.panelOrderPositions.value[panel] = orderIndex >= 0 ? (orderIndex + 1).toString() : '';
        });

        // Initialize availability entries
        this.availabilityEntries.value = [];
        Object.keys(this.config.availabilities).forEach(panel => {
            this.availabilityEntries.value.push({
                panel: panel,
                value: formatters.formatAvailabilityForDisplay(this.config.availabilities[panel])
            });
        });

        // Initialize position constraint entries
        this.positionConstraintEntries.value = formatters.formatConstraintsForDisplay(this.config.position_constraints);

        // Initialize conflict entries
        this.conflictEntries.value = formatters.formatConflictsForDisplay(this.config.panel_conflicts);
    },

        /**
     * Update panels configuration
     */
    updatePanels() {
        const oldPanels = { ...this.config.panels };
        const oldNames = Object.keys(oldPanels);

        this.config.panels = {};
        this.panelNames.value.forEach((name, i) => {
            if (name && name.trim()) {
                this.config.panels[name.trim()] = this.panelDurations.value[i] || '';
            }
        });

        // Check for renamed panels and transfer their data
        oldNames.forEach((oldName, index) => {
            const currentName = this.panelNames.value[index];
            const trimmedNewName = currentName ? currentName.trim() : '';

            // Handle both exact renames and whitespace changes
            if (oldName !== trimmedNewName && trimmedNewName) {
                this.transferPanelData(oldName, trimmedNewName);
            }
            // Also handle cases where the name has whitespace but content is the same
            else if (oldName === trimmedNewName && currentName !== trimmedNewName) {
                // Name content is same but has whitespace - ensure data is under trimmed name
                this.transferPanelData(oldName, trimmedNewName);
            }
        });
    },

    /**
     * Transfer panel data from old name to new name
     */
    transferPanelData(oldName, newName) {
        // Transfer availability data
        if (this.config.availabilities[oldName] && !this.config.availabilities[newName]) {
            this.config.availabilities[newName] = this.config.availabilities[oldName];
            delete this.config.availabilities[oldName];
        }

        // Transfer position constraints
        if (this.config.position_constraints[oldName] && !this.config.position_constraints[newName]) {
            this.config.position_constraints[newName] = this.config.position_constraints[oldName];
            delete this.config.position_constraints[oldName];
        }

        // Transfer panel order positions
        if (this.panelOrderPositions.value[oldName] && !this.panelOrderPositions.value[newName]) {
            this.panelOrderPositions.value[newName] = this.panelOrderPositions.value[oldName];
            delete this.panelOrderPositions.value[oldName];
        }

        // Update order array
        const orderIndex = this.config.order.indexOf(oldName);
        if (orderIndex > -1) {
            this.config.order[orderIndex] = newName;
        }

        // Update panel conflicts
        this.config.panel_conflicts = this.config.panel_conflicts.map(conflict => {
            return conflict.map(panel => panel === oldName ? newName : panel);
        });

        console.log(`✅ Transferred panel data from "${oldName}" to "${newName}"`);
    },

    /**
     * Update panel order based on position assignments
     */
    updatePanelOrder() {
        const panels = Object.keys(this.config.panels);

        // Get panels with positions, sorted by position
        const orderedPanels = panels
            .filter(panel => this.panelOrderPositions.value[panel])
            .sort((a, b) => {
                const posA = parseInt(this.panelOrderPositions.value[a]);
                const posB = parseInt(this.panelOrderPositions.value[b]);
                return posA - posB;
            });

        // Add unspecified panels at the end
        const unspecifiedPanels = panels.filter(panel => !this.panelOrderPositions.value[panel]);

        this.config.order = [...orderedPanels, ...unspecifiedPanels];
    },

    /**
     * Update availabilities from entries
     */
    updateAvailabilities() {
        const formatters = window.InterviewScheduler.Formatters;
        this.config.availabilities = {};

        this.availabilityEntries.value.forEach(entry => {
            if (entry.panel && entry.value) {
                this.config.availabilities[entry.panel] = formatters.parseAvailabilityFromInput(entry.value);
            }
        });
    },

    /**
     * Update position constraints from entries
     */
    updatePositionConstraints() {
        const formatters = window.InterviewScheduler.Formatters;
        this.config.position_constraints = formatters.parseConstraintsFromDisplay(this.positionConstraintEntries.value);
    },

    /**
     * Update panel conflicts from entries
     */
    updatePanelConflicts() {
        const formatters = window.InterviewScheduler.Formatters;
        this.config.panel_conflicts = formatters.parseConflictsFromDisplay(this.conflictEntries.value);
    },

    /**
     * Add a new panel
     */
    addPanel() {
        const formatters = window.InterviewScheduler.Formatters;
        const newIndex = this.panelNames.value.length;
        const newName = formatters.generateDefaultPanelName(newIndex);

        this.panelNames.value.push(newName);
        this.panelDurations.value.push('');
        this.updatePanels();
    },

    /**
     * Remove a panel
     */
    removePanel(index) {
        const panelName = this.panelNames.value[index];

        // Remove from arrays
        this.panelNames.value.splice(index, 1);
        this.panelDurations.value.splice(index, 1);
        this.updatePanels();

        // Remove from order
        const orderIdx = this.config.order.indexOf(panelName);
        if (orderIdx > -1) {
            this.config.order.splice(orderIdx, 1);
        }

        // Remove from availabilities
        if (this.config.availabilities[panelName]) {
            delete this.config.availabilities[panelName];
        }

        // Remove from availability entries
        const availabilityIdx = this.availabilityEntries.value.findIndex(entry => entry.panel === panelName);
        if (availabilityIdx > -1) {
            this.availabilityEntries.value.splice(availabilityIdx, 1);
        }

        // Remove from position constraints
        const constraintIdx = this.positionConstraintEntries.value.findIndex(entry => entry.panel === panelName);
        if (constraintIdx > -1) {
            this.positionConstraintEntries.value.splice(constraintIdx, 1);
            this.updatePositionConstraints();
        }

        // Remove from panel order positions
        if (this.panelOrderPositions.value[panelName] !== undefined) {
            delete this.panelOrderPositions.value[panelName];
        }
    },

    /**
     * Load configuration from external data
     */
    loadConfiguration(yamlData) {
        const formatters = window.InterviewScheduler.Formatters;

        // Update basic fields
        if (yamlData.num_candidates) this.config.num_candidates = yamlData.num_candidates;
        if (yamlData.start_time) this.config.start_time = yamlData.start_time;
        if (yamlData.end_time) this.config.end_time = yamlData.end_time;
        if (yamlData.slot_duration_minutes) this.config.slot_duration_minutes = yamlData.slot_duration_minutes;
        if (yamlData.max_gap_minutes) this.config.max_gap_minutes = yamlData.max_gap_minutes;

        // Update panels
        if (yamlData.panels) {
            this.config.panels = yamlData.panels;
            this.panelNames.value = Object.keys(this.config.panels);
            this.panelDurations.value = Object.values(this.config.panels);
        }

        // Update order and positions
        if (yamlData.order) {
            this.config.order = yamlData.order;
            this.panelOrderPositions.value = {};
            Object.keys(this.config.panels).forEach(panel => {
                const orderIndex = this.config.order.indexOf(panel);
                this.panelOrderPositions.value[panel] = orderIndex >= 0 ? (orderIndex + 1).toString() : '';
            });
        }

        // Update availabilities
        if (yamlData.availabilities) {
            this.config.availabilities = yamlData.availabilities;
            this.availabilityEntries.value = [];
            Object.keys(this.config.availabilities).forEach(panel => {
                this.availabilityEntries.value.push({
                    panel: panel,
                    value: formatters.formatAvailabilityForDisplay(this.config.availabilities[panel])
                });
            });
        }

        // Update position constraints
        if (yamlData.position_constraints) {
            this.config.position_constraints = yamlData.position_constraints;
            this.positionConstraintEntries.value = formatters.formatConstraintsForDisplay(this.config.position_constraints);
        }

        // Update panel conflicts
        if (yamlData.panel_conflicts) {
            this.config.panel_conflicts = yamlData.panel_conflicts;
            this.conflictEntries.value = formatters.formatConflictsForDisplay(this.config.panel_conflicts);
        }

        console.log('✅ Configuration loaded from external data');
    },

    /**
     * Get current configuration as clean object
     */
    getConfiguration() {
        const formatters = window.InterviewScheduler.Formatters;
        return formatters.formatConfigForExport(this.config);
    },

    /**
     * Reset to default configuration
     */
    resetToDefaults() {
        const defaults = window.InterviewScheduler.Defaults;
        const defaultConfig = defaults.getDefaultConfig();

        // Reset main config
        Object.assign(this.config, defaultConfig);

        // Re-initialize derived state
        this.initializeDerivedState();

        console.log('✅ Configuration reset to defaults');
    },

    /**
     * Validate current configuration
     */
    validateConfiguration() {
        const validators = window.InterviewScheduler.Validators;
        return validators.validateConfig(this.config);
    }
};