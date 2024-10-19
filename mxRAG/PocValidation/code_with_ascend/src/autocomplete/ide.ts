import path from "path";
import type {
    IDE
} from "./index";

import * as vscode from 'vscode';
import { uriFromFilePath } from "../util/util";

class VsCodeIde implements IDE {
    private static MAX_BYTES = 100000;

    getWorkspaceDirectories(): string[] {
        return (
            vscode.workspace.workspaceFolders?.map((folder) => folder.uri.fsPath) || 
            []
        );
    }

    getAbsolutePath(filepath: string): string {
        const workspaceDirectories = this.getWorkspaceDirectories();
        if (!path.isAbsolute(filepath) && workspaceDirectories.length === 1) {
            return path.join(workspaceDirectories[0], filepath);
        } else {
            return filepath;
        }
    }

    async readFile(filepath: string): Promise<string> {
        try {
          filepath = this.getAbsolutePath(filepath);
          const uri = uriFromFilePath(filepath);

          const notebook =
            vscode.workspace.notebookDocuments.find(
              (doc) => doc.uri.toString() === uri.toString(),
            ) ??
            (uri.fsPath.endsWith("ipynb")
              ? await vscode.workspace.openNotebookDocument(uri)
              : undefined);
          if (notebook) {
            return notebook
              .getCells()
              .map((cell) => cell.document.getText())
              .join("\n\n");
          }

          const openTextDocument = vscode.workspace.textDocuments.find(
            (doc) => doc.uri.fsPath === uri.fsPath,
          );
          if (openTextDocument !== undefined) {
            return openTextDocument.getText();
          }
    
          const fileStats = await vscode.workspace.fs.stat(
            uriFromFilePath(filepath),
          );
          if (fileStats.size > 10 * VsCodeIde.MAX_BYTES) {
            return "";
          }
    
          const bytes = await vscode.workspace.fs.readFile(uri);
    
          // Truncate the buffer to the first MAX_BYTES
          const truncatedBytes = bytes.slice(0, VsCodeIde.MAX_BYTES);
          const contents = new TextDecoder().decode(truncatedBytes);
          return contents;
        } catch (e) {
          console.warn("Error reading file", e);
          return "";
        }
      }
}

export { VsCodeIde };