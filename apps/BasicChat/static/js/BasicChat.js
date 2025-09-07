// BasicChat.js - Raum-Management ohne Nachrichten-Funktionalität
console.log("🚀 BasicChat Frontend geladen");

// === GLOBALE VARIABLEN ===
let socket = null;
let isConnected = false;
let currentChatRoom = null;

// === SOCKET.IO INTEGRATION ===
function initializeSocketIO() {
  if (typeof io === "undefined") {
    console.error("❌ Socket.IO nicht verfügbar!");
    return;
  }

  console.log("🔌 Initialisiere Socket.IO...");

  try {
    socket = io();
    setupSocketEvents();
  } catch (error) {
    console.error("❌ Socket.IO Fehler:", error);
  }
}

function setupSocketEvents() {
  // === BASIS VERBINDUNGS-EVENTS ===
  socket.on("connect", () => {
    console.log("✅ Socket.IO verbunden!");
    isConnected = true;
  });

  socket.on("disconnect", () => {
    console.log("❌ Socket.IO getrennt");
    isConnected = false;
    currentChatRoom = null;
  });

  socket.on("connect_error", (error) => {
    console.error("❌ Verbindungsfehler:", error);
  });

  // === RAUM-MANAGEMENT EVENTS (mit SocketIOManager Prefix) ===
  socket.on("BasicChat_room_joined_successfully", (data) => {
    console.log(`✅ Erfolgreich Raum ${data.room_number} beigetreten`);
    currentChatRoom = data.room_number;
    updateUIForRoomJoin(data);
  });

  socket.on("BasicChat_room_left_successfully", (data) => {
    console.log(`👋 Raum ${data.room_number} verlassen`);
    currentChatRoom = null;
    updateUIForRoomLeave(data);
  });

  socket.on("BasicChat_user_joined_room", (data) => {
    console.log(`👤 ${data.username} ist Raum ${data.room_number} beigetreten`);
    if (data.room_number === currentChatRoom) {
      showRoomNotification(`${data.username} ist dem Chat beigetreten`, "join");
    }
  });

  socket.on("BasicChat_user_left_room", (data) => {
    console.log(`👋 ${data.username} hat Raum ${data.room_number} verlassen`);
    if (data.room_number === currentChatRoom) {
      const reason =
        data.reason === "disconnected"
          ? "die Verbindung verloren"
          : "den Chat verlassen";
      showRoomNotification(`${data.username} hat ${reason}`, "leave");
    }
  });

  socket.on("BasicChat_room_info_response", (data) => {
    console.log("🏠 Raum-Info:", data);
    currentChatRoom = data.current_room;
    updateUIForCurrentRoom(data);
  });

  socket.on("BasicChat_client_message_recieved", (data) => {
    console.log("Neue Nachricht von Client:", data.message);
    console.log("Aktuelle Zeit:", data.current_time);

    // Element erstellen UND zum DOM hinzufügen
    const messageElement = createMessageElement(data.message, data);
    const chatContainer = document.getElementById("chat-messages-container");

    if (chatContainer) {
      chatContainer.appendChild(messageElement); // ✅ Jetzt wird es angezeigt!
    } else {
      console.error("Chat-Container nicht gefunden!");
    }
  });

  // === HARLEMSHAKE EVENT (bleibt global) ===
  socket.on("BasicChat_do_the_harlemshake_reply", (data) => {
    console.log("🕺 Harlemshake von:", data.sender, "Admin:", data.isAdmin);

    if (data.isAdmin === true) {
      doScreenShake();
    } else {
      const currentUser = getCurrentUser();
      if (currentUser.name === data.sender) {
        doScreenShake();
      }
    }
  });

  console.log("🎮 Socket.IO Events für Raum-Management registriert");
}

// === RAUM-MANAGEMENT FUNKTIONEN ===
function joinChatRoom(roomNumber) {
  if (!socket || !isConnected) {
    console.error("❌ Socket.IO nicht verbunden");
    return false;
  }

  console.log(`🏠 Betrete Chat-Raum: ${roomNumber}`);

  socket.emit("BasicChat_join_chat_room", {
    room_number: roomNumber,
  });

  return true;
}

