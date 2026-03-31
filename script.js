// ===== GESTION DU MENU DÉROULANT =====
const menuBtn = document.getElementById('menuBtn');
const menuDropdown = document.getElementById('menuDropdown');

if (menuBtn && menuDropdown) {
    menuBtn.onclick = function(e) {
        e.stopPropagation();
        menuDropdown.classList.toggle('show');
    };

    document.onclick = function(e) {
        if (!menuBtn.contains(e.target) && !menuDropdown.contains(e.target)) {
            menuDropdown.classList.remove('show');
        }
    };
}

// ===== LOGIQUE DU CHATBOT IA =====
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const chatSendBtn = document.getElementById('chat-send-btn');

/**
 * Affiche un message dans la zone de chat
 * @param {string} text - Le texte du message
 * @param {string} sender - 'user' ou 'bot'
 */
function addMessage(text, sender) {
    if (!chatMessages) return;
    
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message');
    
    // Style et alignement selon l'expéditeur
    if (sender === 'user') {
        msgDiv.classList.add('user-message');
        msgDiv.style.alignSelf = 'flex-end';
        msgDiv.style.backgroundColor = 'rgba(0, 0, 0, 0.25)';
        msgDiv.textContent = "Vous : " + text;
    } else {
        msgDiv.classList.add('bot-message');
        msgDiv.style.alignSelf = 'flex-start';
        msgDiv.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
        msgDiv.textContent = "IA : " + text;
    }
    
    msgDiv.style.margin = "8px 0";
    msgDiv.style.padding = "10px";
    msgDiv.style.borderRadius = "10px";
    msgDiv.style.maxWidth = "85%";
    msgDiv.style.color = "white";
    
    chatMessages.appendChild(msgDiv);
    
    // Scroll automatique vers le bas
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Envoie le message au serveur Flask (app.py)
 * @param {string} userText - Le texte tapé par l'utilisateur
 */
async function sendToAI(userText) {
    try {
        // On affiche un message temporaire pour faire patienter
        const loadingId = "loading-" + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.style.color = "rgba(255,255,255,0.6)";
        loadingDiv.style.fontSize = "0.8rem";
        loadingDiv.style.fontStyle = "italic";
        loadingDiv.textContent = "Gemini réfléchit...";
        chatMessages.appendChild(loadingDiv);

        const response = await fetch('http://127.0.0.1:5000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userText })
        });

        const data = await response.json();
        
        // Supprimer l'indicateur de chargement
        const loader = document.getElementById(loadingId);
        if (loader) loader.remove();

        if (data.response) {
            addMessage(data.response, 'bot');
        } else {
            addMessage("Erreur : " + (data.error || "L'IA ne répond pas."), 'bot');
        }
    } catch (error) {
        addMessage("Le serveur Python n'est pas lancé ou est inaccessible.", 'bot');
    }
}

// Événement au clic sur le bouton Envoyer
if (chatSendBtn) {
    chatSendBtn.onclick = function() {
        const text = chatInput.value.trim();
        if (text !== "") {
            addMessage(text, 'user'); // Affiche ton message immédiatement
            chatInput.value = "";      // Vide le champ de texte
            sendToAI(text);            // Appelle l'API Python
        }
    };
}

// Permettre l'envoi avec la touche "Entrée"
if (chatInput) {
    chatInput.onkeypress = function(e) {
        if (e.key === 'Enter') {
            chatSendBtn.click();
        }
    };
}