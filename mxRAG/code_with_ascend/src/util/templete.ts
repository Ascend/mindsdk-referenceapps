const simpleEditPrompt = `Here is the code before editing:
\`\`\`{{{language}}}
{{{code}}}
\`\`\`

Here is the edit requested:
According to the cleancode standards, make modifications to the above code.

Here is the code after editing:`;

const generateTestPrompt = `Consider the following code:
\`\`\`{{{language}}}
{{{code}}}
\`\`\`

Generate test case for the above code, output nothing except for the code, no explanation.

Here is the case:`;

const explainCodePrompt =  `考虑以下代码：
\`\`\`{{{language}}}
{{{code}}}
\`\`\`

请使用中文提供对上述代码的解释，包括对变量和函数名称的理解。

以下是解释:`;
// // The following is in English prompt
// `Consider the following code:
// \`\`\`{{{language}}}
// {{{code}}}
// \`\`\`

// Provide an explanation of the above code, including understanding of variable and function names.

// Here is the explanation:`;

const chatPrompt = `You are an AI coding assistant that helps people with programing. Write a reponse that appropriately completes the user's request.
Please answer the questions:{{{code}}}`;

export {
    simpleEditPrompt,
    generateTestPrompt,
    explainCodePrompt,
    chatPrompt
};