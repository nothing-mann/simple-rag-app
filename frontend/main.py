import streamlit as st
from typing import Dict
import json
from collections import Counter
import re
import sys
import os
import time
from datetime import datetime
import pytz

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.config import COLLECTION_NAME, DEFAULT_MODEL
from backend.get_transcript import YouTubeTranscriptDownloader
from backend.chat import LiteLLMChat
from backend.rag_chat import HeritageRAGChat

st.set_page_config(
    page_title="Cultural Heritage Information",
    page_icon="🇳🇵",
    layout="wide"
)

nepal_timezone = pytz.timezone('Asia/Kathmandu')

if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'is_typing' not in st.session_state:
    st.session_state.is_typing = False

def render_header():
    st.title("🇳🇵 Enlighten Nepal Heritage Information")
    st.markdown("""
    Transform YouTube transcripts into interactive culture learning experiences.
    
    This tool demonstrates:
    - Base LLM Capabilities
    - RAG (Retrieval Augmented Generation)
    - LiteLLM OpenAI Integration
    - Agent-based Learning Systems
    """)

def render_sidebar():
    with st.sidebar:
        st.header("Development Stages")
        
        selected_stage = st.radio(
            "Select Stage:",
            [
                "1. Chat with OpenAI",
                "2. Raw Transcript",
                "3. Structured Data",
                "4. RAG Implementation",
                "5. Interactive Learning"
            ]
        )
        
        stage_info = {
            "1. Chat with OpenAI": """
            **Current Focus:**
            - Basic Cultural Heritage Information
            - Understanding LLM capabilities
            - Identifying limitations
            """,
            
            "2. Raw Transcript": """
            **Current Focus:**
            - YouTube transcript download
            - Raw text visualization
            - Initial data examination
            """,
            
            "3. Structured Data": """
            **Current Focus:**
            - Text cleaning
            - Dialogue extraction
            - Data structuring
            """,
            
            "4. RAG Implementation": """
            **Current Focus:**
            - OpenAI Embedding (text-embedding-ada-002)
            - Vector storage
            - Context retrieval
            """,
            
            "5. Interactive Learning": """
            **Current Focus:**
            - Scenario generation
            - Audio synthesis
            - Interactive practice
            """
        }
        
        st.markdown("---")
        st.markdown(stage_info[selected_stage])
        
        return selected_stage

def format_message(message, with_timestamp=True):
    content = message.get("content", "")
    
    if with_timestamp and "timestamp" in message:
        return content, message['timestamp']
    return content, None

def get_nepal_time():
    now = datetime.now(nepal_timezone)
    return now.strftime("%H:%M")

def display_chat_message(message, container=None):
    role = message.get("role", "assistant")
    
    avatar = "🧑" if role == "user" else "🤖"
    
    display = container if container else st
    
    content, timestamp = format_message(message)
    
    with display.chat_message(role, avatar=avatar):
        display.markdown(content)
        
        if timestamp:
            display.caption(f"sent at {timestamp}")

def render_chat_stage():
    st.header("Chat with OpenAI")
    
    if 'bedrock_chat' not in st.session_state:
        st.session_state.bedrock_chat = LiteLLMChat()
    
    st.markdown("""
    Start by exploring OpenAI's base Nepali Cultural heritage information capabilities. Try asking questions about cultural heritages in Nepal.
    """)

    chat_container = st.container()
    with chat_container:
        st.markdown("### Conversation")
        
        if not st.session_state.messages:
            st.info("👋 Send a message to start the conversation!")
            
        for message in st.session_state.messages:
            display_chat_message(message)
            
        if st.session_state.is_typing:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown("_Thinking..._")

    prompt = st.chat_input("Ask about Nepali heritage sites...", disabled=st.session_state.is_typing)
    if prompt:
        process_message(prompt)

    with st.sidebar:
        st.markdown("### Try These Examples")
        example_questions = [
            "Tell me about Krishna Mandir in Patan Durbar Square",
            "What is the historical significance of Bouddhanath Stupa?",
            "When was Krishna Mandir built and by whom?",
            "What are the architectural features of Bouddhanath Stupa?",
            "How did Krishna Mandir survive the 2015 earthquake?",
            "What rituals are performed at Bouddhanath Stupa by Buddhists?"
        ]
        
        for q in example_questions:
            if st.button(q, use_container_width=True, type="secondary"):
                process_message(q)
                st.rerun()

    if st.session_state.messages:
        col1, col2 = st.columns([5, 1])
        with col2:
            if st.button("Clear Chat", type="primary"):
                st.session_state.messages = []
                st.rerun()

def process_message(message: str):
    timestamp = get_nepal_time()
    st.session_state.messages.append({
        "role": "user", 
        "content": message,
        "timestamp": timestamp
    })
    
    with st.chat_message("user", avatar="👤"):
        content, timestamp = format_message(st.session_state.messages[-1])
        st.markdown(content)
        if timestamp:
            st.caption(f"sent at {timestamp}")
    
    st.session_state.is_typing = True
    st.rerun()

