from typing import Optional, Dict, Any, List
from litellm import completion
import os
import sys
import json
import argparse
from dotenv import load_dotenv
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration
from backend.config import HERITAGE_SITES_DIR, TRANSCRIPTS_DIR, DEFAULT_MODEL

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    print("WARNING: OPENAI_API_KEY not found in the .env file")

class HeritageDataStructurer:
    def __init__(self, model_id: str = DEFAULT_MODEL):
        """Initialize with LiteLLM model"""
        self.model_id = model_id

    def structure_heritage_data(self, heritage_site: str) -> Optional[str]:
        """Structure the heritage site data using LiteLLM"""
        prompt = f"""Extract information about the Nepalese cultural heritage site from the following text. 
        Format your response as a JSON object with the structure shown below.
        
        # IMPORTANT INSTRUCTIONS:
        1. Use the information provided in the input text. 2. Don't generate information on your own.
3.Focus on structuring the existing content with proper English spelling corrections.
4. Don't cut or crop out the information passed to you. 
5. Make sure the information structured is not changed and it flows as is like passed.
6. There is no character limit in the description key so pass all the information. Don't leave out anything.
7. You can skip the parts that seem like self promotion of the channels
8. Return valid JSON format.
        9. ONLY include fields where information is explicitly available in the text
        10. Leave fields empty (null) if no information is provided
        11. DO NOT make up or hallucinate any information not present in the text
        12. Use exact measurements, dates, and names as they appear in the text
        13. If there are multiple entries (e.g., historical_events), create an array of objects
        14. For any dates mentioned, preserve the original date format and calendar system
        
        JSON STRUCTURE:
        {{
          "monument_name": string or null,
          "alternative_names": [array of strings] or null,
          "typology": {{
            "monument_type": string or null,
            "main_deity": string or null,
            "religion": string or null
          }},
          "location": {{
            "province": string or null,
            "district": string or null,
            "municipality": string or null,
            "heritage_area": string or null,
            "tola": string or null
          }},
          "description": string or null,
          "fun_fact": string or null,
          "architecture": {{
            "shape": string or null,
            "storeys": number or null,
            "dimensions": object or null,
            "construction_materials": [array of strings] or null
          }},
          "condition": {{
            "status": string or null,
            "threats": [array of strings] or null
          }},
          "cultural_activities": [array of objects] or null,
          "historical_events": [array of objects] or null
        }}
        
        HERITAGE SITE TEXT:
        {heritage_site} 
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

    def save_to_file(self, structured_data: str, directory: str = None) -> bool:
        """Save structured heritage data to a JSON file named after the monument"""
        try:
            # Use configured directory if none provided
            if directory is None:
                directory = HERITAGE_SITES_DIR
                
            # Create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)
            
            # Extract monument name and create filename
            monument_name = self._extract_monument_name(structured_data)
            if not monument_name:
                raise ValueError("Could not extract monument name from structured data")
            
            filename = os.path.join(directory, f"{monument_name}.json")
            print(f"Saving to file: {filename}")
            
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
        """Load transcript from a file"""
        try:
            # If filename doesn't have a directory part, use TRANSCRIPTS_DIR
            if not os.path.dirname(filename):
                filename = os.path.join(TRANSCRIPTS_DIR, os.path.basename(filename))
            
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading transcript: {str(e)}")
            return None
            
    def process_transcript_file(self, transcript_file: str, output_dir: str = None) -> bool:
        """Process a single transcript file into structured data"""
        print(f"Processing transcript file: {transcript_file}")
        transcript = self.load_transcript(transcript_file)
        
        if not transcript:
            print(f"Failed to load transcript from {transcript_file}")
            return False
            
        print(f"Structuring data from transcript...")
        site_data = self.structure_heritage_data(transcript)
        
        if not site_data:
            print(f"Failed to structure transcript data from {transcript_file}")
            return False
            
        print("Transcript structured successfully")
        if self.save_to_file(site_data, output_dir):
            print(f"Structured data saved to {output_dir or HERITAGE_SITES_DIR}")
            return True
        else:
            print(f"Failed to save structured data for {transcript_file}")
            return False
    
    def process_all_transcripts(self, transcripts_dir: str = TRANSCRIPTS_DIR, output_dir: str = None) -> Dict[str, bool]:
        """Process all transcript files in the directory"""
        results = {}
        
        # List all transcript files
        if not os.path.exists(transcripts_dir):
            print(f"Transcripts directory not found: {transcripts_dir}")
            return results
            
        transcript_files = [os.path.join(transcripts_dir, f) for f in os.listdir(transcripts_dir) 
                          if f.endswith('.txt') and os.path.isfile(os.path.join(transcripts_dir, f))]
        
        if not transcript_files:
            print(f"No transcript files found in {transcripts_dir}")
            return results
            
        print(f"Found {len(transcript_files)} transcript files to process")
        
        # Process each file
        for i, file_path in enumerate(transcript_files, 1):
            file_name = Path(file_path).name
            print(f"Processing file {i}/{len(transcript_files)}: {file_name}")
            
            success = self.process_transcript_file(file_path, output_dir)
            results[file_path] = success
            print("-" * 40)
            
        # Print summary
        successful = sum(1 for success in results.values() if success)
        print(f"\nProcessing complete: {successful}/{len(results)} files processed successfully")
        
        return results

def main():
    """Process transcripts into structured data"""
    parser = argparse.ArgumentParser(description="Structure Heritage Site Transcripts")
    parser.add_argument('--transcript', type=str, help="Path to specific transcript file")
    parser.add_argument('--output-dir', type=str, default=HERITAGE_SITES_DIR, 
                        help="Directory to save structured data")
    parser.add_argument('--all', action='store_true', 
                        help="Process all transcript files in the transcripts directory")
    
    args = parser.parse_args()
    structurer = HeritageDataStructurer()
    
    if args.all:
        # Process all transcript files
        structurer.process_all_transcripts(TRANSCRIPTS_DIR, args.output_dir)
    elif args.transcript:
        # Process specific transcript file
        structurer.process_transcript_file(args.transcript, args.output_dir)
    else:
        # Default: Find the most recent transcript
        transcript_files = [os.path.join(TRANSCRIPTS_DIR, f) for f in os.listdir(TRANSCRIPTS_DIR) 
                          if f.endswith('.txt') and os.path.isfile(os.path.join(TRANSCRIPTS_DIR, f))]
        
        if not transcript_files:
            print(f"No transcript files found in {TRANSCRIPTS_DIR}")
            return
            
        transcript_file = max(transcript_files, key=os.path.getmtime)
        print(f"Using most recent transcript: {transcript_file}")
        structurer.process_transcript_file(transcript_file, args.output_dir)

if __name__ == "__main__":
    main()
