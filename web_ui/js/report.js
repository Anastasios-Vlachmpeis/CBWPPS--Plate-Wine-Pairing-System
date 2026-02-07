/**
 * Report creation workflow logic
 * Manages the complete report creation flow
 */

// Global state
let reportState = {
    menuFiles: [],
    menuResult: null,
    wineFiles: [],
    wineOptions: {
        use_detected_wines: false,
        use_knowledge_base: false,
        additional_files: []
    },
    wineResult: null,
    similarPairs: null,
    pairings: null,
    rankings: null,
    report: null
};

/**
 * Initialize report creation page
 */
function initReportCreation() {
    // Check authentication
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (!user) {
        window.location.href = 'index.html';
        return;
    }

    // Initialize file upload
    initFileUpload();
    
    // Initialize breadcrumb
    updateBreadcrumb(['Home', 'Create Report']);
}

/**
 * Initialize file upload area
 */
function initFileUpload() {
    const uploadArea = document.getElementById('file-upload-area');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const processButton = document.getElementById('process-button');

    if (!uploadArea || !fileInput) return;

    // Click to upload
    uploadArea.addEventListener('click', () => fileInput.click());

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

/**
 * Handle file selection
 */
function handleFiles(files) {
    const validation = validateFiles(files);
    const errorContainer = document.getElementById('file-errors');
    
    // Display errors
    if (!validation.valid) {
        displayValidationErrors('file-errors', validation.errors);
    } else {
        clearValidationErrors('file-errors');
    }

    // Add valid files to state
    validation.validFiles.forEach(file => {
        if (!reportState.menuFiles.find(f => f.name === file.name && f.size === file.size)) {
            reportState.menuFiles.push(file);
        }
    });

    updateFileList();
    updateProcessButton();
}

/**
 * Update file list display
 */
function updateFileList() {
    const fileList = document.getElementById('file-list');
    if (!fileList) return;

    fileList.innerHTML = '';

    if (reportState.menuFiles.length === 0) {
        fileList.innerHTML = '<p style="text-align: center; color: #999;">No files selected</p>';
        return;
    }

    reportState.menuFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-item-info">
                <div class="file-item-name">${file.name}</div>
                <div class="file-item-size">${formatFileSize(file.size)}</div>
            </div>
            <button class="file-item-remove" onclick="removeFile(${index})">Remove</button>
        `;
        fileList.appendChild(fileItem);
    });
}

/**
 * Remove file from list
 */
function removeFile(index) {
    reportState.menuFiles.splice(index, 1);
    updateFileList();
    updateProcessButton();
    clearValidationErrors('file-errors');
}

/**
 * Update process button state
 */
function updateProcessButton() {
    const processButton = document.getElementById('process-button');
    if (processButton) {
        processButton.disabled = reportState.menuFiles.length === 0;
    }
}

/**
 * Process menu files
 */
async function processMenuFiles() {
    if (reportState.menuFiles.length === 0) {
        showToast('Please select at least one file', 'error');
        return;
    }

    // Show loading screen
    showLoadingScreen('menu-processing');

    try {
        // Initialize progress
        const progressTracker = initProgressTracker(6, 'loading-progress');
        progressTracker.setSteps([
            'Uploading files',
            'Extracting dishes',
            'Mapping flavors',
            'Detecting wines',
            'Processing complete'
        ]);
        progressTracker.nextStep();

        // Process menu
        const result = await processMenu(reportState.menuFiles, (status) => {
            progressTracker.nextStep();
        });

        progressTracker.nextStep();
        progressTracker.nextStep();
        progressTracker.nextStep();

        reportState.menuResult = result;

        // Hide loading, show wine options
        hideLoadingScreen();
        showWineOptions(result);

    } catch (error) {
        hideLoadingScreen();
        showError('menu-error', handleApiError(error));
        showToast('Failed to process menu files', 'error');
    }
}

/**
 * Show wine options screen
 */
function showWineOptions(menuResult) {
    const uploadSection = document.getElementById('file-upload-section');
    const wineOptionsSection = document.getElementById('wine-options-section');

    if (!uploadSection || !wineOptionsSection) return;

    uploadSection.style.display = 'none';
    wineOptionsSection.style.display = 'block';

    const hasWines = menuResult.has_wines;
    const wineCount = menuResult.wine_count || 0;

    // Update wine options UI
    const wineOptionsContent = document.getElementById('wine-options-content');
    if (wineOptionsContent) {
        if (hasWines) {
            wineOptionsContent.innerHTML = `
                <div class="wine-detection-message">
                    <p>We found <strong>${wineCount}</strong> wines in your menu files.</p>
                </div>
                <div class="checkbox-group">
                    <div class="checkbox-item">
                        <input type="checkbox" id="use-detected-wines" checked>
                        <label for="use-detected-wines">Use detected wines from menu files</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="add-wine-file">
                        <label for="add-wine-file">Add additional wine file</label>
                    </div>
                    <div id="wine-file-upload" style="display: none; margin-top: 15px;">
                        <input type="file" id="wine-file-input" accept=".pdf,.csv,.json,.xlsx" multiple>
                        <div id="wine-file-list" class="file-list"></div>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="use-knowledge-base">
                        <label for="use-knowledge-base">Use knowledge base wines</label>
                    </div>
                </div>
            `;

            // Handle checkbox changes
            document.getElementById('add-wine-file').addEventListener('change', (e) => {
                document.getElementById('wine-file-upload').style.display = e.target.checked ? 'block' : 'none';
            });

            document.getElementById('wine-file-input').addEventListener('change', (e) => {
                handleWineFiles(e.target.files);
            });
        } else {
            wineOptionsContent.innerHTML = `
                <div class="wine-detection-message">
                    <p>No wines were detected in your menu files.</p>
                </div>
                <div class="checkbox-group">
                    <div class="checkbox-item">
                        <input type="checkbox" id="add-wine-file">
                        <label for="add-wine-file">Add wine file</label>
                    </div>
                    <div id="wine-file-upload" style="display: none; margin-top: 15px;">
                        <input type="file" id="wine-file-input" accept=".pdf,.csv,.json,.xlsx" multiple>
                        <div id="wine-file-list" class="file-list"></div>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="use-knowledge-base">
                        <label for="use-knowledge-base">Use knowledge base wines</label>
                    </div>
                </div>
            `;

            // Handle checkbox changes
            document.getElementById('add-wine-file').addEventListener('change', (e) => {
                document.getElementById('wine-file-upload').style.display = e.target.checked ? 'block' : 'none';
            });

            document.getElementById('wine-file-input').addEventListener('change', (e) => {
                handleWineFiles(e.target.files);
            });
        }
    }

    updateBreadcrumb(['Home', 'Create Report', 'Wine Options']);
}

/**
 * Handle wine file selection
 */
function handleWineFiles(files) {
    const validation = validateFiles(files);
    const errorContainer = document.getElementById('wine-file-errors');
    
    if (!validation.valid) {
        displayValidationErrors('wine-file-errors', validation.errors);
    } else {
        clearValidationErrors('wine-file-errors');
    }

    validation.validFiles.forEach(file => {
        if (!reportState.wineFiles.find(f => f.name === file.name && f.size === file.size)) {
            reportState.wineFiles.push(file);
        }
    });

    updateWineFileList();
}

/**
 * Update wine file list
 */
function updateWineFileList() {
    const fileList = document.getElementById('wine-file-list');
    if (!fileList) return;

    fileList.innerHTML = '';

    reportState.wineFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-item-info">
                <div class="file-item-name">${file.name}</div>
                <div class="file-item-size">${formatFileSize(file.size)}</div>
            </div>
            <button class="file-item-remove" onclick="removeWineFile(${index})">Remove</button>
        `;
        fileList.appendChild(fileItem);
    });
}

