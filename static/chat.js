const chatPanel = document.querySelector('#ai-chat');
const chatForm = document.querySelector('#chat-form');
const chatInput = document.querySelector('#chat-input');
const chatMessages = document.querySelector('#chat-messages');
const chatStatus = document.querySelector('#chat-status');
const sendChat = document.querySelector('#send-chat');
let chatBusy = false;
let failedRequest = null;
function chatBubble(text, role) {
 const bubble = document.createElement('p');
 bubble.className = `chat-bubble ${role}`; bubble.textContent = text;
 chatMessages.append(bubble); chatMessages.scrollTop = chatMessages.scrollHeight;
}
function setBusy(value) {
 chatBusy = value; document.querySelector('#upload-timetable').disabled = value; sendChat.disabled = value; document.querySelector('#clear-chat').disabled = value;
}
async function restoreChat() {
 setBusy(true);
 try {
  const response = await fetch('/chat/history');
  if (!response.ok) throw new Error('Nu am putut încărca conversația.');
  const result = await response.json();
  if (result.messages.length) {
   chatMessages.replaceChildren(); result.messages.forEach(message => chatBubble(message.content, message.role));
  }
 } catch (error) { chatStatus.textContent = error.message; }
 finally { setBusy(false); }
}
async function refreshPlan(week) {
 const response = await fetch(`/?week=${encodeURIComponent(week)}`);
 if (!response.ok) throw new Error('Activitatea este salvată. Reîncarcă pagina pentru a actualiza calendarul.');
 const doc = new DOMParser().parseFromString(await response.text(), 'text/html');
 document.querySelector('main').replaceWith(doc.querySelector('main'));
 chatPanel.dataset.week = week;
 document.querySelector('.chat-context span').textContent = doc.querySelector('.chat-context span').textContent;
 const url = new URL(location.href); url.searchParams.set('week', week); window.history.replaceState(null, '', url);
 document.querySelector('#activity-form').elements.week.value = week;
}
chatForm.addEventListener('submit', async event => {
 event.preventDefault();
 const message = chatInput.value.trim();
 if (!message || chatBusy) return;
 const requestId = failedRequest?.message === message ? failedRequest.id : crypto.randomUUID();
 setBusy(true);
 if (failedRequest?.message !== message) chatBubble(message, 'user');
 chatInput.value = '';
 chatStatus.textContent = 'Asistentul îți pregătește răspunsul…';
 try {
  const response = await fetch('/chat', {method:'POST',headers:{'Content-Type':'application/json','X-Chat-Token':chatPanel.dataset.token},body:JSON.stringify({message,request_id:requestId,week:chatPanel.dataset.week})});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Chatul nu a putut răspunde.');
  failedRequest = null; chatBubble(result.reply, 'assistant'); chatStatus.textContent = '';
  if (result.changed) await refreshPlan(result.week);
 } catch (error) {
  failedRequest = {message, id:requestId}; chatStatus.textContent = error.message || 'Conexiunea a fost întreruptă.'; chatInput.value = message;
 } finally { setBusy(false); }
});
document.querySelectorAll('[data-chat-prompt]').forEach(button => button.addEventListener('click', () => {
 if (!chatBusy) { chatInput.value = button.dataset.chatPrompt; chatInput.focus(); }
}));
document.querySelector('#clear-chat').addEventListener('click', async () => {
 if (chatBusy) return;
 setBusy(true);
 try {
  const response = await fetch('/chat/clear', {method:'POST', headers:{'X-Chat-Token':chatPanel.dataset.token}});
  if (!response.ok) throw new Error('Nu am putut începe conversația nouă.');
  failedRequest = null; chatMessages.replaceChildren(); chatStatus.textContent = ''; chatInput.value = '';
  chatBubble('Cu ce începem? Spune-mi ce ai de făcut sau unde ai nevoie de ajutor.', 'assistant');
 } catch (error) { chatStatus.textContent = error.message; }
 finally { setBusy(false); }
});
const openChat = document.querySelector('#open-chat');
const closeChat = document.querySelector('#close-chat');
function toggleChat(open) {
 chatPanel.classList.toggle('chat-open', open); openChat.setAttribute('aria-expanded', String(open));
 if (open) chatInput.focus(); else openChat.focus();
}
openChat.addEventListener('click', () => toggleChat(true));
closeChat.addEventListener('click', () => toggleChat(false));
chatPanel.addEventListener('keydown', event => {
 if (event.key === 'Escape' && window.matchMedia('(max-width:1099px)').matches) toggleChat(false);
});
chatInput.addEventListener('keydown', event => {
 if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); chatForm.requestSubmit(); }
});
restoreChat();

const photoInput=document.querySelector('#timetable-photo');
document.querySelector('#upload-timetable').addEventListener('click',()=>{if(!chatBusy)photoInput.click();});
photoInput.addEventListener('change',async()=>{
 const file=photoInput.files[0];if(!file||chatBusy)return;
 if(file.size>8*1024*1024){chatStatus.textContent='Poza trebuie să aibă cel mult 8 MB.';photoInput.value='';return;}
 setBusy(true);chatStatus.textContent='Citesc orarul din poză… Poate dura câteva minute.';
 const form=new FormData();form.append('photo',file);form.append('request_id',crypto.randomUUID());form.append('message',chatInput.value.trim());
 try{
 const response=await fetch('/chat/photo',{method:'POST',headers:{'X-Chat-Token':chatPanel.dataset.token},body:form});
 const result=await response.json();if(!response.ok)throw new Error(result.error||'Nu am putut citi poza.');
 chatBubble('📷 Fotografie cu orarul','user');chatBubble(result.reply,'assistant');chatInput.value='';chatStatus.textContent='';if(result.changed)await refreshPlan(result.week);
 }catch(error){chatStatus.textContent=error.message;}finally{setBusy(false);photoInput.value='';}
});
