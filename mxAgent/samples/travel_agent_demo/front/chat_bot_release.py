import streamlit as st
from samples.travel_agent.travelagent import TravelAgent

if __name__ == "__main__":
    st.set_page_config(
        page_title = "旅游规划agent",
        page_icon = "./logo.jpg"
    )
    st.logo("logo.jpg")
    st.markdown('<h3 style="font-size: 24px;">旅游规划Agent</h3>', unsafe_allow_html=True)
    

    placeholder1 = st.empty()
    placeholder2 = st.empty()
    placeholder3 = st.empty()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "aagent" not in st.session_state:
        st.session_state.agent = TravelAgent()

    with placeholder1:
        container = st.container(height=300,border=False)
    with placeholder2:
        _,col1,_ = st.columns([10,2,10])
        with col1:
            st.image("logo.jpg", use_column_width=True)
    with placeholder3:
        _,col2,_ = st.columns([1,20,1])
        helloinfo = """<p style='font-size: 16px; padding-left: 10px;'>您好，我是旅游规划agent，擅长旅行规划、景点攻略查询</p>
        <p style='font-size: 16px; padding-left: 10px;'>例如：从北京到西安旅游规划</p>
        <p style='font-size: 16px; padding-left: 10px;'>例如：西安有哪些免费的博物馆景点</p>
        <p style='font-size: 16px; padding-left: 10px;'>例如：查一下西安的酒店</p>"""
        with col2:
                st.markdown(helloinfo,unsafe_allow_html=True)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.empty()
            st.markdown(message["content"])

    if prompt := st.chat_input("send message"):
        st.session_state.messages.append({"role":"user", "content":prompt})
        placeholder1.empty()
        placeholder2.empty()
        placeholder3.empty()

        agent = st.session_state["agent"]

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("thinking..."):
                response = agent.run(query=prompt, stream=True)
            if isinstance(response, str):
                st.markdown(response)
            else:
                response = st.write_stream(response)

        st.session_state.messages.append({"role":"assistant", "content":response})
