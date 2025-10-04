// BasicChat.js - KORRIGIERTE VERSION mit Benutzerinformationen
console.log("🚀 BasicChat Frontend geladen");

// === GLOBALE VARIABLEN ===
let socket = null;
let isConnected = false;
let currentChatRoom = null;
let currentChatInfo = null; // ✅ NEU: Chat-Info mit User-Details speichern

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
    currentChatInfo = null; // ✅ NEU: Chat-Info zurücksetzen
  });

  socket.on("connect_error", (error) => {
    console.error("❌ Verbindungsfehler:", error);
  });

  // === ERWEITERTE RAUM-MANAGEMENT EVENTS ===
  socket.on("BasicChat_room_joined_successfully", (data) => {
    console.log(`✅ Erfolgreich Raum ${data.room_number} beigetreten`);
    currentChatRoom = data.room_number;
    currentChatInfo = data.chat_info; // ✅ NEU: Chat-Info speichern
    updateUIForRoomJoin(data);
  });

  socket.on("BasicChat_room_left_successfully", (data) => {
    console.log(`👋 Raum ${data.room_number} verlassen`);
    currentChatRoom = null;
    currentChatInfo = null; // ✅ NEU: Chat-Info zurücksetzen
    updateUIForRoomLeave(data);
  });

  socket.on("BasicChat_user_joined_room", (data) => {
    console.log(`👤 ${data.username} ist Raum ${data.room_number} beigetreten`);
    if (data.room_number === currentChatRoom) {
      // ✅ ERWEITERT: Admin-Badge in Notification berücksichtigen
      const adminBadge = data.is_admin ? " 👑" : "";
      showRoomNotification(
        `${data.username}${adminBadge} ist dem Chat beigetreten`,
        "join"
      );
    }
  });

  socket.on("BasicChat_user_left_room", (data) => {
    console.log(`👋 ${data.username} hat Raum ${data.room_number} verlassen`);
    if (data.room_number === currentChatRoom) {
      const reason =
        data.reason === "disconnected"
          ? "die Verbindung verloren"
          : "den Chat verlassen";
      const adminBadge = data.is_admin ? " 👑" : "";
      showRoomNotification(
        `${data.username}${adminBadge} hat ${reason}`,
        "leave"
      );
    }
  });

  socket.on("BasicChat_room_info_response", (data) => {
    console.log("🏠 Raum-Info:", data);
    currentChatRoom = data.current_room;
    currentChatInfo = data.chat_info; // ✅ NEU: Chat-Info speichern
    updateUIForCurrentRoom(data);
  });

  // ✅ ERWEITERT: Nachrichten mit vollständigen Benutzerinformationen
  socket.on("BasicChat_client_message_recieved", (data) => {
    console.log("📨 Neue Nachricht empfangen:", data);

    if (data.success && data.message) {
      console.log("✅ Nachricht erfolgreich empfangen:", data.message);
      console.log("👤 User-Info in Nachricht:", {
        username: data.message.username,
        is_admin: data.message.is_admin,
        user_exists: data.message.user_exists,
      });

      // ✅ NEU: Erweiterte createMessageElement mit User-Info
      const messageElement = createMessageElementWithUserInfo(
        data.message,
        data
      );
      const chatContainer = document.getElementById("chat-messages-container");

      if (chatContainer) {
        chatContainer.appendChild(messageElement);
        scrollToBottom(); // ✅ NEU: Auto-scroll zu neuesten Nachrichten
      } else {
        console.error("❌ Chat-Container nicht gefunden!");
      }
    } else {
      console.error("❌ Nachricht-Fehler:", data.error);
      showRoomNotification(`Fehler: ${data.error}`, "error");
    }
  });

  // ✅ NEU: Error-Handler für Raum-Beitritt
  socket.on("BasicChat_join_room_error", (data) => {
    console.error("❌ Fehler beim Raum-Beitritt:", data.error);
    showRoomNotification(`Zugang verweigert: ${data.error}`, "error");
  });

  // ✅ NEU: User-Info Response
  socket.on("BasicChat_user_info_response", (data) => {
    if (data.success) {
      console.log("👤 User-Info erhalten:", data.user);
      // Hier könntest du die User-Info im UI verwenden
    } else {
      console.error("❌ User-Info Fehler:", data.error);
    }
  });

  // === HARLEMSHAKE EVENT (unverändert) ===
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

  console.log("🎮 Socket.IO Events mit Benutzerinformationen registriert");
}

