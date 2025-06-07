document.addEventListener("DOMContentLoaded", function() {
    const menuButton = document.getElementById("menu-button");
    const dropdown = document.getElementById("menu-dropdown");

    menuButton.addEventListener("click", function(e) {
        e.preventDefault();
        dropdown.classList.toggle("show");
    });

    window.addEventListener("click", function(e) {
        if (!menuButton.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove("show");
        }
    });

    // --- NEW: Auto-type Request Viewing message ---
    const requestViewingBtn = document.getElementById('requestViewingBtn');
    const chatSendBtn = document.querySelector('.chat-send-btn'); // Assuming this is your send button

    if (requestViewingBtn && chatInput && chatSendBtn) {
        requestViewingBtn.addEventListener('click', function() {
            const predefinedMessage = "Hi, I'm interested in viewing this property. Could we schedule a viewing soon?";
            chatInput.value = predefinedMessage;

            // Optional: Automatically send the message after typing
            // This simulates a click on the send button, which will trigger the form submission.
            // Be aware that this will immediately send the message without user confirmation.
            chatSendBtn.click();

            // Alternatively, just populate the field and let the user click send:
            // No chatSendBtn.click() here if you want user to manually send.
        });
    }
});