import {Range} from "./index";

export function getRangeInString(content: string, range: Range): string {
    const lines = content.split("\n");

    if (range.start.line === range.end.line) {
        return (
            lines[range.start.line]?.substring(
                range.start.character,
                range.end.character + 1,
            ) ?? ""
        );
    }

    const firstLine =
        lines[range.start.line]?.substring(
            range.start.character,
            lines[range.start.line].length,
        ) ?? "";
    const middleLines = lines.slice(range.start.line + 1, range.end.line);
    const lastLine =
        lines[range.end.line]?.substring(0, range.end.character) ?? "";

    return [firstLine, ...middleLines, lastLine].join("\n");
}

export function getBasename(filepath: string, n = 1): string {
    return filepath.split(/[\\/]/).pop() ?? "";
}

export function isOnlyPunctuationAndWhitespace(completion: string): boolean {
    const punctuationAndWhitespaceRegex = /^[^\w\d\}\)\]]+$/;
    return punctuationAndWhitespaceRegex.test(completion);
}