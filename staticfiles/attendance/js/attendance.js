// Attendance Check-in/out JavaScript functionality

// Global variables
let isCheckedIn = false;
let commentsEnabled = false;

// DOM elements
const statusIndicator = document.getElementById('statusIndicator');
const statusIcon = document.getElementById('statusIcon');
const statusText = document.getElementById('statusText');
const statusSubtext = document.getElementById('statusSubtext');
const actionBtn = document.getElementById('actionBtn');
const btnText = document.getElementById('btnText');
const commentsToggle = document.getElementById('commentsToggle');
const commentsSection = document.getElementById('commentsSection');

// Time and date functionality
function updateDateTime() {
    const now = new Date();
    
    const timeOptions = {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    };
    
    const dateOptions = {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    
    const timeElement = document.getElementById('currentTime');
    const dateElement = document.getElementById('currentDate');
    
    if (timeElement) {
        timeElement.textContent = now.toLocaleTimeString('en-US', timeOptions);
    }
    if (dateElement) {
        dateElement.textContent = now.toLocaleDateString('en-US', dateOptions);
    }
}

// Update attendance status display
function updateAttendanceStatus() {
    const btnIcon = actionBtn.querySelector('i');
    
    if (isCheckedIn) {
        statusIndicator.className = 'status-indicator status-checked-in pulse';
        statusIcon.className = 'fas fa-sign-out-alt status-icon';
        statusText.textContent = 'Currently Checked In';
        statusSubtext.textContent = 'You are currently at work. Click to check out.';
        btnText.textContent = 'Check Out';
        btnIcon.className = 'fas fa-sign-out-alt me-2';
        actionBtn.style.background = 'var(--danger-gradient)';
    } else {
        statusIndicator.className = 'status-indicator status-checked-out pulse';
        statusIcon.className = 'fas fa-sign-in-alt status-icon';
        statusText.textContent = 'Ready to Check In';
        statusSubtext.textContent = 'Click the button below to record your attendance';
        btnText.textContent = 'Check In';
        btnIcon.className = 'fas fa-sign-in-alt me-2';
        actionBtn.style.background = 'var(--primary-gradient)';
    }
}

// Show notification message
function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'position-fixed top-0 start-50 translate-middle-x mt-3';
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        <div class="alert alert-success alert-dismissible fade show shadow-lg" role="alert" style="border-radius: 16px; backdrop-filter: blur(10px);">
            <i class="fas fa-check-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

// Initialize functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Update time every second
    updateDateTime();
    setInterval(updateDateTime, 1000);
    
    // Initialize status
    updateAttendanceStatus();
    
    // Comments section toggle
    if (commentsToggle) {
        commentsToggle.addEventListener('click', function() {
            commentsEnabled = !commentsEnabled;
            
            if (commentsEnabled) {
                commentsSection.classList.add('active');
                commentsToggle.classList.add('active');
                commentsToggle.innerHTML = '<i class="fas fa-comment-slash me-2"></i>Hide Comments';
            } else {
                commentsSection.classList.remove('active');
                commentsToggle.classList.remove('active');
                commentsToggle.innerHTML = '<i class="fas fa-comment me-2"></i>Add Comments';
                const commentsField = document.getElementById('comments');
                if (commentsField) {
                    commentsField.value = '';
                }
            }
        });
    }
    
    // Status indicator click animation
    if (statusIndicator) {
        statusIndicator.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    }
    
    // Form submission
    const attendanceForm = document.getElementById('attendanceForm');
    if (attendanceForm) {
        attendanceForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Add loading animation
            actionBtn.disabled = true;
            actionBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            
            // Get comments if enabled
            const commentsField = document.getElementById('comments');
            const hiddenCommentsField = document.getElementById('hiddenComments');
            const comments = commentsEnabled && commentsField ? commentsField.value : '';
            
            if (hiddenCommentsField) {
                hiddenCommentsField.value = comments;
            }
            
            // Simulate processing time
            setTimeout(() => {
                isCheckedIn = !isCheckedIn;
                updateAttendanceStatus();
                
                // Show success message
                showNotification(isCheckedIn ? 'Successfully checked in!' : 'Successfully checked out!');
                
                // Reset button
                actionBtn.disabled = false;
                
                // Clear comments if used
                if (commentsEnabled && commentsField) {
                    commentsField.value = '';
                }
                
                // Remove pulse animation temporarily
                statusIndicator.classList.remove('pulse');
                setTimeout(() => {
                    statusIndicator.classList.add('pulse');
                }, 1000);
                
                // For actual Django integration, uncomment the line below:
                // this.submit(); // This will actually submit the form to Django
                
            }, 1500);
        });
    }
    
    // Add interactive hover effects for action button
    if (actionBtn) {
        actionBtn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) scale(1.02)';
        });

        actionBtn.addEventListener('mouseleave', function() {
            if (!this.disabled) {
                this.style.transform = 'translateY(0) scale(1)';
            }
        });
    }
    
    // Keyboard accessibility
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.ctrlKey && attendanceForm) {
            attendanceForm.dispatchEvent(new Event('submit'));
        }
    });
});

// Utility functions for external use
window.AttendanceUtils = {
    // Set initial check-in status
    setInitialStatus: function(checkedIn) {
        isCheckedIn = checkedIn;
        updateAttendanceStatus();
    },
    
    // Get current status
    getCurrentStatus: function() {
        return isCheckedIn;
    },
    
    // Programmatically toggle comments
    toggleComments: function(show) {
        if (show !== undefined) {
            commentsEnabled = show;
        } else {
            commentsEnabled = !commentsEnabled;
        }
        
        if (commentsToggle) {
            commentsToggle.click();
        }
    },
    
    // Show custom notification
    showNotification: showNotification
};