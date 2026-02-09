document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    const htmlElement = document.documentElement;
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const chatArea = document.getElementById('chatArea');
    const themeBtns = document.querySelectorAll('[data-set-theme]');
    const parallaxBg = document.querySelector('.parallax-bg');

    // --- State ---
    let currentTheme = localStorage.getItem('theme') || 'dark';

    // --- Initialization ---
    setTheme(currentTheme);

    // --- Theme Switcher ---
    themeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const newTheme = btn.getAttribute('data-set-theme');
            setTheme(newTheme);
        });
    });

    function setTheme(theme) {
        htmlElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        currentTheme = theme;
    }

    // --- Parallax Effect ---
    // Optimizing with requestAnimationFrame to prevent jank
    let mouseX = 0.5;
    let mouseY = 0.5;
    let targetMouseX = 0.5;
    let targetMouseY = 0.5;

    window.addEventListener('mousemove', (e) => {
        // Normalize mouse position (0 to 1)
        targetMouseX = e.clientX / window.innerWidth;
        targetMouseY = e.clientY / window.innerHeight;
    });

    function updateParallax() {
        // Smooth interpolation
        mouseX += (targetMouseX - mouseX) * 0.1;
        mouseY += (targetMouseY - mouseY) * 0.1;

        htmlElement.style.setProperty('--mouse-x', mouseX);
        htmlElement.style.setProperty('--mouse-y', mouseY);

        requestAnimationFrame(updateParallax);
    }

    updateParallax();

    // --- Chat Logic ---
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = messageInput.value.trim();
        if (!text) return;

        // 1. Add User Message
        addMessage(text, 'user');
        messageInput.value = '';

        // 2. Simulate Bot Response
        setTimeout(() => {
            const botResponse = generateBotResponse(text);
            addMessage(botResponse, 'bot');
        }, 600);
    });

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);

        const bubble = document.createElement('div');
        bubble.classList.add('bubble');

        // Render Markdown
        bubble.innerHTML = parseMarkdown(text);

        messageDiv.appendChild(bubble);
        chatArea.appendChild(messageDiv);

        // Auto-scroll
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function parseMarkdown(text) {
        // Escape HTML to prevent XSS (basic)
        let safeText = text.replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

        // Bold: **text**
        safeText = safeText.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');

        // Code: `text`
        safeText = safeText.replace(/`(.*?)`/g, '<code>$1</code>');

        return safeText;
    }

    function generateBotResponse(userText) {
        const lowerText = userText.toLowerCase();
        if (lowerText.includes('hello') || lowerText.includes('hi')) {
            return 'Hello there! Try switching the **theme**!';
        }
        if (lowerText.includes('theme')) {
            return 'I like `purple` the best. What about you?';
        }
        if (lowerText.includes('code')) {
            return 'Here is some code: `console.log("Hello World")`';
        }
        return `You said: ${userText}`;
    }
});
