from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional, List, Dict


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
        filename = f"{filename}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for entry in transcript:
                    f.write(f"{entry['text']}\n")
            return True
        except Exception as e:
            print(f"Error saving transcript: {str(e)}")
            return False

def main(video_url, print_transcript=False):
    # Initialize downloader
    downloader = YouTubeTranscriptDownloader()
    
    # Get transcript
    transcript = downloader.get_transcript(video_url)
    if transcript:
        # Save transcript
        video_id = downloader.extract_video_id(video_url)
        if downloader.save_transcript(transcript, f"./data/transcripts/{video_id}"):
            print(f"Transcript saved successfully to {video_id}.txt")
            #Print transcript if True
            if print_transcript:
                # Print transcript
                for entry in transcript:
                    print(f"{entry['text']}")
        else:
            print("Failed to save transcript")
        
    else:
        print("Failed to get transcript")

if __name__ == "__main__":
    video_id = "https://www.youtube.com/watch?v=qUV3Gsy9mjw"
    transcript = main(video_id, print_transcript=True)