def on_response_ready():
    st.session_state.is_typing = False
    
def generate_response(message: str):
    try:
        response = st.session_state.bedrock_chat.generate_response(message)
        
        timestamp = get_nepal_time()
        if response:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "timestamp": timestamp
            })
        else:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "I'm sorry, I couldn't generate a response at this time.",
                "timestamp": timestamp
            })
    finally:
        st.session_state.is_typing = False

def count_characters(text):
    if not text:
        return 0, 0
        
    def is_nepali(char):
        return any([
            '\u0900' <= char <= '\u097F',  # Devnagari Characters
        ])
    
    np_chars = sum(1 for char in text if is_nepali(char))
    return np_chars, len(text)

def render_transcript_stage():
    st.header("Raw Transcript Processing")
    
    url = st.text_input(
        "YouTube URL",
        placeholder="Enter a Heritage site educational video YouTube URL"
    )
    
    if url:
        if st.button("Download Transcript"):
            try:
                with st.spinner("Downloading transcript..."):
                    downloader = YouTubeTranscriptDownloader()
                    transcript = downloader.get_transcript(url)
                    video_id = downloader.extract_video_id(url)
                    
                    transcript_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "data", "transcripts")
                    os.makedirs(transcript_dir, exist_ok=True)
                    
                    file_path = os.path.join(transcript_dir, f"{video_id}")
                    downloader.save_transcript(transcript, file_path)
                    if transcript:
                        transcript_text = "\n".join([entry['text'] for entry in transcript])
                        st.session_state.transcript = transcript_text
                        st.success("Transcript downloaded successfully!")
                    else:
                        st.error("No transcript found for this video.")
            except Exception as e:
                st.error(f"Error downloading transcript: {str(e)}")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Raw Transcript")
        if st.session_state.transcript:
            st.text_area(
                label="Raw text",
                value=st.session_state.transcript,
                height=400,
                disabled=True
            )
        else:
            st.info("No transcript loaded yet")
            
    with col2:
        st.subheader("Transcript Stats")
        if st.session_state.transcript:
            st.metric("Characters", len(st.session_state.transcript))
            st.metric("Lines", len(st.session_state.transcript.split('\n')))
            np_chars, total_chars = count_characters(st.session_state.transcript)
            total_lines = len(st.session_state.transcript.split('\n'))
            
            st.metric("Total Characters", total_chars)
            st.metric("Nepalese Characters", np_chars)
            st.metric("Total Lines", total_lines)
        else:
            st.info("Load a transcript to see statistics")

def render_structured_stage():
    st.header("Structured Data Processing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Dialogue Extraction")
        st.info("Dialogue extraction will be implemented here")
        
    with col2:
        st.subheader("Data Structure")
        st.info("Structured data view will be implemented here")

def render_rag_stage():
    st.header("RAG System")
    
    if 'rag_chat' not in st.session_state:
        st.session_state.rag_chat = HeritageRAGChat(collection_name=COLLECTION_NAME, model_id=DEFAULT_MODEL)
    
    if 'bedrock_chat' not in st.session_state:
        st.session_state.bedrock_chat = LiteLLMChat(model_id=DEFAULT_MODEL)
    
    if "rag_messages" not in st.session_state:
        st.session_state.rag_messages = []
    
    if "comparison_messages" not in st.session_state:
        st.session_state.comparison_messages = []
    
    if "rag_typing" not in st.session_state:
        st.session_state.rag_typing = False
    if "standard_typing" not in st.session_state:
        st.session_state.standard_typing = False
    
    st.markdown("""
    Compare responses between a RAG-enhanced system and standard LLM. Ask questions about Nepali heritage sites to see the difference.
    """)
    
    query = st.chat_input("Ask about Nepali heritage sites...", 
                         disabled=st.session_state.rag_typing or st.session_state.standard_typing)
    
    if query:
        timestamp = get_nepal_time()
        
        st.session_state.rag_messages.append({
            "role": "user", 
            "content": query,
            "timestamp": timestamp
        })
        st.session_state.comparison_messages.append({
            "role": "user", 
            "content": query,
            "timestamp": timestamp
        })
        
        st.session_state.rag_typing = True
        st.session_state.standard_typing = True
        st.rerun()
    
    rag_tab, standard_tab = st.tabs(["RAG-Enhanced Response", "Standard LLM Response"])
    
    with rag_tab:
        for message in st.session_state.rag_messages:
            avatar = "👤" if message["role"] == "user" else "🔍"
            with st.chat_message(message["role"], avatar=avatar):
                content, timestamp = format_message(message)
                st.markdown(content)
                if timestamp:
                    st.caption(f"sent at {timestamp}")
        
        if st.session_state.rag_typing:
            with st.chat_message("assistant", avatar="🔍"):
                st.markdown("_Thinking with RAG enhancement..._")
        
    with standard_tab:
        for message in st.session_state.comparison_messages:
            avatar = "👤" if message["role"] == "user" else "🤖"
            with st.chat_message(message["role"], avatar=avatar):
                content, timestamp = format_message(message)
                st.markdown(content)
                if timestamp:
                    st.caption(f"sent at {timestamp}")
                
        if st.session_state.standard_typing:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown("_Thinking with standard LLM..._")
    
    with st.sidebar:
        st.markdown("### Try These Examples")
        example_questions = [
            "Tell me about Krishna Mandir in Patan Durbar Square",
            "What is the historical significance of Bouddhanath Stupa?",
            "When was Krishna Mandir built and by whom?",
            "What are the architectural features of Pashupatinath Temple?",
            "How did Nyatapola Temple survive the 2015 earthquake?",
            "What makes Bhaktapur Durbar Square unique?"
        ]
        
        for q in example_questions:
            if st.button(q, key=f"rag_{q}", use_container_width=True, type="secondary"):
                timestamp = get_nepal_time()
                
                st.session_state.rag_messages.append({
                    "role": "user", 
                    "content": q,
                    "timestamp": timestamp
                })
                st.session_state.comparison_messages.append({
                    "role": "user", 
                    "content": q,
                    "timestamp": timestamp
                })
                
                st.session_state.rag_typing = True
                st.session_state.standard_typing = True
                st.rerun()

    if st.session_state.rag_messages:
        if st.button("Clear Conversation", type="primary"):
            st.session_state.rag_messages = []
            st.session_state.comparison_messages = []
            st.rerun()

