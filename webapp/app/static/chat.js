document.addEventListener('DOMContentLoaded', () => {
  const htmlElement = document.documentElement;
  const chatForm = document.getElementById('chatForm');
  const messageInput = document.getElementById('messageInput');
  const chatArea = document.getElementById('chatArea');
  const themeBtns = document.querySelectorAll('[data-set-theme]');

  let currentTheme = localStorage.getItem('theme') || 'dark';
  let isSending = false;

  const SESSION_KEY = "rag_session_id";
  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = (crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`).toString();
    localStorage.setItem(SESSION_KEY, sessionId);
  }

  // NEW: pending query waiting for mode selection
  let pendingQuery = null;

  setTheme(currentTheme);

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

  // ---------- SUBMIT HANDLER ----------
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = messageInput.value.trim();
    if (!text || isSending) return;

    // Add user message immediately
    addMessage(text, 'user');
    messageInput.value = '';

    // NEW: Instead of answering immediately, ask for chunking strategy
    pendingQuery = text;
    addChunkingChoiceMessage();
  });

  // ---------- BACKEND CALL ----------
  async function callBackend(message, mode) {
    const res = await fetch("/api/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message, mode })
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`HTTP ${res.status}: ${errText}`);
    }
    return await res.json();
  }

  // ---------- MODE CHOICE UI ----------
  function addChunkingChoiceMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'bot');

    const bubble = document.createElement('div');
    bubble.classList.add('bubble');

    bubble.innerHTML = `
      <div style="font-weight:600; margin-bottom:8px;">Choose a chunking strategy for retrieval:</div>
      <div style="display:flex; gap:8px; flex-wrap:wrap;">
        <button class="mode-btn" data-mode="fixed">Fixed-size (overlap)</button>
        <button class="mode-btn" data-mode="semantic">Semantic (sections + overlap)</button>
        <button class="mode-btn" data-mode="auto">Auto (system decides)</button>
      </div>
      <div style="opacity:.75; margin-top:8px; font-size:12px;">
        Fixed is best for exact quotes/formulas, Semantic is best for sections/ideas.
      </div>
    `;

    messageDiv.appendChild(bubble);
    chatArea.appendChild(messageDiv);
    scrollToBottom();

    // Attach button listeners
    bubble.querySelectorAll(".mode-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const mode = btn.dataset.mode;
        await handleModeSelection(mode, messageDiv);
      });
    });
  }

  async function handleModeSelection(mode, choiceMessageDiv) {
    if (!pendingQuery) return;

    // Disable all buttons to prevent double click
    choiceMessageDiv.querySelectorAll(".mode-btn").forEach(b => b.disabled = true);

    // Add a small confirmation line (optional)
    const bubble = choiceMessageDiv.querySelector(".bubble");
    const confirm = document.createElement("div");
    confirm.style.marginTop = "10px";
    confirm.style.opacity = "0.85";
    confirm.innerHTML = `✅ Selected: <b>${escapeHtml(mode)}</b>. Retrieving...`;
    bubble.appendChild(confirm);

    // Add assistant typing placeholder
    const typingEl = addTypingMessage();
    setSendingState(true);

    try {
      const data = await callBackend(pendingQuery, mode);

      replaceTypingWithAnswer(typingEl, data.answer);
      appendModeUsed(typingEl, data.mode_used);

    } catch (err) {
      replaceTypingWithError(typingEl, err);
    } finally {
      setSendingState(false);
      pendingQuery = null;
    }
  }

  function setSendingState(on) {
    isSending = on;
    messageInput.disabled = on;
    chatForm.querySelector("button[type='submit']").disabled = on;
    if (!on) messageInput.focus();
  }

  // ---------- UI HELPERS ----------
  function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);

    const bubble = document.createElement('div');
    bubble.classList.add('bubble');
    bubble.innerHTML = parseMarkdown(text);

    messageDiv.appendChild(bubble);
    chatArea.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
  }

  function addTypingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'bot');

    const bubble = document.createElement('div');
    bubble.classList.add('bubble');
    bubble.innerHTML = `
      <span style="opacity:.8">Retrieving & generating</span>
      <span class="typing-dots" aria-label="typing">
        <span>.</span><span>.</span><span>.</span>
      </span>
    `;
    messageDiv.appendChild(bubble);
    chatArea.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
  }

  function replaceTypingWithAnswer(typingMessageDiv, answerText) {
    const bubble = typingMessageDiv.querySelector('.bubble');
    bubble.innerHTML = parseMarkdown(answerText);
    scrollToBottom();
  }

  function appendModeUsed(typingMessageDiv, modeUsed) {
    if (!modeUsed) return;
    const bubble = typingMessageDiv.querySelector('.bubble');
    const meta = document.createElement("div");
    meta.style.opacity = "0.7";
    meta.style.fontSize = "12px";
    meta.style.marginTop = "8px";
    meta.textContent = `Mode used: ${modeUsed}`;
    bubble.appendChild(meta);
  }

  function replaceTypingWithError(typingMessageDiv, err) {
    const bubble = typingMessageDiv.querySelector('.bubble');
    bubble.innerHTML = `
      <b style="color:#ff8080">Error:</b>
      <span style="color:#ffb3b3">${escapeHtml(String(err?.message || err))}</span>
    `;
    scrollToBottom();
  }

  function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  function parseMarkdown(text) {
    let safeText = escapeHtml(text);
    safeText = safeText.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    safeText = safeText.replace(/`(.*?)`/g, '<code>$1</code>');
    return safeText;
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