/**
 * Remove wine file
 */
function removeWineFile(index) {
    reportState.wineFiles.splice(index, 1);
    updateWineFileList();
}

/**
 * Continue with wine processing
 */
async function continueWithWines() {
    // Get selected options
    const useDetected = document.getElementById('use-detected-wines')?.checked || false;
    const useKB = document.getElementById('use-knowledge-base')?.checked || false;
    const addFiles = document.getElementById('add-wine-file')?.checked || false;

    if (!useDetected && !useKB && !addFiles) {
        showToast('Please select at least one wine source', 'error');
        return;
    }

    if (addFiles && reportState.wineFiles.length === 0) {
        showToast('Please select wine files or uncheck "Add wine file"', 'error');
        return;
    }

    // Show loading
    showLoadingScreen('wine-processing');

    try {
        const progressTracker = getProgressTracker();
        if (progressTracker) {
            progressTracker.setSteps([
                'Processing wines',
                'Enriching with flavors',
                'Mapping compounds',
                'Complete'
            ]);
            progressTracker.reset();
        }

        // Process wines
        const wineOptions = {
            use_detected_wines: useDetected,
            use_knowledge_base: useKB,
            detected_wines: useDetected ? reportState.menuResult.extracted_wines : null,
            wine_files: addFiles ? reportState.wineFiles : []
        };

        const result = await processWines(wineOptions, (status) => {
            if (progressTracker) progressTracker.nextStep();
        });

        reportState.wineResult = result;

        // Continue with pairing
        await continueWithPairing();

    } catch (error) {
        hideLoadingScreen();
        showError('wine-error', handleApiError(error));
        showToast('Failed to process wines', 'error');
    }
}

