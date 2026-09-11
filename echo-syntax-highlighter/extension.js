const { execFile } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const vscode = require("vscode");

const SOURCE = "echo";

const COMMANDS = {
  check: { title: "Echo: Check file", target: "file", extraArgs: ["--plain"], matchers: ["$echo"] },
  lint: { title: "Echo: Lint workspace", target: "workspace", extraArgs: ["--plain"], matchers: ["$echo-lint", "$echo"] },
  fmt: { title: "Echo: Format workspace", target: "workspace", extraArgs: [], matchers: ["$echo"] },
  test: { title: "Echo: Test workspace", target: "workspace", extraArgs: ["--plain"], matchers: ["$echo-test-detail", "$echo-test"] },
  "lint-file": { title: "Echo: Lint file", verb: "lint", target: "file", extraArgs: ["--plain"], matchers: ["$echo-lint", "$echo"] },
  "fmt-file": { title: "Echo: Format file", verb: "fmt", target: "file", extraArgs: [], matchers: ["$echo"] },
  "test-file": { title: "Echo: Test file", verb: "test", target: "file", extraArgs: ["--plain"], matchers: ["$echo-test-detail", "$echo-test"] },
};

function activate(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand("echo.checkFile", () => executeEchoCommand("check")),
    vscode.commands.registerCommand("echo.lintWorkspace", () => executeEchoCommand("lint")),
    vscode.commands.registerCommand("echo.formatWorkspace", () => executeEchoCommand("fmt")),
    vscode.commands.registerCommand("echo.testWorkspace", () => executeEchoCommand("test")),
    vscode.tasks.registerTaskProvider(SOURCE, {
      provideTasks: () => Object.keys(COMMANDS).map((command) => buildTask({ type: SOURCE, command })),
      resolveTask: (task) => buildTask(task.definition, task.scope),
    }),
    vscode.languages.registerDocumentFormattingEditProvider("echo", {
      provideDocumentFormattingEdits: formatDocument,
    }),
  );
}

function deactivate() {}

function cliPath() {
  const configured = vscode.workspace.getConfiguration("echo").get("path");
  return typeof configured === "string" && configured.trim() ? configured.trim() : "echolang";
}

function workspaceFolder() {
  const active = vscode.window.activeTextEditor?.document.uri;
  if (active) {
    const folder = vscode.workspace.getWorkspaceFolder(active);
    if (folder) {
      return folder;
    }
  }
  return vscode.workspace.workspaceFolders?.[0];
}

function hasSavedEchoEditor() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.isUntitled) {
    return false;
  }
  return editor.document.languageId === "echo" || editor.document.fileName.endsWith(".echo");
}

async function executeEchoCommand(command) {
  const spec = COMMANDS[command];
  const hasWorkspace = Boolean(workspaceFolder());
  if (spec.target === "file" && !hasSavedEchoEditor()) {
    vscode.window.showWarningMessage("Echo: open a saved .echo file first. The Echo CLI must be on PATH.");
    return;
  }
  if (spec.target === "workspace" && !hasWorkspace && !hasSavedEchoEditor()) {
    vscode.window.showWarningMessage("Echo: open a workspace folder or .echo file first. The Echo CLI must be on PATH.");
    return;
  }
  const editor = vscode.window.activeTextEditor;
  if (editor?.document.isDirty) {
    await editor.document.save();
  }
  const task = buildTask({ type: SOURCE, command });
  await vscode.tasks.executeTask(task);
}

function substitution(target) {
  return target === "file" ? "${file}" : "${workspaceFolder}";
}

function buildTask(definition, scope) {
  const command = definition?.command;
  const spec = COMMANDS[command];
  if (!spec) {
    return undefined;
  }
  const verb = spec.verb || command;
  const target = definition.target === "file" || definition.target === "workspace" ? definition.target : spec.target;
  const args = [verb, ...spec.extraArgs, substitution(target)];
  const folder = workspaceFolder();
  const execution = new vscode.ShellExecution(cliPath(), args, {
    cwd: folder?.uri.fsPath,
  });
  const taskScope = scope || folder || vscode.TaskScope.Workspace;
  const task = new vscode.Task(
    { type: SOURCE, command, target },
    taskScope,
    spec.title,
    SOURCE,
    execution,
    spec.matchers,
  );
  task.presentationOptions = {
    reveal: vscode.TaskRevealKind.Always,
    panel: vscode.TaskPanelKind.Dedicated,
    showReuseMessage: false,
    clear: false,
  };
  if (verb === "test") {
    task.group = vscode.TaskGroup.Test;
  } else if (verb === "check" || verb === "lint") {
    task.group = vscode.TaskGroup.Build;
  }
  return task;
}

function formatDocument(document) {
  return new Promise((resolve) => {
    const tmp = path.join(os.tmpdir(), `echo-fmt-${process.pid}-${Date.now()}.echo`);
    try {
      fs.writeFileSync(tmp, document.getText(), "utf8");
    } catch (error) {
      vscode.window.showErrorMessage(`Echo: could not write a temp file for format (${error.message}).`);
      resolve([]);
      return;
    }
    execFile(cliPath(), ["fmt", "--plain", tmp], { timeout: 20000 }, (error) => {
      try {
        if (error) {
          if (error.code === "ENOENT") {
            vscode.window.showErrorMessage(
              `Echo: CLI not found (${cliPath()}). Install Echo and put echolang on PATH, or set echo.path.`,
            );
          }
          resolve([]);
          return;
        }
        const formatted = fs.readFileSync(tmp, "utf8");
        if (formatted === document.getText()) {
          resolve([]);
          return;
        }
        const fullRange = new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length));
        resolve([vscode.TextEdit.replace(fullRange, formatted)]);
      } catch (readError) {
        vscode.window.showErrorMessage(`Echo: format failed (${readError.message}).`);
        resolve([]);
      } finally {
        fs.unlink(tmp, () => {});
      }
    });
  });
}

module.exports = { activate, deactivate };
