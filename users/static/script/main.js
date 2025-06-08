document.addEventListener("DOMContentLoaded", function() {

    // --- NEW: Auto-type Request Viewing message ---
    const requestViewingBtn = document.getElementById('requestViewingBtn');
    const chatInput = document.querySelector('.chat-message-input'); // Your textarea
    const chatSendBtn = document.querySelector('.chat-send-btn'); // Your send button


    if (requestViewingBtn && chatInput && chatSendBtn) {
        console.log('All elements found. Attaching Request Viewing listener.'); // Added for debugging
        requestViewingBtn.addEventListener('click', function() {
            const predefinedMessage = "Hi, I'm interested in viewing this property. Could we schedule a viewing soon?";
            chatInput.value = predefinedMessage;

            // Optional: Automatically send the message after typing
            chatSendBtn.click();

        });
    } else {
        console.warn('One or more elements for Request Viewing functionality not found.'); // Added for debugging
    }

    // --- NEW: Chat Popup Logic ---
    const openChatPopupBtn = document.getElementById('openChatPopupBtn');
    const chatPopup = document.getElementById('chatPopup');
    const closeChatPopupBtn = chatPopup ? chatPopup.querySelector('.close-btn') : null;
    const chatListContainer = chatPopup ? chatPopup.querySelector('.chat-list') : null;
    const chatListLoading = chatPopup ? chatPopup.querySelector('.chat-list-loading') : null;
    const chatListEmpty = chatPopup ? chatPopup.querySelector('.chat-list-empty') : null;


    if (openChatPopupBtn && chatPopup && chatListContainer) {
        openChatPopupBtn.addEventListener('click', function() {
            chatPopup.classList.toggle('show');
            if (chatPopup.classList.contains('show')) {
                fetchRecentChats(); // Fetch chats when popup opens
            }
        });

        if (closeChatPopupBtn) {
            closeChatPopupBtn.addEventListener('click', function() {
                chatPopup.classList.remove('show');
            });
        }

        // Close popup if clicked outside
        document.addEventListener('click', function(event) {
            if (chatPopup.classList.contains('show') && !chatPopup.contains(event.target) && !openChatPopupBtn.contains(event.target)) {
                chatPopup.classList.remove('show');
            }
        });

        function fetchRecentChats() {
            if (chatListLoading) chatListLoading.style.display = 'block';
            if (chatListEmpty) chatListEmpty.style.display = 'none';
            chatListContainer.innerHTML = ''; // Clear previous content

            // Use the Django URL resolver for the API endpoint
            const recentChatsApiUrl = chatPopup.dataset.apiUrl || '/api/recent-chats/'; // Fallback, but dataset is better
            // IMPORTANT: In your HTML, add data-api-url="{% url 'users:recent_chats_api' %}" to chatPopup div

            fetch(recentChatsApiUrl)
                .then(response => {
                    if (!response.ok) {
                        if (response.status === 403) { // Forbidden, likely not logged in
                            throw new Error('Not logged in or unauthorized.');
                        }
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (chatListLoading) chatListLoading.style.display = 'none';
                    if (data.chats && data.chats.length > 0) {
                        data.chats.forEach(chat => {
                            const chatItem = document.createElement('a'); // Use <a> to make it clickable
                            chatItem.href = `/property/${chat.property_id}/chat/${chat.other_user_id}/`;
                            chatItem.classList.add('chat-list-item');

                            let avatarHtml = `<div class="chat-list-item-avatar">👤</div>`;
                            if (chat.property_main_image) {
                                avatarHtml = `<div class="chat-list-item-avatar"><img src="${chat.property_main_image}" alt="Property Image"></div>`;
                            }

                            chatItem.innerHTML = `
                                 ${avatarHtml}
                                 <div class="chat-list-item-content">
                                     <div class="chat-list-item-name">${chat.other_user_full_name}</div>
                                     <div class="chat-list-item-property">${chat.property_title}</div>
                                     <div class="chat-list-item-message">${chat.last_message_sender_is_me ? 'You: ' : ''}${chat.last_message}</div>
                                 </div>
                                 <div class="chat-list-item-timestamp">${formatTimestamp(chat.last_message_timestamp)}</div>
                             `;
                            chatListContainer.appendChild(chatItem);
                        });
                    } else {
                        if (chatListEmpty) chatListEmpty.style.display = 'block';
                    }
                })
                .catch(error => {
                    if (chatListLoading) chatListLoading.style.display = 'none';
                    console.error('Error fetching recent chats:', error);
                    if (chatListEmpty) {
                        chatListEmpty.style.display = 'block';
                        chatListEmpty.textContent = 'Could not load chats. ' + error.message;
                        chatListEmpty.style.color = '#e53e3e';
                    }
                });
        }

        // Helper function to format timestamp (e.g., "HH:MM AM/PM" or "MM/DD")
        function formatTimestamp(timestampStr) {
            const now = new Date();
            const date = new Date(timestampStr);

            const isToday = date.getDate() === now.getDate() &&
                date.getMonth() === now.getMonth() &&
                date.getFullYear() === now.getFullYear();

            if (isToday) {
                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            } else {
                return date.toLocaleDateString([], { month: 'numeric', day: 'numeric' });
            }
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const menuButton = document.getElementById('menu-button');
    const dropdown = document.getElementById('menu-dropdown');

    menuButton.addEventListener('click', function(e) {
        e.preventDefault();
        dropdown.classList.toggle('show');
    });

    window.addEventListener('click', function(e) {
        if (!menuButton.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('show');
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // ... (Existing Login Page Role Toggle, Profile Dropdown, Chat Input Auto-resize, Chat Popup Logic) ...

    // --- NEW: Dynamic Back Link Logic for Chat Page ---
    const dynamicBackLink = document.getElementById('dynamicBackLink');
    const backLinkText = document.getElementById('backLinkText');

    if (dynamicBackLink && backLinkText) {
        // Function to determine if we should use history.back()
        // Heuristic: If there's more than 2 items in history (current page + one before),
        // and the current referrer is not empty or is not the property detail page itself.
        // This is tricky; a robust solution might require passing referrer via URL parameter.
        // For simplicity, we'll assume if history.length > 2, it's likely not direct navigation.
        const shouldGoBackInHistory = (window.history.length > 2); // Adjust '2' as needed.

        if (shouldGoBackInHistory) {
            // Change text
            backLinkText.textContent = dynamicBackLink.dataset.historyText;

            // Override click behavior to go back in history
            dynamicBackLink.addEventListener('click', function(event) {
                event.preventDefault(); // Prevent default link navigation
                window.history.back(); // Go back in browser history
            });
        }
        // If shouldGoBackInHistory is false, the default 'href' to property_detail remains active.
    }
});