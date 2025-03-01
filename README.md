# Nepalese Heritage Learning Assistant

An AI-powered tool for learning about Nepalese cultural heritage sites using modern NLP techniques and YouTube content.

## Project Overview

This project creates a language learning and cultural heritage assistant focused on Nepalese cultural sites and monuments. The system processes YouTube videos about Nepalese cultural heritage, extracts transcripts, translates them when needed, structures the information, and provides interactive access to this knowledge.

## Key Features

- **YouTube Transcript Processing**: Automatically extracts transcripts from YouTube videos about heritage sites
- **Smart Language Handling**: Prioritizes manually created transcripts and translates non-English content
- **AI-Powered Structuring**: Formats unstructured transcript data into consistent heritage site information
- **Interactive Chat Interface**: Ask questions about Nepalese heritage sites through a conversational interface

## Technical Components

### 1. Transcript Acquisition
- YouTube API integration for retrieving video transcripts
- Prioritization of manually created transcripts over automated ones
- Automatic language detection and translation to English

### 2. Data Structuring
- Processing raw transcript data into meaningful, structured information
- Information extraction for monument names, facts, and descriptions
- Dynamic file organization based on monument names

### 3. AI Interaction
- GPT-4o-mini integration via LiteLLM
- Contextual understanding of heritage site information
- Natural language responses to user queries

## Project Structure

```
language-learning-assistant/
├── backend/
│   ├── chat.py             # AI chat interface using LiteLLM
│   ├── get_transcript.py   # YouTube transcript extraction and processing
│   └── structured_data.py  # Data structuring for heritage site information
├── data/
│   ├── heritage_sites/     # Structured information about heritage sites
│   └── transcripts/        # Raw and processed YouTube transcripts
└── README.md
```

## How It Works

1. **Data Collection**: The system downloads transcripts from YouTube videos about Nepalese heritage sites
2. **Language Processing**: 
   - Identifies the best available transcript (manual > automatic)
   - Translates non-English content to English when needed
3. **Information Structuring**:
   - Processes raw transcript data using AI
   - Formats into consistent sections: Monument Name, Fun Fact, and Description
4. **User Interaction**:
   - Provides a chat interface for inquiries about heritage sites
   - Generates responses based on processed information

## Getting Started

1. Clone this repository
2. Install dependencies:
   ```
   cd into backend folder
   # Create Virtual environment
   python -m venv venv
   # Activate the virtual environment
   source venv/bin/activate
   # Install the dependencies listed in requirements.txt
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Create a `.env` file with your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```
4. Run the application:
   ```
   cd into the frontend
   streamlit run app.py
   ```

## Dependencies

- litellm
- youtube_transcript_api
- python-dotenv
- streamlit

## Future Enhancements

- Web scraping for additional heritage site information
- Multi-language support for user interaction
- Integration of image recognition for monument identification
- Geographic mapping of heritage sites
- User contribution to expand the knowledge base