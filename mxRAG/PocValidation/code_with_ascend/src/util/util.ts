import * as vscode from "vscode";

function isWindowsLocalButNotRemote(): boolean {
    return (
        vscode.env.remoteName !== undefined &&
        ["wsl", "ssh-remote", "dev-container", "attached-container"].includes(
            vscode.env.remoteName,
        ) &&
        process.platform === "win32"
    );
}

function windowsToPosix(winPath: string): string {
    let posPath = winPath.split("\\").join("/");
    if (posPath[1] === ":") {
        posPath = posPath.slice(2);
    }
    return posPath;
}

export function uriFromFilePath(filepath: string): vscode.Uri {
    let path = filepath;
    if (vscode.env.remoteName) {
        if (isWindowsLocalButNotRemote()) {
            path = windowsToPosix(filepath);
        }
        return vscode.Uri.parse(
            `vscode-remote://${vscode.env.remoteName}${path}`,
        );
    } else {
        return vscode.Uri.file(path);
    }
}

const LANGUAGES_NAME: { [extension: string]: string } = {
    ts: 'typescript',
    js: 'typescript',
    tsx: 'typescript',
    jsx: 'typescript',
    ipynb: 'python',
    py: 'python',
    pyi: 'python',
    java: 'java',
    cpp: 'cpp',
    cxx: 'cpp',
    h: 'cpp',
    hpp: 'cpp',
    cs: 'csharp',
    c: 'c',
    scala: 'scala',
    sc: 'scala',
    go: 'go',
    rs: 'rust',
    hs: 'haskell',
    php: 'php',
    rb: 'ruby',
    rails: 'rubyOnRails',
    swift: 'swift',
    kt: 'kotlin',
    clj: 'clojure',
    cljs: 'clojure',
    cljc: 'clojure',
    jl: 'julia',
    fs: 'fsharp',
    fsi: 'fsharp',
    fsx: 'fsharp',
    fsscript: 'fsharp',
    r: 'r',
    R: 'r',
    dart: 'dart',
    sol: 'solidity',
};

export function languageNameForFilepath(
    filename: string,
): string {
    return LANGUAGES_NAME[filename.split(".").slice(-1)[0]] || "typescript";
}