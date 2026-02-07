/**
 * File validation utilities
 * Validates file types, sizes, and provides error messages
 */

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.jpg', '.jpeg', '.png', '.xlsx', '.csv', '.json'];

/**
 * Get file extension from filename
 */
function getFileExtension(filename) {
    const parts = filename.split('.');
    return parts.length > 1 ? '.' + parts[parts.length - 1].toLowerCase() : '';
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Validate single file
 * Returns {valid: boolean, error: string|null, file: File}
 */
function validateFile(file) {
    // Check if file exists
    if (!file) {
        return {
            valid: false,
            error: 'No file provided',
            file: null
        };
    }

    // Check file extension
    const extension = getFileExtension(file.name);
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
        return {
            valid: false,
            error: `File type ${extension} is not supported. Allowed types: ${ALLOWED_EXTENSIONS.join(', ')}`,
            file: file
        };
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
        return {
            valid: false,
            error: `File ${file.name} exceeds maximum size of ${formatFileSize(MAX_FILE_SIZE)}`,
            file: file
        };
    }

    if (file.size === 0) {
        return {
            valid: false,
            error: `File ${file.name} is empty`,
            file: file
        };
    }

    return {
        valid: true,
        error: null,
        file: file
    };
}

/**
 * Validate multiple files
 * Returns {valid: boolean, errors: Array, validFiles: Array}
 */
function validateFiles(files) {
    const errors = [];
    const validFiles = [];

    if (!files || files.length === 0) {
        return {
            valid: false,
            errors: ['No files selected'],
            validFiles: []
        };
    }

    for (let i = 0; i < files.length; i++) {
        const validation = validateFile(files[i]);
        if (validation.valid) {
            validFiles.push(validation.file);
        } else {
            errors.push({
                filename: files[i].name,
                error: validation.error
            });
        }
    }

    return {
        valid: errors.length === 0,
        errors: errors,
        validFiles: validFiles
    };
}

/**
 * Display validation errors
 */
function displayValidationErrors(containerId, errors) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Clear existing errors
    container.innerHTML = '';

    if (errors.length === 0) return;

    errors.forEach(error => {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'file-error';
        errorDiv.textContent = `${error.filename || 'File'}: ${error.error}`;
        container.appendChild(errorDiv);
    });
}

/**
 * Clear validation errors
 */
function clearValidationErrors(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
    }
}
