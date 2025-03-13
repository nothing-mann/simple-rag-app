# Nepalese Heritage Learning Assistant

An AI-powered tool for learning about Nepalese cultural heritage sites using modern NLP techniques and YouTube content along with manually added raw text files.

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
│   ├── chat.py             # Basic AI chat interface using LiteLLM
│   ├── config.py           # Central configuration settings
│   ├── get_transcript.py   # YouTube transcript extraction and processing
│   ├── init_db.py          # Database initialization script 
│   ├── rag.py              # Vector database management for heritage sites
│   ├── rag_chat.py         # RAG-enhanced chat interface
│   └── structured_data.py  # Data structuring for heritage site information
├── data/
│   ├── heritage_sites/     # Structured JSON information about heritage sites
│   └── transcripts/        # Raw and processed YouTube transcripts
├── frontend/
│   └── main.py             # Streamlit user interface
├── chroma_db/              # Vector database storage
└── README.md
```

## Complete Setup Guide

### 1. Environment Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd simple-rag-app
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Create a `.env` file in the project root with your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

### 2. Data Collection and Processing

1. **Download transcripts from YouTube**:
   ```bash
   # Download a single transcript
   python backend/get_transcript.py https://www.youtube.com/watch?v=VIDEO_ID
   
   # Print transcript content while downloading
   python backend/get_transcript.py https://www.youtube.com/watch?v=VIDEO_ID true
   ```

2. **Structure the transcript data**:
   ```bash
   # Process most recent transcript
   python backend/structured_data.py
   
   # Process a specific transcript
   python backend/structured_data.py --transcript data/transcripts/VIDEO_ID.txt
   
   # Process all transcripts
   python backend/structured_data.py --all
   
   # Specify a custom output directory
   python backend/structured_data.py --all --output-dir path/to/output
   ```

### 3. Database Initialization and Management

1. **Initialize the vector database**:
   ```bash
   # This will process all heritage site data and create the vector database
   python backend/init_db.py
   ```

2. **Update the database with new content**:
   ```bash
   # Update database with all heritage site data
   python backend/rag.py
   
   # Test query against the database
   python backend/rag.py --query "Tell me about Krishna Mandir" --results 3
   ```

### 4. Running the Chat Interface

1. **Use the command line RAG chat interface**:
   ```bash
   python backend/rag_chat.py
   
   # Use a different model
   python backend/rag_chat.py --model gpt-4
   ```

2. **Run the web application**:
   ```bash
   # Start the Streamlit web interface
   streamlit run frontend/main.py
   ```

## API Usage

The project includes an API server that allows you to access the heritage information and chat features from other applications.

### Starting the API Server

```bash
# Install Flask and other requirements if needed
pip install -r requirements.txt

# Start the API server
python backend/api_server.py
```

By default, the server runs on port 5000. You can change this by setting the PORT environment variable.

### API Endpoints

1. **Health Check**
   ```
   GET /api/health
   ```

2. **Standard LLM Chat**
   ```
   POST /api/chat
   {
     "message": "Your question about heritage sites",
     "json_format": false,
     "temperature": 0.7,
     "model_id": "gpt-4o-mini" (optional)
   }
   ```

3. **RAG-Enhanced Chat**
   ```
   POST /api/rag-chat
   {
     "message": "Your question about heritage sites",
     "n_results": 3,
     "temperature": 0.7,
     "model_id": "gpt-4o-mini" (optional),
     "include_sources": false (optional)
   }
   ```

4. **List Available Monuments**
   ```
   GET /api/monuments
   ```

### Example API Usage

Here's how to use the API from Python:

```python
import requests

# Example: Query RAG-enhanced chat
response = requests.post(
    "http://localhost:5000/api/rag-chat",
    json={
        "message": "Tell me about Krishna Mandir",
        "include_sources": True
    }
)

if response.status_code == 200:
    data = response.json()
    print(data["response"])
    
    # Print sources if available
    if "sources" in data:
        print("\nSources:")
        for source in data["sources"]:
            print(f"- {source['monument']} ({source['source']})")
```

See `api_example.py` for more detailed usage examples.

## Troubleshooting

### Database Synchronization Issues

If the RAG responses aren't using your latest data:

1. Make sure JSON files are in the correct format in the `data/heritage_sites` directory
2. Re-initialize the database:
   ```bash
   python backend/init_db.py
   ```
3. If problems persist, try clearing the database:
   ```bash
   rm -rf chroma_db
   python backend/init_db.py
   ```

### Import Errors

If you encounter import errors:

1. Make sure you're running commands from the project root directory
2. Verify that the virtual environment is activated
3. Check that all dependencies are installed correctly

### API Key Issues

If you get authentication errors:

1. Verify your OpenAI API key is correctly set in the `.env` file
2. Ensure the `.env` file is in the correct location (project root)
3. Check if your API key has sufficient quota/credits

## Complete Workflow Example

Here's a complete example of processing a new heritage site video:

```bash
# 1. Activate the environment
source venv/bin/activate

# 2. Download a transcript from a YouTube video
python backend/get_transcript.py https://www.youtube.com/watch?v=EXAMPLE_ID

# 3. Convert the transcript to structured data
python backend/structured_data.py

# 4. Update the vector database with the new data
python backend/init_db.py

# 5. Start the web application
streamlit run frontend/main.py
```

## Dependencies

- litellm
- youtube_transcript_api
- python-dotenv
- streamlit
- chromadb
- openai

## Future Enhancements

- Web scraping for additional heritage site information
- Multi-language support for user interaction
- Integration of image recognition for monument identification
- Geographic mapping of heritage sites
- User contribution to expand the knowledge base
