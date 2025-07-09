import * as vscode from 'vscode';
import {CodeLLM} from './llm';
import {ChatWebview} from './sidebar/chatWebview';
import {v4 as uuidv4} from 'uuid';
import {getPrompt} from './util/prompt';
import {languageNameForFilepath} from './util/util';
import {MxCompletionProvider} from './autocomplete/completionProvider';

async function verifyMenuSettings(llm: CodeLLM) {
    const config = vscode.workspace.getConfiguration('CodeLLM');
    const url = config.get('url') as string;
    const modelName = config.get('modelName') as string;

    if (url.trim() === "") {
        vscode.window.showWarningMessage('The setting "url" should not be empty.');
        return;
    }
    try {
        llm.url = url;
        llm.modelName = modelName;
        await llm.verifyModel();
    } catch (error: any) {
        const errorMesseage = error?.message || "Unkonwn error occurred";
        vscode.window.showErrorMessage(errorMesseage);
        return;
    }
    vscode.window.showInformationMessage("Configuration completed, you can start using code with ascend!");
}

function registerMenuSetting(llm: CodeLLM) {
    vscode.workspace.onDidChangeConfiguration(async event => {
        if (event.affectsConfiguration('CodeLLM.url') || event.affectsConfiguration('CodeLLM.modelName')) {
            verifyMenuSettings(llm);
        }
    });
}

async function codeWithLLM(chatWebview: ChatWebview, llm: CodeLLM, templeteType: string) {
    if (!llm.avaiable) {
        vscode.window.showWarningMessage('Please configure the avaiable model parameters first.');
        return;
    }
    vscode.commands.executeCommand("Chat-sidebar.focus");
    const editor = vscode.window.activeTextEditor;
    if (editor) {
        const selection = editor.selection;
        const selecedText = editor.document.getText(selection);
        const fileName = editor.document.fileName;
        chatWebview?.webview?.webview.postMessage({
            command: "vscodeSendMesToWeb",
            data: selecedText
        });
        const languageName = languageNameForFilepath(fileName);
        const prompt = getPrompt(templeteType, selecedText, languageName);
        const generator = llm.chatStreamly(prompt);

        const id = uuidv4();
        try {
            for await (const update of generator) {
                chatWebview?.webview?.webview.postMessage({
                    id: id,
                    command: "LLMSendMesToWeb",
                    model: llm.modelName,
                    data: update
                });
            }
        } catch (e: any) {
            throw e;
        }
    }
}

const commandsMap: (
    chatWebview: ChatWebview,
    llm: CodeLLM
) => { [command: string]: (...args: any) => any } = (
    chatWebview,
    llm
) => {
    return {
        'ascend.simpleEditCases': async () => {
            codeWithLLM(chatWebview, llm, "edit");
        },
        'ascend.generateTestCases': async () => {
            codeWithLLM(chatWebview, llm, "test");
        },
        'ascend.explainCodeCases': async () => {
            codeWithLLM(chatWebview, llm, "explain");
        }
    };
};

export function registerAllCommands(context: vscode.ExtensionContext) {
    const llm = new CodeLLM();

    verifyMenuSettings(llm);
    registerMenuSetting(llm);

    context.subscriptions.push(
        vscode.languages.registerInlineCompletionItemProvider(
            {pattern: "**"},
            new MxCompletionProvider(llm)
        )
    );

    const chatWebview = new ChatWebview(llm);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            "Chat-sidebar",
            chatWebview,
            {
                webviewOptions: {
                    retainContextWhenHidden: true
                }
            }
        )
    );

    for (const [command, callback] of Object.entries(
        commandsMap(
            chatWebview,
            llm
        )
    )) {
        context.subscriptions.push(
            vscode.commands.registerCommand(command, callback)
        );
    }
}