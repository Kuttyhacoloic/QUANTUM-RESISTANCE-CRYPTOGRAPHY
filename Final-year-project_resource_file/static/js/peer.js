/**
 * QuantumFTP functionality for send/receive operations
 */

document.addEventListener('DOMContentLoaded', function() {
    // Mode switching
    const encryptMode = document.getElementById('encrypt-mode');
    const sendMode = document.getElementById('send-mode');
    const receiveMode = document.getElementById('receive-mode');
    
    const encryptSection = document.getElementById('encrypt-section');
    const sendSection = document.getElementById('send-section');
    const receiveSection = document.getElementById('receive-section');
    
    // Send form elements
    const sendUploadArea = document.getElementById('sendUploadArea');
    const sendFileInput = document.getElementById('sendFileInput');
    const sendFileInfo = document.getElementById('sendFileInfo');
    const sendFileName = document.getElementById('sendFileName');
    const sendFileSize = document.getElementById('sendFileSize');
    const changeSendFile = document.getElementById('changeSendFile');
    const sendBtn = document.getElementById('sendBtn');
    const sendForm = document.getElementById('sendForm');
    
    // Mode change handlers
    encryptMode.addEventListener('change', function() {
        if (this.checked) {
            encryptSection.style.display = 'block';
            sendSection.style.display = 'none';
            receiveSection.style.display = 'none';
        }
    });
    
    sendMode.addEventListener('change', function() {
        if (this.checked) {
            encryptSection.style.display = 'none';
            sendSection.style.display = 'block';
            receiveSection.style.display = 'none';
            checkPeerStatus();
        }
    });
    
    receiveMode.addEventListener('change', function() {
        if (this.checked) {
            encryptSection.style.display = 'none';
            sendSection.style.display = 'none';
            receiveSection.style.display = 'block';
            loadReceivedFiles();
        }
    });
    
    // Send file upload handlers
    if (sendUploadArea) {
        let dragCounter = 0;
        
        sendUploadArea.addEventListener('click', function() {
            sendFileInput.click();
        });
        
        sendUploadArea.addEventListener('dragenter', function(e) {
            e.preventDefault();
            e.stopPropagation();
            dragCounter++;
            sendUploadArea.classList.add('dragover');
        });
        
        sendUploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            dragCounter--;
            if (dragCounter === 0) {
                sendUploadArea.classList.remove('dragover');
            }
        });
        
        sendUploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
        });
        
        sendUploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            sendUploadArea.classList.remove('dragover');
            dragCounter = 0;
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleSendFileSelection(files[0]);
            }
        });
        
        sendFileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                handleSendFileSelection(e.target.files[0]);
            }
        });
        
        changeSendFile.addEventListener('click', function() {
            clearSendFileSelection();
        });
        
        sendForm.addEventListener('submit', function(e) {
            if (!sendFileInput.files.length) {
                e.preventDefault();
                showAlert('Please select a file to send.', 'error');
                return;
            }
            
            // Show loading state
            sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending...';
            sendBtn.disabled = true;
        });
    }
    
    /**
     * Handle file selection for sending
     */
    function handleSendFileSelection(file) {
        // Validate file size (16MB limit)
        const maxSize = 16 * 1024 * 1024;
        if (file.size > maxSize) {
            showAlert('File is too large. Maximum size is 16MB.', 'error');
            return;
        }
        
        // Update file display
        sendFileName.textContent = file.name;
        sendFileSize.textContent = formatFileSize(file.size) + ' • ' + file.type;
        
        sendFileInfo.style.display = 'block';
        sendUploadArea.style.display = 'none';
        sendBtn.disabled = false;
        
        // Update file input
        const dt = new DataTransfer();
        dt.items.add(file);
        sendFileInput.files = dt.files;
    }
    
    /**
     * Clear send file selection
     */
    function clearSendFileSelection() {
        sendFileInput.value = '';
        sendFileInfo.style.display = 'none';
        sendUploadArea.style.display = 'block';
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<i class="fas fa-share me-2"></i>Send File to Peer';
    }
    
    /**
     * Check peer server status
     */
    function checkPeerStatus() {
        const statusDiv = document.getElementById('peer-status');
        
        fetch('/peer-status')
            .then(response => response.json())
            .then(data => {
                if (data.server_running) {
                    statusDiv.innerHTML = `
                        <div class="d-flex align-items-center text-success">
                            <i class="fas fa-check-circle me-2"></i>
                            <div>
                                <div>Server running on port ${data.port}</div>
                                <small class="text-muted">${data.message}</small>
                            </div>
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = `
                        <div class="d-flex align-items-center text-danger">
                            <i class="fas fa-times-circle me-2"></i>
                            <div>
                                <div>Server not running</div>
                                <small class="text-muted">${data.message}</small>
                            </div>
                        </div>
                    `;
                }
            })
            .catch(error => {
                statusDiv.innerHTML = `
                    <div class="d-flex align-items-center text-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <div>Unable to check server status</div>
                    </div>
                `;
            });
    }
    
    /**
     * Load received files
     */
    function loadReceivedFiles() {
        const listDiv = document.getElementById('received-files-list');
        
        fetch('/received-files')
            .then(response => response.text())
            .then(html => {
                // Extract just the file list content
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const content = doc.querySelector('.card-body');
                
                if (content) {
                    listDiv.innerHTML = content.innerHTML;
                } else {
                    listDiv.innerHTML = '<p class="text-muted">No received files found.</p>';
                }
            })
            .catch(error => {
                listDiv.innerHTML = '<p class="text-danger">Error loading received files.</p>';
            });
    }
    
    /**
     * Format file size for display
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
});