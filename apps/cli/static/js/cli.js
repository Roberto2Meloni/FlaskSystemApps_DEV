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

function handleKeyDown(event, url_receive_command, url_check_output) {
  const inputField = document.getElementById("cli-input-field");
  const command = inputField.value;

  if (event.key === "Enter" && command.length > 0) {
    processCommand(command, url_receive_command, url_check_output);
    inputField.value = "";
  } else if (event.key === "Escape") {
    inputField.value = "";
  }
}

async function processCommand(command, url_check_command, url_check_output) {
  try {
    const response = await fetch(url_check_command, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ command: command }),
    });

    if (!response.ok) {
      throw new Error(`HTTP Fehler! Status: ${response.status}`);
    }

    const data = await response.json();
    const commandId = data.command_id;

    addCommandToHistory(command, { output: [] }, commandId);

    // Starte periodische Überprüfung der Befehlsausgabe
    checkCommandOutput(commandId, url_check_output);
  } catch (error) {
    console.error("Fehler bei der Verarbeitung des Befehls:", error);
    addCommandToHistory(command, { error: [error.message] });
  }
}

function safeDecodeURIComponent(str) {
  try {
    // Versuche zuerst, den String als UTF-8 zu dekodieren
    return decodeURIComponent(escape(str));
  } catch (e) {
    try {
      // Wenn das fehlschlägt, versuche eine direkte Dekodierung
      return decodeURIComponent(str);
    } catch (e2) {
      console.warn("Fehler beim Dekodieren:", e2);
      // Wenn auch das fehlschlägt, gib den Originalstring zurück
      return str;
    }
  }
}
function updateCommandOutput(commandId, output, error) {
  const historyEntry = document.querySelector(
    `[data-command-id="${commandId}"]`
  );
  if (historyEntry) {
    const outputElement = historyEntry.querySelector(".cli-output-command");
    if (output && output.length > 0) {
      output.forEach((line) => {
        const decodedLine = safeDecodeURIComponent(line);
        outputElement.innerHTML += decodedLine + "<br>";
      });
    }
    if (error && error.length > 0) {
      error.forEach((line) => {
        const decodedLine = safeDecodeURIComponent(line);
        outputElement.innerHTML += `<span style="color: red;">${decodedLine}</span><br>`;
      });
    }
    // Scroll to the top after updating
    const cliWrapper = document.querySelector(".cli-console-container");
    cliWrapper.scrollTop = 0;
  }
}

function checkCommandOutput(commandId, url_check_output) {
  console.log("checkCommandOutput");
  console.log(commandId);
  let new_url = url_check_output.replace("/0", `/${commandId}`);
  console.log(new_url);
  const intervalId = setInterval(async () => {
    try {
      const response = await fetch(new_url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();

      updateCommandOutput(commandId, data.output, data.error);

      if (data.complete) {
        clearInterval(intervalId);
      }
    } catch (error) {
      console.error("Fehler beim Abrufen der Befehlsausgabe:", error);
      updateCommandOutput(commandId, [], [`Fehler: ${error.message}`]);
      clearInterval(intervalId);
    }
  }, 500);
}

function addCommandToHistory(command, response, commandId) {
  const history = document.getElementById("cli-history");
  const commandUl = document.createElement("div");
  commandUl.classList.add("cli-history-entry");
  commandUl.dataset.commandId = commandId;

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

function replaceSpecialChars(str) {
  const specialChars = {
    "Ã¼": "ü",
    "Ã¤": "ä",
    "Ã¶": "ö",
    Ã: "Ü",
    "Ã„": "Ä",
    "Ã–": "Ö",
    ÃŸ: "ß",
    "â‚¬": "€",
  };
  return str.replace(/[ÃüäöÜÄÖßâ‚¬]/g, (match) => specialChars[match] || match);
}

function safeDecodeURIComponent(str) {
  try {
    return replaceSpecialChars(decodeURIComponent(escape(str)));
  } catch (e) {
    try {
      return replaceSpecialChars(decodeURIComponent(str));
    } catch (e2) {
      console.warn("Fehler beim Dekodieren:", e2);
      return replaceSpecialChars(str);
    }
  }
}
