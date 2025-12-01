import streamlit as st
import asyncio
import uuid
import logging
import sys

import agent
import feedback
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("streamlit")

# Page configuration
st.set_page_config(
    page_title='Pharma SOP Chatbot',
    page_icon='💊',
    layout="centered",
    initial_sidebar_state="auto",
)

# Sidebar
with st.sidebar:
    st.title("Settings")

    st.markdown(
        "Strands Agents SDK 기반의 제약 SOP 챗봇입니다. "
        "Amazon Bedrock Knowledge Base를 활용하여 SOP 문서에서 정보를 검색하고 답변합니다."
    )

    # Model selection
    model_name = st.selectbox(
        'Foundation Model',
        list(config.MODEL_OPTIONS.keys()),
        index=0
    )

    # Knowledge Base ID input
    kb_id = st.text_input(
        'Knowledge Base ID',
        value=config.KNOWLEDGE_BASE_ID,
        help="Amazon Bedrock Knowledge Base ID를 입력하세요."
    )
    if kb_id:
        config.KNOWLEDGE_BASE_ID = kb_id

    # Reset button
    clear_button = st.button("대화 초기화", key="clear")

# Main title
st.title('💊 Pharma SOP Chatbot')

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.greetings = False
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.last_question = ""
    st.session_state.last_answer = ""
    st.session_state.awaiting_feedback = False

# Handle reset
if clear_button:
    st.session_state.messages = []
    st.session_state.greetings = False
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.last_question = ""
    st.session_state.last_answer = ""
    st.session_state.awaiting_feedback = False
    agent.clear_conversation()
    st.rerun()


# Display chat messages
def display_chat_messages():
    """Display chat message history."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


display_chat_messages()

# Greeting message
if not st.session_state.greetings:
    with st.chat_message("assistant"):
        intro = """안녕하세요! 제약 SOP 챗봇입니다.

SOP(Standard Operating Procedure)에 대한 질문을 입력해 주세요.
다음과 같은 질문에 답변할 수 있습니다:

- 문서 작성 시 오기 처리 방법
- Deviation Level 구분 기준
- 환경 모니터링 샘플링 기준
- 신규 장비 도입 절차
- 기타 SOP 관련 문의"""
        st.markdown(intro)
        st.session_state.messages.append({"role": "assistant", "content": intro})
        st.session_state.greetings = True


# Feedback section
def show_feedback_section():
    """Display feedback buttons after assistant response."""
    if st.session_state.awaiting_feedback and st.session_state.last_answer:
        st.markdown("---")
        st.markdown("**이 답변이 도움이 되셨나요?**")

        col1, col2, col3 = st.columns([1, 1, 4])

        with col1:
            if st.button("👍 도움됨", key="helpful"):
                success = feedback.save_feedback(
                    question=st.session_state.last_question,
                    answer=st.session_state.last_answer,
                    is_helpful=True,
                    session_id=st.session_state.session_id
                )
                if success:
                    st.success("피드백이 저장되었습니다. 감사합니다!")
                st.session_state.awaiting_feedback = False
                st.rerun()

        with col2:
            if st.button("👎 아쉬움", key="not_helpful"):
                success = feedback.save_feedback(
                    question=st.session_state.last_question,
                    answer=st.session_state.last_answer,
                    is_helpful=False,
                    session_id=st.session_state.session_id
                )
                if success:
                    st.info("피드백이 저장되었습니다. 더 나은 답변을 위해 노력하겠습니다.")
                st.session_state.awaiting_feedback = False
                st.rerun()


# Show feedback section if awaiting
if st.session_state.awaiting_feedback:
    show_feedback_section()

# Chat input
if prompt := st.chat_input("SOP 관련 질문을 입력하세요..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.last_question = prompt
    logger.info(f"User query: {prompt}")

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        response_container = [""]

        # Run agent with streaming
        async def stream_response():
            async for chunk in agent.run_agent_stream(prompt, model_name):
                response_container[0] += chunk
                message_placeholder.markdown(response_container[0] + "▌")
            message_placeholder.markdown(response_container[0])

        asyncio.run(stream_response())
        full_response = response_container[0]

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.session_state.last_answer = full_response
    st.session_state.awaiting_feedback = True
    st.rerun()
