import * as vscode from 'vscode';
import {registerAllCommands} from './commands';

export function activate(context: vscode.ExtensionContext) {
    try {
        registerAllCommands(context);
        console.log('extension "code-with-ascend" is now active!');
    } catch (e) {
        console.error("Error activating extension: ", e);
        vscode.window.showErrorMessage(
            "Error activating the ascend extension.",
            "Cancel",
            "Retry"
        )
            .then((selection) => {
                if (selection === "Retry") {
                    vscode.commands.executeCommand("workbench.action.reloadWindow");
                }
            });
    }
}

export function deactivate() {
}
