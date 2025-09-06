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
  // Chat-Header aktualisieren wenn möglich
  const chatNameElement = document.getElementById("chat-name");
  if (chatNameElement) {
    chatNameElement.textContent = `Raum: ${data.room_number}`;
  }

  showRoomNotification(`Du bist dem Chat beigetreten`, "success");
}

function updateUIForRoomLeave(data) {
  const chatNameElement = document.getElementById("chat-name");
  if (chatNameElement) {
    chatNameElement.textContent = "Kein Chat ausgewählt";
  }

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
      setTimeout(() => modifyChatMessages(data), 100);
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

function modifyChatMessages(data) {
  console.log("Nachrichten-Daten:", data);

  if (data.success && data.info) {
    console.log("ℹ️", data.info);
  }

  // Placeholder - echte Nachrichten kommen in Phase 2
  if (data.messages && data.messages.length > 0) {
    console.log(`📨 ${data.messages.length} Nachrichten geladen`);
  }
}

// === HARLEMSHAKE FUNKTION ===
function sendHarlemshake() {
  if (socket && isConnected) {
    const user = getCurrentUser();
    console.log("🕺 Sende Harlemshake-Befehl");

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

  leaveRoom: () => {
    return leaveChatRoom();
  },

  getRoomInfo: () => {
    getCurrentRoomInfo();
  },

  // Harlemshake testen
  harlemshake: () => {
    sendHarlemshake();
  },
};

console.log("📚 BasicChat Modul geladen - Raum-Management aktiv");
