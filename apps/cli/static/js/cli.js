function handleKeyDown(event, url, host) {
  const input = document.getElementById("cli-input");
  const command = input.value;

  if (event.key === "Enter" && command.trim() !== "") {
    // Ausgabe des Befehls im CLI-Bereich
    const commandLine = document.createElement("p");
    commandLine.textContent = `${host} # ${command}`;
    document.getElementById("cli-output").appendChild(commandLine);

    // Sende den Befehl an den Server
    sendCommand(command, url);

    // Leere das Eingabefeld
    input.value = "";

    // Scrolle zum Ende des CLI-Bereichs
    const cliWrapper = document.querySelector(".cli-wrapper");
    cliWrapper.scrollTop = cliWrapper.scrollHeight;
  }
}

function sendCommand(command, url) {
  const output = document.getElementById("cli-output");

  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ command: command }),
  })
    .then((response) => response.json())
    .then((data) => {
      // Ausgabe der Serverantwort im CLI-Bereich
      if (data.output) {
        data.output.forEach((line) => {
          const responseLine = document.createElement("p");
          responseLine.textContent = line;
          output.appendChild(responseLine);
        });
      }

      if (data.error) {
        data.error.forEach((line) => {
          const errorLine = document.createElement("p");
          errorLine.textContent = `Fehler: ${line}`;
          errorLine.style.color = "red";
          output.appendChild(errorLine);
        });
      }

      // Scrolle zum Ende des CLI-Bereichs
      const cliWrapper = document.querySelector(".cli-wrapper");
      cliWrapper.scrollTop = cliWrapper.scrollHeight;
    })
    .catch((error) => {
      const errorLine = document.createElement("p");
      errorLine.textContent = `Fehler: ${error.message}`;
      output.appendChild(errorLine);

      // Scrolle zum Ende des CLI-Bereichs
      const cliWrapper = document.querySelector(".cli-wrapper");
      cliWrapper.scrollTop = cliWrapper.scrollHeight;
    });
}

function clearConsole() {
  const output = document.getElementById("cli-output");
  output.innerHTML = '<p>Connected</p><p id="host">{{ config.app_name }} #</p>';
}
