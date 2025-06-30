// Interview Scheduler - Main Application
// GitHub Pages compatible namespace pattern

window.InterviewScheduler = window.InterviewScheduler || {};

// Initialize the application
window.InterviewScheduler.App = {
    /**
     * Initialize and mount the Vue application
     */
    async init() {
        console.log('🚀 Initializing Interview Scheduler App...');

        try {
            // Initialize the configuration store
            const store = window.InterviewScheduler.ConfigStore.init();

            // Create Vue application
            const app = this.createVueApp(store);

            // Mount the application
            const mountedApp = app.mount('#app');
            console.log('✅ Vue app mounted successfully');

            // Hide loading state and show form
            this.hideLoadingState();

            // Initialize API connectivity check
            await this.checkApiConnectivity();

            // Setup global functions for legacy compatibility
            this.setupGlobalFunctions(store);

            console.log('✅ Interview Scheduler App initialized successfully');

            return {
                app: mountedApp,
                store: store
            };

        } catch (error) {
            console.error('❌ Error initializing app:', error);
            this.showErrorState(error);
            throw error;
        }
    },

    /**
     * Create the Vue application with all reactive data and methods
     */
    createVueApp(store) {
        const { createApp } = Vue;

        return createApp({
            setup() {
                console.log('📝 Setting up Vue component...');

                // Helper functions for UI
                const getPanelIndex = (panelName) => {
                    return store.panelNames.value.indexOf(panelName);
                };

                const getPanelDisplayOrder = (panelName) => {
                    if (!panelName || !panelName.trim()) return 999;
                    const position = store.panelOrderPositions.value[panelName];
                    return position ? parseInt(position) : 999;
                };

                const getAvailabilityForPanel = (panelName) => {
                    if (!panelName) return '';
                    // Always use trimmed panel name for consistency
                    const trimmedName = panelName.trim();
                    const availability = store.config.availabilities[trimmedName];
                    if (!availability) return '';
                    return Array.isArray(availability) ? availability.join('\n') : availability;
                };

                const updateAvailabilityForPanel = (panelName, event) => {
                    if (!panelName) return;
                    const value = event.target.value;
                    const formatters = window.InterviewScheduler.Formatters;
                    // Always use trimmed panel name for consistency
                    const trimmedName = panelName.trim();

                    if (!value.trim()) {
                        delete store.config.availabilities[trimmedName];
                    } else {
                        store.config.availabilities[trimmedName] = formatters.parseAvailabilityFromInput(value);
                    }
                };

                // Position constraint management
                const addPositionConstraint = () => {
                    store.positionConstraintEntries.value.push({
                        panel: '',
                        value: 'first'
                    });
                };

                const removePositionConstraint = (index) => {
                    store.positionConstraintEntries.value.splice(index, 1);
                    store.updatePositionConstraints();
                };

                // Conflict management
                const addConflictGroup = () => {
                    store.conflictEntries.value.push({
                        panel1: '',
                        panel2: ''
                    });
                };

                const removeConflictGroup = (index) => {
                    store.conflictEntries.value.splice(index, 1);
                    store.updatePanelConflicts();
                };

                // YAML download
                const downloadYAML = () => {
                    const yamlService = window.InterviewScheduler.YamlService;
                    const config = store.getConfiguration();
                    const result = yamlService.downloadYaml(config);

                    if (!result.success) {
                        console.error('Failed to download YAML:', result.error);
                        // Could show user notification here
                    }
                };

                console.log('✅ Vue component setup complete');

                // Return all reactive data and methods for the template
                return {
                    // Store data
                    config: store.config,
                    panelNames: store.panelNames,
                    panelDurations: store.panelDurations,
                    panelOrderPositions: store.panelOrderPositions,
                    positionConstraintEntries: store.positionConstraintEntries,
                    conflictEntries: store.conflictEntries,

                    // Store methods
                    addPanel: () => store.addPanel(),
                    removePanel: (index) => store.removePanel(index),
                    updatePanels: () => store.updatePanels(),
                    updatePanelOrder: () => store.updatePanelOrder(),
                    updatePositionConstraints: () => store.updatePositionConstraints(),
                    updatePanelConflicts: () => store.updatePanelConflicts(),

                    // Helper functions
                    getPanelIndex,
                    getPanelDisplayOrder,
                    getAvailabilityForPanel,
                    updateAvailabilityForPanel,

                    // UI actions
                    addPositionConstraint,
                    removePositionConstraint,
                    addConflictGroup,
                    removeConflictGroup,
                    downloadYAML,

                    // Expose store for external access
                    store: store
                };
            }
        });
    },

    /**
     * Hide loading state and show the form
     */
    hideLoadingState() {
        const loadingEl = document.getElementById('vue-loading');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }

        const fallbackEl = document.getElementById('vue-fallback');
        if (fallbackEl) {
            fallbackEl.style.display = 'none';
        }
    },

    /**
     * Show error state
     */
    showErrorState(error) {
        const loadingEl = document.getElementById('vue-loading');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }

        const appContainer = document.getElementById('app');
        if (appContainer) {
            appContainer.innerHTML = `
                <div style="background: #fdf2f2; color: #e74c3c; padding: 20px; border-radius: 6px; border-left: 4px solid #e74c3c;">
                    <h3>Error Loading Form</h3>
                    <p>There was an error initializing the configuration form. Please refresh the page or check the browser console for details.</p>
                    <p><strong>Error:</strong> ${error.message}</p>
                </div>
            `;
        }
    },

    /**
     * Check API connectivity and update status
     */
    async checkApiConnectivity() {
        const apiService = window.InterviewScheduler.ApiService;
        const apiStatus = document.getElementById('apiStatus');

        if (!apiStatus) return;

        try {
            const connectivity = await apiService.testConnectivity();
            apiStatus.innerHTML = connectivity.message;
        } catch (error) {
            console.warn('Could not check API connectivity:', error);
            apiStatus.innerHTML = '🔗 API: Status unknown';
        }
    },

    /**
     * Setup global functions for backward compatibility
     */
    setupGlobalFunctions(store) {
        // Global function for YAML upload integration
        window.populateFormFromYAML = function(yamlData) {
            store.loadConfiguration(yamlData);
            console.log('✅ Form populated from YAML data');
        };

        // Global function for getting current config
        window.getInterviewConfig = function() {
            return store.getConfiguration();
        };

        // Global function for validation
        window.validateInterviewConfig = function() {
            return store.validateConfiguration();
        };

        // Store reference for external access
        window.vueApp = {
            store: store,
            getConfig: () => store.getConfiguration(),
            populateFromYAML: (data) => store.loadConfiguration(data),
            validateConfig: () => store.validateConfiguration()
        };
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Add a small delay to ensure all scripts are loaded
    setTimeout(() => {
        window.InterviewScheduler.App.init().catch(error => {
            console.error('Failed to initialize app:', error);
        });
    }, 100);
});

// Fallback timeout - if app doesn't load within 5 seconds, show fallback
setTimeout(() => {
    const loadingEl = document.getElementById('vue-loading');
    const fallbackEl = document.getElementById('vue-fallback');

    if (loadingEl && loadingEl.style.display !== 'none') {
        console.warn('⚠️ Vue app taking too long to load, showing fallback');
        loadingEl.style.display = 'none';
        if (fallbackEl) {
            fallbackEl.style.display = 'block';
        }
    }
}, 5000);