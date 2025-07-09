import fetch, {Response} from "node-fetch";

export class FetchHttpClient {
    responseLimitSize: number = 1024 * 1024;
    static HTTP_SUCCESS: number = 200;

    async post(url: string, body: any, headers: { [key: string]: string } = {}): Promise<any> {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
                ...headers
            },
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        try {
            return await response.json();
        } catch (error: any) {
            const errorMesseage = error?.message || 'Unknown error occurred';
            throw new Error('Failed to parse JSON response:' + errorMesseage);
        }
    }

    async get(url: string): Promise<any> {
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        try {
            return await response.json();
        } catch (error: any) {
            const errorMesseage = error?.message || 'Unknown error occurred';
            throw new Error('Failed to parse JSON response:' + errorMesseage);
        }
    }

    async* postStreamly(url: string, body: any, headers: { [key: string]: string } = {}): AsyncGenerator<string> {
        let response: Response;

        try {
            response = await fetch(url, {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                    ...headers
                },
                body: JSON.stringify(body)
            });
        } catch (e) {
            console.error(`request ${url} failed, find exception: ${e}`);
            throw new Error(`request failed: ${e}`);
        }

        if (response.status === FetchHttpClient.HTTP_SUCCESS) {
            try {
                const contentType: string | null = response.headers.get("Content-Type");
                if (contentType === null || !contentType.includes('text/event-stream')) {
                    console.error("content type is not stream");
                    throw new Error("content type is not stream");
                }
            } catch (e) {
                console.error(`get content type failed, find exception: ${e}`);
                throw new Error("get content type failed");
            }
            for await (const result of this.iterLines(response)) {
                yield result;
            }
        } else {
            console.error(`request failed with statu code ${response.status}`);
            throw new Error("request failed");
        }
    }

    private async* iterLines(response: Response): AsyncGenerator<string> {
        let totalLength: number = 0;
        let buffer = new Uint8Array(0);
        try {
            const stream = response.body as any;
            const decoder = new TextDecoder("utf-8");
            if (!stream) {
                throw new Error("Response body is not readable");
            }

            for await (const chunk of stream) {
                totalLength += chunk.length;
                if (totalLength > this.responseLimitSize) {
                    console.error("content length exceed limit");
                    throw new Error("content length exceed limit");
                }
                const newBuffer = new Uint8Array(buffer.length + chunk.length);
                newBuffer.set(buffer);
                newBuffer.set(chunk, buffer.length);
                buffer = newBuffer;

                let lineIndex;
                while ((lineIndex = buffer.indexOf('\n'.charCodeAt(0))) !== -1) {
                    const line = buffer.subarray(0, lineIndex + 1);
                    buffer = buffer.subarray(lineIndex + 2);
                    lineIndex = buffer.indexOf('\n'.charCodeAt(0));
                    yield decoder.decode(line);
                }
            }
        } catch (e) {
            console.error(`read response failed, find exception: ${e}`);
            throw new Error("read response failed");
        }
    }
}