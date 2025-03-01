import os

# Base paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Database settings
CHROMA_DB_DIR = os.path.join(PROJECT_ROOT, "chroma_db")
COLLECTION_NAME = "cultural-heritage-information"

# Data paths
HERITAGE_SITES_DIR = os.path.join(DATA_DIR, "heritage_sites")
TRANSCRIPTS_DIR = os.path.join(DATA_DIR, "transcripts")

# Create directories if they don't exist
os.makedirs(CHROMA_DB_DIR, exist_ok=True)
os.makedirs(HERITAGE_SITES_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

# Model settings
DEFAULT_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-ada-002"
