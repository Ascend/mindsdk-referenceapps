import {AutocompleteInput, AutocompleteOutcome, IDE,} from "./index";

import path from "path";

import {getTemplateForModel} from "./templates";
import Handlebars from "handlebars";

import {CodeLLM} from "../llm";
import {languageForFilepath} from "./languages";
import {getBasename, getRangeInString, isOnlyPunctuationAndWhitespace} from "./util";

import {avoidPathLine, stopAtLines, stopAtRepeatingLines, stopAtSimilarLine} from "./lineStream";

import {noFirstCharNewline, onlyWhitespaceAfterEndOfLine} from "./charStream";

export async function getTabCompletion(
    input: AutocompleteInput,
    token: AbortSignal,
    llm: CodeLLM,
    ide: IDE
): Promise<AutocompleteOutcome | undefined> {
    const {
        filepath,
        pos
    } = input;

    const fileContents = await ide.readFile(filepath);
    const filelines = fileContents.split("\n");

    const lang = languageForFilepath(filepath);
    const line = filelines[pos.line] ?? "";
    for (const endOfLine of lang.endOfLine) {
        if (line.endsWith(endOfLine) && pos.character >= line.length) {
            return undefined;
        }
    }

    if (!llm) {
        return;
    }

    let fullPrefix =
        getRangeInString(fileContents, {
            start: {line: 0, character: 0},
            end: input.selectedCompletionInfo?.range.start ?? pos,
        }) + (input.selectedCompletionInfo?.text ?? "");

    const fullSuffix =
        getRangeInString(fileContents, {
            start: pos,
            end: {line: filelines.length - 1, character: Number.MAX_SAFE_INTEGER},
        });

    let lineBelowCursor = "";
    let i = 1;
    while (
        lineBelowCursor.trim() === "" &&
        pos.line + i <= filelines.length - 1
        ) {
        lineBelowCursor = filelines[Math.min(pos.line + i, filelines.length - 1)];
        i++;
    }

    const {template, completionOptions} = getTemplateForModel("code");

    const workspaceDirs = ide.getWorkspaceDirectories();

    let prompt: string;
    const filename = getBasename(filepath);
    const reponame = getBasename(workspaceDirs[0] ?? "myproject");

    if (typeof template === "string") {
        const compiledTemplate = Handlebars.compile(template);

        prompt = compiledTemplate({
            fullPrefix,
            fullSuffix,
            filename,
            reponame
        });
    } else {
        prompt = template(fullPrefix, fullSuffix);
    }

    let generator = llm.chatStreamly(prompt);

    let cancelled = false;
    const generatorWithCancellation = async function* () {
        for await (const update of generator) {
            if (token.aborted) {
                cancelled = true;
                return;
            }
            yield update;
        }
    };
    let charGenerator = generatorWithCancellation();
    charGenerator = noFirstCharNewline(charGenerator);
    charGenerator = onlyWhitespaceAfterEndOfLine(charGenerator, lang.endOfLine);

    let lineGenerator = stopAtLines(charGenerator);
    lineGenerator = stopAtRepeatingLines(lineGenerator);
    lineGenerator = avoidPathLine(lineGenerator, lang.comment);

    const finalGenerator = stopAtSimilarLine(lineGenerator, lineBelowCursor);

    let completion = "";
    try {
        for await (const update of finalGenerator) {
            completion += update;
        }
    } catch (e: any) {
        throw e;
    }

    if (cancelled) {
        return undefined;
    }

    if (completion.trim().length <= 0) {
        return undefined;
    }

    completion = completion.trimEnd();

    if (completion[0] === " " && completion[1] !== " ") {
        if (fullPrefix.endsWith(" ") && fullSuffix.startsWith("\n")) {
            completion = completion.slice(1);
        }
    }

    let stop = completionOptions?.stop?.[0] || " ";

    if (completion.endsWith(stop)) {
        completion = completion.substring(0, completion.length - stop.length);
    }

    return {
        completion,
        prompt,
        completionOptions
    };
}

export class CompletionProvider {
    constructor(
        private readonly ide: IDE,
        private readonly llm: CodeLLM
    ) {
    }

    public async provideInlineCompletionItems(
        input: AutocompleteInput,
        token: AbortSignal
    ): Promise<AutocompleteOutcome | undefined> {
        const workspaceDirs = this.ide.getWorkspaceDirectories();
        let filepath = input.filepath;
        for (const workspaceDir of workspaceDirs) {
            if (filepath.startsWith(workspaceDir)) {
                filepath = path.relative(workspaceDir, filepath);
                break;
            }
        }

        const outcome = await getTabCompletion(input, token, this.llm, this.ide);

        if (!outcome?.completion) {
            return undefined;
        }

        if (isOnlyPunctuationAndWhitespace(outcome.completion)) {
            return undefined;
        }

        return outcome;
    }
}