# Bio Clean Agent Helper (VS Code Extension)

This lightweight extension surfaces common commands for the Bio Clean Agent project:

- `Bio Clean Agent: Create Dataset Config` – opens a quick picker and launches `bio-clean-agent init` with the selected dataset file or folder in an integrated terminal.
- `Bio Clean Agent: Open Quickstart` – jumps to the repo README or falls back to the online documentation.

## Local development

1. Install dependencies:
   ```bash
   npm install --save-dev @types/vscode
   ```
2. Press `F5` in VS Code to launch a new Extension Development Host.
3. Verify that the commands appear in the Command Palette (`Cmd/Ctrl+Shift+P`).

To package the extension, install [`vsce`](https://code.visualstudio.com/api/working-with-extensions/publishing-extension) and run `npm run package` inside this directory.