// === ERWEITERTE UI UPDATE FUNKTIONEN ===
function updateUIForRoomJoin(data) {
  const chatNameElement = document.getElementById("chat-name");
  if (chatNameElement) {
    // ✅ ERWEITERT: Zeige Chat-Name basierend auf Chat-Info
    if (data.chat_info) {
      if (data.chat_info.group_name) {
        // Gruppenchat
        chatNameElement.textContent = data.chat_info.group_name;
      } else if (data.chat_info.display_name) {
        // Normaler Chat
        chatNameElement.textContent = data.chat_info.display_name;
      } else {
        chatNameElement.textContent = `Raum: ${data.room_number}`;
      }

      // ✅ NEU: Zeige zusätzliche Chat-Info
      updateChatDetails(data.chat_info);
    } else {
      chatNameElement.textContent = `Raum: ${data.room_number}`;
    }
  }

  showChatInput();
  showRoomNotification(`Du bist dem Chat beigetreten`, "success");
}

function updateUIForRoomLeave(data) {
  const chatNameElement = document.getElementById("chat-name");
  if (chatNameElement) {
    chatNameElement.textContent = "Kein Chat ausgewählt";
  }

  clearChatDetails(); // ✅ NEU: Chat-Details zurücksetzen
  hideChatInput();
  showRoomNotification(`Du hast den Chat verlassen`, "info");
}

function updateUIForCurrentRoom(data) {
  if (data.is_in_room && data.current_room) {
    console.log(`📍 Aktuell in Raum: ${data.current_room}`);
    // ✅ NEU: Chat-Details aktualisieren wenn vorhanden
    if (data.chat_info) {
      updateChatDetails(data.chat_info);
    }
  } else {
    console.log("📍 Nicht in einem Raum");
    clearChatDetails();
  }
}

// ✅ NEU: Chat-Details anzeigen
function updateChatDetails(chatInfo) {
  const chatStatusElement = document.querySelector(".chat-status");
  if (!chatStatusElement) return;

  let statusText = "";

  if (chatInfo.group_name) {
    // Gruppenchat
    const memberCount = chatInfo.members_with_names
      ? chatInfo.members_with_names.length
      : 0;
    statusText = `${memberCount} Mitglieder`;

    if (chatInfo.creator_username) {
      statusText += ` • Erstellt von ${chatInfo.creator_username}`;
    }
  } else if (chatInfo.display_name) {
    // Normaler Chat
    statusText = "Privater Chat";
  }

  chatStatusElement.textContent = statusText;
}

// ✅ NEU: Chat-Details zurücksetzen
function clearChatDetails() {
  const chatStatusElement = document.querySelector(".chat-status");
  if (chatStatusElement) {
    chatStatusElement.textContent = "";
  }
}

// === ERWEITERTE NACHRICHT-ERSTELLUNG ===
function createMessageElementWithUserInfo(message, data) {
  // === 1. HAUPT-CONTAINER ERSTELLEN ===
  const messageDiv = document.createElement("div");

  // === 2. CSS-KLASSEN BASIEREND AUF ABSENDER ===
  const currentUser = getCurrentUser();
  if (message.username === currentUser.name) {
    messageDiv.className = "chat-message-container chat-message-container-self";
  } else {
    messageDiv.className = "chat-message-container";
  }

  // ✅ ERWEITERT: Admin-Style für Admin-Nachrichten
  if (message.is_admin) {
    messageDiv.classList.add("chat-message-admin");
  }

  // ✅ ERWEITERT: Style für gelöschte User
  if (!message.user_exists) {
    messageDiv.classList.add("chat-message-deleted-user");
  }

  // === 3. ERWEITERTE BENUTZER-INFO ===
  const userInfo = document.createElement("div");
  userInfo.className = "chat-message-user-info";

  // ✅ NEU: Username mit Admin-Badge
  let displayName = message.username || "Unbekannt";
  if (message.is_admin) {
    displayName += " 👑";
  }

  userInfo.innerHTML = displayName;

  // ✅ NEU: Zusätzliche User-Info als Tooltip
  if (!message.user_exists) {
    userInfo.title = "Dieser Benutzer wurde gelöscht";
    userInfo.style.fontStyle = "italic";
    userInfo.style.opacity = "0.7";
  } else if (message.is_admin) {
    userInfo.title = "Administrator";
  }

  // === 4. NACHRICHTEN-TEXT ===
  const messageText = document.createElement("div");
  messageText.className = "chat-message-text";
  messageText.textContent = message.message || "Leere Nachricht";

  // === 5. ERWEITERTE ZEIT-ANZEIGE ===
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
  messageDiv.appendChild(userInfo);
  messageDiv.appendChild(messageText);
  messageDiv.appendChild(footer);

  return messageDiv;
}

