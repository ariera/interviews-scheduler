const { createApp, reactive, watch, ref, computed } = Vue;

// Global function to populate form from YAML (called from existing upload logic)
window.populateFormFromYAML = function(yamlData) {
    if (window.vueApp) {
        window.vueApp.populateFromYAML(yamlData);
    }
};

// Debug logging
console.log('🚀 Initializing Vue app...');

try {
    const app = createApp({
        setup() {
            console.log('📝 Setting up Vue component...');

            const config = reactive({
                num_candidates: 3,
                start_time: '08:30',
                end_time: '17:00',
                slot_duration_minutes: 15,
                max_gap_minutes: 15,
                panels: { Director: '15min', Competencies: '1h', HR: '45min', Lunch: '1h', Team: '45min', Goodbye: '30min' },
                order: ['Director', 'Competencies', 'HR', 'Lunch', 'Team', 'Goodbye'],
                availabilities: {
                    Director: '08:30-10:00',
                    Competencies: ['08:30-11:00', '12:00-14:00', '16:00-17:00'],
                    HR: '08:30-17:00',
                    Lunch: '11:45-13:30',
                    Team: '08:30-17:00',
                    Goodbye: '08:30-17:00'
                },
                position_constraints: {
                    Goodbye: 'last'
                },
                panel_conflicts: [
                    ['Team', 'Goodbye']
                ]
            });

            console.log('✅ Config initialized:', config);

            // For dynamic panel editing
            const panelNames = ref(Object.keys(config.panels));
            const panelDurations = ref(Object.values(config.panels));

            // For order editing
            const panelOrderPositions = ref({});
            let isUpdatingOrder = false; // Guard flag to prevent infinite loops

            // For availabilities editing
            const availabilityPanels = ref(Object.keys(config.availabilities));
            const availabilityEntries = ref([]);

            // For position constraints editing
            const positionConstraintPanels = ref(Object.keys(config.position_constraints));
            const positionConstraintEntries = ref([]);

            // For panel conflicts editing
            const conflictEntries = ref([]);

            // Initialize availability entries
            Object.keys(config.availabilities).forEach(panel => {
                availabilityEntries.value.push({
                    panel: panel,
                    value: Array.isArray(config.availabilities[panel])
                        ? config.availabilities[panel].join('\n')
                        : config.availabilities[panel]
                });
            });

            // Initialize position constraint entries
            Object.keys(config.position_constraints).forEach(panel => {
                positionConstraintEntries.value.push({
                    panel: panel,
                    value: config.position_constraints[panel]
                });
            });

            // Initialize conflict entries
            config.panel_conflicts.forEach(conflict => {
                conflictEntries.value.push({
                    panel1: conflict[0] || '',
                    panel2: conflict[1] || ''
                });
            });

            // Initialize panel order positions
            Object.keys(config.panels).forEach(panel => {
                panelOrderPositions.value[panel] = '';
            });

            console.log('✅ Reactive data initialized');

            // Using CSS order property for sorting instead of reordering the array

            function getPanelIndex(panelName) {
                return panelNames.value.indexOf(panelName);
            }

            function getPanelDisplayOrder(panelName) {
                if (!panelName || !panelName.trim()) return 999;
                const position = panelOrderPositions.value[panelName];
                return position ? parseInt(position) : 999;
            }

            function addPanel() {
                const newIndex = panelNames.value.length;
                panelNames.value.push(`Panel ${newIndex + 1}`);
                panelDurations.value.push('');
                updatePanels();
            }

            function getAvailabilityForPanel(panelName) {
                if (!panelName) return '';
                const availability = config.availabilities[panelName];
                if (!availability) return '';
                return Array.isArray(availability) ? availability.join('\n') : availability;
            }

            function updateAvailabilityForPanel(panelName, event) {
                if (!panelName) return;
                const value = event.target.value;
                if (!value.trim()) {
                    delete config.availabilities[panelName];
                } else {
                    const windows = value.split('\n').filter(w => w.trim());
                    config.availabilities[panelName] = windows.length === 1 ? windows[0] : windows;
                }
            }

            function removePanel(idx) {
                const panelName = panelNames.value[idx];
                panelNames.value.splice(idx, 1);
                panelDurations.value.splice(idx, 1);
                updatePanels();

                // Remove from order if exists
                const orderIdx = config.order.indexOf(panelName);
                if (orderIdx > -1) {
                    config.order.splice(orderIdx, 1);
                    updateOrder();
                }

                // Remove from availabilities if exists
                if (config.availabilities[panelName]) {
                    delete config.availabilities[panelName];
                }

                // Remove from position constraints if exists
                const positionConstraintIdx = positionConstraintEntries.value.findIndex(entry => entry.panel === panelName);
                if (positionConstraintIdx > -1) {
                    positionConstraintEntries.value.splice(positionConstraintIdx, 1);
                    updatePositionConstraints();
                }
            }



            function updatePanelName(idx) {
                const oldName = panelNames.value[idx];
                const newName = panelNames.value[idx];

                // Don't update if name hasn't actually changed
                if (oldName === newName) return;

                // Don't update if new name is empty or just whitespace
                if (!newName || !newName.trim()) return;

                // Store the old name before updating
                const previousName = oldName;

                updatePanels();

                // Update order if panel name changed
                const orderIdx = config.order.indexOf(previousName);
                if (orderIdx > -1) {
                    config.order[orderIdx] = newName.trim();
                    updateOrder();
                }

                // Update availabilities if panel name changed
                const availabilityIdx = availabilityEntries.value.findIndex(entry => entry.panel === previousName);
                if (availabilityIdx > -1) {
                    availabilityEntries.value[availabilityIdx].panel = newName.trim();
                }

                // Update position constraints if panel name changed
                const positionConstraintIdx = positionConstraintEntries.value.findIndex(entry => entry.panel === previousName);
                if (positionConstraintIdx > -1) {
                    positionConstraintEntries.value[positionConstraintIdx].panel = newName.trim();
                }

                // Update panel order positions if panel name changed
                if (panelOrderPositions.value[previousName] !== undefined) {
                    panelOrderPositions.value[newName.trim()] = panelOrderPositions.value[previousName];
                    delete panelOrderPositions.value[previousName];
                }
            }



            function updatePanelDuration(idx) {
                updatePanels();
            }

            function updatePanels() {
                config.panels = {};
                panelNames.value.forEach((name, i) => {
                    if (name && name.trim()) {
                        config.panels[name.trim()] = panelDurations.value[i] || '';
                    }
                });
            }

            function updateOrder() {
                config.order = config.order.filter(panel => panel && config.panels[panel]);
            }

            function updatePanelOrder() {
                if (isUpdatingOrder) return; // Prevent recursive calls
                isUpdatingOrder = true;

                try {
                    // Generate order array based on positions
                    const panels = Object.keys(config.panels);
                    const orderedPanels = panels
                        .filter(panel => panelOrderPositions.value[panel]) // Only panels with positions
                        .sort((a, b) => {
                            const posA = parseInt(panelOrderPositions.value[a]);
                            const posB = parseInt(panelOrderPositions.value[b]);
                            return posA - posB;
                        });

                    // Add unspecified panels at the end
                    const unspecifiedPanels = panels.filter(panel => !panelOrderPositions.value[panel]);
                    config.order = [...orderedPanels, ...unspecifiedPanels];
                } finally {
                    isUpdatingOrder = false;
                }
            }

            function updateAvailabilities() {
                config.availabilities = {};
                availabilityEntries.value.forEach(entry => {
                    if (entry.panel && entry.value) {
                        const windows = entry.value.split('\n').filter(w => w.trim());
                        config.availabilities[entry.panel] = windows.length === 1 ? windows[0] : windows;
                    }
                });
            }

            function addAvailabilityPanel() {
                availabilityEntries.value.push({
                    panel: '',
                    value: ''
                });
            }

            function removeAvailabilityPanel(index) {
                availabilityEntries.value.splice(index, 1);
                updateAvailabilities();
            }

            function updatePositionConstraints() {
                config.position_constraints = {};
                positionConstraintEntries.value.forEach(entry => {
                    if (entry.panel && entry.value) {
                        config.position_constraints[entry.panel] = entry.value;
                    }
                });
            }

            function addPositionConstraint() {
                positionConstraintEntries.value.push({
                    panel: '',
                    value: 'first'
                });
            }

            function removePositionConstraint(index) {
                positionConstraintEntries.value.splice(index, 1);
                updatePositionConstraints();
            }

            function addConflictGroup() {
                conflictEntries.value.push({
                    panel1: '',
                    panel2: ''
                });
            }

            function removeConflictGroup(idx) {
                conflictEntries.value.splice(idx, 1);
                updatePanelConflicts();
            }

            function updatePanelConflicts() {
                config.panel_conflicts = conflictEntries.value.filter(entry =>
                    entry.panel1 && entry.panel2
                ).map(entry => [entry.panel1, entry.panel2]);
            }

            function downloadYAML() {
                const yaml = jsyaml.dump(JSON.parse(JSON.stringify(config)));
                const blob = new Blob([yaml], { type: 'text/yaml' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'interview_config.yaml';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }

            function populateFromYAML(yamlData) {
                // Update basic fields
                if (yamlData.num_candidates) config.num_candidates = yamlData.num_candidates;
                if (yamlData.start_time) config.start_time = yamlData.start_time;
                if (yamlData.end_time) config.end_time = yamlData.end_time;
                if (yamlData.slot_duration_minutes) config.slot_duration_minutes = yamlData.slot_duration_minutes;
                if (yamlData.max_gap_minutes) config.max_gap_minutes = yamlData.max_gap_minutes;

                // Update panels
                if (yamlData.panels) {
                    config.panels = yamlData.panels;
                    panelNames.value = Object.keys(config.panels);
                    panelDurations.value = Object.values(config.panels);
                }

                // Update order
                if (yamlData.order) {
                    isUpdatingOrder = true; // Prevent watchers from firing
                    config.order = yamlData.order;
                    // Convert order array to position assignments
                    panelOrderPositions.value = {};
                    Object.keys(config.panels).forEach(panel => {
                        const orderIndex = config.order.indexOf(panel);
                        if (orderIndex >= 0) {
                            panelOrderPositions.value[panel] = (orderIndex + 1).toString();
                        } else {
                            panelOrderPositions.value[panel] = '';
                        }
                    });
                    isUpdatingOrder = false;
                }

                // Update availabilities
                if (yamlData.availabilities) {
                    config.availabilities = yamlData.availabilities;
                    availabilityPanels.value = Object.keys(config.availabilities);
                    availabilityEntries.value = [];
                    Object.keys(config.availabilities).forEach(panel => {
                        availabilityEntries.value.push({
                            panel: panel,
                            value: Array.isArray(config.availabilities[panel])
                                ? config.availabilities[panel].join('\n')
                                : config.availabilities[panel]
                        });
                    });
                }

                // Update position constraints
                if (yamlData.position_constraints) {
                    config.position_constraints = yamlData.position_constraints;
                    positionConstraintPanels.value = Object.keys(config.position_constraints);
                    positionConstraintEntries.value = [];
                    Object.keys(config.position_constraints).forEach(panel => {
                        positionConstraintEntries.value.push({
                            panel: panel,
                            value: config.position_constraints[panel]
                        });
                    });
                }

                // Update panel conflicts
                if (yamlData.panel_conflicts) {
                    config.panel_conflicts = yamlData.panel_conflicts;
                    conflictEntries.value = [];
                    config.panel_conflicts.forEach(conflict => {
                        conflictEntries.value.push({
                            panel1: conflict[0] || '',
                            panel2: conflict[1] || ''
                        });
                    });
                }
            }

            function getConfig() {
                return JSON.parse(JSON.stringify(config));
            }

            // Keep reactive arrays in sync
            // Removed problematic watcher that was overwriting panelNames during editing
            // watch(() => config.panels, (newPanels) => {
            //     panelNames.value = Object.keys(newPanels);
            //     panelDurations.value = Object.values(newPanels);
            // }, { deep: true });

            // Removed problematic watcher that was causing infinite loops
            // watch(() => config.order, (newOrder) => {
            //     config.order = [...newOrder];
            // }, { deep: true });

            watch(() => config.availabilities, (newAvailabilities) => {
                availabilityPanels.value = Object.keys(newAvailabilities);
                // Only update entries if they're empty (don't overwrite user input)
                if (availabilityEntries.value.length === 0) {
                    Object.keys(newAvailabilities).forEach(panel => {
                        availabilityEntries.value.push({
                            panel: panel,
                            value: Array.isArray(newAvailabilities[panel])
                                ? newAvailabilities[panel].join('\n')
                                : newAvailabilities[panel]
                        });
                    });
                }
            }, { deep: true });

            watch(() => config.position_constraints, (newConstraints) => {
                positionConstraintPanels.value = Object.keys(newConstraints);
                // Only update entries if they're empty (don't overwrite user input)
                if (positionConstraintEntries.value.length === 0) {
                    Object.keys(newConstraints).forEach(panel => {
                        positionConstraintEntries.value.push({
                            panel: panel,
                            value: newConstraints[panel]
                        });
                    });
                }
            }, { deep: true });

            watch(() => config.panel_conflicts, (newConflicts) => {
                // Only update entries if they're empty (don't overwrite user input)
                if (conflictEntries.value.length === 0) {
                    newConflicts.forEach(conflict => {
                        conflictEntries.value.push({
                            panel1: conflict[0] || '',
                            panel2: conflict[1] || ''
                        });
                    });
                }
            }, { deep: true });

            console.log('✅ All functions and watchers initialized');

            // Expose functions globally for external use
            const appInstance = {
                config,
                panelNames,
                panelDurations,
                panelOrderPositions,
                availabilityPanels,
                availabilityEntries,
                positionConstraintPanels,
                positionConstraintEntries,
                conflictEntries,
                addPanel,
                removePanel,
                updatePanelName,
                updatePanelDuration,
                updatePanels,
                getPanelIndex,
                getPanelDisplayOrder,
                getAvailabilityForPanel,
                updateAvailabilityForPanel,
                updateOrder,
                updatePanelOrder,
                updateAvailabilities,
                addAvailabilityPanel,
                removeAvailabilityPanel,
                updatePositionConstraints,
                addPositionConstraint,
                removePositionConstraint,
                addConflictGroup,
                removeConflictGroup,
                updatePanelConflicts,
                downloadYAML,
                populateFromYAML,
                getConfig
            };

            // Make app globally accessible
            window.vueApp = appInstance;

            console.log('✅ Vue app setup complete');

            return appInstance;
        }
    });

    console.log('🎯 Mounting Vue app...');
    const mountedApp = app.mount('#app');
    console.log('✅ Vue app mounted successfully:', mountedApp);

    // Hide loading state and show form
    const loadingEl = document.getElementById('vue-loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }

    // Hide fallback if it was shown
    const fallbackEl = document.getElementById('vue-fallback');
    if (fallbackEl) {
        fallbackEl.style.display = 'none';
    }

} catch (error) {
    console.error('❌ Error initializing Vue app:', error);

    // Hide loading state
    const loadingEl = document.getElementById('vue-loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }

    // Show error in the UI
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
}

// Fallback timeout - if Vue doesn't load within 5 seconds, show fallback
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