def render_interactive_stage():
    st.header("Interactive Learning")
    
    practice_type = st.selectbox(
        "Select Practice Type",
        ["Dialogue Practice", "Vocabulary Quiz", "Listening Exercise"]
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Practice Scenario")
        st.info("Practice scenario will appear here")
        
        options = ["Option 1", "Option 2", "Option 3", "Option 4"]
        selected = st.radio("Choose your answer:", options)
        
    with col2:
        st.subheader("Audio")
        st.info("Audio will appear here")
        
        st.subheader("Feedback")
        st.info("Feedback will appear here")

def main():
    render_header()
    selected_stage = render_sidebar()
    
    if selected_stage == "1. Chat with OpenAI":
        render_chat_stage()
        
        if st.session_state.is_typing:
            user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
            if user_messages:
                last_user_message = user_messages[-1]["content"]
                generate_response(last_user_message)
                st.rerun()
                
    elif selected_stage == "2. Raw Transcript":
        render_transcript_stage()
    elif selected_stage == "3. Structured Data":
        render_structured_stage()
    elif selected_stage == "4. RAG Implementation":
        render_rag_stage()
        
        if st.session_state.rag_typing or st.session_state.standard_typing:
            user_messages = [msg for msg in st.session_state.rag_messages if msg["role"] == "user"]
            if user_messages:
                last_user_message = user_messages[-1]["content"]
                
                if st.session_state.rag_typing:
                    timestamp = get_nepal_time()
                    rag_response = st.session_state.rag_chat.generate_rag_response(last_user_message)
                    if rag_response:
                        st.session_state.rag_messages.append({
                            "role": "assistant", 
                            "content": rag_response,
                            "timestamp": timestamp
                        })
                    else:
                        st.session_state.rag_messages.append({
                            "role": "assistant", 
                            "content": "Sorry, I couldn't generate a RAG-enhanced response.",
                            "timestamp": timestamp
                        })
                    st.session_state.rag_typing = False
                
                if st.session_state.standard_typing:
                    timestamp = get_nepal_time()
                    standard_response = st.session_state.bedrock_chat.generate_response(last_user_message)
                    if standard_response:
                        st.session_state.comparison_messages.append({
                            "role": "assistant", 
                            "content": standard_response,
                            "timestamp": timestamp
                        })
                    else:
                        st.session_state.comparison_messages.append({
                            "role": "assistant", 
                            "content": "Sorry, I couldn't generate a response.",
                            "timestamp": timestamp
                        })
                    st.session_state.standard_typing = False
                
                st.rerun()
                
    elif selected_stage == "5. Interactive Learning":
        render_interactive_stage()
    
    with st.expander("Debug Information"):
        st.json({
            "selected_stage": selected_stage,
            "transcript_loaded": st.session_state.transcript is not None,
            "chat_messages": len(st.session_state.messages),
            "rag_messages": len(st.session_state.rag_messages) if "rag_messages" in st.session_state else 0,
            "comparison_messages": len(st.session_state.comparison_messages) if "comparison_messages" in st.session_state else 0,
            "typing_status": {
                "main_chat": st.session_state.is_typing,
                "rag": st.session_state.rag_typing if "rag_typing" in st.session_state else False,
                "standard": st.session_state.standard_typing if "standard_typing" in st.session_state else False
            }
        })

if __name__ == "__main__":
    main()