/**
 * Continue with pairing process
 */
async function continueWithPairing() {
    try {
        const progressTracker = getProgressTracker();
        if (progressTracker) {
            progressTracker.setSteps([
                'Analyzing similarity',
                'Pairing wines to dishes',
                'Ranking wines',
                'Generating report',
                'Complete'
            ]);
            progressTracker.reset();
        }

        // Analyze similarity
        if (progressTracker) progressTracker.nextStep();
        const similarityResult = await analyzeSimilarity();
        reportState.similarPairs = similarityResult.similar_pairs;

        // Pair wines
        if (progressTracker) progressTracker.nextStep();
        const pairingResult = await pairWines();
        reportState.pairings = pairingResult.pairings;

        // Rank wines
        if (progressTracker) progressTracker.nextStep();
        const rankingResult = await rankWines();
        reportState.rankings = rankingResult.rankings;

        // Generate report
        if (progressTracker) progressTracker.nextStep();
        const reportResult = await generateReport('dict');
        reportState.report = reportResult.report;

        if (progressTracker) progressTracker.nextStep();

        // Navigate to preview
        setTimeout(() => {
            // Store report in sessionStorage for preview/report view
            sessionStorage.setItem('current_report', JSON.stringify(reportResult));
            window.location.href = 'report-preview.html';
        }, 1000);

    } catch (error) {
        hideLoadingScreen();
        showError('pairing-error', handleApiError(error));
        showToast('Failed to generate report', 'error');
    }
}

/**
 * Show loading screen with logo
 */
function showLoadingScreen(type) {
    const loadingContainer = document.getElementById('loading-container');
    if (!loadingContainer) return;

    loadingContainer.style.display = 'block';
    loadingContainer.innerHTML = `
        <div class="loading-container">
            <img src="assets/logo.png" alt="Logo" class="loading-logo">
            <div class="loading-spinner"></div>
            <div class="loading-text" id="loading-text">Processing...</div>
            <div id="loading-progress"></div>
        </div>
    `;

    // Hide other sections
    document.getElementById('file-upload-section').style.display = 'none';
    document.getElementById('wine-options-section').style.display = 'none';
}

/**
 * Hide loading screen
 */
function hideLoadingScreen() {
    const loadingContainer = document.getElementById('loading-container');
    if (loadingContainer) {
        loadingContainer.style.display = 'none';
    }
}

/**
 * Update breadcrumb navigation
 */
function updateBreadcrumb(items) {
    const breadcrumb = document.getElementById('breadcrumb');
    if (!breadcrumb) return;

    breadcrumb.innerHTML = items.map((item, index) => {
        if (index === items.length - 1) {
            return `<span class="breadcrumb-item active">${item}</span>`;
        } else {
            return `<a href="#" class="breadcrumb-item">${item}</a><span class="breadcrumb-separator"> > </span>`;
        }
    }).join('');
}

/**
 * Show error message
 */
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.textContent = message;
        container.style.display = 'block';
    }
}

/**
 * Show toast (from auth.js, but available here too)
 */
function showToast(message, type = 'success') {
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initReportCreation);
} else {
    initReportCreation();
}
