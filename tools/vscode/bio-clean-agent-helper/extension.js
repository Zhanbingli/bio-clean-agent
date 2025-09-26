const vscode = require('vscode');

function activate(context) {
  const startWizard = vscode.commands.registerCommand('bioCleanAgent.startWizard', async () => {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
      vscode.window.showErrorMessage('Open the bio-clean-agent workspace before running the wizard.');
      return;
    }

    const datasetPath = await vscode.window.showOpenDialog({ canSelectMany: false, openLabel: 'Select dataset file or folder' });
    if (!datasetPath || datasetPath.length === 0) {
      return;
    }

    runCliWizard(datasetPath[0]);
  });

  const openDocs = vscode.commands.registerCommand('bioCleanAgent.openDocs', async () => {
    const readmeFiles = await vscode.workspace.findFiles('README.md', '**/node_modules/**', 1);
    if (readmeFiles.length > 0) {
      vscode.workspace.openTextDocument(readmeFiles[0]).then(doc => vscode.window.showTextDocument(doc));
    } else {
      vscode.env.openExternal(vscode.Uri.parse('https://github.com/你的仓库/bio-clean-agent#readme'));
    }
  });

  context.subscriptions.push(startWizard, openDocs);
}

function runCliWizard(resourceUri) {
  const terminal = vscode.window.createTerminal({ name: 'Bio Clean Agent' });
  terminal.show(true);
  terminal.sendText(`bio-clean-agent init "${resourceUri.fsPath}"`);
  vscode.window.showInformationMessage('Run wizard command in the Bio Clean Agent terminal to scaffold your config.');
}

function deactivate() {}

module.exports = {
  activate,
  deactivate
};
