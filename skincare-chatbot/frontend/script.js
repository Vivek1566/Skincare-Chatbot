// ============================================================================
// GLOW.AI - Advanced Skincare Detection Frontend
// Improved with multi-condition detection and enhanced chatbot
// ============================================================================

const API_BASE = window.location.origin.includes('file:') 
    ? 'http://127.0.0.1:5000' 
    : `${window.location.protocol}//${window.location.hostname}:5000`;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadContent = document.getElementById('uploadContent');
const previewContainer = document.getElementById('previewContainer');
const imagePreview = document.getElementById('imagePreview');
const removeBtn = document.getElementById('removeBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const btnLoader = document.getElementById('btnLoader');
const resultsContainer = document.getElementById('resultsContainer');

// Chatbot elements
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendChatBtn = document.getElementById('sendChatBtn');
const quickPrompts = document.querySelectorAll('.quick-prompt-btn');

// State
let selectedFile = null;
let lastDetectionData = null;

// ============================================================================
// FILE UPLOAD HANDLERS
// ============================================================================

uploadArea.addEventListener('click', (e) => {
    if (e.target !== removeBtn) {
        fileInput.click();
    }
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

removeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    resetUpload();
});

function handleFile(file) {
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif', 'image/bmp'];
    
    if (!validTypes.includes(file.type)) {
        showError('Please upload a valid image file (JPG, PNG, GIF, BMP).');
        return;
    }
    
    if (file.size > 16 * 1024 * 1024) {
        showError('File size exceeds 16MB limit.');
        return;
    }

    selectedFile = file;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        uploadContent.style.display = 'none';
        previewContainer.style.display = 'flex';
        analyzeBtn.disabled = false;
        resultsContainer.style.display = 'none';
    };
    reader.readAsDataURL(file);
}

function resetUpload() {
    selectedFile = null;
    fileInput.value = '';
    imagePreview.src = '';
    previewContainer.style.display = 'none';
    uploadContent.style.display = 'block';
    analyzeBtn.disabled = true;
    resultsContainer.style.display = 'none';
}

// ============================================================================
// ANALYSIS & DETECTION
// ============================================================================

analyzeBtn.addEventListener('click', analyzeImage);

async function analyzeImage() {
    if (!selectedFile) return;

    analyzeBtn.disabled = true;
    btnLoader.style.display = 'flex';
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    const skinType = document.getElementById('skin_type')?.value || 'auto';
    if (skinType !== 'auto') {
        formData.append('skin_type', skinType);
    }

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
        } else {
            lastDetectionData = data;
            displayResults(data);
        }
    } catch (error) {
        console.error('Analysis error:', error);
        showError(`Analysis failed: ${error.message}`);
    } finally {
        analyzeBtn.disabled = false;
        btnLoader.style.display = 'none';
    }
}

