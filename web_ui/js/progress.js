/**
 * Progress tracking and indicators
 * Manages step-by-step progress display and cancel functionality
 */

/**
 * Progress tracker class
 */
class ProgressTracker {
    constructor(totalSteps) {
        this.totalSteps = totalSteps;
        this.currentStep = 0;
        this.steps = [];
        this.cancelled = false;
        this.onCancelCallback = null;
    }

    /**
     * Initialize progress display
     */
    initialize(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        // Create progress UI
        this.container.innerHTML = this.createProgressHTML();
        this.updateDisplay();
    }

    /**
     * Create progress HTML structure
     */
    createProgressHTML() {
        return `
            <div class="progress-container">
                <div class="progress-steps" id="progress-steps"></div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
                </div>
                <div class="progress-text" id="progress-text">Starting...</div>
                <button class="btn btn-secondary" id="cancel-button" onclick="progressTracker.cancel()" style="margin-top: 20px;">
                    Cancel
                </button>
            </div>
        `;
    }

    /**
     * Define steps
     */
    setSteps(steps) {
        this.steps = steps;
        this.totalSteps = steps.length;
        this.updateDisplay();
    }

    /**
     * Update to next step
     */
    nextStep(stepName = null) {
        if (this.cancelled) return;
        
        this.currentStep++;
        if (stepName && this.currentStep <= this.steps.length) {
            this.steps[this.currentStep - 1] = stepName;
        }
        this.updateDisplay();
    }

    /**
     * Set current step by name
     */
    setStep(stepName) {
        const stepIndex = this.steps.findIndex(s => s === stepName);
        if (stepIndex !== -1) {
            this.currentStep = stepIndex + 1;
            this.updateDisplay();
        }
    }

    /**
     * Update progress display
     */
    updateDisplay() {
        if (!this.container) return;

        const stepsContainer = document.getElementById('progress-steps');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');

        if (!stepsContainer || !progressFill || !progressText) return;

        // Update steps
        stepsContainer.innerHTML = '';
        for (let i = 0; i < this.totalSteps; i++) {
            const stepDiv = document.createElement('div');
            stepDiv.className = 'progress-step';
            
            if (i < this.currentStep) {
                stepDiv.classList.add('completed');
            } else if (i === this.currentStep - 1) {
                stepDiv.classList.add('active');
            }

            const indicator = document.createElement('div');
            indicator.className = 'step-indicator';
            indicator.textContent = i < this.currentStep ? '✓' : (i + 1);
            stepDiv.appendChild(indicator);

            const label = document.createElement('div');
            label.className = 'step-label';
            label.textContent = this.steps[i] || `Step ${i + 1}`;
            stepDiv.appendChild(label);

            stepsContainer.appendChild(stepDiv);
        }

        // Update progress bar
        const percentage = (this.currentStep / this.totalSteps) * 100;
        progressFill.style.width = `${percentage}%`;

        // Update progress text
        if (this.currentStep > 0 && this.currentStep <= this.steps.length) {
            progressText.textContent = `Step ${this.currentStep} of ${this.totalSteps}: ${this.steps[this.currentStep - 1]}`;
        } else if (this.currentStep >= this.totalSteps) {
            progressText.textContent = 'Complete!';
        } else {
            progressText.textContent = 'Starting...';
        }
    }

    /**
     * Cancel processing
     */
    cancel() {
        if (confirm('Are you sure you want to cancel? All progress will be lost.')) {
            this.cancelled = true;
            if (this.onCancelCallback) {
                this.onCancelCallback();
            }
            this.showCancelled();
        }
    }

    /**
     * Show cancelled state
     */
    showCancelled() {
        const progressText = document.getElementById('progress-text');
        if (progressText) {
            progressText.textContent = 'Cancelled';
            progressText.style.color = 'var(--error-red)';
        }
    }

    /**
     * Set cancel callback
     */
    onCancel(callback) {
        this.onCancelCallback = callback;
    }

    /**
     * Reset progress
     */
    reset() {
        this.currentStep = 0;
        this.cancelled = false;
        this.updateDisplay();
    }

    /**
     * Check if cancelled
     */
    isCancelled() {
        return this.cancelled;
    }
}

// Global progress tracker instance
let progressTracker = null;

/**
 * Initialize progress tracker
 */
function initProgressTracker(totalSteps, containerId) {
    progressTracker = new ProgressTracker(totalSteps);
    progressTracker.initialize(containerId);
    return progressTracker;
}

/**
 * Get current progress tracker
 */
function getProgressTracker() {
    return progressTracker;
}
