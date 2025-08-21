import speech_recognition as sr
import io
import tempfile
import os
from typing import Optional, Tuple
import wave
import threading
import time
import logging

class SpeechHandler:
    """Handle speech-to-text conversion for StudyMate"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_recording = False
        
        # Get Google API key from environment
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        # Try to initialize microphone, but don't fail if not available
        try:
            self.microphone = sr.Microphone()
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            logging.info("Microphone initialized successfully")
        except Exception as e:
            logging.warning(f"Microphone not available: {str(e)}. File upload will still work.")
            self.microphone = None
    
    def record_audio(self, duration: int = 5) -> Optional[sr.AudioData]:
        """Record audio from microphone"""
        if not self.microphone:
            logging.error("Microphone not available. Please use file upload instead.")
            return None
            
        try:
            with self.microphone as source:
                logging.info(f"Recording for {duration} seconds...")
                audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
                return audio
        except sr.WaitTimeoutError:
            logging.error("Recording timeout. Please try again.")
            return None
        except Exception as e:
            logging.error(f"Recording error: {str(e)}")
            return None
    
    def convert_speech_to_text(self, audio_data: sr.AudioData) -> Optional[str]:
        """Convert audio data to text using Google Speech Recognition"""
        if not audio_data:
            return None
            
        try:
            # Use Google Speech Recognition with API key if available for better reliability
            if self.google_api_key:
                text = self.recognizer.recognize_google(audio_data, key=self.google_api_key)
                logging.info("Using enhanced Google Speech API")
            else:
                # Fallback to free Google Speech Recognition
                text = self.recognizer.recognize_google(audio_data)
                logging.info("Using free Google Speech Recognition")
            return text
        except sr.UnknownValueError:
            logging.error("Could not understand the audio. Please speak clearly and try again.")
            return None
        except sr.RequestError as e:
            logging.error(f"Speech recognition service error: {str(e)}")
            return None
    
    def process_uploaded_audio(self, uploaded_file_content: bytes, filename: str) -> Optional[str]:
        """Process uploaded audio file and convert to text"""
        try:
            # Save uploaded file temporarily
            file_extension = filename.split('.')[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                tmp_file.write(uploaded_file_content)
                tmp_file_path = tmp_file.name
            
            # Load audio file
            with sr.AudioFile(tmp_file_path) as source:
                audio = self.recognizer.record(source)
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            # Convert to text
            return self.convert_speech_to_text(audio)
            
        except Exception as e:
            logging.error(f"Error processing audio file: {str(e)}")
            return None
    
    def is_microphone_available(self) -> bool:
        """Check if microphone is available"""
        return self.microphone is not None
    
    def record_and_convert(self, duration: int = 5) -> Optional[str]:
        """Record audio and convert to text in one step"""
        audio_data = self.record_audio(duration)
        if audio_data:
            return self.convert_speech_to_text(audio_data)
        return None
