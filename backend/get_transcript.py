from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional, List, Dict
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration
from backend.config import TRANSCRIPTS_DIR

class YouTubeTranscriptDownloader:
    def __init__(self, languages: List[str] = ["ne", "en", "en-US", "hi"]):
        self.languages = languages
        self.target_language = "en"  # Default translation target language

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL
        
        Args:
            url (str): YouTube URL
            
        Returns:
            Optional[str]: Video ID if found, None otherwise
        """
        if "v=" in url:
            return url.split("v=")[1][:11]
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1][:11]
        return None

    def get_transcript(self, video_id: str) -> Optional[List[Dict]]:
        """
        Download YouTube Transcript and translate if needed
        
        Args:
            video_id (str): YouTube video ID or URL
            
        Returns:
            Optional[List[Dict]]: Transcript if successful, None otherwise
        """
        # Extract video ID if full URL is provided
        if "youtube.com" in video_id or "youtu.be" in video_id:
            video_id = self.extract_video_id(video_id)
            
        if not video_id:
            print("Invalid video ID or URL")
            return None

        print(f"Downloading transcript for video ID: {video_id}")
        
        try:
            # Try to get transcript list for language detection and translation
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Step 1: Check if there's a manually created English transcript (highest priority)
            try:
                manual_en_transcript = transcript_list.find_manually_created_transcript(['en'])
                print("Found manually created English transcript")
                return manual_en_transcript.fetch()
            except Exception as e:
                print(f"No manually created English transcript available: {str(e)}")
            
            # Step 2: Check for manually created transcripts in other requested languages
            for lang in self.languages:
                if lang == 'en':
                    continue  # Already checked above
                try:
                    manual_transcript = transcript_list.find_manually_created_transcript([lang])
                    print(f"Found manually created transcript in {lang}")
                    
                    # Only translate if not in English
                    if manual_transcript.is_translatable:
                        print(f"Translating manually created transcript from {lang} to English...")
                        translated = manual_transcript.translate(self.target_language)
                        return translated.fetch()
                    else:
                        return manual_transcript.fetch()
                except Exception as e:
                    print(f"No manually created transcript in {lang}: {str(e)}")
            
            # Step 3: Check for automatically generated English transcript
            try:
                auto_en_transcript = transcript_list.find_generated_transcript(['en'])
                print("Found automatically generated English transcript")
                return auto_en_transcript.fetch()
            except Exception as e:
                print(f"No automatically generated English transcript available: {str(e)}")
            
            # Step 4: Check for automatically generated transcripts in other languages and translate
            for lang in self.languages:
                if lang == 'en':
                    continue  # Already checked above
                try:
                    auto_transcript = transcript_list.find_generated_transcript([lang])
                    print(f"Found automatically generated transcript in {lang}")
                    
                    # Only translate if not in English
                    if auto_transcript.is_translatable:
                        print(f"Translating automatically generated transcript from {lang} to English...")
                        translated = auto_transcript.translate(self.target_language)
                        return translated.fetch()
                    else:
                        return auto_transcript.fetch()
                except Exception as e:
                    print(f"No automatically generated transcript in {lang}: {str(e)}")
            
            # Step 5: Fallback to the default method which will use any available transcript
            print("Using fallback method to get transcript")
            return YouTubeTranscriptApi.get_transcript(video_id, languages=self.languages, preserve_formatting=True)
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return None

    def save_transcript(self, transcript: List[Dict], filename: str) -> bool:
        """
        Save transcript to file
        
        Args:
            transcript (List[Dict]): Transcript data
            filename (str): Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Make sure we're saving to the configured transcript directory
        if not os.path.dirname(filename):
            filename = os.path.join(TRANSCRIPTS_DIR, os.path.basename(filename))
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Add .txt extension if not present
        if not filename.endswith('.txt'):
            filename = f"{filename}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for entry in transcript:
                    f.write(f"{entry['text']}\n")
            print(f"Transcript saved to: {filename}")
            return True
        except Exception as e:
            print(f"Error saving transcript: {str(e)}")
            return False

def main(video_url, print_transcript=False):
    """Process and save a transcript from a YouTube URL"""
    # Initialize downloader
    downloader = YouTubeTranscriptDownloader()
    
    # Get transcript
    transcript = downloader.get_transcript(video_url)
    if transcript:
        # Save transcript to configured directory
        video_id = downloader.extract_video_id(video_url)
        file_path = os.path.join(TRANSCRIPTS_DIR, video_id)
        
        if downloader.save_transcript(transcript, file_path):
            print(f"Transcript saved successfully to {file_path}.txt")
            
            # Print transcript if requested
            if print_transcript:
                print("\nTranscript content:")
                for entry in transcript:
                    print(f"{entry['text']}")
        else:
            print("Failed to save transcript")
    else:
        print("Failed to get transcript")

if __name__ == "__main__":
    # If run directly, get video from command line argument or use default
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
    else:
        video_url = "https://www.youtube.com/watch?v=qUV3Gsy9mjw"  # Default video
    
    # Use second argument as flag for printing transcript (if provided)
    print_transcript = len(sys.argv) > 2 and sys.argv[2].lower() in ['true', 'yes', 'y', '1']
    
    main(video_url, print_transcript=print_transcript)