function leaveChatRoom() {
  if (!socket || !isConnected || !currentChatRoom) {
    console.log("❌ Nicht in einem Raum oder nicht verbunden");
    return false;
  }

  console.log(`👋 Verlasse Chat-Raum: ${currentChatRoom}`);

  socket.emit("BasicChat_leave_chat_room", {
    room_number: currentChatRoom,
  });

  return true;
}

function getCurrentRoomInfo() {
  if (!socket || !isConnected) {
    console.error("❌ Socket.IO nicht verbunden");
    return;
  }

  socket.emit("BasicChat_get_room_info");
}

// === UI UPDATE FUNKTIONEN ===
function updateUIForRoomJoin(data) {
  const chatNameElement = document.getElementById("chat-name");
  if (chatNameElement) {
    chatNameElement.textContent = `Raum: ${data.room_number}`;
  }

  showChatInput(); // ✅ NEU: Input anzeigen
  showRoomNotification(`Du bist dem Chat beigetreten`, "success");
}

function updateUIForRoomLeave(data) {
  const chatNameElement = document.getElementById("chat-name");
  if (chatNameElement) {
    chatNameElement.textContent = "Kein Chat ausgewählt";
  }

  hideChatInput(); // ✅ NEU: Input verstecken
  showRoomNotification(`Du hast den Chat verlassen`, "info");
}
function updateUIForCurrentRoom(data) {
  if (data.is_in_room && data.current_room) {
    console.log(`📍 Aktuell in Raum: ${data.current_room}`);
  } else {
    console.log("📍 Nicht in einem Raum");
  }
}

function showRoomNotification(message, type = "info") {
  console.log(`📢 ${type.toUpperCase()}: ${message}`);

  // TODO: Hier könnte eine Toast-Notification oder ähnliches angezeigt werden
  // Für jetzt nur Console-Output
}

// === HILFSFUNKTIONEN ===
function getCurrentUser() {
  const userElement = document.querySelector(".main-sidbar-profil p");
  const isAdmin = document.querySelector('[href="#"]') !== null;

  return {
    name: userElement ? userElement.textContent.trim() : "Unbekannt",
    isAdmin: isAdmin,
  };
}

function extractRoomNumberFromUrl(url) {
  const match = url.match(/\/([^\/]+)$/);
  return match ? match[1] : null;
}

function doScreenShake() {
  document.body.style.transition = "transform 2s ease-in-out";
  document.body.style.transform = "rotate(360deg)";

  setTimeout(() => {
    document.body.style.transform = "rotate(0deg)";
  }, 2000);
}

// === CHAT LADEN FUNKTIONEN (erweitert) ===
function loadChat(load_chat_url, load_chat_messages_url) {
  console.log("📥 Lade Chat von:", load_chat_url);

  // Chat-Raum-Nummer aus URL extrahieren
  const roomNumber = extractRoomNumberFromUrl(load_chat_url);

  // Raum beitreten (falls roomNumber vorhanden)
  if (roomNumber) {
    joinChatRoom(roomNumber);
  }

  // Chat-Informationen laden
  fetch(load_chat_url)
    .then((response) => response.json())
    .then((data) => {
      setTimeout(() => modifyChat(data), 100);
    })
    .catch((error) => {
      console.error("❌ Fehler beim Laden des Chats:", error);
    });

  // Chat-Nachrichten laden (Placeholder)
  fetch(load_chat_messages_url)
    .then((response) => response.json())
    .then((data) => {
      setTimeout(() => modifyChatMessages(data, roomNumber), 100);
    })
    .catch((error) => {
      console.error("❌ Fehler beim Laden der Nachrichten:", error);
    });
}

function modifyChat(data) {
  const { chat, type, error_message } = data;
  console.log("Chat-Daten:", chat);
  console.log("Chat-Typ:", type);

  if (chat && chat.group_name) {
    const chatNameElement = document.getElementById("chat-name");
    if (chatNameElement) {
      chatNameElement.innerHTML = chat.group_name;
    }
  }

  if (error_message) {
    console.error("Chat-Fehler:", error_message);
    showRoomNotification(`Fehler: ${error_message}`, "error");
  }
}