// ✅ ERWEITERTE NACHRICHTEN-DARSTELLUNG für geladene Nachrichten
function modifyChatMessages(data, room_number) {
  console.log("📨 Nachrichten-Daten mit User-Info:", data);

  const chatContainer = document.getElementById("chat-messages-container");
  if (!chatContainer) {
    console.error("❌ Chat-Container nicht gefunden!");
    return;
  }

  chatContainer.innerHTML = "";

  if (data.success && data.room_number === room_number) {
    console.log(`✅ ${data.messages.length} Nachrichten mit User-Info geladen`);

    if (data.messages && data.messages.length > 0) {
      data.messages.forEach((message) => {
        console.log(
          `👤 Nachricht von: ${message.username} (Admin: ${message.is_admin}, Existiert: ${message.user_exists})`
        );

        // ✅ VERWENDE: Neue Funktion mit User-Info
        const messageElement = createMessageElementWithUserInfo(message, data);
        chatContainer.appendChild(messageElement);
      });

      scrollToBottom();
    } else {
      // Leerer Chat - Placeholder anzeigen
      const placeholderDiv = document.createElement("div");
      placeholderDiv.className = "chat-empty-placeholder";
      placeholderDiv.textContent =
        "Noch nichts los hier, schreibe den ersten Nachricht! 💬";
      chatContainer.appendChild(placeholderDiv);
    }
  } else {
    console.error("❌ Fehler beim Laden der Nachrichten:", data.error);
  }
}

// === HILFSFUNKTIONEN ===
function scrollToBottom() {
  const chatContainer = document.getElementById("chat-messages-container");
  if (chatContainer) {
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
}

function showRoomNotification(message, type = "info") {
  console.log(`📢 ${type.toUpperCase()}: ${message}`);

  // ✅ NEU: Visueller Toast (optional)
  const toast = document.createElement("div");
  toast.className = `chat-toast chat-toast-${type}`;
  toast.textContent = message;

  document.body.appendChild(toast);

  // Auto-remove nach 3 Sekunden
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 3000);
}

// === BENUTZER-INFO FUNKTIONEN ===
function getCurrentUser() {
  const userName =
    document.querySelector(".main-sidbar-profil p") ||
    document.querySelector(".sidebar-header .user-details h3");
  const isAdmin =
    document.querySelector(".admin-badge") !== null ||
    document.querySelector('[href="#"]') !== null;

  return {
    name: userName ? userName.textContent.trim() : "Unbekannt",
    isAdmin: isAdmin,
  };
}

// ✅ NEU: User-Info von Server abrufen
function getUserInfo(userId) {
  if (!socket || !isConnected) {
    console.error("❌ Socket.IO nicht verbunden");
    return;
  }

  socket.emit("BasicChat_get_user_info", { user_id: userId });
}

// === NACHRICHTEN SENDEN (erweitert) ===
function sendMessage() {
  const messageInput = document.getElementById("messageInput");
  const message = messageInput.value.trim();

  if (!message) {
    console.log("❌ Leere Nachricht");
    return;
  }

  if (!currentChatRoom) {
    console.log("❌ Kein Chat ausgewählt");
    showRoomNotification("Kein Chat ausgewählt", "error");
    return;
  }

  if (!socket || !isConnected) {
    console.log("❌ Socket.IO nicht verbunden");
    showRoomNotification("Nicht mit Server verbunden", "error");
    return;
  }

  console.log(`📤 Sende Nachricht: "${message}" an Raum: ${currentChatRoom}`);

  // ✅ ERWEITERT: Mehr Kontext senden
  socket.emit("BasicChat_send_message", {
    message: message,
    room_number: currentChatRoom,
    timestamp: new Date().toISOString(),
  });

  messageInput.value = "";
}

