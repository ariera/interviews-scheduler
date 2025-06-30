// Interview Scheduler - API Service
// GitHub Pages compatible namespace pattern

window.InterviewScheduler = window.InterviewScheduler || {};

window.InterviewScheduler.ApiService = {
    /**
     * Get the base API URL
     */
    getBaseUrl() {
        return window.InterviewScheduler.Defaults.getApiUrl();
    },

    /**
     * Make HTTP request with error handling
     */
    async makeRequest(endpoint, options = {}) {
        const baseUrl = this.getBaseUrl();
        const url = `${baseUrl}${endpoint}`;

        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: window.InterviewScheduler.Defaults.api.timeout
        };

        const requestOptions = { ...defaultOptions, ...options };

        try {
            console.log(`🌐 API Request: ${requestOptions.method} ${url}`);

            const response = await fetch(url, requestOptions);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`✅ API Response: ${requestOptions.method} ${url}`, data);

            return {
                success: true,
                data: data,
                status: response.status
            };

        } catch (error) {
            console.error(`❌ API Error: ${requestOptions.method} ${url}`, error);

            return {
                success: false,
                error: error.message,
                status: error.status || 0
            };
        }
    },

    /**
     * Check API health
     */
    async checkHealth() {
        const endpoint = window.InterviewScheduler.Defaults.api.endpoints.health;
        return await this.makeRequest(endpoint);
    },

    /**
     * Validate configuration
     */
    async validateConfig(config) {
        const endpoint = window.InterviewScheduler.Defaults.api.endpoints.validate;

        return await this.makeRequest(endpoint, {
            method: 'POST',
            body: JSON.stringify({ config: config })
        });
    },

    /**
     * Generate interview schedules
     */
    async generateSchedules(config, maxSolutions = null) {
        const endpoint = window.InterviewScheduler.Defaults.api.endpoints.schedule;
        const solutions = maxSolutions || window.InterviewScheduler.Defaults.api.maxSolutions;

        return await this.makeRequest(endpoint, {
            method: 'POST',
            body: JSON.stringify({
                config: config,
                max_solutions: solutions
            })
        });
    },

    /**
     * Get API status information
     */
    async getApiStatus() {
        const health = await this.checkHealth();
        const envInfo = window.InterviewScheduler.Defaults.getEnvironmentInfo();

        return {
            ...envInfo,
            isHealthy: health.success,
            healthData: health.data,
            error: health.error
        };
    },

    /**
     * Test API connectivity and return user-friendly status
     */
    async testConnectivity() {
        const status = await this.getApiStatus();

        let message = `🔗 API: ${status.environment}`;

        if (status.isHealthy) {
            message += ' ✅ Connected';
        } else {
            message += ' ❌ Not Connected';
            if (status.isLocal) {
                message += '<br><small style="color: #e74c3c;">Make sure to run: cd api && python app.py</small>';
            }
        }

        return {
            isConnected: status.isHealthy,
            message: message,
            details: status
        };
    }
};