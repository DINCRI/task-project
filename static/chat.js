const chatPanel = document.querySelector('#ai-chat');
const chatForm = document.querySelector('#chat-form');
const chatInput = document.querySelector('#chat-input');
const chatMessages = document.querySelector('#chat-messages');
const chatStatus = document.querySelector('#chat-status');
const sendChat = document.querySelector('#send-chat');
let chatHistory = [];
let chatBusy = false;
function chatBubble(text, role) {
 const bubble = document.createElement('p');
 bubble.className = `chat-bubble ${role}`;
 bubble.textContent = text;
 chatMessages.append(bubble);
 chatMessages.scrollTop = chatMessages.scrollHeight;
}
chatForm.addEventListener('submit', async event => {
 event.preventDefault();
 const message = chatInput.value.trim();
 if (!message || chatBusy) return;
 chatBusy = true; sendChat.disabled = true;
 document.querySelector('#clear-chat').disabled = true;
 chatBubble(message, 'user'); chatInput.value = '';
 chatStatus.textContent = 'Asistentul îți pregătește răspunsul…';
 try {
  const response = await fetch('/chat', {method:'POST',headers:{'Content-Type':'application/json','X-Chat-Token':chatPanel.dataset.token},body:JSON.stringify({message,history:chatHistory.slice(-10),week:chatPanel.dataset.week})});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Chatul nu a putut răspunde.');
  chatBubble(result.reply, 'assistant');
  chatHistory.push({role:'user',content:message},{role:'assistant',content:result.reply});
  chatHistory = chatHistory.slice(-10);
  chatStatus.textContent = '';
 } catch (error) {
  chatStatus.textContent = error.message || 'Conexiunea a fost întreruptă. Încearcă din nou.';
  chatInput.value = message;
 } finally {
  chatBusy = false; sendChat.disabled = false;
  document.querySelector('#clear-chat').disabled = false;
 }
});
document.querySelectorAll('[data-chat-prompt]').forEach(button => button.addEventListener('click', () => {
 if (chatBusy) return;
 chatInput.value = button.dataset.chatPrompt;
 chatInput.focus();
}));
document.querySelector('#clear-chat').addEventListener('click', () => {
 if (chatBusy) return;
 chatHistory = []; chatMessages.replaceChildren(); chatStatus.textContent = ''; chatInput.value = '';
 chatBubble('O conversație nouă. Cu ce te ajut pentru săptămâna aceasta?', 'assistant');
});
const openChat = document.querySelector('#open-chat');
const closeChat = document.querySelector('#close-chat');
function toggleChat(open) {
 chatPanel.classList.toggle('chat-open', open);
 openChat.setAttribute('aria-expanded', String(open));
 if (open) chatInput.focus(); else openChat.focus();
}
openChat.addEventListener('click', () => toggleChat(true));
closeChat.addEventListener('click', () => toggleChat(false));
chatPanel.addEventListener('keydown', event => {
 if (event.key === 'Escape' && window.matchMedia('(max-width:1099px)').matches) toggleChat(false);
});
chatInput.addEventListener('keydown', event => {
 if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
  event.preventDefault(); chatForm.requestSubmit();
 }
});