// === BESTEHENDE FUNKTIONEN (unverändert) ===
function joinChatRoom(roomNumber) {
  if (!socket || !isConnected) {
    console.error("❌ Socket.IO nicht verbunden");
    return false;
  }

  console.log(`🏠 Betrete Chat-Raum: ${roomNumber}`);
  socket.emit("BasicChat_join_chat_room", { room_number: roomNumber });
  return true;
}

function leaveChatRoom() {
  if (!socket || !isConnected || !currentChatRoom) {
    console.log("❌ Nicht in einem Raum oder nicht verbunden");
    return false;
  }

  console.log(`👋 Verlasse Chat-Raum: ${currentChatRoom}`);
  socket.emit("BasicChat_leave_chat_room", { room_number: currentChatRoom });
  return true;
}

function getCurrentRoomInfo() {
  if (!socket || !isConnected) {
    console.error("❌ Socket.IO nicht verbunden");
    return;
  }

  socket.emit("BasicChat_get_room_info");
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

// === CHAT-LADEN (erweitert) ===
function loadChat(load_chat_url, load_chat_messages_url) {
  console.log("📥 Lade Chat von:", load_chat_url);

  const roomNumber = extractRoomNumberFromUrl(load_chat_url);
  if (roomNumber) {
    joinChatRoom(roomNumber);
  }

  fetch(load_chat_url)
    .then((response) => response.json())
    .then((data) => {
      setTimeout(() => modifyChat(data), 100);
    })
    .catch((error) => {
      console.error("❌ Fehler beim Laden des Chats:", error);
    });

  // ✅ WICHTIG: Messages werden jetzt mit User-Info geladen
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
  console.log("📋 Chat-Daten mit User-Info:", chat);
  console.log("📋 Chat-Typ:", type);

  if (chat) {
    currentChatInfo = chat; // ✅ NEU: Chat-Info speichern

    const chatNameElement = document.getElementById("chat-name");
    if (chatNameElement) {
      if (chat.group_name) {
        chatNameElement.textContent = chat.group_name;
      } else if (chat.display_name) {
        chatNameElement.textContent = chat.display_name;
      }
    }

    // ✅ NEU: Chat-Details anzeigen
    updateChatDetails(chat);
  }

  if (error_message) {
    console.error("❌ Chat-Fehler:", error_message);
    showRoomNotification(`Fehler: ${error_message}`, "error");
  }
}

// === INPUT FUNKTIONEN (unverändert) ===
function initializeMessageInput() {
  const messageInput = document.getElementById("messageInput");
  const sendButton = document.getElementById("sendButton");

  if (!messageInput || !sendButton) return;

  sendButton.addEventListener("click", () => {
    sendMessage();
  });

  messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  });

  console.log("✅ Message Input mit erweiterten Features initialisiert");
}

function showChatInput() {
  const inputArea = document.getElementById("chat-input-area");
  if (inputArea) {
    inputArea.style.display = "block";
  }
}

function hideChatInput() {
  const inputArea = document.getElementById("chat-input-area");
  if (inputArea) {
    inputArea.style.display = "none";
  }
}

// === INITIALISIERUNG ===
document.addEventListener("DOMContentLoaded", function () {
  console.log("🏁 DOM bereit - BasicChat mit Benutzerinformationen geladen");
  initializeSocketIO();
  initializeMessageInput();
});

// === ERWEITERTE DEBUG-FUNKTIONEN ===
window.ChatDebug = {
  status: () => {
    return {
      connected: isConnected,
      socket: socket ? "initialized" : "not initialized",
      currentRoom: currentChatRoom,
      currentChatInfo: currentChatInfo, // ✅ NEU!
    };
  },

  joinRoom: (roomNumber) => {
    return joinChatRoom(roomNumber);
  },

  getRoomInfo: () => {
    getCurrentRoomInfo();
  },

  getUserInfo: (userId) => {
    // ✅ NEU!
    getUserInfo(userId);
  },

  harlemshake: () => {
    sendHarlemshake();
  },

  // ✅ NEU: Test-Funktionen für User-Info
  testUserInfo: () => {
    const currentUser = getCurrentUser();
    console.log("🧪 Aktueller User:", currentUser);

    if (currentChatInfo) {
      console.log("🧪 Chat-Info:", currentChatInfo);
    }

    return { currentUser, currentChatInfo };
  },
};

