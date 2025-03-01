"""
Initialize the vector database with heritage site data
Run this script before starting the application
"""

import os
import sys

# Add project root to path (this is the most reliable way)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Now import modules
from backend.rag import HeritageRAG
from backend.config import HERITAGE_SITES_DIR

def init_database():
    """Initialize the database with all heritage site data"""
    print("Initializing vector database...")
    
    # Check if heritage sites directory exists and has files
    if not os.path.exists(HERITAGE_SITES_DIR):
        print(f"Error: Heritage sites directory not found at {HERITAGE_SITES_DIR}")
        return False
    
    json_files = [f for f in os.listdir(HERITAGE_SITES_DIR) if f.endswith('.json')]
    if not json_files:
        print(f"No JSON files found in {HERITAGE_SITES_DIR}")
        return False
    
    # Initialize RAG system
    rag = HeritageRAG()
    
    # Load documents
    count = rag.load_documents()
    print(f"Database initialized with {count} document chunks.")
    
    return count > 0

if __name__ == "__main__":
    success = init_database()
    if success:
        print("Database initialization completed successfully.")
    else:
        print("Database initialization failed or no documents were added.")
