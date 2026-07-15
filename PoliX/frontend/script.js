const API = '/ask';

const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const quicks = document.querySelectorAll('.quick');

/*CHAT UI FUNCTIONS*/

function createMsgNode(text, who = 'bot', debugScore = null) {
  const row = document.createElement('div');
  row.className = 'msg-row ' + (who === 'bot' ? 'bot' : 'user');

  if (who === 'bot') {
  const av = document.createElement('div');
  av.className = 'avatar';
  av.textContent = '🤖';
  const bubble = document.createElement('div');
  bubble.className = 'bubble';

  bubble.innerHTML = sanitizeHTML(text) +
    (debugScore ? `<div style="margin-top:8px;font-size:12px;color:rgba(0,0,0,0.45)">score: ${debugScore.toFixed(3)}</div>` : '');

  row.appendChild(av);
  row.appendChild(bubble);
} else {
    const bubble = document.createElement('div');
    bubble.className = 'bubble user';
    bubble.textContent = text;
    row.appendChild(bubble);
  }
  return row;
}

function sanitizeHTML(s) {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

function appendMessage(text, who = 'bot', score = null) {
  const node = createMsgNode(text, who, score);
  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

/*SEND QUESTION*/

async function sendQuestion(q) {
  if (!q) return;
  appendMessage(q, 'user');

  const typing = createMsgNode('...', 'bot');
  messagesEl.appendChild(typing);

  try {
    const res = await fetch(API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    });
    const data = await res.json();

    typing.remove();
    appendMessage(data.answer || 'Nuk gjeta informacion.', 'bot', data.debug_score || null);

  } catch (err) {
    typing.remove();
    appendMessage('Gabim: serveri nuk përgjigjet.', 'bot');
  }
}

/*INPUT HANDLERS */

sendBtn.addEventListener('click', () => {
  const v = inputEl.value.trim();
  if (!v) return;
  sendQuestion(v);
  inputEl.value = '';
});

inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    sendBtn.click();
  }
});

quicks.forEach(btn => {
  btn.addEventListener('click', () => sendQuestion(btn.dataset.q));
});

function clearChat() {
  messagesEl.innerHTML = "";
}

/*CHAT HISTORY*/

window.onload = () => {
  loadHistory();
};

function saveToHistory(text) {
  let history = JSON.parse(localStorage.getItem("chatHistory") || "[]");
  history.unshift(text);
  localStorage.setItem("chatHistory", JSON.stringify(history));
  loadHistory();
}

function loadHistory() {
  let history = JSON.parse(localStorage.getItem("chatHistory") || "[]");
  let container = document.getElementById("chat-history");
  container.innerHTML = "";

  history.forEach(item => {
    let div = document.createElement("div");
    div.classList.add("history-item");
    div.innerText = item;
    div.onclick = () => loadConversation(item);
    container.appendChild(div);
  });
}

function handleUserMessage(msg) {
  saveToHistory(msg);
}

/*GOOGLE LOGIN*/


google.accounts.id.initialize({
  client_id: "YOUR_CLIENT_ID_HERE",
  callback: handleCredentialResponse
});


try {
  google.accounts.id.renderButton(
    document.getElementById("googleButton"),
    { theme: "outline", size: "large" }
  );
} catch (e) {

}


google.accounts.id.prompt();


function manualGoogleLogin() {
  google.accounts.id.prompt();
}


async function handleCredentialResponse(response) {
  const idToken = response.credential;

  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idToken })
  });

  const data = await res.json();

  if (data.status === "success") {
    alert("Logged in as: " + data.email);
    localStorage.setItem("userEmail", data.email);
  } else {
    alert("Login failed");
  }
}
