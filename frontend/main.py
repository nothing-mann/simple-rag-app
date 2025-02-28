import streamlit as st
from typing import Dict
import json
from collections import Counter
import re
import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.get_transcript import YouTubeTranscriptDownloader
from backend.chat import LiteLLMChat


# Page config
st.set_page_config(
    page_title="Cultural Heritage Information",
    page_icon="🇳🇵",
    layout="wide"
)

# Initialize session state
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

def render_header():
    """Render the header section"""
    st.title("🇳🇵 Enlighten Nepal Heritage Information")
    st.markdown("""
    Transform YouTube transcripts into interactive culture learning experiences.
    
    This tool demonstrates:
    - Base LLM Capabilities
    - RAG (Retrieval Augmented Generation)
    - Amazon Bedrock Integration
    - Agent-based Learning Systems
    """)

def render_sidebar():
    """Render the sidebar with component selection"""
    with st.sidebar:
        st.header("Development Stages")
        
        # Main component selection
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
        
        # Stage descriptions
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
            - Bedrock embeddings
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

def render_chat_stage():
    """Render an improved chat interface"""
    st.header("Chat with OpenAI")
    
    # Initialize the bedrock instance
    if 'bedrock_chat' not in st.session_state:
        st.session_state.bedrock_chat = LiteLLMChat()
    
    # Introduction text
    st.markdown("""
    Start by exploring OpenAI's base Nepali Cultural heritage information capabilities. Try asking questions about cultural heritages in Nepal.
    """)

    # Initialize chat history if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages in a cleaner format
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

    # Chat input area
    if prompt := st.chat_input("Ask about Nepali heritage sites..."):
        # # Add user message to state and display
        # st.session_state.messages.append({"role": "user", "content": prompt})
        # with st.chat_message("user", avatar="🧑‍💻"):
        #     st.markdown(prompt)

        # # Add OpenAI's response to state and display
        # response = "This is where OpenAI's response will go. We'll integrate the actual Bedrock call here."
        # st.session_state.messages.append({"role": "assistant", "content": response})
        # with st.chat_message("assistant", avatar="🤖"):
        #     st.markdown(response)
        
        # Process the user input
        process_message(prompt)

    # Example questions in a clean sidebar card
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
                # # When example is clicked, add it to chat input
                # st.session_state.messages.append({"role": "user", "content": q})
                # # This will trigger a rerun with the new message

                # Process the example question
                process_message(q)
                st.rerun()

    # Add a clear chat button
    if st.session_state.messages:  # Only show if there are messages
        if st.button("Clear Chat", type="primary"):
            st.session_state.messages = []
            st.rerun()

def process_message(message: str):
    """Process a message and generate a response"""
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": message})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(message)

    # Generate and display assistant's response
    with st.chat_message("assistant", avatar="🤖"):
        response = st.session_state.bedrock_chat.generate_response(message)
        if response:
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

def count_characters(text):
    """Count Nepali and total characters in text"""
    if not text:
        return 0, 0
        
    def is_nepali(char):
        return any([
            '\u0900' <= char <= '\u097F',  # Devnagari Characters
        ])
    
    np_chars = sum(1 for char in text if is_nepali(char))
    return np_chars, len(text)



def render_transcript_stage():
    """Render the raw transcript stage"""
    st.header("Raw Transcript Processing")
    
    # URL input
    url = st.text_input(
        "YouTube URL",
        placeholder="Enter a Heritage site educational video YouTube URL"
    )
    
     # Download button and processing
    if url:
        if st.button("Download Transcript"):
            try:
                with st.spinner("Downloading transcript..."):
                    downloader = YouTubeTranscriptDownloader()
                    transcript = downloader.get_transcript(url)
                    video_id = downloader.extract_video_id(url)
                    
                    # Create a directory for storing transcripts if it doesn't exist
                    transcript_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "data", "transcripts")
                    os.makedirs(transcript_dir, exist_ok=True)
                    
                    # Save the transcript with a proper name and extension
                    file_path = os.path.join(transcript_dir, f"{video_id}")
                    downloader.save_transcript(transcript, file_path)
                    if transcript:
                        # Store the raw transcript text in session state
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
            # Calculate stats
            np_chars, total_chars = count_characters(st.session_state.transcript)
            total_lines = len(st.session_state.transcript.split('\n'))
            
            # Display stats
            st.metric("Total Characters", total_chars)
            st.metric("Nepalese Characters", np_chars)
            st.metric("Total Lines", total_lines)
        else:
            st.info("Load a transcript to see statistics")

def render_structured_stage():
    """Render the structured data stage"""
    st.header("Structured Data Processing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Dialogue Extraction")
        # Placeholder for dialogue processing
        st.info("Dialogue extraction will be implemented here")
        
    with col2:
        st.subheader("Data Structure")
        # Placeholder for structured data view
        st.info("Structured data view will be implemented here")

def render_rag_stage():
    """Render the RAG implementation stage"""
    st.header("RAG System")
    
    # Query input
    query = st.text_input(
        "Test Query",
        placeholder="Enter a question about a Nepali heritage site..."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Retrieved Context")
        # Placeholder for retrieved contexts
        st.info("Retrieved contexts will appear here")
        
    with col2:
        st.subheader("Generated Response")
        # Placeholder for LLM response
        st.info("Generated response will appear here")

def render_interactive_stage():
    """Render the interactive learning stage"""
    st.header("Interactive Learning")
    
    # Practice type selection
    practice_type = st.selectbox(
        "Select Practice Type",
        ["Dialogue Practice", "Vocabulary Quiz", "Listening Exercise"]
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Practice Scenario")
        # Placeholder for scenario
        st.info("Practice scenario will appear here")
        
        # Placeholder for multiple choice
        options = ["Option 1", "Option 2", "Option 3", "Option 4"]
        selected = st.radio("Choose your answer:", options)
        
    with col2:
        st.subheader("Audio")
        # Placeholder for audio player
        st.info("Audio will appear here")
        
        st.subheader("Feedback")
        # Placeholder for feedback
        st.info("Feedback will appear here")

def main():
    render_header()
    selected_stage = render_sidebar()
    
    # Render appropriate stage
    if selected_stage == "1. Chat with OpenAI":
        render_chat_stage()
    elif selected_stage == "2. Raw Transcript":
        render_transcript_stage()
    elif selected_stage == "3. Structured Data":
        render_structured_stage()
    elif selected_stage == "4. RAG Implementation":
        render_rag_stage()
    elif selected_stage == "5. Interactive Learning":
        render_interactive_stage()
    
    # Debug section at the bottom
    with st.expander("Debug Information"):
        st.json({
            "selected_stage": selected_stage,
            "transcript_loaded": st.session_state.transcript is not None,
            "chat_messages": len(st.session_state.messages)
        })

if __name__ == "__main__":
    main()