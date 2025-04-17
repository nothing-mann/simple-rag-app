"""
API Server for Heritage Learning Assistant

This server exposes the LLM chat and RAG chat features through REST API endpoints
allowing them to be used in other projects.

Run with: python api_server.py
"""

from flask import Flask, request, jsonify
import os
import sys
import traceback
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

# Direct imports to avoid potential circular imports
from backend.config import COLLECTION_NAME, DEFAULT_MODEL
from backend.chat import LiteLLMChat
from backend.rag import HeritageRAG  # Make sure this import is explicit
from backend.rag_chat import HeritageRAGChat

# Initialize Flask app
app = Flask(__name__)

# Initialize chat instances
llm_chat = LiteLLMChat(model_id=DEFAULT_MODEL)
try:
    rag_chat = HeritageRAGChat(collection_name=COLLECTION_NAME, model_id=DEFAULT_MODEL)
    print("Successfully initialized HeritageRAGChat")
except Exception as e:
    print(f"Error initializing HeritageRAGChat: {str(e)}")
    print(traceback.format_exc())
    rag_chat = None

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify the API is running"""
    return jsonify({
        "status": "ok",
        "message": "Heritage Learning Assistant API is operational"
    })

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Standard LLM chat endpoint
    
    Request body:
    {
        "message": "Your question about heritage sites",
        "json_format": false,
        "temperature": 0.7,
        "model_id": "mistral/mistral-large-latest" (optional)
    }
    """
    data = request.json
    
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400
    
    message = data["message"]
    json_format = data.get("json_format", False)
    temperature = data.get("temperature", 0.7)
    model_id = data.get("model_id", DEFAULT_MODEL)
    
    # Use a new instance if a custom model is requested
    if model_id != DEFAULT_MODEL:
        chat_instance = LiteLLMChat(model_id=model_id)
    else:
        chat_instance = llm_chat
    
    # Generate response
    response = chat_instance.generate_response(
        message=message, 
        inference_config={"temperature": temperature},
        json_format=json_format
    )
    
    if response:
        return jsonify({
            "response": response,
            "model_used": model_id,
            "json_format": json_format
        })
    else:
        return jsonify({"error": "Failed to generate response"}), 500

@app.route("/api/rag-chat", methods=["POST"])
def rag_chat_endpoint():
    """
    RAG-enhanced chat endpoint
    
    Request body:
    {
        "message": "Your question about heritage sites",
        "n_results": 3,
        "temperature": 0.7,
        "model_id": "gpt-4o-mini" (optional),
        "include_sources": false (optional)
    }
    """
    try:
        data = request.json
        
        if not data or "message" not in data:
            return jsonify({"error": "No message provided"}), 400
        
        message = data["message"]
        n_results = int(data.get("n_results", 3))
        temperature = float(data.get("temperature", 0.7))
        model_id = data.get("model_id", DEFAULT_MODEL)
        include_sources = data.get("include_sources", False)
        
        print(f"RAG Chat request: message='{message}', n_results={n_results}, temperature={temperature}")
        
        # Check if rag_chat was successfully initialized
        if rag_chat is None:
            print("ERROR: rag_chat instance is None")
            return jsonify({"error": "RAG system not properly initialized"}), 500
            
        # Use a new instance if a custom model is requested
        if model_id != DEFAULT_MODEL:
            print(f"Using custom model: {model_id}")
            try:
                rag_instance = HeritageRAGChat(model_id=model_id)
            except Exception as e:
                print(f"Error creating custom RAG instance: {str(e)}")
                print(traceback.format_exc())
                return jsonify({"error": f"Failed to initialize RAG with custom model: {str(e)}"}), 500
        else:
            rag_instance = rag_chat
        
        # Generate RAG response
        print("Generating RAG response...")
        response = rag_instance.generate_rag_response(
            user_query=message,
            n_results=n_results,
            temperature=temperature
        )
        
        print(f"RAG response received: {response is not None}")
        
        # Check if response is None
        if response is None:
            print("WARNING: RAG response is None")
            return jsonify({"error": "Failed to generate RAG response - received empty response"}), 500
        
        result = {
            "response": response,
            "model_used": model_id
        }
        
        # Include context sources if requested
        if include_sources and response:
            try:
                results = rag_instance.rag.query(message, n_results=n_results)
                sources = []
                
                if results['metadatas'][0]:
                    for i, metadata in enumerate(results['metadatas'][0]):
                        monument = metadata.get('monument_name', 'Unknown')
                        source = metadata.get('source', 'Unknown source')
                        sources.append({
                            "monument": monument,
                            "source": source
                        })
                
                result["sources"] = sources
            except Exception as src_e:
                print(f"Error retrieving sources: {str(src_e)}")
                # Continue without sources rather than failing
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"Error in RAG chat endpoint: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({"error": error_msg}), 500

@app.route("/api/monuments", methods=["GET"])
def list_monuments():
    """List all available monument names in the database"""
    try:
        print("Starting list_monuments endpoint")
        
        # Import the required class directly
        from backend.rag import HeritageRAG
        
        # Initialize a new RAG instance
        rag = HeritageRAG()
        print("Successfully created HeritageRAG instance")
        
        all_monuments = set()
        
        # Use a simple query that should return results
        results = rag.query("heritage site", n_results=100)
        print(f"Query returned results: {bool(results)}")
        
        # Extract unique monument names
        if 'metadatas' in results and results['metadatas'] and results['metadatas'][0]:
            for metadata in results['metadatas'][0]:
                monument = metadata.get('monument_name')
                if monument and monument != 'Unknown':
                    all_monuments.add(monument)
            
            print(f"Found {len(all_monuments)} unique monuments")
        else:
            print("No metadata returned from query")
        
        return jsonify({
            "count": len(all_monuments),
            "monuments": sorted(list(all_monuments))
        })
    except ImportError as e:
        error_msg = f"ImportError: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_msg = f"Failed to list monuments: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({"error": error_msg}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    print(f"Starting Heritage Learning Assistant API server on port {port}")
    print(f"API Documentation available at http://localhost:{port}/api/health")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
