// Main JavaScript for AI Student Web Application

// Global variables
let currentStep = 0;
const loadingSteps = [
    'Extracting subtitles',
    'Generating timestamps', 
    'AI summarization'
];

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Add smooth scrolling to all internal links
    addSmoothScrolling();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Add loading step animations
    initializeLoadingSteps();
    
    // Add hover effects
    addHoverEffects();
}

// Smooth scrolling for internal links
function addSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Form validation
function initializeFormValidation() {
    const form = document.getElementById('video-form');
    if (form) {
        const input = document.getElementById('video-url');
        
        input.addEventListener('input', function() {
            validateYouTubeUrl(this.value);
        });
        
        input.addEventListener('blur', function() {
            validateYouTubeUrl(this.value);
        });
    }
}

function validateYouTubeUrl(url) {
    const input = document.getElementById('video-url');
    const patterns = [
        /^(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=[\w-]+/,
        /^(?:https?:\/\/)?youtu\.be\/[\w-]+/,
        /^(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/[\w-]+/
    ];
    
    const isValid = patterns.some(pattern => pattern.test(url));
    
    if (url && !isValid) {
        input.classList.add('error');
        showInputError('Please enter a valid YouTube URL');
    } else {
        input.classList.remove('error');
        hideInputError();
    }
    
    return isValid;
}

function showInputError(message) {
    let errorDiv = document.querySelector('.input-error');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'input-error';
        errorDiv.style.cssText = `
            color: var(--error-color);
            font-size: var(--font-size-sm);
            margin-top: var(--spacing-xs);
            display: flex;
            align-items: center;
            gap: var(--spacing-xs);
        `;
        document.getElementById('video-url').parentNode.appendChild(errorDiv);
    }
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i>${message}`;
}

function hideInputError() {
    const errorDiv = document.querySelector('.input-error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Loading steps animation
function initializeLoadingSteps() {
    const steps = document.querySelectorAll('.loading-steps .step');
    if (steps.length > 0) {
        steps.forEach((step, index) => {
            step.addEventListener('animationend', () => {
                if (index < steps.length - 1) {
                    setTimeout(() => {
                        steps[index + 1].classList.add('active');
                    }, 1000);
                }
            });
        });
    }
}

// Hover effects
function addHoverEffects() {
    // Add hover effects to cards
    document.querySelectorAll('.feature-card, .stat-card, .timestamp-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Show loading overlay
function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'flex';
        startLoadingAnimation();
    }
}

// Hide loading overlay
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
        resetLoadingSteps();
    }
}

// Start loading animation
function startLoadingAnimation() {
    const steps = document.querySelectorAll('.loading-steps .step');
    currentStep = 0;
    
    steps.forEach((step, index) => {
        step.classList.remove('active');
        if (index === 0) {
            setTimeout(() => {
                step.classList.add('active');
            }, 500);
        }
    });
}

// Reset loading steps
function resetLoadingSteps() {
    const steps = document.querySelectorAll('.loading-steps .step');
    steps.forEach(step => {
        step.classList.remove('active');
    });
    currentStep = 0;
}

// Show error modal
function showError(message, suggestions = []) {
    const modal = document.getElementById('error-modal');
    const messageEl = document.getElementById('error-message');
    const suggestionsEl = document.getElementById('error-suggestions');
    
    if (modal && messageEl) {
        messageEl.textContent = message;
        
        // Clear previous suggestions
        suggestionsEl.innerHTML = '';
        
        // Add suggestions if provided
        if (suggestions && suggestions.length > 0) {
            const suggestionsList = document.createElement('ul');
            suggestionsList.style.cssText = `
                list-style: none;
                padding: 0;
                margin-top: var(--spacing-md);
            `;
            
            suggestions.forEach(suggestion => {
                const li = document.createElement('li');
                li.textContent = suggestion;
                li.style.cssText = `
                    color: var(--text-secondary);
                    padding: var(--spacing-xs) 0;
                    border-left: 2px solid var(--success-color);
                    padding-left: var(--spacing-md);
                    margin-bottom: var(--spacing-xs);
                `;
                suggestionsList.appendChild(li);
            });
            
            suggestionsEl.appendChild(suggestionsList);
        }
        
        modal.style.display = 'flex';
    }
}

// Close modal
function closeModal() {
    const modal = document.getElementById('error-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Download PDF function
function downloadPDF(filename) {
    const btn = event.target.closest('button');
    const originalText = btn.innerHTML;
    
    // Show loading state
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating PDF...';
    btn.disabled = true;
    
    // Make download request
    fetch(`/download/${filename}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        } else {
            throw new Error('PDF generation failed');
        }
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Show success message
        showSuccessMessage('PDF downloaded successfully!');
    })
    .catch(error => {
        console.error('Download error:', error);
        showError('Failed to download PDF. Please try again.');
    })
    .finally(() => {
        // Restore button
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
}

// Show success message
function showSuccessMessage(message) {
    // Create success notification
    const notification = document.createElement('div');
    notification.className = 'success-notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--success-color);
        color: var(--text-primary);
        padding: var(--spacing-md) var(--spacing-lg);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-md);
        z-index: 1001;
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        animation: slideInRight 0.3s ease-out;
    `;
    
    notification.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Scroll to section
function scrollToSection(sectionNumber) {
    const section = document.getElementById(`section-${sectionNumber}`);
    if (section) {
        section.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
        
        // Add highlight effect
        section.classList.add('highlighted');
        setTimeout(() => {
            section.classList.remove('highlighted');
        }, 2000);
    }
}

// Utility function to format time
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

// Utility function to truncate text
function truncateText(text, maxLength = 100) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .input-error {
        animation: fadeIn 0.3s ease-out;
    }
    
    .highlighted {
        animation: pulse 2s ease-out;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 212, 170, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(0, 212, 170, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 212, 170, 0); }
    }
`;
document.head.appendChild(style);

// Export functions for use in templates
window.AIStudent = {
    showLoading,
    hideLoading,
    showError,
    closeModal,
    downloadPDF,
    scrollToSection,
    formatTime,
    truncateText
}; 