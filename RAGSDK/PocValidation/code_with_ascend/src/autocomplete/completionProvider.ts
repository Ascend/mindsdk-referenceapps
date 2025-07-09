import * as vscode from 'vscode';
import {v4 as uuidv4} from "uuid";
import type {AutocompleteInput, AutocompleteOutcome} from '.';
import {CodeLLM} from '../llm';
import {VsCodeIde} from './ide';
import {CompletionProvider} from './autoCompletion';

export class MxCompletionProvider implements vscode.InlineCompletionItemProvider {
    private completionProvider: CompletionProvider;

    constructor(
        private readonly llm: CodeLLM
    ) {
        this.completionProvider = new CompletionProvider(
            new VsCodeIde(),
            this.llm
        );
    }

    public async provideInlineCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        context: vscode.InlineCompletionContext,
        token: vscode.CancellationToken
        // @ts-ignore
    ): vscode.ProviderResult<vscode.InlineCompletionItem[] | vscode.InlineCompletionList> {
        const enableTabAutocomplete =
            vscode.workspace
                .getConfiguration("Completion")
                .get<boolean>("Autocomplete") || false;

        if (token.isCancellationRequested || !enableTabAutocomplete) {
            return null;
        }

        if (
            context.selectedCompletionInfo &&
            !context.selectedCompletionInfo.text.startsWith(
                document.getText(context.selectedCompletionInfo.range)
            )
        ) {
            return null;
        }

        const selectedCompletionInfo = context.selectedCompletionInfo;

        const pos = {
            line: position.line,
            character: position.character
        };

        const input: AutocompleteInput = {
            completionId: uuidv4(),
            filepath: document.uri.fsPath,
            pos,
            selectedCompletionInfo,
            documentText: document.getText()
        };

        const abortController = new AbortController();
        const signal = abortController.signal;
        token.onCancellationRequested(() => abortController.abort());

        const outcome =
            await this.completionProvider.provideInlineCompletionItems(
                input,
                signal
            );

        if (!outcome || !outcome.completion) {
            return null;
        }

        if (selectedCompletionInfo) {
            outcome.completion = selectedCompletionInfo.text + outcome.completion;
        }

        const willDisplay = this.willDispaly(
            selectedCompletionInfo,
            signal,
            outcome
        );

        if (!willDisplay) {
            return null;
        }
        ;

        const startPos = selectedCompletionInfo?.range.start ?? position;
        const completionRange = new vscode.Range(
            startPos,
            startPos.translate(0, outcome.completion.length)
        );
        const completionItem = new vscode.InlineCompletionItem(
            outcome.completion,
            completionRange
        );
        return [completionItem];
    }

    willDispaly(
        selectedCompletionInfo: vscode.SelectedCompletionInfo | undefined,
        abortSignal: AbortSignal,
        outcome: AutocompleteOutcome
    ): boolean {
        if (selectedCompletionInfo) {
            const {text, range} = selectedCompletionInfo;
            if (!outcome.completion.startsWith(text)) {
                console.log(
                    `Won't display completion because doesn't match: ${text}, ${outcome.completion}`,
                    range
                );
            }
            ;
        }

        if (abortSignal.aborted) {
            return false;
        }

        return true;
    }
}