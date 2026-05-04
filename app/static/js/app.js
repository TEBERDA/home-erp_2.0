// Toast notification system
function showToast(title, message, type = 'primary') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast show mb-2" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <span class="status-dot bg-${type} me-2"></span>
                <strong class="me-auto">${title}</strong>
                <small>Just now</small>
                <button type="button" class="ms-2 btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toastElement) {
            toastElement.classList.remove('show');
            setTimeout(() => toastElement.remove(), 500);
        }
    }, 5000);
}

// Global HTMX error handler
document.body.addEventListener('htmx:responseError', function(evt) {
    showToast('Error', evt.detail.xhr.responseText || 'Something went wrong', 'danger');
});

// Global success handler for specific actions
document.body.addEventListener('htmx:afterOnLoad', function(evt) {
    if (evt.detail.xhr.status >= 200 && evt.detail.xhr.status < 300) {
        // You can add logic here to show toasts based on response headers
    }
});
