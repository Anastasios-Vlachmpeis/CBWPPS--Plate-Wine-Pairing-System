/**
 * API communication module
 * Handles all API calls with error handling and retry logic
 */

const API_BASE = '/api';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

/**
 * Show network error with retry option
 */
function showNetworkError(message, onRetry) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'network-error';
    errorDiv.innerHTML = `
        <div class="network-error-icon">⚠️</div>
        <div class="network-error-message">${message}</div>
        ${onRetry ? `<button class="btn btn-primary network-error-retry" onclick="this.parentElement.remove(); (${onRetry.toString()})()">Retry</button>` : ''}
    `;
    
    // Insert at top of page or specific container
    const container = document.querySelector('.main-content') || document.body;
    container.insertBefore(errorDiv, container.firstChild);
}

/**
 * Make API request with retry logic
 */
async function apiRequest(url, options = {}, retries = MAX_RETRIES) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                ...options.headers,
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        // Retry on network errors
        if (retries > 0 && (error.message.includes('fetch') || error.message.includes('network'))) {
            await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
            return apiRequest(url, options, retries - 1);
        }
        throw error;
    }
}

/**
 * Process menu files
 */
async function processMenu(files, onProgress) {
    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file);
    });

    try {
        if (onProgress) onProgress('Uploading files...');
        
        const response = await apiRequest(`${API_BASE}/process-menu`, {
            method: 'POST',
            body: formData
        });

        return response;
    } catch (error) {
        throw new Error(`Failed to process menu: ${error.message}`);
    }
}

/**
 * Process wines
 */
async function processWines(options, onProgress) {
    const formData = new FormData();
    
    formData.append('use_detected_wines', options.use_detected_wines || false);
    formData.append('use_knowledge_base', options.use_knowledge_base || false);
    
    if (options.detected_wines) {
        formData.append('detected_wines', JSON.stringify(options.detected_wines));
    }

    if (options.wine_files && options.wine_files.length > 0) {
        options.wine_files.forEach(file => {
            formData.append('wine_files', file);
        });
    }

    try {
        if (onProgress) onProgress('Processing wines...');
        
        const response = await apiRequest(`${API_BASE}/process-wines`, {
            method: 'POST',
            body: formData
        });

        return response;
    } catch (error) {
        throw new Error(`Failed to process wines: ${error.message}`);
    }
}

/**
 * Analyze wine similarity
 */
async function analyzeSimilarity(threshold = null) {
    const formData = new FormData();
    if (threshold !== null) {
        formData.append('threshold', threshold);
    }

    try {
        const response = await apiRequest(`${API_BASE}/analyze-similarity`, {
            method: 'POST',
            body: formData
        });

        return response;
    } catch (error) {
        throw new Error(`Failed to analyze similarity: ${error.message}`);
    }
}

/**
 * Pair wines to dishes
 */
async function pairWines() {
    try {
        const response = await apiRequest(`${API_BASE}/pair-wines`, {
            method: 'POST'
        });

        return response;
    } catch (error) {
        throw new Error(`Failed to pair wines: ${error.message}`);
    }
}

/**
 * Rank wines
 */
async function rankWines() {
    try {
        const response = await apiRequest(`${API_BASE}/rank-wines`, {
            method: 'POST'
        });

        return response;
    } catch (error) {
        throw new Error(`Failed to rank wines: ${error.message}`);
    }
}

/**
 * Generate report
 */
async function generateReport(format = 'dict') {
    const formData = new FormData();
    formData.append('format', format);

    try {
        const response = await apiRequest(`${API_BASE}/generate-report`, {
            method: 'POST',
            body: formData
        });

        return response;
    } catch (error) {
        throw new Error(`Failed to generate report: ${error.message}`);
    }
}

/**
 * Handle API errors with user-friendly messages
 */
function handleApiError(error) {
    let message = 'An error occurred';
    
    if (error.message.includes('Failed to fetch') || error.message.includes('network')) {
        message = 'Network error. Please check your connection and try again.';
    } else if (error.message.includes('400')) {
        message = 'Invalid request. Please check your input and try again.';
    } else if (error.message.includes('500')) {
        message = 'Server error. Please try again later.';
    } else if (error.message.includes('timeout')) {
        message = 'Request timed out. Please try again.';
    } else {
        message = error.message;
    }
    
    return message;
}
