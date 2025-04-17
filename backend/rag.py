import chromadb
from chromadb.utils import embedding_functions
import os
import json
import sys
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# After adding project root to path, now we can import from backend
from backend.config import CHROMA_DB_DIR, COLLECTION_NAME, HERITAGE_SITES_DIR, EMBEDDING_MODEL

# Load environment variables
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    print("WARNING: MISTRAL_API_KEY not found in the .env file")

# Import directly from sentence_transformers to avoid the token parameter issue
import sentence_transformers
import numpy as np

class CustomInstructorEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, model_name: str = "hkunlp/instructor-large"):
        """Initialize with a sentence transformer model that doesn't require the instructor pattern"""
        self.model_name = model_name
        print(f"Loading sentence-transformers model {model_name}...")
        # Using regular SentenceTransformer instead of INSTRUCTOR to avoid compatibility issues
        self._model = sentence_transformers.SentenceTransformer(model_name)

    def __call__(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        # Get embeddings directly without instruction format
        embeddings = self._model.encode(texts)
        
        # Convert to native Python lists for JSON serialization
        return embeddings.tolist()

class HeritageRAG:
    def __init__(self, collection_name: str = COLLECTION_NAME):
        """Initialize RAG system with ChromaDB"""
        self.collection_name = collection_name
        
        # Setup Chroma persistent client with explicit path
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        self.chroma_client.heartbeat()
        
        # Use our custom embedding function with a standard model
        self.embedding_function = CustomInstructorEmbeddingFunction()
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name, 
            embedding_function=self.embedding_function
        )
    
    def load_documents(self, documents_dir: str = HERITAGE_SITES_DIR) -> int:
        """
        Load and embed documents from JSON files in the specified directory
        
        Args:
            documents_dir: Path to directory containing JSON files
            
        Returns:
            Number of documents added to the collection
        """
        documents = []
        metadatas = []
        ids = []
        
        # Read all JSON files in the directory
        for i, filename in enumerate(os.listdir(documents_dir)):
            if filename.endswith('.json'):
                file_path = os.path.join(documents_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        # Load JSON content
                        json_content = json.load(file)
                        
                        # Handle both individual objects and lists of objects
                        if isinstance(json_content, list):
                            # Process each item in the list
                            for j, item in enumerate(json_content):
                                document, metadata, id_str = self._process_json_item(
                                    item, file_path, f"doc{i+1}_{j}", j
                                )
                                documents.append(document)
                                metadatas.append(metadata)
                                ids.append(id_str)
                        else:
                            # Process individual object
                            document, metadata, id_str = self._process_json_item(
                                json_content, file_path, f"doc{i+1}"
                            )
                            documents.append(document)
                            metadatas.append(metadata)
                            ids.append(id_str)
                except Exception as e:
                    print(f"Error processing file {filename}: {str(e)}")
        
        # Check if we have documents to add
        if documents:
            # Add documents to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            print(f"Added {len(documents)} document chunks to the collection.")
            return len(documents)
        else:
            print("No documents found to add to the collection.")
            return 0
    
    def _process_json_item(self, item: Dict, file_path: str, id_str: str, index: int = None) -> tuple:
        """
        Process a single JSON item into document, metadata, and ID
        
        Args:
            item: JSON object
            file_path: Path to the source file
            id_str: ID string
            index: Optional index within a list
            
        Returns:
            Tuple of (formatted_content, metadata, id_str)
        """
        # Format the content for embedding
        formatted_content = f"""
        Monument: {item.get('monument_name', 'Unknown')}
        Fun Fact: {item.get('fun_fact', 'N/A')}
        Description: {item.get('description', 'N/A')}
        """
        
        # Create metadata
        metadata = {
            "source": file_path,
            "monument_name": item.get('monument_name', 'Unknown'),
        }
        
        # Add index to metadata if provided
        if index is not None:
            metadata["index"] = index
            
        return formatted_content, metadata, id_str
    
    def query(self, query_text: str, n_results: int = 2) -> Dict[str, Any]:
        """
        Query the collection for similar documents
        
        Args:
            query_text: Text to search for
            n_results: Number of results to return
            
        Returns:
            Results dictionary from ChromaDB
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
        )
        return results
    
    def _prepare_context_from_results(self, results: Dict[str, Any]) -> str:
        """
        Prepare context from query results
        
        Args:
            results: Results dictionary from query method
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            monument_name = metadata.get('monument_name', 'Unknown Monument')
            context_parts.append(f"--- Information about {monument_name} ---\n{doc}\n")
        
        return "\n".join(context_parts)
    
    def print_query_results(self, results: Dict[str, Any], query_text: str = None) -> None:
        """
        Print the results of a query in a readable format
        
        Args:
            results: Results from query method
            query_text: Optional query text to display
        """
        if query_text:
            print(f"\nResults for query: '{query_text}'")
            
        if results['documents'][0]:
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                print(f"\n--- Result {i+1} ---")
                print(f"Source: {metadata['source']}")
                print(f"Monument: {metadata['monument_name']}")
                print(f"Content excerpt: {doc[:150]}...")
        else:
            print("No results found.")


def main():
    """Main function focused on updating the database"""
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Heritage RAG System - Database Operations')
    parser.add_argument('--data-dir', type=str, default=HERITAGE_SITES_DIR,
                      help=f'Directory containing heritage site JSON files (default: {HERITAGE_SITES_DIR})')
    parser.add_argument('--query', type=str, default=None,
                      help='Optional: Run a test query against the database')
    parser.add_argument('--results', type=int, default=3,
                      help='Number of results to return for test query (default: 3)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize RAG system
    rag = HeritageRAG()
    
    # Update the database
    print(f"Updating database with documents from {args.data_dir}...")
    count = rag.load_documents(args.data_dir)
    print(f"Database update complete. Added {count} document chunks.")
    
    # Run test query if provided
    if args.query:
        print(f"\nRunning test query: '{args.query}'")
        results = rag.query(args.query, n_results=args.results)
        rag.print_query_results(results, args.query)


if __name__ == "__main__":
    main()