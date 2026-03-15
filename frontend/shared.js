// Generic modal management
function setupModal(modalId, toggleBtnId, closeBtnId, cancelBtnId) {
    const modal = document.getElementById(modalId);
    const toggleBtn = document.getElementById(toggleBtnId);
    const closeBtn = document.getElementById(closeBtnId);
    const cancelBtn = document.getElementById(cancelBtnId);

    if (!modal || !toggleBtn) return;

    // Open modal
    toggleBtn.addEventListener('click', () => {
        modal.style.display = 'block';
    });

    // Close modal
    const closeModal = () => {
        modal.style.display = 'none';
    };

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

    // Close when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });
}

// Initialize Lucide icons if available
if (typeof lucide !== 'undefined') {
    lucide.createIcons();
}
