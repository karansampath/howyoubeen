/**
 * HowYouBeen Onboarding Frontend
 * Handles the multi-step onboarding process
 */

// Global state
let currentStep = 'start';
let sessionId = null;
let availablePlatforms = [];
let connectedPlatforms = new Set();
let uploadedFiles = [];

// API base URL
const API_BASE = '/api/onboarding';

/**
 * Initialize the onboarding interface
 */
document.addEventListener('DOMContentLoaded', function() {
    loadAvailablePlatforms();
});

/**
 * Show error message
 */
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

/**
 * Show success message in processing status
 */
function showProcessingStatus(message) {
    const statusDiv = document.getElementById('processing-status');
    statusDiv.innerHTML = `<p>${message}</p>`;
}

/**
 * Navigate to a specific step
 */
function goToStep(stepName) {
    // Hide current step
    const currentStepElement = document.querySelector('.step.active');
    if (currentStepElement) {
        currentStepElement.classList.remove('active');
    }
    
    // Show new step
    const newStepElement = document.getElementById(`step-${stepName}`);
    if (newStepElement) {
        newStepElement.classList.add('active');
        currentStep = stepName;
        
        // Update progress bar
        updateProgressBar(stepName);
    }
}

/**
 * Update progress bar
 */
function updateProgressBar(stepName) {
    const stepMap = {
        'start': 1,
        'basic-info': 2,
        'data-sources': 3,
        'visibility-config': 4,
        'processing': 5,
        'complete': 5
    };
    
    const stepNumber = stepMap[stepName] || 1;
    
    // Update progress steps
    for (let i = 1; i <= 5; i++) {
        const stepElement = document.getElementById(`step-${i}`);
        if (i < stepNumber) {
            stepElement.classList.add('completed');
            stepElement.classList.remove('active');
        } else if (i === stepNumber) {
            stepElement.classList.add('active');
            stepElement.classList.remove('completed');
        } else {
            stepElement.classList.remove('active', 'completed');
        }
    }
}

/**
 * Start the onboarding process
 */
