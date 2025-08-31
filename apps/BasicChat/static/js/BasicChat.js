// BasicChat.js - Vollständige Socket.IO Chat-Funktionalität
console.log("🚀 BasicChat Frontend geladen");

class BasicChat {
  constructor() {
    this.messageInput = document.getElementById("messageInput");
    this.sendButton = document.getElementById("sendButton");
    this.chatMessages = document.getElementById("chatMessages");

    // Socket.IO
    this.socket = null;
    this.isConnected = false;

    // Benutzer-Info
    this.currentUser = this.getCurrentUser();

    this.initializeEventListeners();
    this.clearExampleMessages();
    this.initializeSocketIO();

    console.log("✅ BasicChat initialisiert");
  }

  initializeEventListeners() {
    // Send Button Click
    this.sendButton.addEventListener("click", () => {
      this.sendMessage();
    });

    // Enter-Taste zum Senden
    this.messageInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Input-Status für Send-Button
    this.messageInput.addEventListener("input", () => {
      this.updateSendButton();
    });

    console.log("🎮 Event Listeners registriert");
  }

  initializeSocketIO() {
    if (typeof io === "undefined") {
      console.error("❌ Socket.IO nicht verfügbar!");
      this.addMessage("❌ Socket.IO nicht verfügbar", "system");
      return;
    }

    console.log("🔌 Initialisiere Socket.IO...");

    try {
      this.socket = io();
      this.setupBasicSocketEvents();
    } catch (error) {
      console.error("❌ Socket.IO Fehler:", error);
      this.addMessage("❌ Verbindungsfehler", "system");
    }
  }

  setupBasicSocketEvents() {
    // === BESTEHENDE EVENTS aus __init__.py nutzen ===

    this.socket.on("connect", () => {
      console.log("✅ Socket.IO verbunden!");
      this.isConnected = true;
      this.addMessage("✅ Mit Server verbunden!", "system");

      // Trete dem globalen Chat bei
      this.socket.emit("BasicChat_join_global_chat");
    });

    this.socket.on("disconnect", () => {
      console.log("❌ Socket.IO getrennt");
      this.isConnected = false;
      this.addMessage("❌ Verbindung getrennt", "system");
    });

    // Nutzt bestehenden Handler aus __init__.py
    this.socket.on("connection_response", (data) => {
      console.log("📡 Server Antwort:", data);
      this.addMessage(`Server: ${data.data}`, "system");
    });

    // Nutzt bestehenden Handler aus __init__.py
    this.socket.on("status", (data) => {
      console.log("📊 Status:", data);
      this.addMessage(`Status: ${data.msg}`, "system");
    });

    // === NEUE CHAT EVENTS aus socketio_events.py ===

    this.socket.on("new_message", (data) => {
      console.log("💬 Neue Nachricht:", data);

      // Bestimme ob es unsere eigene Nachricht ist
      const isOwnMessage = data.username === this.currentUser.name;
      const messageType = isOwnMessage ? "sent" : "received";

      // Admin-Status prüfen (falls im Backend gesendet)
      const isAdmin = data.is_admin || false;

      this.addMessage(
        data.message,
        messageType,
        data.username,
        data.timestamp,
        isAdmin
      );
    });

    this.socket.on("user_joined_chat", (data) => {
      console.log("👤+ Benutzer beigetreten:", data);
      const adminBadge = data.is_admin ? " 👑" : "";
      this.addMessage(
        `${data.username}${adminBadge} ist dem Chat beigetreten`,
        "system"
      );
    });

    // Nutzt bestehenden Handler aus __init__.py
    this.socket.on("pong", (data) => {
      console.log("🏓 Pong empfangen:", data);
      this.addMessage(`🏓 Pong: ${data.message}`, "system");
    });

    // Error handling
    this.socket.on("connect_error", (error) => {
      console.error("❌ Verbindungsfehler:", error);
      this.addMessage("❌ Kann nicht mit Server verbinden", "system");
    });

    console.log("🎮 Socket.IO Events registriert");
  }

  getCurrentUser() {
    const userName = document.querySelector(".sidebar-header .user-details h3");
    return {
      name: userName ? userName.textContent.trim() : "Unbekannt",
      isAdmin: document.querySelector(".admin-badge") !== null,
    };
  }

  clearExampleMessages() {
    this.chatMessages.innerHTML = "";
  }

  sendMessage() {
    const message = this.messageInput.value.trim();
    if (message === "" || !this.isConnected) {
      if (!this.isConnected) {
        this.addMessage("❌ Nicht mit Server verbunden", "system");
      }
      return;
    }

    console.log("📤 Sende Nachricht:", message);

    // Nachricht über Socket.IO senden (neuer Event aus socketio_events.py)
    this.socket.emit("BasicChat_send_message", {
      message: message,
      timestamp: this.getCurrentTime(),
    });

    // Input zurücksetzen
    this.messageInput.value = "";
    this.updateSendButton();
    this.messageInput.focus();
  }