function modifyChatMessages(data, room_number) {
  console.log("Nachrichten-Daten:", data);
  // Chat-Container finden
  const chatContainer = document.getElementById("chat-messages-container");
  if (!chatContainer) {
    console.error("Chat-Container nicht gefunden!");
    return;
  }

  // Container leeren (Placeholder entfernen)
  chatContainer.innerHTML = "";

  if (data.success && data.room_number === room_number) {
    console.log("System meldet Sucess True und Room-Nummer stimmt");
    console.log("Hier die Nachrichten:", data.messages);
  } else {
    console.log("System meldet Sucess True und Room-Nummer stimmt nicht");
    console.log("Hier die Nachrichten:", data.messages);
    return;
  }
  // Prüfen ob Nachrichten vorhanden
  if (data.messages && data.messages.length > 0) {
    console.log(`📨 ${data.messages.length} Nachrichten geladen`);

    // Für jede Nachricht ein HTML-Element erstellen
    data.messages.forEach((message) => {
      const messageElement = createMessageElement(message, data);
      chatContainer.appendChild(messageElement);
    });
  }

  // Falls der Chat Leer ist, dann kann eine standart Nachritch im Gui angezeigt werden. Noch nichts los hier, schreibe denen Compadres ;)
  if (data.messages && data.messages.length > 0) {
    console.log(`📨 ${data.messages.length} Nachrichten geladen`);
  }
}

// === HARLEMSHAKE FUNKTION ===
function sendHarlemshake() {
  if (socket && isConnected) {
    const user = getCurrentUser();
    console.log("🕺 Sende Harlemshake-Befehl");
    console.log(user);

    socket.emit("BasicChat_do_the_harlemshake", {
      name: user.name,
      isAdmin: user.isAdmin,
    });
  } else {
    console.log("❌ Nicht mit Socket verbunden");
  }
}

// === INITIALISIERUNG ===
document.addEventListener("DOMContentLoaded", function () {
  console.log("🏁 DOM bereit - BasicChat geladen");

  // Socket.IO initialisieren
  initializeSocketIO();
  initializeMessageInput(); // ✅ NEU
});

// === DEBUG-FUNKTIONEN ===
window.ChatDebug = {
  // Socket Status
  status: () => {
    return {
      connected: isConnected,
      socket: socket ? "initialized" : "not initialized",
      currentRoom: currentChatRoom,
    };
  },

  // Raum-Management
  joinRoom: (roomNumber) => {
    return joinChatRoom(roomNumber);
  },

  getRoomInfo: () => {
    getCurrentRoomInfo();
  },

  // Harlemshake testen
  harlemshake: () => {
    sendHarlemshake();
  },
};

function initializeMessageInput() {
  const messageInput = document.getElementById("messageInput");
  const sendButton = document.getElementById("sendButton");

  if (!messageInput || !sendButton) return;

  // Send Button Click
  sendButton.addEventListener("click", () => {
    sendMessage();
  });

  // Enter-Taste
  messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  });

  console.log("✅ Message Input initialisiert");
}

function showChatInput() {
  document.getElementById("chat-input-area").style.display = "block";
}

function hideChatInput() {
  document.getElementById("chat-input-area").style.display = "none";
}
console.log("📚 BasicChat Modul geladen - Raum-Management aktiv");

function sendMessage() {
  const messageInput = document.getElementById("messageInput");
  const message = messageInput.value.trim();

  if (!message) {
    console.log("❌ Leere Nachricht");
    return;
  }

  if (!currentChatRoom) {
    console.log("❌ Kein Chat ausgewählt");
    return;
  }

  console.log(`📤 Sende Nachricht: "${message}" an Raum: ${currentChatRoom}`);

  // TODO: Hier kommt später die Socket.IO Logik
  socket.emit("BasicChat_send_message", {
    message: message,
    room_number: currentChatRoom,
  });

  // Input leeren
  messageInput.value = "";
}

