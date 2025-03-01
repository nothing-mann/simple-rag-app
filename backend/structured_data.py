from typing import Optional, Dict, Any
from litellm import completion
import os
import json
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
        prompt = f"""For the following heritage site, extract and structure information in JSON format with these fields:
- monument_name: The name of the monument
- fun_fact: An interesting fact about the monument
- description: A detailed description of the monument with historical significance

Use the information provided in the input text. Don't generate information on your own.
Focus on structuring the existing content with proper English spelling corrections.
Don't cut or crop out the information passed to you. 
Make sure the information structured is not changed and it flows as is like passed.
There is no character limit in the description key so pass all the information. Don't leave out anything.
You can skip the parts that seem like self promotion of the channels
Return valid JSON format. 

Heritage site to structure: {heritage_site}
"""

        try:
            response = completion(
                model=self.model_id,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a Nepalese historical expert. Structure heritage site information in clean JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error structuring heritage data: {str(e)}")
            return None

    def _extract_monument_name(self, json_data: str) -> Optional[str]:
        """Extract monument name from JSON data"""
        try:
            data = json.loads(json_data)
            if "monument_name" in data:
                name = data["monument_name"]
                # Convert to lowercase and replace spaces with underscores for filename
                return '_'.join(name.lower().split())
            return None
        except Exception as e:
            print(f"Error extracting monument name from JSON: {str(e)}")
            return None

    def save_to_file(self, structured_data: str, directory: str = "data/heritage_sites") -> bool:
        """Save structured heritage data to a JSON file named after the monument"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)
            
            # Extract monument name and create filename
            monument_name = self._extract_monument_name(structured_data)
            if not monument_name:
                raise ValueError("Could not extract monument name from structured data")
            
            filename = os.path.join(directory, f"{monument_name}.json")
            
            # Parse the JSON data
            try:
                new_data = json.loads(structured_data)
            except json.JSONDecodeError:
                print("Warning: Data is not valid JSON. Saving as text.")
                # Save as text if not valid JSON
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(structured_data)
                return True
            
            # Handle append mode for JSON data
            if os.path.exists(filename):
                try:
                    # Read existing file
                    with open(filename, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    # Try parsing existing content as JSON
                    try:
                        existing_data = json.loads(file_content)
                        
                        # If existing data is a list, append the new data
                        if isinstance(existing_data, list):
                            existing_data.append(new_data)
                            final_data = existing_data
                        # If it's a dictionary, create a list with both
                        else:
                            final_data = [existing_data, new_data]
                    except json.JSONDecodeError:
                        # If existing content is not valid JSON, create a list with the new data
                        final_data = [new_data]
                        
                    # Write updated data
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(final_data, f, indent=2, ensure_ascii=False)
                    
                except Exception as e:
                    print(f"Error appending to JSON file: {str(e)}")
                    return False
            else:
                # New file, just write the data
                with open(filename, 'w', encoding='utf-8') as f:
                    # Write the JSON data
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
    transcript = structurer.load_transcript("data/transcripts/ypoB6S5mrts.txt")
    site_data = structurer.structure_heritage_data(transcript)
    if site_data:
        print(site_data)
        # Now just pass the directory, filename will be created automatically
        structurer.save_to_file(site_data, "data/heritage_sites")