async function startOnboarding() {
    try {
        const response = await fetch(`${API_BASE}/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            sessionId = data.session_id;
            goToStep('basic-info');
        } else {
            showError(data.detail || 'Failed to start onboarding');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

/**
 * Submit basic information
 */
async function submitBasicInfo() {
    const form = document.getElementById('basic-info-form');
    const formData = new FormData(form);
    
    const requestData = {
        session_id: sessionId,
        full_name: formData.get('full_name'),
        bio: formData.get('bio'),
        username: formData.get('username'),
        email: formData.get('email')
    };
    
    try {
        const response = await fetch(`${API_BASE}/basic-info`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            goToStep('data-sources');
        } else {
            showError(data.detail || 'Failed to save basic information');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

/**
 * Load available platforms
 */
async function loadAvailablePlatforms() {
    try {
        const response = await fetch(`${API_BASE}/available-platforms`);
        const data = await response.json();
        
        if (response.ok) {
            availablePlatforms = data.platforms;
            renderPlatformsGrid(data.platforms, data.descriptions);
        }
    } catch (error) {
        console.error('Failed to load platforms:', error);
    }
}

/**
 * Render platforms grid
 */
function renderPlatformsGrid(platforms, descriptions) {
    const grid = document.getElementById('platforms-grid');
    grid.innerHTML = '';
    
    platforms.forEach(platform => {
        const card = document.createElement('div');
        card.className = 'platform-card';
        card.innerHTML = `
            <h4>${platform.charAt(0).toUpperCase() + platform.slice(1)}</h4>
            <p>${descriptions[platform] || 'Connect your account'}</p>
            <button onclick="connectPlatform('${platform}')" class="btn-secondary">
                ${connectedPlatforms.has(platform) ? 'Connected ✓' : 'Connect'}
            </button>
        `;
        
        if (connectedPlatforms.has(platform)) {
            card.classList.add('connected');
        }
        
        grid.appendChild(card);
    });
}

/**
 * Connect to a platform
 */
async function connectPlatform(platform) {
    if (connectedPlatforms.has(platform)) {
        return; // Already connected
    }
    
    try {
        const response = await fetch(`${API_BASE}/data-source`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                platform: platform,
                credentials: {} // Mock credentials
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            connectedPlatforms.add(platform);
            // Re-render grid to show connected state
            loadAvailablePlatforms();
            showProcessingStatus(`Successfully connected to ${platform}`);
        } else {
            showError(data.detail || `Failed to connect to ${platform}`);
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

/**
 * Upload a file
 */
async function uploadFile() {
    const fileInput = document.getElementById('file-upload');
    const descriptionInput = document.getElementById('file-description');
    
    if (!fileInput.files.length) {
        showError('Please select a file to upload');
        return;
    }
    
    const file = fileInput.files[0];
    const description = descriptionInput.value;
    
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('description', description);
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/upload-document`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            uploadedFiles.push({
                filename: file.name,
                description: description,
                document_id: data.document_id
            });
            
            renderUploadedFiles();
            
            // Clear form
            fileInput.value = '';
            descriptionInput.value = '';
            
            showProcessingStatus(`Successfully uploaded ${file.name}`);
        } else {
            showError(data.detail || 'Failed to upload file');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

/**
 * Render uploaded files list
 */
function renderUploadedFiles() {
    const list = document.getElementById('uploaded-files-list');
    list.innerHTML = '';
    
    if (uploadedFiles.length === 0) {
        return;
    }
    
    const header = document.createElement('h4');
    header.textContent = 'Uploaded Files:';
    list.appendChild(header);
    
    uploadedFiles.forEach(file => {
        const fileDiv = document.createElement('div');
        fileDiv.className = 'uploaded-file';
        fileDiv.innerHTML = `
            <div>
                <strong>${file.filename}</strong>
                ${file.description ? `<br><small>${file.description}</small>` : ''}
            </div>
            <span style="color: #4CAF50;">✓</span>
        `;
        list.appendChild(fileDiv);
    });
}

/**
 * Submit visibility configuration
 */
async function submitVisibilityConfig() {
    const checkboxes = document.querySelectorAll('.visibility-categories input[type="checkbox"]:checked');
    const categories = [];
    
    checkboxes.forEach(checkbox => {
        categories.push({
            type: checkbox.value,
            name: checkbox.value === 'custom' ? 'Custom Category' : null
        });
    });
    
    if (categories.length === 0) {
        showError('Please select at least one visibility category');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/visibility-config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                categories: categories
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            goToStep('processing');
        } else {
            showError(data.detail || 'Failed to configure visibility settings');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

/**
 * Process user data
 */
async function processUserData() {
    const processBtn = document.getElementById('process-btn');
    processBtn.disabled = true;
    processBtn.textContent = 'Processing...';
    
    showProcessingStatus('Starting AI profile generation...');
    
    try {
        // Simulate processing steps
        setTimeout(() => showProcessingStatus('Analyzing uploaded documents...'), 1000);
        setTimeout(() => showProcessingStatus('Connecting to data sources...'), 2000);
        setTimeout(() => showProcessingStatus('Generating your AI personality...'), 3000);
        setTimeout(() => showProcessingStatus('Finalizing your profile...'), 4000);
        
        const response = await fetch(`${API_BASE}/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            displayCompletionResults(data);
            goToStep('complete');
        } else {
            showError(data.error || 'Failed to process user data');
            processBtn.disabled = false;
            processBtn.textContent = 'Retry Processing';
        }
    } catch (error) {
        showError('Network error: ' + error.message);
        processBtn.disabled = false;
        processBtn.textContent = 'Retry Processing';
    }
}

/**
 * Display completion results
 */
function displayCompletionResults(data) {
    const completionDiv = document.getElementById('completion-details');
    
    completionDiv.innerHTML = `
        <div class="completion-card">
            <h3>Your AI Profile is Ready!</h3>
            <p>Profile URL: <strong>${data.profile_url}</strong></p>
            <p>User ID: <strong>${data.user_id}</strong></p>
        </div>
        
        <div class="ai-summary">
            <h4>AI Generated Summary:</h4>
            <p style="font-style: italic; padding: 20px; background: #f9f9f9; border-radius: 8px; margin: 20px 0;">
                "${data.ai_summary}"
            </p>
        </div>
        
        <div class="next-steps">
            <h4>Next Steps:</h4>
            <ul>
                ${data.next_steps.map(step => `<li>${step}</li>`).join('')}
            </ul>
        </div>
        
        <div style="margin-top: 30px;">
            <button onclick="viewProfile('${data.user_id}')" class="btn-primary">View Your Profile</button>
            <button onclick="startOver()" class="btn-secondary" style="margin-left: 15px;">Start Over</button>
        </div>
    `;
}

/**
 * View profile
 */
async function viewProfile(userId) {
    try {
        const response = await fetch(`${API_BASE}/user/${userId}`);
        const data = await response.json();
        
        if (response.ok) {
            alert(`Profile Data:\\n\\nUsername: ${data.username}\\nName: ${data.full_name}\\nBio: ${data.bio}\\nDiary Entries: ${data.diary_entries_count}\\nFacts: ${data.facts_count}\\nSources: ${data.sources_count}`);
        } else {
            showError('Failed to load profile data');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

/**
 * Start over
 */
function startOver() {
    if (confirm('Are you sure you want to start over? This will reset all your progress.')) {
        // Reset state
        sessionId = null;
        connectedPlatforms.clear();
        uploadedFiles = [];
        
        // Reset form
        document.getElementById('basic-info-form').reset();
        document.getElementById('file-description').value = '';
        document.getElementById('file-upload').value = '';
        document.getElementById('uploaded-files-list').innerHTML = '';
        
        // Uncheck visibility options
        document.querySelectorAll('.visibility-categories input[type="checkbox"]').forEach(cb => {
            cb.checked = ['close-family', 'best-friends', 'good-friends'].includes(cb.id);
        });
        
        // Go back to start
        goToStep('start');
        
        // Reload platforms
        loadAvailablePlatforms();
    }
}