// Hilfsfunktion: HTML-Element für eine Nachricht erstellen
function createMessageElement(message, data) {
  // === 1. HAUPT-CONTAINER ERSTELLEN ===
  const messageDiv = document.createElement("div");

  // === 2. CSS-KLASSEN BASIEREND AUF ABSENDER ===
  const currentUser = getCurrentUser();
  if (message.username === currentUser.name) {
    // Eigene Nachricht - rechtsbündig
    messageDiv.className = "chat-message-container chat-message-container-self";
  } else {
    // Fremde Nachricht - linksbündig
    messageDiv.className = "chat-message-container";
  }

  // === 3. BENUTZER-INFO ELEMENT ===
  const userInfo = document.createElement("div");
  userInfo.className = "chat-message-user-info";
  userInfo.textContent = message.username || "Unbekannt";

  // === 4. NACHRICHTEN-TEXT ELEMENT ===
  const messageText = document.createElement("div");
  messageText.className = "chat-message-text";
  // HIER den eigentlichen Nachrichtentext hinzufügen:
  messageText.textContent = message.message || "Leere Nachricht";

  // === 5. DATUM/ZEIT FOOTER ===
  const footer = document.createElement("div");
  footer.className = "chat-message-footer";

  if (message.created_at) {
    const messageDate = new Date(message.created_at);
    const currentDate = new Date(data.current_time);

    const isToday = messageDate.toDateString() === currentDate.toDateString();

    if (isToday) {
      footer.textContent = messageDate.toLocaleTimeString("de-DE", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else {
      const time = messageDate.toLocaleTimeString("de-DE", {
        hour: "2-digit",
        minute: "2-digit",
      });
      const date = messageDate.toLocaleDateString("de-DE", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      });
      footer.textContent = `${time} / ${date}`;
    }
  }

  // === 6. ALLES ZUSAMMENSETZEN ===
  messageDiv.appendChild(userInfo); // Username oben
  messageDiv.appendChild(messageText); // Nachricht in der Mitte
  messageDiv.appendChild(footer); // Zeit unten

  return messageDiv;
}

// Chat erstellene

// === DYNAMISCHE MODAL FUNKTIONEN ===
function openModal(modalId) {
  const modalElement = document.getElementById(modalId);
  if (modalElement) {
    modalElement.style.display = "block";
    modalElement.classList.add("show");
    document.body.classList.add("modal-open");
  }
}

function closeModal(modalId) {
  const modalElement = document.getElementById(modalId);
  if (modalElement) {
    modalElement.style.display = "none";
    modalElement.classList.remove("show");
  }

  // Prüfen ob noch andere Modals offen sind
  const openModals = document.querySelectorAll(".modal.show");
  if (openModals.length === 0) {
    document.body.classList.remove("modal-open");
  }
}

function closeAndOpenNewModal(closeModalId, openModalId) {
  // Erstes Modal schließen
  const closeModalElement = document.getElementById(closeModalId);
  if (closeModalElement) {
    closeModalElement.style.display = "none";
    closeModalElement.classList.remove("show");
  }

  // Zweites Modal öffnen
  const openModalElement = document.getElementById(openModalId);
  if (openModalElement) {
    openModalElement.style.display = "block";
    openModalElement.classList.add("show");
  }

  // Body-Klasse bleibt (da ein Modal noch offen ist)
  document.body.classList.add("modal-open");
}

function closeAllModals() {
  document.querySelectorAll(".modal").forEach((modal) => {
    modal.style.display = "none";
    modal.classList.remove("show");
  });
  document.body.classList.remove("modal-open");
}

// === SPEZIFISCHE MODAL FUNKTIONEN ===
function openNewChatModal() {
  openModal("new-chat-modal-main");
}

function createGroupTest() {
  const groupName = document.getElementById("group-name-input").value.trim();

  if (!groupName) {
    alert("Bitte geben Sie einen Gruppennamen ein!");
    return;
  }

  // Test-Funktion
  console.log(`Test: Neue Gruppe erstellt mit Namen: "${groupName}"`);
  alert(`Test: Gruppe "${groupName}" wurde erstellt!`);

  // Modal schließen und Input zurücksetzen
  closeAllModals();
  document.getElementById("group-name-input").value = "";
}
