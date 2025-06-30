// Interview Scheduler - YAML Service
// GitHub Pages compatible namespace pattern

window.InterviewScheduler = window.InterviewScheduler || {};

window.InterviewScheduler.YamlService = {
    /**
     * Parse YAML string to JavaScript object
     */
    parseYaml(yamlString) {
        try {
            if (!yamlString || yamlString.trim() === '') {
                throw new Error('Empty YAML content');
            }

            const data = jsyaml.load(yamlString);
            console.log('✅ YAML parsed successfully:', data);

            return {
                success: true,
                data: data
            };

        } catch (error) {
            console.error('❌ YAML parsing error:', error);

            return {
                success: false,
                error: error.message || 'Invalid YAML format'
            };
        }
    },

    /**
     * Convert JavaScript object to YAML string
     */
    stringifyYaml(data) {
        try {
            if (!data || typeof data !== 'object') {
                throw new Error('Invalid data for YAML conversion');
            }

            // Clean the data before conversion
            const cleanData = window.InterviewScheduler.Formatters.formatConfigForExport(data);
            const yamlString = jsyaml.dump(cleanData, {
                indent: 2,
                lineWidth: 120,
                noRefs: true,
                sortKeys: false
            });

            console.log('✅ YAML generated successfully');

            return {
                success: true,
                yaml: yamlString
            };

        } catch (error) {
            console.error('❌ YAML generation error:', error);

            return {
                success: false,
                error: error.message || 'Failed to generate YAML'
            };
        }
    },

    /**
     * Validate YAML file before processing
     */
    validateYamlFile(file) {
        const errors = [];
        const defaults = window.InterviewScheduler.Defaults;

        // Check file type
        const fileName = file.name.toLowerCase();
        const hasValidExtension = defaults.files.allowedExtensions.some(ext =>
            fileName.endsWith(ext)
        );

        if (!hasValidExtension) {
            errors.push(defaults.errorMessages.invalidFile);
        }

        // Check file size
        if (file.size > defaults.files.maxFileSize) {
            errors.push(defaults.errorMessages.fileTooLarge);
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    },

    /**
     * Read and parse YAML file
     */
    async readYamlFile(file) {
        return new Promise((resolve) => {
            // First validate the file
            const validation = this.validateYamlFile(file);
            if (!validation.isValid) {
                resolve({
                    success: false,
                    errors: validation.errors
                });
                return;
            }

            const reader = new FileReader();

            reader.onload = (event) => {
                const yamlString = event.target.result;
                const parseResult = this.parseYaml(yamlString);

                if (parseResult.success) {
                    resolve({
                        success: true,
                        data: parseResult.data,
                        fileName: file.name,
                        fileSize: file.size
                    });
                } else {
                    resolve({
                        success: false,
                        errors: [parseResult.error]
                    });
                }
            };

            reader.onerror = () => {
                resolve({
                    success: false,
                    errors: ['Failed to read file']
                });
            };

            reader.readAsText(file);
        });
    },

    /**
     * Download configuration as YAML file
     */
    downloadYaml(config, fileName = null) {
        try {
            const defaults = window.InterviewScheduler.Defaults;
            const finalFileName = fileName || defaults.files.defaultFileName;

            // Convert to YAML
            const yamlResult = this.stringifyYaml(config);
            if (!yamlResult.success) {
                throw new Error(yamlResult.error);
            }

            // Create and trigger download
            const blob = new Blob([yamlResult.yaml], { type: 'text/yaml' });
            const url = window.URL.createObjectURL(blob);

            const downloadLink = document.createElement('a');
            downloadLink.href = url;
            downloadLink.download = finalFileName;
            downloadLink.style.display = 'none';

            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);

            // Clean up the URL
            window.URL.revokeObjectURL(url);

            console.log(`✅ YAML file downloaded: ${finalFileName}`);

            return {
                success: true,
                fileName: finalFileName,
                message: defaults.successMessages.yamlDownloaded
            };

        } catch (error) {
            console.error('❌ YAML download error:', error);

            return {
                success: false,
                error: error.message || 'Failed to download YAML file'
            };
        }
    },

    /**
     * Validate configuration data structure
     */
    validateConfigStructure(data) {
        const validators = window.InterviewScheduler.Validators;
        return validators.validateConfig(data);
    },

    /**
     * Process uploaded YAML file and return formatted data
     */
    async processUploadedFile(file) {
        console.log(`📁 Processing YAML file: ${file.name}`);

        // Read and parse the file
        const readResult = await this.readYamlFile(file);

        if (!readResult.success) {
            return {
                success: false,
                errors: readResult.errors
            };
        }

        // Validate the configuration structure
        const validation = this.validateConfigStructure(readResult.data);

        if (!validation.isValid) {
            return {
                success: false,
                errors: validation.errors,
                warnings: ['File was parsed but contains validation errors']
            };
        }

        return {
            success: true,
            data: readResult.data,
            fileName: readResult.fileName,
            fileSize: readResult.fileSize,
            message: window.InterviewScheduler.Defaults.successMessages.fileUploaded
        };
    }
};