// === MODAL FUNKTIONEN (unverändert) ===
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

  const openModals = document.querySelectorAll(".modal.show");
  if (openModals.length === 0) {
    document.body.classList.remove("modal-open");
  }
}

function closeAndOpenNewModal(closeModalId, openModalId) {
  const closeModalElement = document.getElementById(closeModalId);
  if (closeModalElement) {
    closeModalElement.style.display = "none";
    closeModalElement.classList.remove("show");
  }

  const openModalElement = document.getElementById(openModalId);
  if (openModalElement) {
    openModalElement.style.display = "block";
    openModalElement.classList.add("show");
  }

  document.body.classList.add("modal-open");
}

function closeAllModals() {
  document.querySelectorAll(".modal").forEach((modal) => {
    modal.style.display = "none";
    modal.classList.remove("show");
  });
  document.body.classList.remove("modal-open");
}

function openNewChatModal() {
  openModal("new-chat-modal-main");
}

function createNewGroupChat(url_new_group_chat, url_group_members) {
  const groupName = document.getElementById("group-name-input").value.trim();

  if (!groupName) {
    alert("Bitte Namen eingeben!");
    return;
  }

  fetch(url_new_group_chat, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ group_name: groupName }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        console.log("Gruppe erstellt!", data.all_users);
        document.getElementById("group-name-input").value = "";
      }
    })
    .catch((error) => alert("Fehler!"));

  // closeAllModals();
}

function createUserListInModal(all_user_json) {}

function addMemberToGroup(groupId, all_user_id) {}

console.log("📚 BasicChat mit erweiterten Benutzerinformationen geladen");
let adminGroupsData = [];
let selectedGroupIds = new Set();

// Admin-Modal öffnen
function openAdminModal() {
  console.log("🔧 Öffne Admin-Modal...");
  openModal("admin-modal-main");
  loadGroupChatsForAdmin();
}

// Prüfe ob aktueller User Admin ist
function isCurrentUserAdmin() {
  return (
    document.querySelector('.main-sidbar-settings-and-apps [href="#"]') !== null
  );
}

