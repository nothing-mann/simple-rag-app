from typing import Optional
from litellm import completion
import os
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    print("WARNING: OPENAI_API_KEY not found in the .env file")

class HeritageDataStructurer:
    def __init__(self, model_id: str = "gpt-4o-mini"):
        """Initialize with LiteLLM model"""
        self.model_id = model_id

    def structure_heritage_data(self, heritage_site: str) -> Optional[str]:
        """Structure the heritage site data using LiteLLM"""
        prompt = f"""For the following heritage site, provide information in this exact format. Use the information that will be passed about the heritage site and only focus on structuring. Don't generate the information on your own. You should reference the data passed as much as possible.

Monument name: 
[name of the monument]
...................................
Fun fact:
[one interesting fact about the monument]
.....................
Description:
[detailed description of the monument]
.................

Heritage site to structure: {heritage_site}
"""

        try:
            response = completion(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": "You are a Nepalese historical expert. Provide detailed information about heritage sites in the specified format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error structuring heritage data: {str(e)}")
            return None

    def save_to_file(self, structured_data: str, filename: str) -> bool:
        """Save structured heritage data to a file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(structured_data)
            return True
        except Exception as e:
            print(f"Error saving data: {str(e)}")
            return False

    def load_transcript(self, filename: str) -> Optional[str]:
        """Load heritage data from a file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return None

if __name__ == "__main__":
    structurer = HeritageDataStructurer()
    # Example usage
    transcript = structurer.load_transcript("data/transcripts/q_HLhjtQUM8.json.txt")
    site_data = structurer.structure_heritage_data(transcript)
    if site_data:
        print(site_data)
        structurer.save_to_file(site_data, "data/heritage_sites/basantapur.txt")
