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

// Fonction pour afficher un message dans l'interface
function addMessage(text, sender) {
    if (!chatMessages) return;
    
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message');
    
    // On applique le style en fonction de l'expéditeur
    if (sender === 'user') {
        msgDiv.style.textAlign = 'right';
        msgDiv.style.color = '#33e1cf';
        msgDiv.textContent = "Vous : " + text;
    } else {
        msgDiv.style.textAlign = 'left';
        msgDiv.style.color = 'white';
        msgDiv.textContent = "IA : " + text;
    }
    
    msgDiv.style.margin = "8px 0";
    chatMessages.appendChild(msgDiv);
    
    // Scroll automatique vers le bas
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Fonction pour envoyer le message au serveur Python (app.py)
async function sendToAI(userText) {
    try {
        const response = await fetch('http://127.0.0.1:5000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userText })
        });

        const data = await response.json();

        if (data.reply) {
            addMessage(data.reply, 'bot');
        } else {
            addMessage("Erreur : " + (data.error || "L'IA ne répond pas."), 'bot');
        }
    } catch (error) {
        addMessage("Le serveur Python n'est pas lancé.", 'bot');
    }
}

// Événement au clic sur le bouton Envoyer
if (chatSendBtn) {
    chatSendBtn.onclick = function() {
        const text = chatInput.value.trim();
        if (text !== "") {
            addMessage(text, 'user'); // Affiche ton message
            chatInput.value = "";      // Vide le champ
            sendToAI(text);            // Envoie à l'IA
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