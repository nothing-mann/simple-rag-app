import os
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from litellm import completion

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from backend
from backend.config import COLLECTION_NAME, DEFAULT_MODEL
from backend.rag import HeritageRAG

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not found in the .env file")

class HeritageRAGChat:
    def __init__(self, collection_name: str = COLLECTION_NAME, model_id: str = DEFAULT_MODEL):
        """Initialize RAG Chat system"""
        self.model_id = model_id
        self.rag = HeritageRAG(collection_name=collection_name)
    
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
        results = self.rag.query(user_query, n_results=n_results)
        
        if not results['documents'][0]:
            # Fall back to regular LLM response if no context is found
            return self._generate_llm_response(user_query, context="", temperature=temperature)
        
        # Prepare context from retrieved documents
        context = self.rag._prepare_context_from_results(results)
        
        # Generate response with context
        return self._generate_llm_response(user_query, context, temperature)
    
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
    
    def start_chat(self) -> None:
        """Start an interactive chat session with the RAG system"""
        print("\n=== Nepali Heritage RAG Assistant ===")
        print("Type '/exit' to quit, '/help' for commands")
        
        while True:
            user_input = input("\nYou: ")
            
            # Command handling
            if user_input.lower() == '/exit':
                print("Goodbye!")
                break
            elif user_input.lower() == '/help':
                print("\nAvailable commands:")
                print("/exit - Exit the chat")
                print("/help - Show this help message")
                print("/debug <query> - Show retrieved documents for a query")
                continue
            elif user_input.lower().startswith('/debug '):
                query = user_input[7:]  # Remove '/debug ' prefix
                results = self.rag.query(query, n_results=3)
                self.rag.print_query_results(results, query)
                continue
                
            # Generate RAG-enhanced response
            response = self.generate_rag_response(user_input)
            if response:
                print("\nBot:", response)
            else:
                print("\nBot: I'm sorry, I couldn't generate a response. Please try again.")


def main():
    """Main function to start the chat interface"""
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Heritage RAG Chat Interface')
    parser.add_argument('--model', type=str, default='gpt-4o-mini',
                      help='LLM model to use (default: gpt-4o-mini)')
    parser.add_argument('--collection', type=str, default='cultural-heritage-information',
                      help='ChromaDB collection name (default: cultural-heritage-information)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize and start chat
    chat = HeritageRAGChat(collection_name=args.collection, model_id=args.model)
    chat.start_chat()


if __name__ == "__main__":
    main()
