// ===== GESTION DU MENU DEROULANT =====
const menuBtn = document.getElementById('menuBtn');
const menuDropdown = document.getElementById('menuDropdown');
const headerActions = document.getElementById('headerActions');

if (menuBtn && menuDropdown) {
    menuBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        menuDropdown.classList.toggle('show');
    });
}

// ===== LOGIQUE DU CHATBOT IA =====
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const chatSendBtn = document.getElementById('chat-send-btn');

function addMessage(text, sender) {
    if (!chatMessages) return;

    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message');

    if (sender === 'user') {
        msgDiv.classList.add('user-message');
        msgDiv.style.alignSelf = 'flex-end';
        msgDiv.style.backgroundColor = 'rgba(0, 0, 0, 0.25)';
        msgDiv.textContent = 'Vous : ' + text;
    } else {
        msgDiv.classList.add('bot-message');
        msgDiv.style.alignSelf = 'flex-start';
        msgDiv.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
        msgDiv.textContent = 'IA : ' + text;
    }

    msgDiv.style.margin = '8px 0';
    msgDiv.style.padding = '10px';
    msgDiv.style.borderRadius = '10px';
    msgDiv.style.maxWidth = '85%';
    msgDiv.style.color = 'white';

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendToAI(userText) {
    try {
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.style.color = 'rgba(255,255,255,0.6)';
        loadingDiv.style.fontSize = '0.8rem';
        loadingDiv.style.fontStyle = 'italic';
        loadingDiv.textContent = 'Gemini reflechit...';
        chatMessages.appendChild(loadingDiv);

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userText })
        });

        const data = await response.json();

        const loader = document.getElementById(loadingId);
        if (loader) loader.remove();

        if (data.response) {
            addMessage(data.response, 'bot');
        } else {
            addMessage("Erreur : " + (data.error || "L'IA ne repond pas."), 'bot');
        }
    } catch (error) {
        addMessage('Le serveur Python n\'est pas lance ou est inaccessible.', 'bot');
    }
}

if (chatSendBtn) {
    chatSendBtn.addEventListener('click', function () {
        const text = chatInput.value.trim();
        if (text !== '') {
            addMessage(text, 'user');
            chatInput.value = '';
            sendToAI(text);
        }
    });
}

if (chatInput) {
    chatInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            chatSendBtn.click();
        }
    });
}

// ===== SYSTEME D'AMIS =====
const friendSearchInput = document.getElementById('friendSearchInput');
const friendSearchResults = document.getElementById('friendSearchResults');
const friendRequestsList = document.getElementById('friendRequestsList');
const friendsList = document.getElementById('friendsList');
const notificationsList = document.getElementById('notificationsList');
const messagePanelTitle = document.getElementById('messagePanelTitle');
const conversationMessages = document.getElementById('conversationMessages');
const conversationInput = document.getElementById('conversationInput');
const conversationSendBtn = document.getElementById('conversationSendBtn');
let currentUser = null;
let friendSearchTimer = null;
let selectedFriend = null;

async function refreshSessionUI() {
    if (!headerActions) return;

    try {
        const response = await fetch('/api/me', { method: 'GET' });
        const data = await response.json();
        currentUser = data.authenticated ? data.user : null;

        if (data.authenticated && data.user) {
            headerActions.innerHTML = `
                <span style="color:white; margin-right:10px;">Bonjour, ${data.user.prenom}</span>
                <button type="button" id="logoutBtn" class="btn-logout">Deconnexion</button>
            `;

            const logoutBtn = document.getElementById('logoutBtn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', async function () {
                    await fetch('/api/logout', { method: 'POST' });
                    window.location.reload();
                });
            }

            await loadFriendRequests();
            await loadFriends();
            await loadNotifications();
        } else {
            if (friendRequestsList) friendRequestsList.textContent = 'Connectez-vous pour voir vos demandes.';
            if (friendsList) friendsList.textContent = 'Connectez-vous pour voir vos amis.';
            if (notificationsList) notificationsList.textContent = 'Connectez-vous pour voir vos notifications.';
        }
    } catch (err) {
        // En cas d'erreur reseau, on garde l'UI par defaut.
    }
}

