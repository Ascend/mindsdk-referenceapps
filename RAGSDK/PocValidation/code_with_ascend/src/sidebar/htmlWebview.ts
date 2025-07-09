export const HTML_WEBVIEW =
    `<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                height: 100vh;
            }
            #chat-box {
                flex: 1;
                overflow-y: scroll;
                padding: 10px;
            }
            #input-container {
                display: flex;
                padding: 5px;
            }
            #input-box {
                flex: 1;
                padding: 5px;
                box-sizing: border-box;
                background-color: black;
                color: white;
                border: none;
            }
            #send-button {
                padding: 8px;
                margin-left: 5px;
                background-color: black;
                color: white;
                border: none;
                font-family: Arial, sans-serif;
            }
            .styled-div {
                background-color: #f0f0f0;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                padding: 16px;
                margin: 16px 0;
                font-family: Arial, sans-serif;
                color: #333;
                border: 1px solid #ddd;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
            }
        </style>
    </head>
    <body>
        <div id="chat-box"></div>
        <div id="input-container">
            <input type="text" id="input-box" placeholder="输入消息..." />
            <button id="send-button" onclick="sendMessage()">发送</button>
        </div>

        <script>
            console.log('hello from the ascend webview!')
            const vscode = acquireVsCodeApi();

            document.getElementById('input-box').addEventListener("keydown", function(event) {
                if (event.key === "Enter") {
                    sendMessage();
                }
            })

            function sendMessage() {
                var inputElement = document.getElementById("input-box");
                var message = inputElement.value;
                if (message.trim() === "") {
                    return;
                };
                inputElement.value = "";
                appendMessage("user", message);
                const messageEvent = {command: 'WebSendMesToVscode', data: message};
                vscode.postMessage(messageEvent);
            }

            function appendMessage(sender, message) {
                var chatBox = document.getElementById("chat-box");
                var messageElement = document.createElement('div');
                messageElement.className = "styled-div";
                messageElement.innerHTML = "<strong>" + sender + ": </strong>" + message;
                messageElement.style.whiteSpace = "pre-wrap";
                chatBox.appendChild(messageElement);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            function appendStreamMessage(sender, message) {
                var chatBox = document.getElementById("chat-box");
                var lastMessageElement = chatBox.lastElementChild;
                if (lastMessageElement && lastMessageElement.dataset.id === message.id) {
                    lastMessageElement.innerHTML += message.data;
                } else {
                    var messageElement = document.createElement('div');
                    messageElement.className = "styled-div";
                    messageElement.dataset.id = message.id;
                    messageElement.innerHTML = '<strong style="color:blue">' + message.model + ": </strong>" + message.data;
                    messageElement.style.whiteSpace = "pre-wrap";
                    chatBox.appendChild(messageElement);
                }
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            window.addEventListener('message', event => {
                const message = event.data;
                switch (message.command) {
                    case 'vscodeSendMesToWeb':
                        if (message.data.trim() === "") {
                            return;
                        }
                        
                        appendMessage("user", message.data);
                        break
                    case 'LLMSendMesToWeb':
                        appendStreamMessage("model", message);
                        break;
                }
            })
        </script>
    </body>
</html>`;