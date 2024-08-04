document.addEventListener("DOMContentLoaded", function () {
  let connectedElement = document.querySelector(".cli-connected p");
  console.log(connectedElement);
  let connectedRow = connectedElement.textContent;
  console.log(connectedRow);
  let systemName = connectedRow.match(/Verbunden mit (.*)/)[1];
  console.log(systemName);
  var commandSystemName = systemName + " # ";
  console.log(commandSystemName);
});

function clearConsole() {
  const output = document.getElementById("cli-history");
  output.innerHTML = "";
}

function handleKeyDown(event, url) {
  // Zugriff auf den aktuellen Wert des Eingabefelds
  const inputField = document.getElementById("cli-input-field");
  const command = inputField.value;

  // Reagiere auf bestimmte Tasten oder andere Bedingungen
  if (event.key === "Enter" && command.length > 0) {
    // Verarbeite den Befehl
    processCommand(command, url);

    // Leere das Eingabefeld nach der Verarbeitung
    inputField.value = "";
  } else if (event.key === "Escape") {
    // Handle Escape Key (zum Beispiel, um das Eingabefeld zu leeren)
    inputField.value = "";
  }
}

async function processCommand(command, url) {
  try {
    // Sende den Befehl an den Server und warte auf die Antwort
    const response = await sendCommand(command, url);

    // Füge den Befehl und die Serverantwort in die Historie ein
    addCommandToHistory(command, response);
  } catch (error) {
    console.error("Fehler bei der Verarbeitung des Befehls:", error);
    // Füge den Befehl zur Historie hinzu, auch wenn ein Fehler aufgetreten ist
    addCommandToHistory(command, { error: [error.message] });
  }
}
function addCommandToHistory(command, response) {
  const history = document.getElementById("cli-history");
  const commandUl = document.createElement("div");
  commandUl.classList.add("cli-history-entry");

  const commandInput = document.createElement("div");
  const commandOutput = document.createElement("div");

  commandInput.classList.add("cli-input-command");
  commandOutput.classList.add("cli-output-command");

  let connectedElement = document.querySelector(".cli-connected p");
  let connectedRow = connectedElement.textContent;
  let systemName = connectedRow.match(/Verbunden mit (.*)/)[1];
  var commandSystemName = systemName + " # ";

  commandInput.textContent = commandSystemName + command;

  if (response.output) {
    commandOutput.innerHTML = response.output.join("<br>");
  } else if (response.error) {
    commandOutput.innerHTML = `Fehler: ${response.error.join("<br>")}`;
    commandOutput.style.color = "red";
  } else {
    commandOutput.textContent = "Keine Antwort vom Server";
  }

  commandUl.appendChild(commandInput);
  commandUl.appendChild(commandOutput);

  // Füge den neuen Befehl ganz oben ein
  history.prepend(commandUl);

  // Scrolle zum Anfang des CLI-Bereichs
  const cliWrapper = document.querySelector(".cli-console-container");
  cliWrapper.scrollTop = 0; // Scrolle ganz nach oben
}

async function sendCommand(command, url) {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ command: command }),
    });

    // Überprüfen, ob die Antwort erfolgreich war
    if (!response.ok) {
      throw new Error(`HTTP Fehler! Status: ${response.status}`);
    }

    const data = await response.json();

    // Die Daten zurückgeben
    return data;
  } catch (error) {
    // Fehler zurückwerfen, die von processCommand gefangen werden
    throw new Error(`Fehler beim Senden des Befehls: ${error.message}`);
  }
}
