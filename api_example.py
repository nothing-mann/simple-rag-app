"""
Example code demonstrating how to use the Heritage Learning Assistant API
from another project.
"""

import requests
import json

# API base URL - change this to your server address when deployed
API_BASE_URL = "http://localhost:5000/api"

def query_standard_llm(message, json_format=False):
    """Query the standard LLM chat endpoint"""
    url = f"{API_BASE_URL}/chat"
    
    payload = {
        "message": message,
        "json_format": json_format,
        "temperature": 0.7
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def query_rag_enhanced(message, include_sources=True):
    """Query the RAG-enhanced chat endpoint"""
    url = f"{API_BASE_URL}/rag-chat"
    
    payload = {
        "message": message,
        "n_results": 3,
        "temperature": 0.7,
        "include_sources": include_sources
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def get_available_monuments():
    """Get a list of all monuments in the database"""
    url = f"{API_BASE_URL}/monuments"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def print_response(title, data):
    """Pretty print a response"""
    print(f"\n===== {title} =====")
    if isinstance(data, dict):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(data)
    print("=" * (len(title) + 12))

if __name__ == "__main__":
    # Example 1: Query standard LLM
    standard_response = query_standard_llm(
        "What is the significance of Krishna Mandir?"
    )
    print_response("Standard LLM Response", standard_response)
    
    # Example 2: Query standard LLM with JSON format
    json_response = query_standard_llm(
        "What is the significance of Krishna Mandir?", 
        json_format=True
    )
    print_response("JSON Formatted Response", json_response)
    
    # Example 3: Query RAG-enhanced model
    rag_response = query_rag_enhanced(
        "What is the significance of Krishna Mandir?"
    )
    print_response("RAG-Enhanced Response", rag_response)
    
    # Example 4: Get a list of all monuments
    monuments = get_available_monuments()
    if monuments:
        print_response("Available Monuments", monuments)