function renderFriendSearchResults(users) {
    if (!friendSearchResults) return;

    friendSearchResults.innerHTML = '';
    if (!users || users.length === 0) {
        friendSearchResults.style.display = 'none';
        return;
    }

    users.forEach((user) => {
        const row = document.createElement('div');
        row.className = 'friend-search-item';

        const meta = document.createElement('div');
        meta.className = 'friend-user-meta';
        meta.textContent = `${user.prenom} ${user.nom} (${user.email})`;

        const btn = document.createElement('button');
        btn.className = 'friend-btn';

        if (user.relation_status === 'friends') {
            btn.textContent = 'Deja ami';
            btn.disabled = true;
        } else if (user.relation_status === 'request_sent') {
            btn.textContent = 'Demande envoyee';
            btn.disabled = true;
        } else if (user.relation_status === 'request_received') {
            btn.textContent = 'Demande recue';
            btn.disabled = true;
        } else {
            btn.textContent = 'Ajouter';
            btn.addEventListener('click', async () => {
                try {
                    const response = await fetch('/api/friends/request', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ to_user_id: user.id })
                    });
                    const data = await response.json();
                    if (!response.ok) {
                        alert(data.error || "Impossible d'envoyer la demande.");
                        return;
                    }
                    btn.textContent = 'Demande envoyee';
                    btn.disabled = true;
                } catch (err) {
                    alert('Erreur reseau pendant envoi de la demande.');
                }
            });
        }

        row.appendChild(meta);
        row.appendChild(btn);
        friendSearchResults.appendChild(row);
    });

    friendSearchResults.style.display = 'block';
}

async function searchUsers(term) {
    if (!currentUser || !friendSearchResults) return;

    if (!term || term.length < 2) {
        friendSearchResults.style.display = 'none';
        friendSearchResults.innerHTML = '';
        return;
    }

    try {
        const response = await fetch(`/api/users/search?q=${encodeURIComponent(term)}`);
        const data = await response.json();
        if (!response.ok) {
            friendSearchResults.style.display = 'none';
            return;
        }
        renderFriendSearchResults(data.users || []);
    } catch (err) {
        friendSearchResults.style.display = 'none';
    }
}

async function loadFriendRequests() {
    if (!currentUser || !friendRequestsList) return;

    try {
        const response = await fetch('/api/friends/requests');
        const data = await response.json();
        if (!response.ok) {
            friendRequestsList.textContent = data.error || 'Impossible de charger les demandes.';
            return;
        }

        const requests = data.requests || [];
        if (requests.length === 0) {
            friendRequestsList.textContent = 'Aucune demande pour le moment.';
            return;
        }

        friendRequestsList.innerHTML = '';
        requests.forEach((req) => {
            const row = document.createElement('div');
            row.className = 'friend-row';

            const text = document.createElement('div');
            text.textContent = `${req.prenom} ${req.nom} veut vous ajouter.`;
            row.appendChild(text);

            const actions = document.createElement('div');
            actions.className = 'friend-actions';

            const acceptBtn = document.createElement('button');
            acceptBtn.textContent = 'Accepter';
            acceptBtn.style.background = '#33e1cf';
            acceptBtn.addEventListener('click', () => respondFriendRequest(req.id, 'accept'));

            const rejectBtn = document.createElement('button');
            rejectBtn.textContent = 'Refuser';
            rejectBtn.style.background = '#ff90b0';
            rejectBtn.addEventListener('click', () => respondFriendRequest(req.id, 'reject'));

            actions.appendChild(acceptBtn);
            actions.appendChild(rejectBtn);
            row.appendChild(actions);
            friendRequestsList.appendChild(row);
        });
    } catch (err) {
        friendRequestsList.textContent = 'Erreur reseau.';
    }
}

async function respondFriendRequest(requestId, action) {
    try {
        const response = await fetch(`/api/friends/requests/${requestId}/respond`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        });
        const data = await response.json();
        if (!response.ok) {
            alert(data.error || 'Action impossible.');
            return;
        }
        await loadFriendRequests();
        await loadFriends();
        await loadNotifications();
    } catch (err) {
        alert('Erreur reseau.');
    }
}

async function loadNotifications() {
    if (!currentUser || !notificationsList) return;

    try {
        const response = await fetch('/api/notifications');
        const data = await response.json();
        if (!response.ok) {
            notificationsList.textContent = data.error || 'Impossible de charger les notifications.';
            return;
        }

        const items = [];
        const pending = data.pending_friend_requests || 0;
        if (pending > 0) {
            items.push(`Vous avez ${pending} demande(s) d'ami en attente.`);
        }

        const recentMessages = data.recent_messages || [];
        recentMessages.forEach((msg) => {
            const preview = (msg.content || '').length > 60 ? `${msg.content.slice(0, 57)}...` : (msg.content || '');
            items.push(`Nouveau message de ${msg.prenom} ${msg.nom}: ${preview}`);
        });

        notificationsList.innerHTML = '';
        if (items.length === 0) {
            notificationsList.textContent = 'Aucune notification pour le moment.';
            return;
        }

        items.forEach((text) => {
            const el = document.createElement('div');
            el.className = 'notification-item';
            el.textContent = text;
            notificationsList.appendChild(el);
        });
    } catch (err) {
        notificationsList.textContent = 'Erreur reseau.';
    }
}