  addMessage(
    text,
    type = "received",
    sender = null,
    timestamp = null,
    isAdmin = false
  ) {
    const messageWrapper = document.createElement("div");
    messageWrapper.className = `message-wrapper ${type}`;

    // Nachrichtenbubble (OHNE Timestamp)
    const message = document.createElement("div");
    message.className = "message";

    const time = timestamp || this.getCurrentTime();

    if (type === "system") {
      message.classList.add("system-message");
      message.innerHTML = `<p>${this.escapeHtml(text)}</p>`;
      messageWrapper.appendChild(message);
    } else if (type === "received") {
      const senderName = sender || "Anderer Benutzer";
      const adminCrown = isAdmin ? '<span class="admin-crown">👑</span>' : "";

      // NUR Sender und Text in der Bubble
      message.innerHTML = `
                <div class="message-sender">
                    ${this.escapeHtml(senderName)}${adminCrown}
                </div>
                <p>${this.escapeHtml(text)}</p>
            `;

      messageWrapper.appendChild(message);

      // Timestamp UNTER der Bubble als separates Element
      const timestampDiv = document.createElement("div");
      timestampDiv.className = "message-timestamp";
      timestampDiv.textContent = time;
      messageWrapper.appendChild(timestampDiv);
    } else if (type === "sent") {
      // NUR Text in der Bubble
      message.innerHTML = `<p>${this.escapeHtml(text)}</p>`;

      messageWrapper.appendChild(message);

      // Timestamp UNTER der Bubble als separates Element
      const timestampDiv = document.createElement("div");
      timestampDiv.className = "message-timestamp";
      timestampDiv.textContent = time;
      messageWrapper.appendChild(timestampDiv);
    }

    this.chatMessages.appendChild(messageWrapper);
    this.scrollToBottom();
  }

  updateSendButton() {
    const hasText = this.messageInput.value.trim().length > 0;
    this.sendButton.disabled = !hasText || !this.isConnected;

    if (hasText && this.isConnected) {
      this.sendButton.style.background = "#00a884";
    } else {
      this.sendButton.style.background = "#8696a0";
    }
  }

  scrollToBottom() {
    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
  }

  getCurrentTime() {
    return new Date().toLocaleTimeString("de-DE", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // === TEST FUNKTIONEN ===
  testPing() {
    if (this.socket && this.isConnected) {
      console.log("🏓 Sende Ping...");
      this.socket.emit("ping", { timestamp: this.getCurrentTime() });
    }
  }

  // === ZUSÄTZLICHE FUNKTIONEN ===

  clearChat() {
    if (confirm("Möchten Sie alle Nachrichten löschen?")) {
      this.chatMessages.innerHTML = "";
      this.addMessage("Chat wurde geleert", "system");
    }
  }

  reconnect() {
    if (this.socket) {
      console.log("🔄 Reconnecting...");
      this.socket.disconnect();
      this.socket.connect();
    }
  }

  getConnectionStatus() {
    return {
      connected: this.isConnected,
      socket: this.socket ? "initialized" : "not initialized",
      user: this.currentUser,
    };
  }
}

// Chat initialisieren wenn DOM bereit ist
document.addEventListener("DOMContentLoaded", function () {
  console.log("🏁 DOM bereit - starte BasicChat");
  window.basicChat = new BasicChat();
});

// === DEBUG-FUNKTIONEN FÜR DIE KONSOLE ===
window.ChatDebug = {
  // Nutzt bestehenden ping Handler aus __init__.py
  ping: () => {
    if (window.basicChat) {
      window.basicChat.testPing();
    }
  },

  // Nutzt neuen BasicChat_send_message Handler aus socketio_events.py
  sendMessage: (text, isAdmin = false) => {
    if (window.basicChat && window.basicChat.isConnected) {
      // Zum Testen können wir Admin-Status simulieren
      if (isAdmin) {
        window.basicChat.addMessage(
          text,
          "received",
          "Admin User",
          new Date().toLocaleTimeString("de-DE", {
            hour: "2-digit",
            minute: "2-digit",
          }),
          true
        );
      } else {
        window.basicChat.socket.emit("BasicChat_send_message", {
          message: text,
          timestamp: new Date().toLocaleTimeString("de-DE", {
            hour: "2-digit",
            minute: "2-digit",
          }),
        });
      }
    } else {
      console.log("❌ Chat nicht verbunden oder nicht initialisiert");
    }
  },

  // Nutzt neuen BasicChat_join_global_chat Handler aus socketio_events.py
  joinChat: () => {
    if (window.basicChat && window.basicChat.isConnected) {
      window.basicChat.socket.emit("BasicChat_join_global_chat");
    } else {
      console.log("❌ Chat nicht verbunden");
    }
  },

  // Chat-Status abrufen
  status: () => {
    if (window.basicChat) {
      return window.basicChat.getConnectionStatus();
    }
    return "BasicChat nicht initialisiert";
  },

  // Lokale Test-Nachricht hinzufügen
  addTestMessage: (
    text,
    type = "received",
    sender = "TestUser",
    isAdmin = false
  ) => {
    if (window.basicChat) {
      window.basicChat.addMessage(text, type, sender, null, isAdmin);
    }
  },

  // Chat leeren
  clearChat: () => {
    if (window.basicChat) {
      window.basicChat.clearChat();
    }
  },

  // Verbindung neu starten
  reconnect: () => {
    if (window.basicChat) {
      window.basicChat.reconnect();
    }
  },

  // Mehrere Test-Nachrichten für Design-Tests
  simulateConversation: () => {
    if (!window.basicChat) return;

    const messages = [
      { text: "Hallo zusammen!", sender: "Alice", isAdmin: false },
      { text: "Herzlich willkommen!", sender: "Bob", isAdmin: true },
      { text: "Wie geht es euch heute?", sender: "Charlie", isAdmin: false },
      { text: "Das Wetter ist heute schön!", sender: "Diana", isAdmin: false },
    ];

    messages.forEach((msg, index) => {
      setTimeout(() => {
        window.basicChat.addMessage(
          msg.text,
          "received",
          msg.sender,
          null,
          msg.isAdmin
        );
      }, index * 1000);
    });
  },
};

// === GLOBALE HILFSFUNKTIONEN ===

// Prüfung ob Socket.IO verfügbar ist
function checkSocketIOAvailability() {
  return typeof io !== "undefined";
}

// Chat-Instanz abrufen
function getChatInstance() {
  return window.basicChat || null;
}

// === INITIALISIERUNG ===
console.log("📚 BasicChat Modul geladen - bereit für Initialisierung");
