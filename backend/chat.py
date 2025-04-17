# from litellm import completion
# import os 
# from dotenv import load_dotenv

# load_dotenv()
# MistralLarge_api_key = os.getenv("MistralLarge_API_KEY")

# if not MistralLarge_api_key:
#     print("WARNING: MistralLarge_API_KEY not found in the .env file")

# response = completion(
#   model="gpt-4o-mini",
#   response_format={ "type": "json_object" },
#   messages=[
#     {"role": "system", "content": "You are a Nepalese historical expert who is informing the common tourists about the information of the different cultural heritage sites in Nepal. Structure your answer as Name of the heritage site, Exact location of the heritage site, One rarely known Fun fact of the heritage site and A description paragraph about the heritage site with historical significance. Structure the answer in json format."},
#     {"role": "user", "content": "Tell me about Krishna Mandir"}
#   ]
# )
# print(response.choices[0].message.content)


# from litellm import completion
# import os 
# from dotenv import load_dotenv
# from typing import Optional, Dict, Any

# # Load environment variables
# load_dotenv()
# MistralLarge_api_key = os.getenv("MistralLarge_API_KEY")

# if not MistralLarge_api_key:
#     print("WARNING: MistralLarge_API_KEY not found in the .env file")

# class LiteLLMChat:
#     def __init__(self, model_id: str = "gpt-4o-mini"):
#         """Initialize chat client with LiteLLM"""
#         self.model_id = model_id
#         self.system_prompt = "You are a Nepalese historical expert who is informing the common tourists about the information of the different cultural heritage sites in Nepal. Structure your answer as Name of the heritage site, Exact location of the heritage site, One rarely known Fun fact of the heritage site and A description paragraph about the heritage site with historical significance."
        
#     def generate_response(self, message: str, inference_config: Optional[Dict[str, Any]] = None, json_format: bool = True) -> Optional[str]:
#         """Generate a response using LiteLLM
        
#         Args:
#             message: User's input message
#             inference_config: Configuration for the model (temperature, etc.)
#             json_format: Whether to return response in JSON format
            
#         Returns:
#             The generated response text or None if an error occurs
#         """
#         if inference_config is None:
#             inference_config = {"temperature": 0.7}
        
#         response_format = {"type": "json_object"} if json_format else None
        
#         try:
#             response = completion(
#                 model=self.model_id,
#                 messages=[
#                     {"role": "system", "content": self.system_prompt},
#                     {"role": "user", "content": message}
#                 ],
#                 temperature=inference_config.get("temperature", 0.7),
#                 response_format=response_format
#             )
            
#             return response.choices[0].message.content
            
#         except Exception as e:
#             print(f"Error generating response: {str(e)}")
#             return None


# if __name__ == "__main__":
#     chat = LiteLLMChat()
#     print("Chat with the Nepali Heritage Assistant (type '/exit' to quit)")
#     while True:
#         user_input = input("You: ")
#         if user_input.lower() == '/exit':
#             break
#         response = chat.generate_response(user_input)
#         print("Bot:", response)

from litellm import completion
import os 
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# Load environment variables
load_dotenv()
mistral_api_key = os.getenv("MISTRAL_API_KEY")

if not mistral_api_key:
    print("WARNING: MistralLarge_API_KEY not found in the .env file")

class LiteLLMChat:
    def __init__(self, model_id: str = "mistral/mistral-large-latest"):
        """Initialize chat client with LiteLLM"""
        self.model_id = model_id
        
    def generate_response(self, message: str, inference_config: Optional[Dict[str, Any]] = None, json_format: bool = False) -> Optional[str]:
        """Generate a response using LiteLLM
        
        Args:
            message: User's input message
            inference_config: Configuration for the model (temperature, etc.)
            json_format: Whether to return response in JSON format
            
        Returns:
            The generated response text or None if an error occurs
        """
        if inference_config is None:
            inference_config = {"temperature": 0.7}
            
        system_message = "You are a Nepalese historical expert who is informing common tourists about the different cultural heritage sites in Nepal."
        
        if json_format:
            system_message += " Structure your answer as a JSON object with fields: name, location, fun_fact, and description."
            response_format = {"type": "json_object"}
        else:
            response_format = None
        
        try:
            response = completion(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": message}
                ],
                temperature=inference_config.get("temperature", 0.7),
                response_format=response_format if response_format else None
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return None


if __name__ == "__main__":
    chat = LiteLLMChat()
    print("Chat with the Nepali Heritage Assistant (type '/exit' to quit)")
    while True:
        user_input = input("You: ")
        if user_input.lower() == '/exit':
            break
        response = chat.generate_response(user_input)
        print("Bot:", response)