async function loadFriends() {
    if (!currentUser || !friendsList) return;

    try {
        const response = await fetch('/api/friends/list');
        const data = await response.json();
        if (!response.ok) {
            friendsList.textContent = data.error || 'Impossible de charger les amis.';
            return;
        }

        const friends = data.friends || [];
        if (friends.length === 0) {
            friendsList.textContent = 'Aucun ami pour le moment.';
            return;
        }

        friendsList.innerHTML = '';
        friends.forEach((friend) => {
            const row = document.createElement('div');
            row.className = 'friend-row clickable';
            row.textContent = `${friend.prenom} ${friend.nom}`;
            row.addEventListener('click', () => {
                setSelectedFriend(friend);
            });
            friendsList.appendChild(row);
        });
    } catch (err) {
        friendsList.textContent = 'Erreur reseau.';
    }
}

function renderConversation(messages) {
    if (!conversationMessages) return;

    conversationMessages.innerHTML = '';
    if (!messages || messages.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'conversation-placeholder';
        empty.textContent = 'Aucun message pour le moment.';
        conversationMessages.appendChild(empty);
        return;
    }

    messages.forEach((msg) => {
        const bubble = document.createElement('div');
        bubble.className = `conversation-bubble ${msg.sender_id === currentUser.id ? 'me' : 'them'}`;
        bubble.textContent = msg.content;
        conversationMessages.appendChild(bubble);
    });

    conversationMessages.scrollTop = conversationMessages.scrollHeight;
}

async function loadConversation(friendId) {
    if (!conversationMessages) return;

    try {
        const response = await fetch(`/api/messages/conversation/${friendId}`);
        const data = await response.json();
        if (!response.ok) {
            renderConversation([]);
            return;
        }
        renderConversation(data.messages || []);
        await loadNotifications();
    } catch (err) {
        renderConversation([]);
    }
}

function setSelectedFriend(friend) {
    selectedFriend = friend;
    if (messagePanelTitle) {
        messagePanelTitle.textContent = `Messagerie avec ${friend.prenom} ${friend.nom}`;
    }
    if (conversationInput) conversationInput.disabled = false;
    if (conversationSendBtn) conversationSendBtn.disabled = false;
    loadConversation(friend.id);

    if (friendsList) {
        Array.from(friendsList.children).forEach((el) => {
            el.classList.remove('active');
            if (el.textContent === `${friend.prenom} ${friend.nom}`) {
                el.classList.add('active');
            }
        });
    }
}

async function sendConversationMessage() {
    if (!selectedFriend || !conversationInput) return;

    const text = conversationInput.value.trim();
    if (!text) return;

    try {
        const response = await fetch('/api/messages/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ receiver_id: selectedFriend.id, content: text })
        });
        const data = await response.json();
        if (!response.ok) {
            alert(data.error || 'Impossible d\'envoyer le message.');
            return;
        }
        conversationInput.value = '';
        await loadConversation(selectedFriend.id);
        await loadNotifications();
    } catch (err) {
        alert('Erreur reseau.');
    }
}

if (friendSearchInput) {
    friendSearchInput.addEventListener('input', (e) => {
        const term = e.target.value.trim();
        if (friendSearchTimer) {
            clearTimeout(friendSearchTimer);
        }
        friendSearchTimer = setTimeout(() => {
            searchUsers(term);
        }, 250);
    });

    friendSearchInput.addEventListener('focus', () => {
        const term = friendSearchInput.value.trim();
        if (term.length >= 2) {
            searchUsers(term);
        }
    });
}

document.addEventListener('click', (e) => {
    if (menuBtn && menuDropdown && !menuBtn.contains(e.target) && !menuDropdown.contains(e.target)) {
        menuDropdown.classList.remove('show');
    }

    if (friendSearchResults && friendSearchInput && !friendSearchResults.contains(e.target) && e.target !== friendSearchInput) {
        friendSearchResults.style.display = 'none';
    }
});

if (conversationSendBtn) {
    conversationSendBtn.addEventListener('click', sendConversationMessage);
}

if (conversationInput) {
    conversationInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendConversationMessage();
        }
    });
}

refreshSessionUI();