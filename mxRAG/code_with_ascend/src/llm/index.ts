import { FetchHttpClient } from "./httpClient";

interface RequestBody {
    model: string;
    messages: {
        role: string,
        content: string
    }[];
    max_tokens: number;
    presence_penalty: number;
    frequency_penalty: number;
    seed: number | null;
    temperature: number;
    top_p: number;
    stream: boolean;
}

export class CodeLLM {
    private readonly httpClient: FetchHttpClient = new FetchHttpClient();
    private readonly MAX_QUERY_LEN: number = 16000; // 定义最大的查询长度
    url: string = "";
    modelName: string = "";
    avaiable: boolean = false;

    async verifyModel() {
        let current = "";
        try {
            current = await this.getModels();
        } catch (error: any) {
            const errorMesseage = error?.message || 'Unknown error occurred';
            throw new Error(errorMesseage);
        }

        if (!current || current !== this.modelName) {
            throw new Error(`The current model is ${current}, inconsistent with the expected model ${this.modelName}`);
        } else {
            this.avaiable = true;
        }
    }

    async getModels(): Promise<string> {
        const chatUrl = new URL("v1/models", this.url).toString();
        try {
            const response = await this.httpClient.get(chatUrl);
            return response?.data?.[0]?.id || "";
        } catch (error: any) {
            const errorMesseage = error?.message || 'Unknown error occurred';
            throw new Error('Failed to get response:' + errorMesseage);
        }
    }

    private getRequestBody(
        query: string,
        role: string,
        max_tokens: number,
        presence_penalty: number,
        frequency_penalty: number,
        seed: number | null,
        temperature: number,
        top_p: number
    ): RequestBody {
        const requestBody: RequestBody = {
            "model": this.modelName,
            "messages": [
                {
                    "role": role,
                    "content": query
                }
            ],
            "max_tokens": max_tokens,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "seed": seed,
            "temperature": temperature,
            "top_p": top_p,
            "stream": false
        };

        return requestBody;
    }

    async chat(
        query: string,
        role: string = "user",
        max_tokens: number = 4096,
        presence_penalty: number = 1,
        frequency_penalty: number = 1,
        seed: number | null = null,
        temperature: number = 1,
        top_p: number = 1
    ): Promise<string> {
        if (query === null || query.length > this.MAX_QUERY_LEN) {
            console.error(`query cannot be null or cantent length not in (0, ${this.MAX_QUERY_LEN}]`);
            throw new Error('query is not compliance');
        }
        const reqrequestBody = this.getRequestBody(
            query,
            role,
            max_tokens,
            presence_penalty,
            frequency_penalty,
            seed,
            temperature,
            top_p
        );
        const chatUrl = new URL("v1/chat/completions", this.url).toString();
        try {
            const response = await this.httpClient.post(chatUrl, reqrequestBody);
            const finishReason = response?.choices?.[0]?.finish_reason;
            let ans = response?.choices?.[0]?.message?.content || "";

            if (finishReason === "length") {
                console.log("for the content length reason, it stopped.");
                ans += "......";
            } 

            return ans;
        } catch (error: any) {
            const errorMesseage = error?.message || 'Unknown error occurred';
            console.error('Fetch error:' + errorMesseage);
            throw new Error(errorMesseage);
        }
    }

    async* chatStreamly(
        query: string,
        role: string = "user",
        max_tokens: number = 4096,
        presence_penalty: number = 1,
        frequency_penalty: number = 1,
        seed: number | null = null,
        temperature: number = 1,
        top_p: number = 1
    ): AsyncGenerator<string, void, unknown> {
        if (query === null || query.length > this.MAX_QUERY_LEN) {
            console.error(`query cannot be null or cantent length not in (0, ${this.MAX_QUERY_LEN}]`);
            throw new Error('query is not compliance');
        }
        const reqrequestBody = this.getRequestBody(
            query,
            role,
            max_tokens,
            presence_penalty,
            frequency_penalty,
            seed,
            temperature,
            top_p
        );
        reqrequestBody.stream = true;
        const chatUrl = new URL("v1/chat/completions", this.url).toString();
        const response = this.httpClient.postStreamly(chatUrl, reqrequestBody);
        for await (const chunk of response) {
            try {
                const data = JSON.parse(chunk.substring(5).trim());
                if (!data.choices[0]) {
                    break;
                }
                const finishReason = data.choices[0].finish_reason;
                if (finishReason === "stop") {
                    break;
                } else if (finishReason === "length") {
                    console.log("for the content length reason, it stopped.");
                    yield "......";
                    break;
                } else if (finishReason === "") {
                    console.error("finish reason is empty.");
                    break;
                }
                yield data.choices[0].delta?.content || "";
            } catch (e) {
                console.error(`Response content cannot be converted to JSON format: ${e}`);
                break;
            }
        }
    }
}