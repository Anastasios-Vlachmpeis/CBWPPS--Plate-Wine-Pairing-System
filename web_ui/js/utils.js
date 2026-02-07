/**
 * Utility functions
 * localStorage management, PDF generation, date formatting, etc.
 */

const STORAGE_KEY_REPORTS = 'culinary_expert_reports';
const STORAGE_KEY_USER = 'user';
const MAX_STORAGE_SIZE = 5 * 1024 * 1024; // 5MB (approximate localStorage limit is 5-10MB)

/**
 * localStorage Helpers
 */

/**
 * Get all saved reports
 */
function getSavedReports() {
    try {
        const reportsJson = localStorage.getItem(STORAGE_KEY_REPORTS);
        return reportsJson ? JSON.parse(reportsJson) : [];
    } catch (error) {
        console.error('Error loading reports:', error);
        return [];
    }
}

/**
 * Save report to localStorage
 */
function saveReport(report) {
    try {
        const reports = getSavedReports();
        
        // Add metadata
        const reportWithMeta = {
            ...report,
            id: report.id || generateId(),
            savedAt: new Date().toISOString(),
            savedAtFormatted: formatDate(new Date())
        };
        
        reports.push(reportWithMeta);
        
        // Check storage size
        const size = JSON.stringify(reports).length;
        if (size > MAX_STORAGE_SIZE * 0.9) {
            // Warn user if approaching limit
            if (!confirm('You are approaching the storage limit. Some old reports may need to be deleted. Continue?')) {
                return false;
            }
        }
        
        localStorage.setItem(STORAGE_KEY_REPORTS, JSON.stringify(reports));
        return true;
    } catch (error) {
        console.error('Error saving report:', error);
        if (error.name === 'QuotaExceededError') {
            alert('Storage limit exceeded. Please delete some old reports.');
        }
        return false;
    }
}

/**
 * Get report by ID
 */
function getReportById(id) {
    const reports = getSavedReports();
    return reports.find(r => r.id === id);
}

/**
 * Delete report by ID
 */
function deleteReport(id) {
    try {
        const reports = getSavedReports();
        const filtered = reports.filter(r => r.id !== id);
        localStorage.setItem(STORAGE_KEY_REPORTS, JSON.stringify(filtered));
        return true;
    } catch (error) {
        console.error('Error deleting report:', error);
        return false;
    }
}

/**
 * Update report
 */