function displayResults(data) {
    resultsContainer.style.display = 'block';
    
    // Display skin type
    const skinTypeEl = document.getElementById('skinTypeResult');
    const skinTypeConfEl = document.getElementById('skinTypeConfidenceText');
    const skinTypeFillEl = document.getElementById('skinTypeConfidenceFill');
    
    if (skinTypeEl && data.skin_type) {
        skinTypeEl.textContent = data.skin_type;
        const confidence = (data.skin_type_confidence * 100).toFixed(1);
        if (skinTypeConfEl) skinTypeConfEl.textContent = `${confidence}%`;
        if (skinTypeFillEl) skinTypeFillEl.style.width = `${confidence}%`;
    }

    // Display all detected conditions
    const conditionsContainer = document.getElementById('conditionsList');
    if (conditionsContainer && data.all_conditions) {
        conditionsContainer.innerHTML = '';
        data.all_conditions.forEach((cond, index) => {
            const conditionDiv = document.createElement('div');
            conditionDiv.className = 'condition-item';
            conditionDiv.innerHTML = `
                <div class="condition-header">
                    <span class="condition-name">${cond.condition}</span>
                    <span class="condition-percent">${cond.percentage}%</span>
                </div>
                <div class="condition-bar">
                    <div class="condition-fill" style="width: ${cond.percentage}%; animation-delay: ${index * 0.1}s;"></div>
                </div>
            `;
            conditionsContainer.appendChild(conditionDiv);
        });
    }

    // Display detected issues if any
    const issuesCard = document.getElementById('issuesCard');
    const issuesList = document.getElementById('issuesList');
    if (data.detected_issues && data.detected_issues.length > 0) {
        if (issuesCard) issuesCard.style.display = 'block';
        if (issuesList) {
            issuesList.innerHTML = '';
            data.detected_issues.forEach((issue, index) => {
                const issueDiv = document.createElement('div');
                issueDiv.className = 'issue-item';
                issueDiv.innerHTML = `
                    <div class="issue-header">
                        <span class="issue-name">${issue.issue}</span>
                        <span class="issue-percent">${issue.percentage}%</span>
                    </div>
                    <div class="issue-bar">
                        <div class="issue-fill" style="width: ${issue.percentage}%; animation-delay: ${index * 0.1}s;"></div>
                    </div>
                `;
                issuesList.appendChild(issueDiv);
            });
        }
    } else {
        if (issuesCard) issuesCard.style.display = 'none';
    }

    // Display recommendations
    displayRecommendations(data);
    
    // Scroll to results
    setTimeout(() => {
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
}

function displayRecommendations(data) {
    const recList = document.getElementById('recommendationsList');
    if (!recList) return;

    const recommendations = getRecommendationsForCondition(
        data.primary_condition || data.skin_type,
        data.skin_type
    );

    recList.innerHTML = '';
    recommendations.forEach(rec => {
        const li = document.createElement('li');
        li.textContent = rec;
        recList.appendChild(li);
    });
}

function getRecommendationsForCondition(condition, skinType) {
    const tips = {
        'Acne': [
            'Use salicylic acid or benzoyl peroxide daily',
            'Cleanse twice daily with a gentle cleanser',
            'Apply a lightweight, oil-free moisturizer',
            'Use non-comedogenic products only',
            'Wear SPF 30+ daily to prevent scarring'
        ],
        'Oily': [
            'Use a mattifying clay mask 1-2x weekly',
            'Choose oil-free products',
            'Use a gel or foam cleanser',
            'Apply niacinamide serum',
            'Blot excess oil throughout the day'
        ],
        'Dry': [
            'Use a cream cleanser instead of soap',
            'Apply hyaluronic acid on damp skin',
            'Use a rich night cream with ceramides',
            'Use a humidifier in your bedroom',
            'Apply moisturizer within 3 minutes of cleansing'
        ],
        'Normal': [
            'Maintain consistent morning and night routine',
            'Use a mild cleanser',
            'Apply lightweight moisturizer',
            'Wear daily SPF 30+',
            'Stay hydrated and get enough sleep'
        ],
        'Redness': [
            'Use soothing ingredients like Centella Asiatica',
            'Avoid hot water and harsh cleansers',
            'Apply azelaic acid for long-term relief',
            'Use high SPF to prevent irritation',
            'Avoid trigger foods if you have rosacea'
        ],
        'Bags': [
            'Apply caffeine-infused eye cream',
            'Use cold spoons or jade roller in the morning',
            'Sleep with head elevated',
            'Reduce salt intake',
            'Stay well hydrated'
        ],
        'Pigmentation': [
            'Use vitamin C serum every morning',
            'Apply brightening serums with kojic acid',
            'Use chemical exfoliants 2-3x weekly',
            'Wear SPF 50+ religiously',
            'Consider professional treatments'
        ]
    };

    return tips[condition] || tips['Normal'];
}

// ============================================================================
// CHATBOT
// ============================================================================

// ============================================================================
// CHATBOT (Connected to Backend)
// ============================================================================

const chatWindow = document.getElementById('chatWindow');
const chatbotToggle = document.getElementById('chatbotToggle');
const chatClose = document.getElementById('chatClose');
const navChatLink = document.getElementById('navChatLink');

function toggleChat() {
    if (chatWindow) chatWindow.classList.toggle('active');
    if (chatWindow && chatWindow.classList.contains('active')) {
        chatInput.focus();
    }
}

if (chatbotToggle) chatbotToggle.addEventListener('click', toggleChat);
if (chatClose) chatClose.addEventListener('click', () => chatWindow.classList.remove('active'));
if (navChatLink) {
    navChatLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (chatWindow) {
            chatWindow.classList.add('active');
            chatInput.focus();
        }
    });
}

if (sendChatBtn) sendChatBtn.addEventListener('click', sendChatMessage);
if (chatInput) {
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
}

if (quickPrompts) {
    quickPrompts.forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.dataset.prompt;
            sendChatMessage();
        });
    });
}

async function sendChatMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message
    addChatMessage(message, 'user');
    chatInput.value = '';
    
    // Add typing indicator
    const typingId = 'typing-' + Date.now();
    addTypingIndicator(typingId);

    try {
        const context = lastDetectionData ? {
            last_condition: lastDetectionData.primary_condition || lastDetectionData.skin_type
        } : {};

        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message, context })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        if (data.error) {
            addChatMessage(`Error: ${data.error}`, 'bot');
        } else {
            // Add bot response
            addChatMessage(data.reply, 'bot');
        }
    } catch (error) {
        console.error('Chat error:', error);
        removeTypingIndicator(typingId);
        addChatMessage("I'm having trouble connecting right now. Please try again later.", 'bot');
    }
}

function addChatMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    // Convert markdown bold (**) to HTML <strong>
    let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Convert newlines to <br>
    formattedText = formattedText.replace(/\n/g, '<br>');
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${sender === 'bot' ? '🤖' : '👤'}</div>
        <div class="message-content">${formattedText}</div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTypingIndicator(id) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message bot-message typing`;
    messageDiv.id = id;
    messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content" style="padding: 10px 14px; display: flex; gap: 4px; align-items: center;">
            <div class="dot" style="width:6px;height:6px;background:var(--accent-primary);border-radius:50%;animation:typingBounce 1.2s infinite;"></div>
            <div class="dot" style="width:6px;height:6px;background:var(--accent-primary);border-radius:50%;animation:typingBounce 1.2s infinite 0.2s;"></div>
            <div class="dot" style="width:6px;height:6px;background:var(--accent-primary);border-radius:50%;animation:typingBounce 1.2s infinite 0.4s;"></div>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Ask chatbot button
const askChatbotBtn = document.getElementById('askChatbotBtn');
if (askChatbotBtn) {
    askChatbotBtn.addEventListener('click', () => {
        if (chatWindow) {
            chatWindow.classList.add('active');
            chatInput.focus();
        }
        if (lastDetectionData) {
            const condition = lastDetectionData.primary_condition || lastDetectionData.skin_type || 'normal';
            const prompt = `Tell me more about ${condition} skin`;
            chatInput.value = prompt;
            sendChatMessage();
        }
    });
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function showError(message) {
    console.error(message);
    alert(message);
}

// Initialize
console.log('Glow.AI Skincare Detection - Initialized');
