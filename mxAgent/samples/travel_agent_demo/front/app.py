
import argparse
import gradio as gr
from  mxAgent. samples.travel_agent_demo.travelagent import TravelAgent


global mx_agent

def agent_run(messgae):
    query = messgae.get("content")
    TravelAgent


def user_query(user_message, history):
    return "", history + [{"role": "user", "content":user_message}]


def clear_history(history):
    return []

def bot_response(history):
    # 将最新的问题传给RAG
    try:
        response = agent_run(history[-1])
        
        # 返回迭代器
        history += [{"role": "assistant", "content":""}]
        
        history[-1]["content"] = '推理错误'
        for res in response:
            history[-1]["content"] = '推理错误' if res['result'] is None else res['result']
            yield history
        yield history
        print(history)
    except Exception as err:
        history[-1]["content"] = "推理错误"
        yield history

def build_demo():
    with gr.Blocks() as demo:
        gr.HTML("""<center><h1>旅行规划Agent</h1><center>
                <p style='font-size: 16px; padding-left: 10px;'>例如：从北京到西安旅游规划</p>
                <p style='font-size: 16px; padding-left: 10px;'>例如：西安有哪些免费的博物馆景点</p>
                <p style='font-size: 16px; padding-left: 10px;'>例如：查一下西安的酒店</p>
                
                """)
        with gr.Row():
            with gr.Column(scale=200):

                initial_msg =  [ {"role": "assistant", 
                                  "content": "这条消息下想说明的是：如果 Chatbot 的 type 参数为 'messages'，那么发送到/从 Chatbot "
                                                     "的数据将是一个包含 role 和 content 键的字典列表。这种格式符合大多数 LLM API（如 "
                                                     "HuggingChat、OpenAI、Claude）期望的格式。role 键可以是 'user' 或 "
                                                     "'assistant'，content 键可以是一个字符串（支持 markdown/html 格式），一个 "
                                                     "FileDataDict（用于表示在 Chatbot 中显示的文件），或者一个 gradio 组件。"}
                ],
                
                # chatbot = gr.Chatbot(initial_msg, type="messages",)
                chatbot = gr.Chatbot(
                [
                   
                    {"role": "assistant", "content": "你好，我是你的AI小助手，这是你自己预制的一个信息。"},
                    {"role": "assistant", "content": "这条消息下想说明的是：如果 Chatbot 的 type 参数为 'messages'，那么发送到/从 Chatbot "
                                                     "的数据将是一个包含 role 和 content 键的字典列表。这种格式符合大多数 LLM API（如 "
                                                     "HuggingChat、OpenAI、Claude）期望的格式。role 键可以是 'user' 或 "
                                                     "'assistant'，content 键可以是一个字符串（支持 markdown/html 格式），一个 "
                                                     "FileDataDict（用于表示在 Chatbot 中显示的文件），或者一个 gradio 组件。"}
                ],
                type="messages",
                show_label=False,
                height=500,
                show_copy_button=True


            )
    
                with gr.Row():
                    msg = gr.Textbox(placeholder="在此输入问题...", container=False)
                with gr.Row():
                    send_btn = gr.Button(value="发送", variant="primary")
                    clean_btn = gr.Button(value="清空历史")
            send_btn.click(user_query, [msg, chatbot], [msg, chatbot], queue=False).then(bot_response,
                                                                                         [chatbot], chatbot)
            clean_btn.click(clear_history, chatbot, chatbot)
    return demo




def get_args():
    parse = argparse.ArgumentParser()
    parse.add_argument("--model_name", type=str, default="Qwen1.5-32B-Chat", help="OpenAI客户端模型名")
    parse.add_argument("--base_url", type=str, default="http://10.44.115.108:1055/v1", help="OpenAI客户端模型地址")
    parse.add_argument("--api_key", type=str, default="EMPTY", help="OpenAI客户端api key")
    return parse.parse_args().__dict__

if __name__ == "__main__":
    args = get_args()
    base_url = args.pop("base_url")
    api_key = args.pop("api_key")
    llm_name = args.pop("model_name")

    mx_agent = TravelAgent(base_url, api_key, llm_name)
    demo = build_demo()
    demo.launch(share=True)