// Gruppenchats für Admin laden
async function loadGroupChatsForAdmin() {
  console.log("📊 Lade Gruppenchats für Admin...");

  // UI zurücksetzen
  showAdminLoadingState();
  hideAdminStates(["error", "success", "groups"]);

  try {
    const response = await fetch("/BasicChat/api/admin/list_group_chats", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (data.success) {
      console.log("✅ Gruppenchats geladen:", data.groups);
      adminGroupsData = data.groups;
      renderGroupChatsList(data.groups);
      showAdminGroupsContainer();
    } else {
      console.error("❌ Fehler beim Laden:", data.error);
      showAdminError(data.error);
    }
  } catch (error) {
    console.error("❌ Netzwerkfehler:", error);
    showAdminError("Netzwerkfehler beim Laden der Gruppenchats");
  } finally {
    hideAdminLoadingState();
  }
}

// Gruppenchats-Liste rendern
function renderGroupChatsList(groups) {
  const container = document.getElementById("groups-list");
  container.innerHTML = "";

  if (groups.length === 0) {
    container.innerHTML = `
      <div class="text-center text-muted p-4">
        <i class="bi bi-inbox" style="font-size: 2rem;"></i>
        <p class="mt-2">Keine Gruppenchats gefunden</p>
      </div>
    `;
    return;
  }

  groups.forEach((group) => {
    const groupItem = createGroupChatItem(group);
    container.appendChild(groupItem);
  });

  updateSelectedCountDisplay();
}

// Einzelnen Gruppenchat-Item erstellen
function createGroupChatItem(group) {
  const item = document.createElement("div");
  item.className = "admin-group-item";
  item.dataset.groupId = group.id;

  // Zeitformatierung
  const lastMessageDate = group.last_message_date
    ? new Date(group.last_message_date).toLocaleString("de-DE")
    : "Nie";

  const createdAt = group.created_at
    ? new Date(group.created_at).toLocaleDateString("de-DE")
    : "Unbekannt";

  // Nachrichten-Count formatieren
  const messageCount = group.message_count || 0;
  const messageCountText =
    messageCount === 0
      ? "Keine Nachrichten"
      : messageCount === 1
      ? "1 Nachricht"
      : `${messageCount} Nachrichten`;

  item.innerHTML = `
    <div class="form-check">
      <input 
        class="form-check-input group-checkbox" 
        type="checkbox" 
        id="group-${group.id}"
        onchange="toggleGroupSelection(${group.id}, this.checked)"
      >
      <label class="form-check-label w-100" for="group-${group.id}">
        <div class="d-flex justify-content-between align-items-start">
          <div class="flex-grow-1">
            <strong>${escapeHtml(
              group.group_name || "Unbenannte Gruppe"
            )}</strong>
            <div class="group-info-details">
              <div><i class="bi bi-hash"></i> ID: ${group.id}</div>
              <div><i class="bi bi-key"></i> Raum: ${
                group.chat_room_number || "N/A"
              }</div>
              <div><i class="bi bi-calendar"></i> Erstellt: ${createdAt}</div>
              <div><i class="bi bi-chat-dots"></i> <strong>Anzahl Nachrichten: ${messageCount}</strong></div>
            </div>
          </div>
          <div class="text-end">
            <div class="badge ${
              messageCount > 0 ? "bg-primary" : "bg-secondary"
            } mb-2">
              ${messageCountText}
            </div>
            <div>
              <small class="text-muted">
                <div>Letzte Nachricht:</div>
                <div>${lastMessageDate}</div>
              </small>
            </div>
          </div>
        </div>
        <div class="group-info-details mt-1">
          <div><i class="bi bi-chat-quote"></i> "${escapeHtml(
            (group.last_message || "Keine Nachrichten").substring(0, 50)
          )}${
    group.last_message && group.last_message.length > 50 ? "..." : ""
  }"</div>
        </div>
      </label>
    </div>
  `;

  return item;
}

// Gruppen-Auswahl umschalten
function toggleGroupSelection(groupId, isSelected) {
  if (isSelected) {
    selectedGroupIds.add(groupId);
  } else {
    selectedGroupIds.delete(groupId);
  }

  // Visual feedback
  const item = document.querySelector(`[data-group-id="${groupId}"]`);
  if (item) {
    item.classList.toggle("selected", isSelected);
  }

  updateSelectedCountDisplay();
  updateDeleteButton();
}

// "Alle auswählen" Checkbox
document.addEventListener("DOMContentLoaded", function () {
  const selectAllCheckbox = document.getElementById("select-all-groups");
  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener("change", function () {
      const isChecked = this.checked;
      const groupCheckboxes = document.querySelectorAll(".group-checkbox");

      groupCheckboxes.forEach((checkbox) => {
        checkbox.checked = isChecked;
        const groupId = parseInt(checkbox.id.replace("group-", ""));
        toggleGroupSelection(groupId, isChecked);
      });
    });
  }
});

// Ausgewählte Anzahl anzeigen
function updateSelectedCountDisplay() {
  const countElement = document.getElementById("selected-count");
  const infoElement = document.getElementById("selected-groups-info");

  if (countElement) {
    countElement.textContent = selectedGroupIds.size;
  }

  if (infoElement) {
    infoElement.style.display = selectedGroupIds.size > 0 ? "block" : "none";
  }
}

// Löschen-Button aktivieren/deaktivieren
function updateDeleteButton() {
  const deleteBtn = document.getElementById("delete-selected-btn");
  if (deleteBtn) {
    deleteBtn.disabled = selectedGroupIds.size === 0;
  }
}

