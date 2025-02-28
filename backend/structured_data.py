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
        prompt = f"""For the following heritage site, provide information in this exact format. Use the information that will be passed about the heritage site and only focus on structuring. Don't generate the information on your own. You should reference the data passed as much as possible. You don't have a character limit. Give me back all of the content I gave you to structure. Don't cut or crop out any part. I just need what I give you as is with spelling corrections in English and proper structure.

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

    def _extract_monument_name(self, structured_data: str) -> Optional[str]:
        """Extract monument name from structured data"""
        try:
            lines = structured_data.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == 'Monument name:':
                    # Get the next line which contains the actual name
                    if i + 1 < len(lines):
                        name = lines[i + 1].strip()
                        # Convert to lowercase and replace spaces with underscores for filename
                        return '_'.join(name.lower().split())
            return None
        except Exception as e:
            print(f"Error extracting monument name: {str(e)}")
            return None

    def save_to_file(self, structured_data: str, directory: str = "data/heritage_sites") -> bool:
        """Save structured heritage data to a file named after the monument"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)
            
            # Extract monument name and create filename
            monument_name = self._extract_monument_name(structured_data)
            if not monument_name:
                raise ValueError("Could not extract monument name from structured data")
            
            filename = os.path.join(directory, f"{monument_name}.txt")
            
            # Append mode if file exists, write mode if it doesn't
            mode = 'a' if os.path.exists(filename) else 'w'
            with open(filename, mode, encoding='utf-8') as f:
                if mode == 'a':
                    f.write('\n\n' + '='*50 + '\n\n')  # Separator between entries
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
    transcript = structurer.load_transcript("data/transcripts/Ky34soHXXno.txt")
    site_data = structurer.structure_heritage_data(transcript)
    if site_data:
        print(site_data)
        # Now just pass the directory, filename will be created automatically
        structurer.save_to_file(site_data, "data/heritage_sites")
