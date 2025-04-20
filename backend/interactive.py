import os
import base64
import tempfile
from gtts import gTTS
import time
from typing import Optional

class AudioGenerator:
    """
    Class to generate audio files for interactive learning exercises.
    Uses gTTS (Google Text-to-Speech) to create spoken audio from text.
    """
    
    def __init__(self, language="en", cache_dir=None):
        """
        Initialize the AudioGenerator with language settings.
        
        Args:
            language (str): Language code for speech (default: 'en')
            cache_dir (str, optional): Directory to cache audio files
        """
        self.language = language
        
        # Set up caching directory
        if cache_dir is None:
            # Get project root directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            self.cache_dir = os.path.join(project_root, "data", "audio_cache")
        else:
            self.cache_dir = cache_dir
            
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def generate_audio(self, text: str, filename: Optional[str] = None) -> str:
        """
        Generate audio file from text and return the file path.
        
        Args:
            text (str): Text to convert to speech
            filename (str, optional): Custom filename for the audio file
            
        Returns:
            str: Path to the generated audio file
        """
        if not text:
            raise ValueError("Text cannot be empty for audio generation")
        
        # Create a filename based on text hash if not provided
        if filename is None:
            # Use first 10 characters + hash to create unique filename
            text_preview = text[:10].replace(" ", "_")
            text_hash = str(abs(hash(text)) % 10000)
            filename = f"{text_preview}_{text_hash}.mp3"
        
        # Ensure filename has .mp3 extension
        if not filename.endswith('.mp3'):
            filename += '.mp3'
            
        file_path = os.path.join(self.cache_dir, filename)
        
        # Check if file already exists in cache
        if os.path.exists(file_path):
            return file_path
            
        try:
            # Generate audio using gTTS
            tts = gTTS(text=text, lang=self.language, slow=False)
            tts.save(file_path)
            return file_path
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            raise
    
    def generate_audio_base64(self, text: str) -> str:
        """
        Generate audio and return as base64 encoded string for web embedding.
        
        Args:
            text (str): Text to convert to speech
            
        Returns:
            str: Base64 encoded audio data with mime type prefix
        """
        # First generate the audio file
        file_path = self.generate_audio(text)
        
        # Read file and convert to base64
        with open(file_path, "rb") as audio_file:
            audio_data = audio_file.read()
            
        # Encode to base64 and add prefix
        encoded_data = base64.b64encode(audio_data).decode('utf-8')
        return f"data:audio/mp3;base64,{encoded_data}"
    
    def generate_temp_audio(self, text: str) -> str:
        """
        Generate a temporary audio file that will be automatically deleted.
        Useful for one-time playback.
        
        Args:
            text (str): Text to convert to speech
            
        Returns:
            str: Path to the temporary audio file
        """
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
            
        # Generate audio
        tts = gTTS(text=text, lang=self.language, slow=False)
        tts.save(temp_path)
        
        return temp_path
    
    def clear_cache(self):
        """Clear all cached audio files."""
        if os.path.exists(self.cache_dir):
            for file in os.listdir(self.cache_dir):
                if file.endswith(".mp3"):
                    os.remove(os.path.join(self.cache_dir, file))