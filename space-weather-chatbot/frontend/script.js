// --- SHARED UTILS ---
function scrollToBottom(container) {
    if (container) container.scrollTop = container.scrollHeight;
}

// --- SIMULATION LOGIC ---
function initSimulator() {
    const slider = document.getElementById('probSlider');
    const mode = document.getElementById('modeSelect');
    const oil = document.getElementById('oil');
    const glow = document.getElementById('glow');
    const tempDisplay = document.getElementById('tempVal');
    const probDisplay = document.getElementById('probVal');
    const gicDisplay = document.getElementById('gicVal');
    const badge = document.getElementById('mitigationStatus');

    if (!slider) return;

    function updateSim() {
        const p = parseFloat(slider.value);
        const isAuto = mode.value === 'auto';
        
        // 1. Calculate GIC Heat (Prob increases heat)
        const heatInput = p * 120; 
        
        // 2. Innovation Logic: Calculate Oil Immersion Level
        let oilLevel = isAuto ? (30 + (p * 65)) : 30; 
        
        // 3. Calculate Final Temperature
        let coolingFactor = isAuto ? (1 + (p * 4.5)) : 1.0;
        let finalTemp = 75 + (heatInput / coolingFactor);

        // Update UI
        probDisplay.innerText = Math.round(p * 100) + "%";
        oil.style.height = oilLevel + "%";
        tempDisplay.innerText = finalTemp.toFixed(1) + "°C";

        // Temperature Styling
        if (finalTemp > 140) {
            tempDisplay.style.color = "#ef4444";
            glow.style.background = "rgba(239, 68, 68, 0.8)";
        } else if (finalTemp > 100) {
            tempDisplay.style.color = "#f59e0b";
            glow.style.background = "rgba(245, 158, 11, 0.6)";
        } else {
            tempDisplay.style.color = "#22c55e";
            glow.style.background = "rgba(34, 211, 238, 0.2)";
        }

        // GIC Labels
        if (p < 0.4) gicDisplay.innerText = "Low";
        else if (p < 0.7) gicDisplay.innerText = "Moderate";
        else gicDisplay.innerText = "Severe";

        // Badge Update
        if (isAuto && p > 0.39) {
            badge.innerText = "Active Oil Immersion: High";
            badge.className = "mitigation-badge active";
        } else {
            badge.innerText = "Standard Cooling";
            badge.className = "mitigation-badge inactive";
        }
    }

    slider.addEventListener('input', updateSim);
    mode.addEventListener('change', updateSim);
    updateSim(); // Initial run
}

// --- CHATBOT LOGIC ---
function initChatbot() {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const loadingIndicator = document.getElementById('loading-indicator');

    if (!userInput || !sendBtn) return;

    function addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender);
        msgDiv.innerText = text;
        chatBox.insertBefore(msgDiv, loadingIndicator);
        scrollToBottom(chatBox);
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        userInput.value = '';
        
        sendBtn.disabled = true;
        userInput.disabled = true;
        loadingIndicator.style.display = 'flex';
        scrollToBottom(chatBox);

        try {
            // Absolute URL to ensure connectivity in any environment
            const response = await fetch('http://127.0.0.1:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });
            
            const data = await response.json();
            
            if (data && data.response) {
                addMessage(data.response, 'bot');
            } else {
                addMessage("Error: Could not retrieve response.", 'bot');
            }
        } catch (error) {
            addMessage("Connection error! Ensure the AuraShield backend is running.", 'bot');
        } finally {
            sendBtn.disabled = false;
            userInput.disabled = false;
            userInput.focus();
            loadingIndicator.style.display = 'none';
            scrollToBottom(chatBox);
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

// --- INITIALIZE BASED ON PAGE ELEMENTS ---
document.addEventListener('DOMContentLoaded', () => {
    initSimulator();
    initChatbot();
});
