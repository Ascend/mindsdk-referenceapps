import * as vscode from 'vscode';
import {CodeLLM} from '../llm';
import {v4 as uuidv4} from 'uuid';
import {HTML_WEBVIEW} from './htmlWebview';
import {getPrompt} from '../util/prompt';

export class ChatWebview implements vscode.WebviewViewProvider {
    public webview: vscode.WebviewView | null = null;

    constructor(private readonly llm: CodeLLM) {
    }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext<unknown>,
        token: vscode.CancellationToken
    ): void | Thenable<void> {
        this.webview = webviewView;
        webviewView.webview.options = {
            enableScripts: true
        };
        webviewView.webview.onDidReceiveMessage(async (message) => {
            if (message.command === "WebSendMesToVscode") {
                if (!this.llm.avaiable) {
                    vscode.window.showWarningMessage('Please configure the avaiable model parameters first.');
                    return;
                }
                const prompt = getPrompt("chat", message.data);
                const generator = this.llm.chatStreamly(prompt);

                const id = uuidv4();
                try {
                    for await (const update of generator) {
                        webviewView.webview.postMessage({
                            id: id,
                            command: "LLMSendMesToWeb",
                            model: this.llm.modelName,
                            data: update
                        });
                    }
                } catch (e: any) {
                    throw e;
                }
            }
        }, undefined);

        webviewView.webview.html = HTML_WEBVIEW;
    }
}