// Ausgewählte Gruppennachrichten löschen
async function deleteSelectedGroupMessages() {
  if (selectedGroupIds.size === 0) {
    alert("Bitte wählen Sie mindestens eine Gruppe aus.");
    return;
  }

  const selectedGroups = Array.from(selectedGroupIds);
  const groupNames = selectedGroups.map((id) => {
    const group = adminGroupsData.find((g) => g.id === id);
    return group ? group.group_name : `ID ${id}`;
  });

  const confirmMessage =
    `Sind Sie sicher, dass Sie alle Nachrichten aus ${selectedGroups.length} Gruppe(n) löschen möchten?\n\n` +
    `Betroffene Gruppen:\n${groupNames.join("\n")}\n\n` +
    `Diese Aktion kann nicht rückgängig gemacht werden!`;

  if (!confirm(confirmMessage)) {
    return;
  }

  console.log("🗑️ Lösche Nachrichten aus Gruppen:", selectedGroups);

  // UI für Löschvorgang vorbereiten
  showAdminLoadingState();
  hideAdminStates(["error", "success"]);

  const deleteBtn = document.getElementById("delete-selected-btn");
  if (deleteBtn) {
    deleteBtn.disabled = true;
    deleteBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm"></span> Lösche...';
  }

  try {
    let totalDeleted = 0;
    let errors = [];

    // Sequenziell löschen um Server nicht zu überlasten
    for (const groupId of selectedGroups) {
      try {
        const group = adminGroupsData.find((g) => g.id === groupId);
        if (!group || !group.chat_room_number) {
          errors.push(`Gruppe ${groupId}: Keine Raum-Nummer gefunden`);
          continue;
        }

        const response = await fetch(
          `/BasicChat/api/delete_messages_room/${group.chat_room_number}`,
          {
            method: "DELETE",
          }
        );

        const data = await response.json();

        if (data.success) {
          totalDeleted += data.deleted_count || 0;
          console.log(
            `✅ Gruppe "${group.group_name}": ${data.deleted_count} Nachrichten gelöscht`
          );
        } else {
          errors.push(`Gruppe "${group.group_name}": ${data.error}`);
        }
      } catch (error) {
        errors.push(`Gruppe ${groupId}: Netzwerkfehler`);
        console.error(`❌ Fehler bei Gruppe ${groupId}:`, error);
      }
    }

    // Ergebnis anzeigen
    if (errors.length === 0) {
      showAdminSuccess(
        `Erfolgreich ${totalDeleted} Nachrichten aus ${selectedGroups.length} Gruppe(n) gelöscht`
      );
    } else if (totalDeleted > 0) {
      showAdminSuccess(
        `${totalDeleted} Nachrichten gelöscht. Einige Fehler aufgetreten: ${errors.join(
          ", "
        )}`
      );
    } else {
      showAdminError(`Fehler beim Löschen: ${errors.join(", ")}`);
    }

    // UI zurücksetzen
    selectedGroupIds.clear();
    loadGroupChatsForAdmin(); // Liste neu laden
  } catch (error) {
    console.error("❌ Kritischer Fehler beim Löschen:", error);
    showAdminError("Kritischer Fehler beim Löschen der Nachrichten");
  } finally {
    hideAdminLoadingState();

    // Button zurücksetzen
    if (deleteBtn) {
      deleteBtn.innerHTML =
        '<i class="bi bi-trash-fill"></i> Ausgewählte löschen';
      deleteBtn.disabled = false;
    }
  }
}

// UI-Zustand Hilfsfunktionen
function showAdminLoadingState() {
  document.getElementById("admin-loading").style.display = "block";
}

function hideAdminLoadingState() {
  document.getElementById("admin-loading").style.display = "none";
}

function showAdminGroupsContainer() {
  document.getElementById("admin-groups-container").style.display = "block";
}

function showAdminError(message) {
  const errorDiv = document.getElementById("admin-error");
  const messageSpan = document.getElementById("admin-error-message");

  if (errorDiv && messageSpan) {
    messageSpan.textContent = message;
    errorDiv.style.display = "block";
  }
}

function showAdminSuccess(message) {
  const successDiv = document.getElementById("admin-success");
  const messageSpan = document.getElementById("admin-success-message");

  if (successDiv && messageSpan) {
    messageSpan.textContent = message;
    successDiv.style.display = "block";
  }

  // Auto-hide nach 5 Sekunden
  setTimeout(() => {
    successDiv.style.display = "none";
  }, 5000);
}

function hideAdminStates(states) {
  states.forEach((state) => {
    const element = document.getElementById(`admin-${state}`);
    if (element) {
      element.style.display = "none";
    }
  });
}

// HTML escaping für Sicherheit
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Debug-Funktion für Admin-Modal
window.ChatDebug.admin = {
  openModal: () => openAdminModal(),
  loadGroups: () => loadGroupChatsForAdmin(),
  selectedIds: () => Array.from(selectedGroupIds),
  groupsData: () => adminGroupsData,
};

console.log("🔧 Admin-Modal Funktionen geladen");
