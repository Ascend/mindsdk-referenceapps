import Handlebars from "handlebars";
import {chatPrompt, explainCodePrompt, generateTestPrompt, simpleEditPrompt} from "./templete";

export function getPrompt(templeteType: string, code: string, language: string = ""): string {
    let prompt: string;
    let templete = chatPrompt;
    if (templeteType === "edit") {
        templete = simpleEditPrompt;
    } else if (templeteType === "test") {
        templete = generateTestPrompt;
    } else if (templeteType === "explain") {
        templete = explainCodePrompt;
    }
    ;

    const compiledTemplate = Handlebars.compile(templete);
    prompt = compiledTemplate({
        code,
        language
    });
    return prompt;
}