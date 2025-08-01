import streamlit as st
import speech_recognition as sr
import io
import tempfile
import os
from typing import Optional, Tuple
import wave
import threading
import time

class SpeechHandler:
    """Handle speech-to-text conversion for StudyMate"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_recording = False
        
        # Try to initialize microphone, but don't fail if not available
        try:
            self.microphone = sr.Microphone()
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except Exception as e:
            st.warning(f"⚠️ Microphone not available: {str(e)}. File upload will still work.")
            self.microphone = None
    
    def record_audio(self, duration: int = 5) -> Optional[sr.AudioData]:
        """Record audio from microphone"""
        if not self.microphone:
            st.error("❌ Microphone not available. Please use file upload instead.")
            return None
            
        try:
            with self.microphone as source:
                st.info(f"🎤 Recording for {duration} seconds... Speak now!")
                audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
                return audio
        except sr.WaitTimeoutError:
            st.error("⏰ Recording timeout. Please try again.")
            return None
        except Exception as e:
            st.error(f"❌ Recording error: {str(e)}")
            return None
    
    def convert_speech_to_text(self, audio_data: sr.AudioData) -> Optional[str]:
        """Convert audio data to text using Google Speech Recognition"""
        if not audio_data:
            return None
            
        try:
            # Try Google Speech Recognition first (free)
            text = self.recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            st.error("🔇 Could not understand the audio. Please speak clearly and try again.")
            return None
        except sr.RequestError as e:
            st.error(f"❌ Speech recognition service error: {str(e)}")
            return None
    
    def process_uploaded_audio(self, uploaded_file) -> Optional[str]:
        """Process uploaded audio file and convert to text"""
        try:
            # Save uploaded file temporarily
            file_extension = uploaded_file.name.split('.')[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Load audio file
            with sr.AudioFile(tmp_file_path) as source:
                audio = self.recognizer.record(source)
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            # Convert to text
            return self.convert_speech_to_text(audio)
            
        except Exception as e:
            st.error(f"❌ Error processing audio file: {str(e)}")
            return None
    
    def create_voice_input_ui(self) -> Optional[str]:
        """Create the voice input UI components"""
        st.markdown("### 🎤 Voice Input")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Record from Microphone:**")
            if self.microphone:
                duration = st.slider("Recording duration (seconds)", 3, 15, 5)
                
                if st.button("🎤 Start Recording", key="record_btn"):
                    with st.spinner("Recording..."):
                        audio_data = self.record_audio(duration)
                        if audio_data:
                            with st.spinner("Converting speech to text..."):
                                text = self.convert_speech_to_text(audio_data)
                                if text:
                                    st.success(f"✅ Recognized: {text}")
                                    return text
            else:
                st.info("🎤 Microphone not available. Please use file upload.")
        
        with col2:
            st.markdown("**Upload Audio File:**")
            uploaded_audio = st.file_uploader(
                "Choose an audio file",
                type=['wav', 'mp3', 'flac', 'm4a', 'ogg'],
                key="audio_upload"
            )
            
            if uploaded_audio is not None:
                st.audio(uploaded_audio, format='audio/wav')
                
                if st.button("🔄 Convert to Text", key="convert_btn"):
                    with st.spinner("Processing audio file..."):
                        text = self.process_uploaded_audio(uploaded_audio)
                        if text:
                            st.success(f"✅ Recognized: {text}")
                            return text
        
        return None
    
    def create_compact_voice_input(self) -> Optional[str]:
        """Create a compact voice input button for the main interface"""
        if self.microphone:
            if st.button("🎤", help="Click to record voice input", key="voice_input_compact"):
                with st.spinner("Recording for 5 seconds..."):
                    audio_data = self.record_audio(5)
                    if audio_data:
                        with st.spinner("Converting speech to text..."):
                            text = self.convert_speech_to_text(audio_data)
                            if text:
                                return text
        else:
            st.button("🎤", help="Microphone not available - use file upload", key="voice_disabled", disabled=True)
        return None
