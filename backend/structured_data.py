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
mistral_api_key = os.getenv("MISTRAL_API_KEY")

if not mistral_api_key:
    print("WARNING: MISTRAL_API_KEY not found in the .env file")

# Path to the transcript tracking file
TRANSCRIPT_TRACKING_FILE = os.path.join(TRANSCRIPTS_DIR, '.processed_transcripts.json')

class HeritageDataStructurer:
    def __init__(self, model_id: str = DEFAULT_MODEL):
        """Initialize with LiteLLM model"""
        self.model_id = model_id

    def analyze_text_for_multiple_sites(self, text: str) -> Dict:
        """
        Analyze if the text contains information about multiple heritage sites
        
        Args:
            text: The text content to analyze
            
        Returns:
            Dictionary with analysis result
        """
        try:
            # First, extract potential heritage site names using structural patterns
            import re
            
            # Look for common patterns in heritage site descriptions
            potential_sites = []
            
            # Look for capitalized words followed by heritage site type indicators (without hardcoding names)
            site_patterns = [
                # Pattern for "Name Temple/Stupa/etc" format with capitalized first word
                r'([A-Z][A-Za-z\s\-\']+(?:Temple|Stupa|Durbar Square|Palace|Monastery|Chowk|Mandap|Mandir|Pillar|Monument|Bell))',
                
                # Pattern for "Name temple/stupa/etc" format with lowercase type
                r'([A-Z][A-Za-z\s\-\']+(?:temple|stupa|durbar square|palace|monastery|chowk|mandap|mandir|pillar|monument|bell))',
                
                # Pattern for capitalized names in all-caps (often section headers)
                r'([A-Z][A-Z\s\-\']{3,}(?:\s+[A-Z][A-Z\s]+)?)',
            ]
            
            for pattern in site_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if isinstance(match, str) and len(match) > 4:  # Ensure it's a valid name
                        potential_sites.append(match.strip())
            
            # Look for section headers and page transitions (common in PDF structure)
            # This helps identify boundaries between different heritage sites
            section_markers = [
                # PDF page headers
                r'---\s*Page\s+\d+\s*---\s*([A-Z][A-Za-z\s\-\']+)',
                
                # Numbered section headers
                r'\n\d+\.\s+([A-Z][A-Za-z\s\-\']+)',
                
                # Typical document section headers
                r'\n([A-Z][A-Z\s\-\']{2,}[A-Z])\s*\n',
                
                # Heritage type indicators at start of paragraphs
                r'\n([A-Z][A-Za-z\s\-\']+(?:Temple|Stupa|Durbar|Square|Palace|Monastery))'
            ]
            
            for pattern in section_markers:
                matches = re.findall(pattern, text)
                for match in matches:
                    if isinstance(match, str) and len(match) > 4:
                        potential_sites.append(match.strip())
            
            # Clean the potential sites list
            cleaned_sites = []
            for site in potential_sites:
                # Remove trailing punctuation and whitespace
                site = re.sub(r'[\s\.,;:]+$', '', site).strip()
                
                # Skip if too short or common words
                if len(site) < 4:
                    continue
                    
                # Skip common section headers that aren't monument names
                if site.lower() in ['page', 'introduction', 'conclusion', 'history', 'overview', 
                                   'temple', 'stupa', 'square', 'contents', 'references']:
                    continue
                    
                # Normalize site name
                site = site.replace('(', '').replace(')', '')
                
                # Filter out patterns that are just building types with no name
                if site.lower() in ["temple", "stupa", "square", "durbar square", "monastery", 
                                   "palace", "chowk", "mandir", "monument", "pillar"]:
                    continue
                    
                cleaned_sites.append(site)
            
            # Remove duplicates while preserving order
            unique_sites = []
            for site in cleaned_sites:
                # Only add if not already in list and not too long
                if site not in unique_sites and len(site.split()) <= 5:
                    unique_sites.append(site)
            
            # If we found at least 2 potential sites from text analysis, return them directly
            if len(unique_sites) >= 2:
                return {
                    "contains_multiple_sites": True,
                    "site_names": unique_sites
                }
            
            # If direct text analysis didn't find enough sites, use LLM for deeper analysis
            prompt = f"""Analyze the following text about Nepalese heritage sites.
            
            1. Identify ALL distinct heritage sites, monuments, temples, stupas or durbar squares mentioned in the text.
            2. I need a comprehensive list - be thorough and identify even briefly mentioned sites.
            3. For each site, extract the exact name as it appears in the text.
            4. Return your analysis as JSON with this structure:
               {{
                 "contains_multiple_sites": true/false,
                 "site_names": ["Name 1", "Name 2", ...] (empty if no clear names can be identified)
               }}
            5. IMPORTANT: Look for section headings, capitalized monument names, and paragraphs that begin a new topic.
            6. BE COMPREHENSIVE - the document likely contains information about multiple different heritage sites.
            7. DO NOT limit yourself to just famous sites - include ALL heritage sites mentioned in the text.
            
            TEXT TO ANALYZE (first 10,000 characters):
            {text[:10000]}... 

            Additional text (if text is longer):
            {text[10000:20000] if len(text) > 10000 else ""}
            """
            
            response = completion(
                model=self.model_id,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a specialized analyzer for cultural heritage documents. Your task is to identify ALL heritage sites mentioned in a document, even if they're only briefly referenced."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if not isinstance(result, dict):
                return {"contains_multiple_sites": False, "site_names": []}
                
            # Ensure expected structure
            if "contains_multiple_sites" not in result:
                result["contains_multiple_sites"] = False
            if "site_names" not in result or not isinstance(result["site_names"], list):
                result["site_names"] = []
            
            # If we found site names through pattern matching but LLM didn't find them,
            # combine the results
            if unique_sites and (not result["site_names"] or len(unique_sites) > len(result["site_names"])):
                # Combine sites from pattern matching and LLM
                combined_sites = list(set(unique_sites + result["site_names"]))
                result["site_names"] = combined_sites
                result["contains_multiple_sites"] = len(combined_sites) > 1
                
            return result
            
        except Exception as e:
            print(f"Error analyzing text for multiple sites: {str(e)}")
            return {"contains_multiple_sites": False, "site_names": []}

    def structure_heritage_data(self, heritage_site: str, focus_monument: str = None) -> Optional[str]:
        """
        Structure the heritage site data using LiteLLM
        
        Args:
            heritage_site: Text containing heritage site information
            focus_monument: Optional specific monument to focus on if the text 
                          contains information about multiple monuments
        """
        # Modify prompt based on whether we're focusing on a specific monument
        focus_instruction = ""
        if focus_monument:
            focus_instruction = f"""
            IMPORTANT: The text may contain information about multiple heritage sites. 
            FOCUS ONLY on extracting information about '{focus_monument}'. 
            Ignore information about other monuments completely.
            """
        
        prompt = f"""Extract information about the Nepalese cultural heritage site from the following text.
        Format your response as a JSON object with the structure shown below.
        
        # IMPORTANT INSTRUCTIONS:
        1. Use the information provided in the input text. Don't generate information on your own.
        2. Focus on structuring the existing content with proper English spelling corrections.
        3. Don't cut or crop out the information passed to you.
        4. Make sure the information structured is not changed and it flows as is like passed.
        5. There is no character limit in the description key so pass all the information. Don't leave out anything.
        6. You can skip the parts that seem like self promotion of the channels.
        7. Return valid JSON format.
        8. ONLY include fields where information is explicitly available in the text.
        9. Leave fields empty (null) if no information is provided.
        10. DO NOT make up or hallucinate any information not present in the text.
        11. Use exact measurements, dates, and names as they appear in the text.
        12. If there are multiple entries (e.g., historical_events), create an array of objects.
        13. For any dates mentioned, preserve the original date format and calendar system.
        {focus_instruction}
        
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

    def save_to_file(self, structured_data: str, directory: str = None) -> tuple[bool, str]:
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
                return True, monument_name
            
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
                    return False, monument_name
            else:
                # New file, just write the data
                with open(filename, 'w', encoding='utf-8') as f:
                    # Write the JSON data
                    f.write(structured_data)
            
            return True, monument_name
            
        except Exception as e:
            print(f"Error saving data: {str(e)}")
            return False, ""

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
            
    def process_transcript_file(self, transcript_file: str, output_dir: str = None, update_tracking: bool = True) -> bool:
        """Process a single transcript file into structured data"""
        print(f"Processing transcript file: {transcript_file}")
        transcript = self.load_transcript(transcript_file)
        
        if not transcript:
            print(f"Failed to load transcript from {transcript_file}")
            return False
        
        # First analyze if the transcript contains multiple heritage sites
        print("Analyzing if transcript contains multiple heritage sites...")
        analysis = self.analyze_text_for_multiple_sites(transcript)
        
        # If multiple sites detected, process each separately
        if analysis["contains_multiple_sites"] and analysis["site_names"]:
            print(f"Detected information about multiple heritage sites: {', '.join(analysis['site_names'])}")
            success_count = 0
            
            for site_name in analysis["site_names"]:
                print(f"Processing information about: {site_name}")
                site_data = self.structure_heritage_data(transcript, focus_monument=site_name)
                
                if site_data:
                    success, _ = self.save_to_file(site_data, output_dir)
                    if success:
                        success_count += 1
                    else:
                        print(f"Failed to save structured data for {site_name}")
                else:
                    print(f"Failed to structure data for {site_name}")
            
            # Mark the transcript as processed if any site was successfully processed
            if success_count > 0 and update_tracking:
                update_transcript_tracking(os.path.basename(transcript_file))
            return success_count > 0
        else:
            # Process as a single site (original behavior)
            print(f"Processing transcript as a single heritage site")
            site_data = self.structure_heritage_data(transcript)
            
            if not site_data:
                print(f"Failed to structure transcript data from {transcript_file}")
                return False
                
            print("Transcript structured successfully")
            success, _ = self.save_to_file(site_data, output_dir)
            
            # Mark the transcript as processed if successful
            if success and update_tracking:
                update_transcript_tracking(os.path.basename(transcript_file))
                
            if success:
                print(f"Structured data saved to {output_dir or HERITAGE_SITES_DIR}")
                return True
            else:
                print(f"Failed to save structured data for {transcript_file}")
                return False
    
    def process_all_transcripts(self, transcripts_dir: str = TRANSCRIPTS_DIR, output_dir: str = None, only_unprocessed: bool = False) -> Dict[str, bool]:
        """Process all transcript files in the directory"""
        results = {}
        
        # List all transcript files
        if not os.path.exists(transcripts_dir):
            print(f"Transcripts directory not found: {transcripts_dir}")
            return results
        
        # Get all transcript files
        transcript_files = [os.path.join(transcripts_dir, f) for f in os.listdir(transcripts_dir) 
                          if (f.endswith('.txt') or f.endswith('.docx')) 
                          and not f.startswith('.')
                          and os.path.isfile(os.path.join(transcripts_dir, f))]
        
        if not transcript_files:
            print(f"No transcript files found in {transcripts_dir}")
            return results
        
        # Filter for only unprocessed transcripts if requested
        if only_unprocessed:
            processed_files = load_processed_transcripts()
            transcript_files = [file_path for file_path in transcript_files 
                              if os.path.basename(file_path) not in processed_files]
            print(f"Found {len(transcript_files)} unprocessed transcript files to process")
        else:
            print(f"Found {len(transcript_files)} transcript files to process")
        
        if not transcript_files:
            print("No unprocessed transcript files found")
            return results
        
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

def load_processed_transcripts() -> Dict[str, bool]:
    """Load the list of processed transcript files"""
    if not os.path.exists(TRANSCRIPT_TRACKING_FILE):
        return {}
    
    try:
        with open(TRANSCRIPT_TRACKING_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def update_transcript_tracking(transcript_filename: str) -> None:
    """Update the tracking file to mark a transcript as processed"""
    processed = load_processed_transcripts()
    processed[transcript_filename] = True
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(TRANSCRIPT_TRACKING_FILE), exist_ok=True)
    
    # Save the updated tracking data
    with open(TRANSCRIPT_TRACKING_FILE, 'w') as f:
        json.dump(processed, f, indent=2)
    
    print(f"Marked '{transcript_filename}' as processed in tracking file")

def main():
    """Process transcripts into structured data"""
    parser = argparse.ArgumentParser(description="Structure Heritage Site Transcripts")
    parser.add_argument('--transcript', type=str, help="Path to specific transcript file")
    parser.add_argument('--output-dir', type=str, default=HERITAGE_SITES_DIR, 
                        help="Directory to save structured data")
    parser.add_argument('--all', action='store_true', 
                        help="Process all transcript files in the transcripts directory")
    parser.add_argument('--sync', action='store_true',
                        help="Process only unprocessed transcript files and update tracking")
    
    args = parser.parse_args()
    structurer = HeritageDataStructurer()
    
    if args.sync:
        # Process only unprocessed transcript files
        print("Syncing: Processing only unprocessed transcript files...")
        structurer.process_all_transcripts(TRANSCRIPTS_DIR, args.output_dir, only_unprocessed=True)
    elif args.all:
        # Process all transcript files
        structurer.process_all_transcripts(TRANSCRIPTS_DIR, args.output_dir)
    elif args.transcript:
        # Process specific transcript file
        structurer.process_transcript_file(args.transcript, args.output_dir)
    else:
        # Default: Find the most recent transcript
        transcript_files = [os.path.join(TRANSCRIPTS_DIR, f) for f in os.listdir(TRANSCRIPTS_DIR) 
                          if (f.endswith('.txt') or f.endswith('.docx')) 
                          and not f.startswith('.')
                          and os.path.isfile(os.path.join(TRANSCRIPTS_DIR, f))]
        
        if not transcript_files:
            print(f"No transcript files found in {TRANSCRIPTS_DIR}")
            return
            
        transcript_file = max(transcript_files, key=os.path.getmtime)
        print(f"Using most recent transcript: {transcript_file}")
        structurer.process_transcript_file(transcript_file, args.output_dir)

if __name__ == "__main__":
    main()
