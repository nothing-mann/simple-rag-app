import chromadb
from chromadb.utils import embedding_functions
import os
import json
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from litellm import completion

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not found in the .env file")

class HeritageRAG:
    def __init__(self, collection_name: str = "cultural-heritage-information", model_id: str = "gpt-4o-mini"):
        """Initialize RAG system with ChromaDB and LiteLLM"""
        self.collection_name = collection_name
        self.model_id = model_id
        
        # Setup Chroma persistent client
        self.chroma_client = chromadb.PersistentClient()
        self.chroma_client.heartbeat()
        
        # Setup embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            model_name="text-embedding-ada-002", 
            api_key=OPENAI_API_KEY
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name, 
            embedding_function=self.embedding_function
        )
    
    def load_documents(self, documents_dir: str = "data/heritage_sites") -> int:
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
    
    def generate_rag_response(self, user_query: str, n_results: int = 3, temperature: float = 0.7) -> Optional[str]:
        """
        Generate a response using RAG with LiteLLM
        
        Args:
            user_query: User's question
            n_results: Number of context results to retrieve
            temperature: Temperature for LLM generation
            
        Returns:
            Generated response based on retrieved context
        """
        # Get relevant context from the collection
        results = self.query(user_query, n_results=n_results)
        
        if not results['documents'][0]:
            # Fall back to regular LLM response if no context is found
            return self._generate_llm_response(user_query, context="", temperature=temperature)
        
        # Prepare context from retrieved documents
        context = self._prepare_context_from_results(results)
        
        # Generate response with context
        return self._generate_llm_response(user_query, context, temperature)
    
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
    
    def _generate_llm_response(self, user_query: str, context: str, temperature: float = 0.7) -> Optional[str]:
        """
        Generate a response using LiteLLM with provided context
        
        Args:
            user_query: User's question
            context: Context from retrieved documents
            temperature: Temperature for generation
            
        Returns:
            Generated response text
        """
        system_prompt = """You are a Nepalese cultural heritage expert. 
Answer questions about Nepalese monuments and heritage sites based on the context provided.
If the context doesn't contain relevant information, say so and provide general information about Nepalese heritage.
Always be informative, engaging, and respectful of Nepalese culture and history."""

        user_prompt = f"""Question: {user_query}
        
Context information:
{context}

Please provide a helpful and accurate response based on the above context."""

        try:
            response = completion(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating RAG response: {str(e)}")
            return None

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
    """Example usage of the HeritageRAG class with RAG-enhanced chat"""
    # Initialize RAG system
    rag = HeritageRAG()
    
    # Load documents (only needed once or when adding new documents)
    rag.load_documents()
    
    print("Nepali Heritage RAG Assistant (type '/exit' to quit)")
    while True:
        user_input = input("You: ")
        if user_input.lower() == '/exit':
            break
            
        # Generate RAG-enhanced response
        response = rag.generate_rag_response(user_input)
        if response:
            print("\nBot:", response)
        else:
            print("\nBot: I'm sorry, I couldn't generate a response. Please try again.")


if __name__ == "__main__":
    main()