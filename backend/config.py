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
DEFAULT_MODEL = "mistral/mistral-large-latest"
# EMBEDDING_MODEL = "text-embedding-ada-002"
# EMBEDDING_MODEL = "all-MiniLM-L6-v2"
# EMBEDDING_MODEL = "hkunlp/instructor-large"
EMBEDDING_MODEL = "hkunlp/instructor-xl"

# Print configuration for debugging
if __name__ == "__main__":
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"CHROMA_DB_DIR: {CHROMA_DB_DIR}")
    print(f"HERITAGE_SITES_DIR: {HERITAGE_SITES_DIR}")
    print(f"TRANSCRIPTS_DIR: {TRANSCRIPTS_DIR}")
    print(f"COLLECTION_NAME: {COLLECTION_NAME}")
    print(f"DEFAULT_MODEL: {DEFAULT_MODEL}")
    print(f"EMBEDDING_MODEL: {EMBEDDING_MODEL}")
