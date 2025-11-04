async function sendMsg() {
    const input = document.getElementById("user-input");
    const messages = document.getElementById("messages");
  
    const userText = input.value.trim();
    if (!userText) return;
  
    messages.innerHTML += `<div class="msg user"><strong>You:</strong> ${userText}</div>`;
    input.value = "";
  
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userMessage: userText })
    });
    const data = await res.json();
  
    messages.innerHTML += `<div class="msg bot"><strong>Porta:</strong> ${data.reply}</div>`;
    messages.scrollTop = messages.scrollHeight;
  }
  