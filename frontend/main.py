import streamlit as st
from typing import Dict, List
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

from backend.config import COLLECTION_NAME, DEFAULT_MODEL, HERITAGE_SITES_DIR
from backend.get_transcript import YouTubeTranscriptDownloader
from backend.get_pdf_content import PDFContentExtractor
from backend.get_web_content import WebScraper
from backend.chat import LiteLLMChat
from backend.rag_chat import HeritageRAGChat
from backend.interactive import AudioGenerator

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
    - LiteLLM MistralLarge Integration
    - Agent-based Learning Systems
    """)

def render_sidebar():
    with st.sidebar:
        st.header("Development Stages")
        
        selected_stage = st.radio(
            "Select Stage:",
            [
                "1. Chat with MistralLarge",
                "2. Raw Transcript",
                "3. Structured Data",
                "4. RAG Implementation",
                "5. Interactive Learning",
                "6. Monument Database"
            ]
        )
        
        stage_info = {
            "1. Chat with MistralLarge": """
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
            - MistralLarge Embedding (text-embedding-ada-002)
            - Vector storage
            - Context retrieval
            """,
            
            "5. Interactive Learning": """
            **Current Focus:**
            - Scenario generation
            - Audio synthesis
            - Interactive practice
            """,
            
            "6. Monument Database": """
            **Current Focus:**
            - Complete monument inventory
            - Filtering and search
            - Overview of heritage database
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
    st.header("Chat with MistralLarge")
    
    if 'bedrock_chat' not in st.session_state:
        st.session_state.bedrock_chat = LiteLLMChat()
    
    st.markdown("""
    Start by exploring MistralLarge's base Nepali Cultural heritage information capabilities. Try asking questions about cultural heritages in Nepal.
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
    
    # Create tabs for different input sources
    youtube_tab, pdf_tab, web_tab = st.tabs(["YouTube Transcript", "PDF Document", "Web Content"])
    
    # YouTube transcript download tab
    with youtube_tab:
        url = st.text_input(
            "YouTube URL",
            placeholder="Enter a Heritage site educational video YouTube URL",
            key="youtube_url"
        )
        
        if url:
            if st.button("Download Transcript", key="youtube_download"):
                try:
                    with st.spinner("Downloading transcript..."):
                        downloader = YouTubeTranscriptDownloader()
                        transcript = downloader.get_transcript(url)
                        video_id = downloader.extract_video_id(url)
                        
                        transcript_dir = os.path.join(project_root, "data", "transcripts")
                        os.makedirs(transcript_dir, exist_ok=True)
                        
                        file_path = os.path.join(transcript_dir, f"{video_id}.txt")
                        downloader.save_transcript(transcript, file_path)
                        if transcript:
                            transcript_text = "\n".join([entry['text'] for entry in transcript])
                            st.session_state.transcript = transcript_text
                            st.success(f"Transcript downloaded successfully and saved to {file_path}!")
                        else:
                            st.error("No transcript found for this video.")
                except Exception as e:
                    st.error(f"Error downloading transcript: {str(e)}")
    
    # PDF upload tab
    with pdf_tab:
        st.markdown("Upload a PDF document containing heritage site information")
        
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        custom_filename = st.text_input("Custom filename (optional)", placeholder="heritage_site_name", key="pdf_filename")
        
        if uploaded_file is not None:
            if st.button("Process PDF", key="pdf_process"):
                try:
                    with st.spinner("Processing PDF..."):
                        # Save uploaded PDF temporarily
                        temp_pdf_path = os.path.join(project_root, "temp_upload.pdf")
                        with open(temp_pdf_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Process the PDF
                        extractor = PDFContentExtractor()
                        output_filename = f"{custom_filename}.txt" if custom_filename else None
                        text_file_path = extractor.process_pdf(temp_pdf_path, output_filename)
                        
                        # Remove the temporary file
                        os.remove(temp_pdf_path)
                        
                        if text_file_path:
                            # Read the extracted text to display
                            with open(text_file_path, 'r', encoding='utf-8') as f:
                                extracted_text = f.read()
                            
                            st.session_state.transcript = extracted_text
                            st.success(f"PDF processed successfully and saved to {text_file_path}!")
                        else:
                            st.error("Failed to process PDF. Check if it contains extractable text.")
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")
    
    # Web Content tab
    with web_tab:
        st.markdown("Extract content from a webpage about heritage sites")
        
        web_url = st.text_input(
            "Website URL",
            placeholder="Enter a URL with heritage site information (e.g., https://example.com/heritage-site)",
            key="web_url"
        )
        
        custom_web_filename = st.text_input(
            "Custom filename (optional)", 
            placeholder="heritage_site_name", 
            key="web_filename"
        )
        
        if web_url:
            if st.button("Download Web Content", key="web_download"):
                try:
                    with st.spinner("Downloading web content..."):
                        # Initialize the web scraper
                        transcript_dir = os.path.join(project_root, "data", "transcripts")
                        web_scraper = WebScraper(output_dir=transcript_dir)
                        
                        # If custom filename provided, temporarily store it
                        original_generate_filename = None
                        if custom_web_filename:
                            # Save the original method
                            original_generate_filename = web_scraper._generate_filename
                            
                            # Override the filename generation method
                            def custom_filename_generator(url, title=None):
                                return f"{custom_web_filename}.txt"
                            
                            web_scraper._generate_filename = custom_filename_generator
                        
                        # Scrape the URL
                        file_path = web_scraper.scrape_url(web_url)
                        
                        # Restore the original method if needed
                        if original_generate_filename:
                            web_scraper._generate_filename = original_generate_filename
                        
                        if file_path and os.path.exists(file_path):
                            # Read the extracted text to display
                            with open(file_path, 'r', encoding='utf-8') as f:
                                extracted_text = f.read()
                            
                            st.session_state.transcript = extracted_text
                            st.success(f"Web content downloaded successfully and saved to {file_path}!")
                        else:
                            st.error("Failed to download content from the website.")
                except Exception as e:
                    st.error(f"Error downloading web content: {str(e)}")

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
            
            # Add a "Process with Structured Data" button
            if st.button("Process with Structured Data", type="primary"):
                if 'transcript' in st.session_state and st.session_state.transcript:
                    st.session_state.selected_stage = "3. Structured Data"
                    st.rerun()
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
    
    # Initialize session state variables for interactive learning
    if "practice_type" not in st.session_state:
        st.session_state.practice_type = "Dialogue Practice"
    
    if "current_scenario" not in st.session_state:
        st.session_state.current_scenario = None
    
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = []
    
    if "feedback" not in st.session_state:
        st.session_state.feedback = None
    
    if "score" not in st.session_state:
        st.session_state.score = 0
    
    if "total_questions" not in st.session_state:
        st.session_state.total_questions = 0
    
    if "current_monument" not in st.session_state:
        st.session_state.current_monument = None
    
    # Practice type selector
    practice_type = st.selectbox(
        "Select Practice Type",
        ["Dialogue Practice", "Vocabulary Quiz", "Listening Exercise", "Cultural Context"],
        index=["Dialogue Practice", "Vocabulary Quiz", "Listening Exercise", "Cultural Context"].index(st.session_state.practice_type),
        key="practice_selector"
    )
    
    # Update session state if practice type changes
    if practice_type != st.session_state.practice_type:
        st.session_state.practice_type = practice_type
        st.session_state.current_scenario = None
        st.session_state.user_answers = []
        st.session_state.feedback = None
        st.rerun()
    
    # Monument selector for practice context
    if "monuments_list" not in st.session_state:
        with st.spinner("Loading monuments data..."):
            st.session_state.monuments_list = load_monuments()
    
    monuments = st.session_state.monuments_list
    monument_names = ["Random"] + [m["name"] for m in monuments]
    
    selected_monument = st.selectbox(
        "Select Heritage Site Context",
        monument_names,
        index=0 if st.session_state.current_monument is None else monument_names.index(st.session_state.current_monument),
        key="monument_selector"
    )
    
    if selected_monument != "Random" and selected_monument != st.session_state.current_monument:
        st.session_state.current_monument = selected_monument
        st.session_state.current_scenario = None
        st.rerun()
    
    # Generate new scenario button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Generate New Scenario", type="primary", use_container_width=True):
            with st.spinner("Generating practice scenario..."):
                generate_practice_scenario()
                st.rerun()
    
    # Display practice area
    st.markdown("---")
    
    # If no scenario exists, show instructions
    if st.session_state.current_scenario is None:
        st.info("Click 'Generate New Scenario' to start practicing!")
        
        st.markdown("""
        ### How Interactive Learning Works
        
        1. Select a practice type above
        2. Choose a specific heritage site for context (or leave as 'Random')
        3. Generate a new scenario to begin practicing
        4. Complete the exercises to test your knowledge
        5. Get instant feedback and track your progress
        
        This feature uses our RAG system with LLM capabilities to create realistic learning scenarios
        about Nepali cultural heritage.
        """)
    else:
        # Display the current scenario based on practice type
        display_practice_scenario()
    
    # Display the scoring information
    if st.session_state.total_questions > 0:
        st.markdown("---")
        st.subheader("Learning Progress")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Score", f"{st.session_state.score}/{st.session_state.total_questions}")
        with col2:
            percentage = (st.session_state.score / st.session_state.total_questions) * 100
            st.metric("Accuracy", f"{percentage:.1f}%")

def generate_practice_scenario():
    """Generate a new practice scenario based on selected type and monument."""
    practice_type = st.session_state.practice_type
    monument = st.session_state.current_monument
    
    # Initialize LLM if not already done
    if 'bedrock_chat' not in st.session_state:
        st.session_state.bedrock_chat = LiteLLMChat()
    
    # Prepare the appropriate prompt based on practice type
    prompt = create_scenario_prompt(practice_type, monument)
    
    # Generate scenario content using LLM
    try:
        response = st.session_state.bedrock_chat.generate_response(prompt)
        
        # Parse the response into a structured format
        scenario = parse_scenario_response(response, practice_type)
        
        # Store the scenario in session state
        st.session_state.current_scenario = scenario
        st.session_state.feedback = None
        st.session_state.user_answers = []
        
    except Exception as e:
        st.error(f"Error generating scenario: {str(e)}")
        st.session_state.current_scenario = None

def create_scenario_prompt(practice_type, monument=None):
    """Create a prompt for the LLM to generate a practice scenario."""
    base_prompt = "Create an interactive learning exercise about Nepali heritage sites. "
    
    if monument and monument != "Random":
        base_prompt += f"Focus specifically on {monument}. "
    
    if practice_type == "Dialogue Practice":
        prompt = base_prompt + """
        Create a dialogue practice scenario with the following JSON structure:
        {
            "title": "Conversation title",
            "context": "Brief context about where this conversation is taking place",
            "dialogue": [
                {"speaker": "Person 1", "text": "Line 1"},
                {"speaker": "Person 2", "text": "Line 2"},
                {"speaker": "Person 1", "text": "Line 3 with a [BLANK] to fill in"}
            ],
            "options": ["option 1", "option 2", "option 3", "option 4"],
            "correct_answer": "The correct option (full text)",
            "explanation": "Why this is the correct answer"
        }
        
        Include 2-3 blanks in the dialogue where important cultural or historical information should be filled in.
        Make the options challenging but related to Nepali heritage.
        """
        
    elif practice_type == "Vocabulary Quiz":
        prompt = base_prompt + """
        Create a vocabulary quiz about Nepali heritage terms with the following JSON structure:
        {
            "title": "Quiz title",
            "questions": [
                {
                    "term": "Nepali heritage term",
                    "question": "Question about what this term means",
                    "options": ["option 1", "option 2", "option 3", "option 4"],
                    "correct_answer": "The correct option (exactly matching one of the options)",
                    "explanation": "Explanation of the term and its cultural significance"
                },
                {... more questions in the same structure...}
            ]
        }
        
        Include 5 questions about important architectural features, religious terminology, or cultural practices.
        """
        
    elif practice_type == "Listening Exercise":
        prompt = base_prompt + """
        Create a listening comprehension exercise about Nepali heritage with the following JSON structure:
        {
            "title": "Exercise title",
            "audio_script": "A 2-3 paragraph narration describing aspects of a Nepali heritage site, as if it was being explained by a tour guide",
            "questions": [
                {
                    "question": "A question about information contained in the audio",
                    "options": ["option 1", "option 2", "option 3", "option 4"],
                    "correct_answer": "The correct option (exactly matching one of the options)",
                    "explanation": "Why this answer is correct based on the audio"
                },
                {... 2 more questions in the same structure...}
            ]
        }
        """
        
    else:  # Cultural Context
        prompt = base_prompt + """
        Create a cultural context exercise about appropriate behavior at Nepali heritage sites with the following JSON structure:
        {
            "title": "Cultural context scenario",
            "scenario": "A detailed description of a situation a visitor might encounter at a heritage site that involves cultural considerations",
            "question": "What would be the most culturally appropriate action in this situation?",
            "options": ["option 1", "option 2", "option 3", "option 4"],
            "correct_answer": "The correct option (exactly matching one of the options)",
            "explanation": "Explanation of why this is appropriate and the cultural context behind it"
        }
        """
    
    # Add instruction to format properly as JSON
    prompt += "\nReturn ONLY the JSON structure, properly formatted for parsing."
    
    return prompt

def parse_scenario_response(response, practice_type):
    """Parse the LLM response into a structured scenario format."""
    try:
        # Extract JSON from response (some LLMs might wrap it)
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start >= 0 and json_end > 0:
            json_str = response[json_start:json_end]
            scenario = json.loads(json_str)
            return scenario
        else:
            # Fallback simple parsing based on practice type
            lines = response.split('\n')
            scenario = {"title": "Practice Exercise", "error": "Could not parse proper JSON"}
            
            # Add some basic structure based on practice type
            if practice_type == "Dialogue Practice":
                scenario["dialogue"] = []
                scenario["options"] = ["Option A", "Option B", "Option C", "Option D"]
                scenario["correct_answer"] = "Option A"
            elif practice_type == "Vocabulary Quiz":
                scenario["questions"] = [{"term": "Term", "question": "Question", 
                                         "options": ["A", "B", "C", "D"], 
                                         "correct_answer": "A"}]
            
            return scenario
    
    except json.JSONDecodeError:
        # Return a simple error scenario
        return {
            "title": "Error in Scenario Generation",
            "error": "Could not create a proper scenario. Please try again."
        }

def display_practice_scenario():
    """Display the current practice scenario based on type."""
    scenario = st.session_state.current_scenario
    practice_type = st.session_state.practice_type
    
    # Check for error in scenario
    if "error" in scenario:
        st.error(scenario["error"])
        return
    
    # Display based on practice type
    if practice_type == "Dialogue Practice":
        display_dialogue_practice(scenario)
    elif practice_type == "Vocabulary Quiz":
        display_vocabulary_quiz(scenario)
    elif practice_type == "Listening Exercise":
        display_listening_exercise(scenario)
    else:  # Cultural Context
        display_cultural_context(scenario)

def display_dialogue_practice(scenario):
    """Display a dialogue practice scenario."""
    st.subheader(scenario["title"])
    st.markdown(f"**Context:** {scenario['context']}")
    
    # Display dialogue with blanks
    st.markdown("### Dialogue")
    for i, line in enumerate(scenario["dialogue"]):
        speaker = line["speaker"]
        text = line["text"]
        
        # Check if line contains blanks
        if "[BLANK]" in text:
            parts = text.split("[BLANK]")
            st.markdown(f"**{speaker}:** {parts[0]} _____ {parts[1] if len(parts) > 1 else ''}")
            
            # Only show options if no feedback yet
            if st.session_state.feedback is None:
                st.session_state.current_question_idx = i
                options = scenario["options"]
                selected = st.radio(f"Complete the dialogue:", options, key=f"dialogue_option_{i}")
                
                if st.button("Submit Answer", key=f"submit_{i}"):
                    check_answer(selected, scenario["correct_answer"])
        else:
            st.markdown(f"**{speaker}:** {text}")
    
    # Display feedback if available
    if st.session_state.feedback:
        display_feedback(scenario["explanation"])

def display_vocabulary_quiz(scenario):
    """Display a vocabulary quiz scenario."""
    st.subheader(scenario["title"])
    
    # For vocabulary quiz, we display one question at a time
    if "current_question_idx" not in st.session_state or st.session_state.feedback is not None:
        if len(st.session_state.user_answers) < len(scenario["questions"]):
            st.session_state.current_question_idx = len(st.session_state.user_answers)
        else:
            # Quiz completed
            st.success("Quiz completed!")
            
            # Show summary of results
            correct = sum(1 for ans in st.session_state.user_answers if ans["correct"])
            st.markdown(f"### Results: {correct}/{len(scenario['questions'])} correct")
            
            for i, (ans, q) in enumerate(zip(st.session_state.user_answers, scenario["questions"])):
                status = "✓" if ans["correct"] else "✗"
                st.markdown(f"**Question {i+1}**: {status} {q['term']}")
                st.markdown(f"*{q['explanation']}*")
                
            if st.button("Start New Quiz"):
                st.session_state.current_scenario = None
                st.rerun()
                
            return
    
    # Get current question
    idx = st.session_state.current_question_idx
    question = scenario["questions"][idx]
    
    # Display question
    st.markdown(f"### Question {idx+1} of {len(scenario['questions'])}")
    st.markdown(f"**Term:** {question['term']}")
    st.markdown(question["question"])
    
    # Display options
    selected = st.radio("Choose the correct answer:", question["options"], key=f"vocab_option_{idx}")
    
    # Submit button
    if st.button("Submit Answer", key=f"submit_vocab_{idx}"):
        correct = selected == question["correct_answer"]
        
        st.session_state.user_answers.append({
            "question_idx": idx,
            "selected": selected,
            "correct": correct
        })
        
        if correct:
            st.session_state.score += 1
        
        st.session_state.total_questions += 1
        
        # Display feedback
        if correct:
            st.success("Correct! " + question["explanation"])
        else:
            st.error(f"Incorrect. The correct answer is: {question['correct_answer']}")
            st.markdown(question["explanation"])
            
        # Move to next question button
        st.session_state.feedback = {
            "correct": correct,
            "explanation": question["explanation"]
        }
        
        if idx < len(scenario["questions"]) - 1:
            if st.button("Next Question"):
                st.session_state.feedback = None
                st.rerun()
        else:
            if st.button("See Results"):
                st.rerun()

def display_listening_exercise(scenario):
    """Display a listening exercise scenario with audio playback."""
    st.subheader(scenario["title"])
    
    # Initialize audio generator if not already in session state
    if "audio_generator" not in st.session_state:
        st.session_state.audio_generator = AudioGenerator(language="en")
    
    # Generate audio for this scenario if not already generated
    if "current_audio" not in st.session_state or st.session_state.current_scenario != st.session_state.last_audio_scenario:
        try:
            with st.spinner("Generating audio..."):
                audio_base64 = st.session_state.audio_generator.generate_audio_base64(scenario["audio_script"])
                st.session_state.current_audio = audio_base64
                st.session_state.last_audio_scenario = st.session_state.current_scenario
        except Exception as e:
            st.error(f"Error generating audio: {str(e)}")
            st.session_state.current_audio = None
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Audio Player")
        
        # Display audio player if audio is available
        if st.session_state.current_audio:
            st.audio(st.session_state.current_audio, format="audio/mp3")
            st.info("👆 Listen to the audio above to answer the questions on the right.")
            
            # Show/hide transcript button
            if "show_transcript" not in st.session_state:
                st.session_state.show_transcript = False
                
            if st.button("Show/Hide Transcript"):
                st.session_state.show_transcript = not st.session_state.show_transcript
                st.rerun()
                
            if st.session_state.show_transcript:
                st.markdown("### Audio Transcript")
                st.markdown(f"*{scenario['audio_script']}*")
        else:
            st.error("Unable to generate audio. Please try refreshing the page.")
            st.markdown("### Audio Transcript (Fallback)")
            st.markdown(f"*{scenario['audio_script']}*")
        
    with col2:
        st.markdown("### Comprehension Check")
        
        # For listening exercise, we allow answering questions one by one
        if "current_listening_q" not in st.session_state:
            st.session_state.current_listening_q = 0
            
        if st.session_state.current_listening_q < len(scenario["questions"]):
            q = scenario["questions"][st.session_state.current_listening_q]
            
            st.markdown(f"**Question {st.session_state.current_listening_q+1} of {len(scenario['questions'])}:**")
            st.markdown(q["question"])
            
            selected = st.radio("Your answer:", q["options"], key=f"listening_{st.session_state.current_listening_q}")
            
            if st.button("Check Answer", key=f"check_listening_{st.session_state.current_listening_q}"):
                correct = selected == q["correct_answer"]
                
                if correct:
                    st.success("Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"Incorrect. The correct answer was: {q['correct_answer']}")
                
                st.markdown(f"*{q['explanation']}*")
                st.session_state.total_questions += 1
                
                if st.session_state.current_listening_q < len(scenario["questions"]) - 1:
                    if st.button("Next Question", key=f"next_listening_{st.session_state.current_listening_q}"):
                        st.session_state.current_listening_q += 1
                        st.rerun()
                else:
                    if st.button("See Results"):
                        st.session_state.current_listening_q = len(scenario["questions"])
                        st.rerun()
        else:
            # All questions answered
            st.success("Exercise completed!")
            correct = st.session_state.score - (st.session_state.total_questions - len(scenario["questions"]))
            st.markdown(f"### Results: {correct}/{len(scenario['questions'])} correct")
            
            if st.button("Try Another Exercise"):
                st.session_state.current_scenario = None
                st.session_state.current_audio = None
                st.session_state.current_listening_q = 0
                st.rerun()

def display_cultural_context(scenario):
    """Display a cultural context scenario."""
    st.subheader(scenario["title"])
    
    # Display scenario
    st.markdown("### Scenario")
    st.markdown(f"{scenario['scenario']}")
    
    # Display question
    st.markdown(f"**{scenario['question']}**")
    
    # Display options if no feedback yet
    if st.session_state.feedback is None:
        selected = st.radio("Choose the most appropriate response:", scenario["options"], key="cultural_option")
        
        if st.button("Submit Answer", key="submit_cultural"):
            check_answer(selected, scenario["correct_answer"])
    
    # Display feedback if available
    if st.session_state.feedback:
        display_feedback(scenario["explanation"])
        
        # Allow for next scenario
        if st.button("Try Another Scenario"):
            st.session_state.current_scenario = None
            st.rerun()

def check_answer(selected, correct_answer):
    """Check if the selected answer is correct and update session state."""
    correct = selected == correct_answer
    
    st.session_state.feedback = {
        "correct": correct,
        "selected": selected,
        "correct_answer": correct_answer
    }
    
    # Update score
    if correct:
        st.session_state.score += 1
    st.session_state.total_questions += 1
    
    st.rerun()

def display_feedback(explanation):
    """Display feedback for the current answer."""
    feedback = st.session_state.feedback
    
    if feedback["correct"]:
        st.success("✓ Correct!")
    else:
        st.error(f"✗ Incorrect. The correct answer was: {feedback['correct_answer']}")
    
    st.markdown("### Explanation")
    st.markdown(explanation)

def render_monuments_list():
    """Render a list of all available monuments in the database"""
    st.header("📜 Monument Database")
    
    # Load all monuments
    with st.spinner("Loading monument data..."):
        monuments = load_monuments()
    
    st.write(f"Found {len(monuments)} unique monuments in the database.")
    
    # Create filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get unique religions
        religions = sorted(set(m["religion"] for m in monuments if m["religion"]))
        religions = ["All"] + list(religions)
        religion_filter = st.selectbox("Filter by Religion", religions)
    
    with col2:
        # Get unique types
        types = sorted(set(m["type"] for m in monuments if m["type"]))
        types = ["All"] + list(types)
        type_filter = st.selectbox("Filter by Monument Type", types)
    
    with col3:
        # Search by name
        search_query = st.text_input("Search by Name", "")
    
    # Apply filters
    filtered_monuments = monuments
    
    if religion_filter != "All":
        filtered_monuments = [m for m in filtered_monuments if m.get("religion") == religion_filter]
    
    if type_filter != "All":
        filtered_monuments = [m for m in filtered_monuments if m.get("type") == type_filter]
    
    if search_query:
        search_query = search_query.lower()
        filtered_monuments = [m for m in filtered_monuments if search_query in m["name"].lower()]
    
    # Display monuments in a table
    if filtered_monuments:
        # Convert to format suitable for dataframe
        table_data = []
        for m in filtered_monuments:
            table_data.append({
                "Name": m["name"],
                "Location": m["location"] or "Unknown",
                "Religion": m["religion"] or "Unknown",
                "Type": m["type"] or "Unknown"
            })
            
        # Display in a dataframe
        st.dataframe(
            table_data, 
            column_config={
                "Name": st.column_config.TextColumn("Monument Name"),
                "Location": st.column_config.TextColumn("Location"),
                "Religion": st.column_config.TextColumn("Religion"),
                "Type": st.column_config.TextColumn("Type"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No monuments found matching your filters.")

def load_monuments() -> List[Dict]:
    """
    Load all monument data from JSON files in the heritage sites directory,
    deduplicate by monument name, and return sorted by name.
    
    Returns:
        List of dictionaries with monument information
    """
    monuments = []
    seen_names = set()
    
    # Create a map to detect similar names
    normalized_name_map = {}
    
    # Check if heritage sites directory exists
    if not os.path.exists(HERITAGE_SITES_DIR):
        print(f"Error: Heritage sites directory not found at {HERITAGE_SITES_DIR}")
        return []
    
    # Get all JSON files
    json_files = [f for f in os.listdir(HERITAGE_SITES_DIR) if f.endswith('.json')]
    
    # Process all files to extract monument information
    for filename in json_files:
        filepath = os.path.join(HERITAGE_SITES_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle both single monument and arrays of monuments
                items_to_process = []
                if isinstance(data, list):
                    items_to_process = data
                elif isinstance(data, dict):
                    items_to_process = [data]
                    
                for item in items_to_process:
                    # Skip if not a dictionary
                    if not isinstance(item, dict):
                        continue
                        
                    # Get monument name - try different possible field names
                    name = None
                    for field in ["monument_name", "name", "title"]:
                        if field in item and item[field]:
                            name = item[field].strip()
                            break
                            
                    if not name:
                        continue
                    
                    # Normalize name for deduplication
                    name_lower = name.lower()
                    
                    # Extract location details
                    location = item.get("location", {})
                    area = None
                    
                    # Try to get most specific location information available
                    if location and isinstance(location, dict):
                        if location.get("tola"):
                            area = location.get("tola")
                        elif location.get("heritage_area"):
                            area = location.get("heritage_area")
                        elif location.get("municipality"):
                            area = location.get("municipality")
                        elif location.get("district"):
                            area = location.get("district")
                        elif location.get("province"):
                            area = location.get("province")
                    
                    # Get religion and monument type if available
                    typology = item.get("typology", {})
                    religion = None
                    monument_type = None
                    
                    if typology and isinstance(typology, dict):
                        religion = typology.get("religion")
                        monument_type = typology.get("monument_type")
                    
                    # Create a new monument entry
                    monument = {
                        "name": name,
                        "filename": filename,
                        "location": area,
                        "religion": religion,
                        "type": monument_type
                    }
                    
                    # Check for similar names before adding
                    is_duplicate = False
                    normalized_key = normalize_for_comparison(name_lower)
                    
                    if normalized_key in normalized_name_map:
                        is_duplicate = True
                        
                        # If we find a more complete entry, update our stored version
                        existing_idx = normalized_name_map[normalized_key]
                        existing = monuments[existing_idx]
                        
                        # If the current entry has more information, replace the existing one
                        if (not existing["location"] and monument["location"]) or \
                           (not existing["religion"] and monument["religion"]) or \
                           (not existing["type"] and monument["type"]):
                            # Preserve the original name if it's more complete
                            if len(monument["name"]) > len(existing["name"]):
                                existing["name"] = monument["name"]
                            existing["location"] = monument["location"] or existing["location"]
                            existing["religion"] = monument["religion"] or existing["religion"]
                            existing["type"] = monument["type"] or existing["type"]
                    
                    # Add to monuments list if not a duplicate
                    if not is_duplicate:
                        monuments.append(monument)
                        normalized_name_map[normalized_key] = len(monuments) - 1
        
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading {filename}: {str(e)}")
    
    # Sort by name
    monuments.sort(key=lambda x: x["name"])
    return monuments

def normalize_for_comparison(name: str) -> str:
    """
    Normalize a monument name for better comparison and deduplication.
    - Removes common words like "temple", "stupa", etc.
    - Removes special characters
    - Converts to lowercase
    - Removes extra spaces
    
    Args:
        name: The monument name to normalize
        
    Returns:
        A normalized version of the name for comparison
    """
    # Convert to lowercase
    result = name.lower()
    
    # Remove common suffixes/variations
    common_words = [
        "temple", "stupa", "monastery", "mandir", "mandira", "square", 
        "chowk", "dhara", "pillar", "statue", "the", "of", "and"
    ]
    
    for word in common_words:
        result = result.replace(f" {word}", "").replace(f"{word} ", "")
    
    # Remove special characters and extra spaces
    result = re.sub(r'[^\w\s]', '', result)
    result = re.sub(r'\s+', '', result)
    
    return result

def main():
    render_header()
    selected_stage = render_sidebar()
    
    if selected_stage == "1. Chat with MistralLarge":
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
    elif selected_stage == "6. Monument Database":
        render_monuments_list()
    
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