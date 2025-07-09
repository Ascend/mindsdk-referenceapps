import {distance} from "fastest-levenshtein";

export type LineStream = AsyncGenerator<string>;

export async function* avoidPathLine(
    stream: LineStream,
    comment: string,
): LineStream {
    for await (const line of stream) {
        if (line.startsWith(`${comment} Path: `) || line.trim() === comment) {
            continue;
        }
        yield line;
    }
}

const bracketEnding = [")", "]", "}", ";"];

function isBracketEnding(line: string): boolean {
    return line
        .trim()
        .split("")
        .some((char) => bracketEnding.includes(char));
}

function commonPrefixLength(a: string, b: string): number {
    let i = 0;
    while (i < a.length && i < b.length && a[i] === b[i]) {
        i++;
    }
    return i;
}

export async function* stopAtSimilarLine(
    stream: LineStream,
    line: string,
): AsyncGenerator<string> {
    const trimmedLine = line.trim();
    const lineIsBracketEnding = isBracketEnding(trimmedLine);
    for await (const nextLine of stream) {
        if (nextLine === line) {
            break;
        }

        if (lineIsBracketEnding && trimmedLine.trim() === nextLine.trim()) {
            yield nextLine;
            continue;
        }

        let lineQualifies = nextLine.length > 4 && trimmedLine.length > 4;
        if (
            lineQualifies &&
            (commonPrefixLength(nextLine.trim(), trimmedLine.trim()) > 8 ||
                distance(nextLine.trim(), trimmedLine) / trimmedLine.length < 0.1)
        ) {
            break;
        }
        yield nextLine;
    }
}

const LINES_TO_STOP_AT = ["# End of file.", "<STOP EDITING HERE"];

export async function* stopAtLines(
    stream: LineStream,
): LineStream {
    for await (const line of stream) {
        if (LINES_TO_STOP_AT.some((stopAt) => line.trim().includes(stopAt))) {
            break;
        }
        yield line;
    }
}

export async function* stopAtRepeatingLines(
    lines: LineStream,
): LineStream {
    const repeatedLines: string[] = [];
    for await (const line of lines) {
        if (repeatedLines.length === 0) {
            repeatedLines.push(line);
        } else if (repeatedLines.length < 3) {
            if (repeatedLines[repeatedLines.length - 1] === line) {
                repeatedLines.push(line);
            } else {
                while (repeatedLines.length > 0) {
                    yield repeatedLines.shift()!;
                }
                yield line;
            }
        } else {
            yield repeatedLines[0];
            return;
        }
    }

    while (repeatedLines.length > 0) {
        yield repeatedLines.shift()!;
    }
}