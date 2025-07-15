/**
 * Upload functionality with drag and drop support
 * Handles file selection, validation, and form submission
 */

document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const changeFileBtn = document.getElementById('changeFile');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadForm = document.getElementById('uploadForm');

    // Drag and drop functionality
    let dragCounter = 0;

    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });

    uploadArea.addEventListener('dragenter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dragCounter++;
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dragCounter--;
        if (dragCounter === 0) {
            uploadArea.classList.remove('dragover');
        }
    });

    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove('dragover');
        dragCounter = 0;

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    // File input change handler
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    // Change file button
    changeFileBtn.addEventListener('click', function() {
        clearFileSelection();
    });

    // Form submission handler
    uploadForm.addEventListener('submit', function(e) {
        if (!fileInput.files.length) {
            e.preventDefault();
            showAlert('Please select a file to upload.', 'error');
            return;
        }

        // Show loading state
        uploadBtn.classList.add('uploading');
        uploadBtn.disabled = true;

        // Show progress (simulated for better UX)
        showUploadProgress();
    });

    /**
     * Handle file selection and validation
     * @param {File} file - Selected file
     */
    function handleFileSelection(file) {
        // Validate file size (16MB limit)
        const maxSize = 16 * 1024 * 1024; // 16MB
        if (file.size > maxSize) {
            showAlert('File is too large. Maximum size is 16MB.', 'error');
            return;
        }

        // Validate file type
        const allowedTypes = [
            'text/plain', 'application/pdf',
            'image/png', 'image/jpeg', 'image/gif',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
            'application/x-tar', 'application/gzip',
            'audio/mpeg', 'video/mp4', 'video/x-msvideo', 'video/quicktime',
            'text/csv', 'application/json', 'application/xml'
        ];

        const allowedExtensions = [
            'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif',
            'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            'zip', 'rar', '7z', 'tar', 'gz',
            'mp3', 'mp4', 'avi', 'mov',
            'csv', 'json', 'xml'
        ];

        const fileExtension = file.name.split('.').pop().toLowerCase();
        
        if (!allowedExtensions.includes(fileExtension)) {
            showAlert('File type not supported. Please check the supported file types.', 'error');
            return;
        }

        // Update file display
        displayFileInfo(file);
        
        // Enable upload button
        uploadBtn.disabled = false;

        // Update fileInput
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
    }

    /**
     * Display file information
     * @param {File} file - Selected file
     */
    function displayFileInfo(file) {
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size) + ' • ' + file.type;
        
        fileInfo.style.display = 'block';
        uploadArea.style.display = 'none';
    }

    /**
     * Clear file selection
     */
    function clearFileSelection() {
        fileInput.value = '';
        fileInfo.style.display = 'none';
        uploadArea.style.display = 'block';
        uploadBtn.disabled = true;
        uploadBtn.classList.remove('uploading');
    }

    /**
     * Format file size for display
     * @param {number} bytes - File size in bytes
     * @returns {string} Formatted file size
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Show alert message
     * @param {string} message - Alert message
     * @param {string} type - Alert type (success, error, warning, info)
     */
    function showAlert(message, type = 'info') {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());

        // Create new alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            <i class="fas fa-${getAlertIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert alert
        const container = document.querySelector('.container');
        const header = container.querySelector('header');
        header.insertAdjacentElement('afterend', alertDiv);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    /**
     * Get icon for alert type
     * @param {string} type - Alert type
     * @returns {string} Font Awesome icon class
     */
    function getAlertIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-triangle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    /**
     * Show simulated upload progress
     */
    function showUploadProgress() {
        // This provides visual feedback during the actual server processing
        // The form will submit normally, but user sees the loading state
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress >= 90) {
                clearInterval(interval);
                // Let the actual form submission complete
                return;
            }
        }, 200);
    }

    /**
     * Handle paste events for file upload
     */
    document.addEventListener('paste', function(e) {
        const items = e.clipboardData.items;
        
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            
            if (item.kind === 'file') {
                e.preventDefault();
                const file = item.getAsFile();
                handleFileSelection(file);
                break;
            }
        }
    });

    /**
     * Keyboard accessibility
     */
    uploadArea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInput.click();
        }
    });

    // Make upload area focusable for accessibility
    uploadArea.setAttribute('tabindex', '0');
    uploadArea.setAttribute('role', 'button');
    uploadArea.setAttribute('aria-label', 'Click or drag files here to upload');

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});
