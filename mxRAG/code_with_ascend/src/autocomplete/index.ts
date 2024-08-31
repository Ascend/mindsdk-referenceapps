export interface IDE {
    getWorkspaceDirectories(): string[];
    readFile(filepath: string): Promise<string>;
}

export interface Position {
    line: number;
    character: number;
}

export interface Range {
    start: Position;
    end: Position;
}

interface BaseCompletionOptions {
    temperature?: number;
    topP?: number;
    topK?: number;
    presencePenalty?: number;
    frequencyPenalty?: number;
    stop?: string[];
    maxTokens?: number;
    stream?: boolean;
}

export interface CompletionOptions extends BaseCompletionOptions {
    model: string;
}

export interface AutocompleteTemplate {
    template:
        | string
        | ((
            prefix: string,
            suffix: string,
        ) => string);
    completionOptions?: Partial<CompletionOptions>;
}

export interface AutocompleteInput {
    completionId: string,
    filepath: string,
    pos: Position,
    selectedCompletionInfo?: {
        text: string;
        range: Range;
    };
    documentText: string;
}

export interface AutocompleteOutcome {
    completion: string;
    prompt: string;
    completionOptions: any;
}