function updateReport(id, updates) {
    try {
        const reports = getSavedReports();
        const index = reports.findIndex(r => r.id === id);
        if (index !== -1) {
            reports[index] = { ...reports[index], ...updates };
            localStorage.setItem(STORAGE_KEY_REPORTS, JSON.stringify(reports));
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error updating report:', error);
        return false;
    }
}

/**
 * Get storage usage
 */
function getStorageUsage() {
    try {
        let total = 0;
        for (let key in localStorage) {
            if (localStorage.hasOwnProperty(key)) {
                total += localStorage[key].length + key.length;
            }
        }
        return {
            used: total,
            available: MAX_STORAGE_SIZE - total,
            percentage: (total / MAX_STORAGE_SIZE) * 100
        };
    } catch (error) {
        return { used: 0, available: MAX_STORAGE_SIZE, percentage: 0 };
    }
}

/**
 * Clear old reports (keep most recent N)
 */
function clearOldReports(keepCount = 10) {
    try {
        const reports = getSavedReports();
        if (reports.length <= keepCount) return 0;
        
        // Sort by date (newest first)
        reports.sort((a, b) => new Date(b.savedAt) - new Date(a.savedAt));
        
        // Keep only most recent
        const toKeep = reports.slice(0, keepCount);
        localStorage.setItem(STORAGE_KEY_REPORTS, JSON.stringify(toKeep));
        
        return reports.length - keepCount;
    } catch (error) {
        console.error('Error clearing old reports:', error);
        return 0;
    }
}

/**
 * Date Formatting
 */

/**
 * Format date for display
 */
function formatDate(date) {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Generate unique ID
 */
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Confirmation Dialog Helpers
 */

/**
 * Show confirmation dialog
 */
function showConfirmation(message, onConfirm, onCancel) {
    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    
    overlay.innerHTML = `
        <div class="dialog">
            <div class="dialog-title">Confirm</div>
            <div class="dialog-message">${message}</div>
            <div class="dialog-actions">
                <button class="btn btn-secondary" id="confirm-cancel">Cancel</button>
                <button class="btn btn-primary" id="confirm-ok">OK</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    document.getElementById('confirm-ok').addEventListener('click', () => {
        overlay.remove();
        if (onConfirm) onConfirm();
    });
    
    document.getElementById('confirm-cancel').addEventListener('click', () => {
        overlay.remove();
        if (onCancel) onCancel();
    });
    
    // Close on overlay click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.remove();
            if (onCancel) onCancel();
        }
    });
}

/**
 * Tooltip Management
 */

/**
 * Create tooltip element
 */
function createTooltip(text) {
    const tooltip = document.createElement('span');
    tooltip.className = 'tooltip';
    tooltip.innerHTML = `
        <span class="tooltip-icon">?</span>
        <span class="tooltip-text">${text}</span>
    `;
    return tooltip;
}

/**
 * Empty State Helpers
 */

/**
 * Create empty state element
 */
function createEmptyState(icon, title, message, actionText = null, actionCallback = null) {
    const emptyState = document.createElement('div');
    emptyState.className = 'empty-state';
    
    let actionButton = '';
    if (actionText && actionCallback) {
        actionButton = `<button class="btn btn-primary" onclick="(${actionCallback.toString()})()">${actionText}</button>`;
    }
    
    emptyState.innerHTML = `
        <div class="empty-state-icon">${icon}</div>
        <div class="empty-state-title">${title}</div>
        <div class="empty-state-message">${message}</div>
        ${actionButton}
    `;
    
    return emptyState;
}

/**
 * PDF Generation using jsPDF
 */
async function generatePDF(report) {
    // Dynamically load jsPDF if not already loaded
    if (typeof window.jspdf === 'undefined') {
        await loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js');
    }
    
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    let yPos = 20;
    const pageHeight = doc.internal.pageSize.height;
    const margin = 20;
    const lineHeight = 7;
    
    // Helper to add new page if needed
    function checkNewPage(requiredSpace) {
        if (yPos + requiredSpace > pageHeight - margin) {
            doc.addPage();
            yPos = margin;
        }
    }
    
    // Title
    doc.setFontSize(20);
    doc.setFont(undefined, 'bold');
    doc.text('AI Culinary Expert - Wine Pairing Report', margin, yPos);
    yPos += lineHeight * 2;
    
    // Report metadata
    doc.setFontSize(12);
    doc.setFont(undefined, 'normal');
    if (report.report && report.report.timestamp) {
        doc.text(`Generated: ${formatDate(report.report.timestamp)}`, margin, yPos);
        yPos += lineHeight;
    }
    yPos += lineHeight;
    
    // Wine Rankings
    if (report.report && report.report.wine_rankings && report.report.wine_rankings.length > 0) {
        checkNewPage(lineHeight * 3);
        doc.setFontSize(16);
        doc.setFont(undefined, 'bold');
        doc.text('Wine Rankings', margin, yPos);
        yPos += lineHeight * 2;
        
        doc.setFontSize(10);
        doc.setFont(undefined, 'normal');
        
        // Table header
        doc.setFont(undefined, 'bold');
        doc.text('Rank', margin, yPos);
        doc.text('Wine Name', margin + 20, yPos);
        doc.text('Type', margin + 100, yPos);
        doc.text('Matches', margin + 140, yPos);
        doc.text('Score', margin + 170, yPos);
        yPos += lineHeight;
        doc.setFont(undefined, 'normal');
        
        // Table rows
        report.report.wine_rankings.slice(0, 50).forEach(ranking => {
            checkNewPage(lineHeight * 2);
            doc.text(ranking.rank.toString(), margin, yPos);
            doc.text(ranking.wine_name || 'Unknown', margin + 20, yPos);
            doc.text(ranking.type_name || 'Unknown', margin + 100, yPos);
            doc.text(ranking.dishes_matched.toString(), margin + 140, yPos);
            doc.text(ranking.score.toFixed(3), margin + 170, yPos);
            yPos += lineHeight;
        });
        yPos += lineHeight;
    }
    
    // Similar Wines
    if (report.report && report.report.wines_to_remove && report.report.wines_to_remove.length > 0) {
        checkNewPage(lineHeight * 3);
        doc.setFontSize(16);
        doc.setFont(undefined, 'bold');
        doc.text('Wines to Remove (Similar Wines)', margin, yPos);
        yPos += lineHeight * 2;
        
        doc.setFontSize(10);
        doc.setFont(undefined, 'normal');
        report.report.wines_to_remove.forEach(wine => {
            checkNewPage(lineHeight * 2);
            doc.text(`${wine.wine_name} (${wine.type_name}) - ${wine.reason}`, margin, yPos);
            yPos += lineHeight;
        });
        yPos += lineHeight;
    }
    
    // Dish Pairings
    if (report.report && report.report.dish_pairings) {
        const pairings = Object.values(report.report.dish_pairings);
        if (pairings.length > 0) {
            checkNewPage(lineHeight * 3);
            doc.setFontSize(16);
            doc.setFont(undefined, 'bold');
            doc.text('Dish-Wine Pairings', margin, yPos);
            yPos += lineHeight * 2;
            
            doc.setFontSize(10);
            doc.setFont(undefined, 'normal');
            
            pairings.forEach(pairing => {
                checkNewPage(lineHeight * 8);
                doc.setFont(undefined, 'bold');
                doc.text(pairing.dish_name, margin, yPos);
                yPos += lineHeight;
                
                if (pairing.best_wine) {
                    doc.setFont(undefined, 'normal');
                    doc.text(`Best Wine: ${pairing.best_wine.wine_name} (${pairing.best_wine.type_name})`, margin + 5, yPos);
                    yPos += lineHeight;
                    
                    if (pairing.sommelier_explanation) {
                        const explanation = doc.splitTextToSize(pairing.sommelier_explanation, 170);
                        doc.text(explanation, margin + 5, yPos);
                        yPos += lineHeight * explanation.length;
                    }
                    
                    if (pairing.scientific_analysis) {
                        doc.text(`Pairing Score: ${pairing.scientific_analysis.pairing_score.toFixed(3)}`, margin + 5, yPos);
                        yPos += lineHeight;
                        doc.text(`Shared Compounds: ${pairing.scientific_analysis.shared_compounds_count}`, margin + 5, yPos);
                        yPos += lineHeight;
                    }
                }
                yPos += lineHeight;
            });
        }
    }
    
    // Save PDF
    const filename = `wine_pairing_report_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(filename);
}

/**
 * Load external script
 */
function loadScript(src) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}
