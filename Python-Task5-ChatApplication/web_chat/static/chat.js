// Browser side of the chat. Message text is always inserted with
// textContent (never innerHTML), so a message can never inject HTML or scripts.
(function () {
  const socket = io();
  const me = document.body.dataset.username;
  const defaultRoom = document.body.dataset.defaultRoom;
  const roomList = document.getElementById("room-list");
  const messages = document.getElementById("messages");
  const roomTitle = document.getElementById("room-title");
  const errorBar = document.getElementById("error-bar");
  const messageForm = document.getElementById("message-form");
  const messageInput = document.getElementById("message-input");
  const newRoomForm = document.getElementById("new-room-form");
  const newRoomInput = document.getElementById("new-room-input");
  const notifyButton = document.getElementById("notify-button");
  const originalTitle = document.title;
  let currentRoom = null;
  let unread = 0;

  function showError(text) {
    errorBar.textContent = text;
    errorBar.hidden = false;
    setTimeout(() => { errorBar.hidden = true; }, 4000);
  }

  function addLine(className, time, author, text) {
    const item = document.createElement("li");
    item.className = className;
    const timeSpan = document.createElement("span");
    timeSpan.className = "time";
    timeSpan.textContent = "[" + time + "]";
    item.appendChild(timeSpan);
    if (author) {
      const authorSpan = document.createElement("span");
      authorSpan.className = "author";
      authorSpan.textContent = author + ":";
      item.appendChild(authorSpan);
    }
    const body = document.createElement("span");
    body.textContent = text;
    item.appendChild(body);
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
  }

  function addChatMessage(m) {
    addLine(m.username === me ? "mine" : "", m.time, m.username, m.text);
  }

  function renderRooms(rooms) {
    roomList.innerHTML = "";
    rooms.forEach((name) => {
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "# " + name;
      if (name === currentRoom) button.classList.add("active");
      button.addEventListener("click", () => socket.emit("join", { room: name }));
      li.appendChild(button);
      roomList.appendChild(li);
    });
  }

  function notifyIfAway(m) {
    if (m.username === me || document.hasFocus()) return;
    unread += 1;
    document.title = "(" + unread + ") " + originalTitle;
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification(m.username + " in #" + m.room, { body: m.text });
    }
  }

  window.addEventListener("focus", () => { unread = 0; document.title = originalTitle; });

  socket.on("connect", () => socket.emit("join", { room: currentRoom || defaultRoom }));
  socket.on("connect_error", () => { roomTitle.textContent = "Not connected - please log in again."; });
  socket.on("disconnect", () => { roomTitle.textContent = "Disconnected - reconnecting..."; });
  socket.on("rooms", (data) => renderRooms(data.rooms));
  socket.on("history", (data) => {
    currentRoom = data.room;
    roomTitle.textContent = "# " + data.room;
    messages.innerHTML = "";
    data.messages.forEach(addChatMessage);
    Array.from(roomList.querySelectorAll("button")).forEach((b) =>
      b.classList.toggle("active", b.textContent === "# " + data.room));
  });
  socket.on("message", (m) => { addChatMessage(m); notifyIfAway(m); });
  socket.on("system", (m) => addLine("system", m.time, "", m.text));
  socket.on("error_message", (m) => showError(m.error));
  socket.on("room_created", (m) => socket.emit("join", { room: m.room }));

  messageForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = messageInput.value.trim();
    if (!text) return;
    socket.emit("message", { text: text });
    messageInput.value = "";
  });

  newRoomForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const name = newRoomInput.value.trim();
    if (!name) return;
    socket.emit("create_room", { name: name });
    newRoomInput.value = "";
  });

  notifyButton.addEventListener("click", () => {
    if (!("Notification" in window)) { showError("This browser does not support notifications."); return; }
    Notification.requestPermission().then((result) => {
      if (result !== "granted") showError("Notifications were not allowed.");
    });
  });
})();
