import speech_recognition as sr
import pydub
import tempfile
import os
import streamlit as st
from typing import Optional, Dict
import time

class SpeechHandler:
    """Handles speech-to-text and text-to-speech functionality"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.microphone_available = False
        
        # Try to initialize microphone - gracefully handle if not available
        try:
            self.microphone = sr.Microphone()
            self.microphone_available = True
        except OSError as e:
            print(f"Warning: No audio input device available - {str(e)}")
            print("Voice features will be disabled. Audio file upload will still work.")
        except Exception as e:
            print(f"Warning: Could not initialize microphone - {str(e)}")
        
        # Configure recognizer settings
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.operation_timeout = None
        
        # Supported audio formats
        self.supported_formats = ['.wav', '.mp3', '.flac', '.m4a', '.ogg']
        
    def calibrate_microphone(self) -> bool:
        """Calibrate microphone for ambient noise"""
        if not self.microphone_available:
            st.error("No microphone available for calibration")
            return False
            
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            return True
        except Exception as e:
            st.error(f"Error calibrating microphone: {str(e)}")
            return False
    
    def record_audio(self, duration: int = 5) -> Optional[sr.AudioData]:
        """Record audio from microphone"""
        if not self.microphone_available:
            st.error("No microphone available for recording")
            return None
            
        try:
            with self.microphone as source:
                st.info("🎤 Listening... Speak now!")
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Record audio
                audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
                return audio
        except sr.WaitTimeoutError:
            st.warning("⏰ Recording timeout. Please try again.")
            return None
        except Exception as e:
            st.error(f"Error recording audio: {str(e)}")
            return None
    
    def listen_for_speech(self, timeout: int = 5) -> str:
        """Listen for speech input and return transcribed text"""
        if not self.microphone_available:
            st.error("No microphone available for voice input")
            return ""
            
        try:
            with self.microphone as source:
                st.info("🎤 Listening... Speak now!")
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
            # Clear the listening message
            st.success("✅ Audio captured! Processing...")
            
            # Recognize speech using Google's API
            text = self.recognizer.recognize_google(audio)
            return text
            
        except sr.WaitTimeoutError:
            st.warning("⏰ No speech detected. Please try again.")
            return ""
        except sr.UnknownValueError:
            st.warning("🤔 Could not understand the audio. Please try again.")
            return ""
        except sr.RequestError as e:
            st.error(f"❌ Speech recognition service error: {e}")
            return ""
        except Exception as e:
            st.error(f"❌ Error during speech recognition: {str(e)}")
            return ""
    
    def convert_audio_file(self, audio_file_path: str) -> str:
        """Convert audio file to WAV format for processing"""
        try:
            # Get file extension
            file_ext = os.path.splitext(audio_file_path)[1].lower()
            
            if file_ext == '.wav':
                return audio_file_path
            
            # Convert to WAV using pydub
            if file_ext == '.mp3':
                audio = pydub.AudioSegment.from_mp3(audio_file_path)
            elif file_ext == '.flac':
                audio = pydub.AudioSegment.from_file(audio_file_path, "flac")
            elif file_ext == '.m4a':
                audio = pydub.AudioSegment.from_file(audio_file_path, "m4a")
            elif file_ext == '.ogg':
                audio = pydub.AudioSegment.from_ogg(audio_file_path)
            else:
                raise ValueError(f"Unsupported audio format: {file_ext}")
            
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                audio.export(temp_file.name, format="wav")
                return temp_file.name
                
        except Exception as e:
            st.error(f"Error converting audio file: {str(e)}")
            return None
    
    def transcribe_audio(self, audio_data: sr.AudioData = None, audio_file_path: str = None) -> Dict:
        """Transcribe audio to text using multiple recognition services"""
        if audio_data is None and audio_file_path is None:
            return {"success": False, "error": "No audio data provided"}
        
        # If audio file is provided, load it
        if audio_file_path:
            try:
                # Convert to WAV if necessary
                wav_path = self.convert_audio_file(audio_file_path)
                if not wav_path:
                    return {"success": False, "error": "Failed to convert audio file"}
                
                with sr.AudioFile(wav_path) as source:
                    audio_data = self.recognizer.record(source)
                
                # Clean up temporary file if created
                if wav_path != audio_file_path and os.path.exists(wav_path):
                    os.unlink(wav_path)
                    
            except Exception as e:
                return {"success": False, "error": f"Error loading audio file: {str(e)}"}
        
        # Try multiple recognition services
        results = {}
        
        # Google Speech Recognition (free)
        try:
            text = self.recognizer.recognize_google(audio_data)
            results['google'] = {
                'text': text,
                'confidence': 0.9,  # Google doesn't provide confidence scores for free tier
                'success': True
            }
        except sr.UnknownValueError:
            results['google'] = {
                'text': '',
                'confidence': 0.0,
                'success': False,
                'error': 'Could not understand audio'
            }
        except sr.RequestError as e:
            results['google'] = {
                'text': '',
                'confidence': 0.0,
                'success': False,
                'error': f'API request failed: {str(e)}'
            }
        
        # Sphinx (offline recognition as fallback)
        try:
            text = self.recognizer.recognize_sphinx(audio_data)
            results['sphinx'] = {
                'text': text,
                'confidence': 0.7,  # Sphinx typically has lower accuracy
                'success': True
            }
        except sr.UnknownValueError:
            results['sphinx'] = {
                'text': '',
                'confidence': 0.0,
                'success': False,
                'error': 'Could not understand audio'
            }
        except Exception as e:
            results['sphinx'] = {
                'text': '',
                'confidence': 0.0,
                'success': False,
                'error': f'Sphinx recognition failed: {str(e)}'
            }
        
        # Determine best result
        best_result = None
        highest_confidence = 0
        
        for service, result in results.items():
            if result['success'] and result['confidence'] > highest_confidence:
                best_result = result
                best_result['service'] = service
                highest_confidence = result['confidence']
        
        if best_result:
            return {
                'success': True,
                'text': best_result['text'],
                'confidence': best_result['confidence'],
                'service': best_result['service'],
                'all_results': results
            }
        else:
            return {
                'success': False,
                'error': 'All recognition services failed',
                'all_results': results
            }
    
    def process_uploaded_audio(self, uploaded_file) -> Dict:
        """Process uploaded audio file"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name
            
            # Transcribe the audio
            result = self.transcribe_audio(audio_file_path=temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing uploaded audio: {str(e)}'
            }
    
    def get_microphone_info(self) -> Dict:
        """Get information about available microphones"""
        if not self.microphone_available:
            return {
                'success': False,
                'error': 'No microphones available',
                'microphones': [],
                'default_index': None
            }
            
        try:
            microphones = []
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                microphones.append({
                    'index': index,
                    'name': name
                })
            
            return {
                'success': True,
                'microphones': microphones,
                'default_index': self.microphone.device_index if self.microphone else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error getting microphone info: {str(e)}',
                'microphones': []
            }
    
    def test_microphone(self) -> Dict:
        """Test microphone functionality"""
        if not self.microphone_available:
            return {
                'success': False,
                'error': 'No microphone available for testing'
            }
            
        try:
            # Calibrate microphone
            if not self.calibrate_microphone():
                return {
                    'success': False,
                    'error': 'Failed to calibrate microphone'
                }
            
            # Record a short sample
            st.info("Testing microphone... Say something!")
            audio = self.record_audio(duration=3)
            
            if audio is None:
                return {
                    'success': False,
                    'error': 'Failed to record audio'
                }
            
            # Try to transcribe
            result = self.transcribe_audio(audio_data=audio)
            
            return {
                'success': True,
                'test_transcription': result,
                'message': 'Microphone test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Microphone test failed: {str(e)}'
            }
    
    def create_voice_interface(self):
        """Create clean voice interface"""
        st.markdown("#### 🎤 Voice Input")
        
        # Show microphone status
        if not self.microphone_available:
            st.warning("⚠️ No microphone available. You can upload audio files instead.")
        
        # Two columns for record and upload
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Record Audio**")
            if self.microphone_available:
                if st.button("🎤 Start Recording", type="primary"):
                    with st.spinner("Recording for 5 seconds..."):
                        audio = self.record_audio(duration=5)
                        if audio:
                            with st.spinner("Converting to text..."):
                                result = self.transcribe_audio(audio_data=audio)
                                if result['success']:
                                    st.success(f"Transcribed: {result['text']}")
                                    st.session_state['voice_query'] = result['text']
                                    return result['text']
                                else:
                                    st.error("Failed to transcribe audio")
            else:
                st.info("Recording disabled - no microphone")
        
        with col2:
            st.markdown("**Upload Audio File**")
            uploaded_audio = st.file_uploader(
                "Choose audio file",
                type=['wav', 'mp3', 'flac', 'm4a', 'ogg'],
                label_visibility="collapsed"
            )
            
            if uploaded_audio:
                st.audio(uploaded_audio)
                if st.button("📝 Transcribe", type="primary"):
                    with st.spinner("Processing..."):
                        result = self.process_uploaded_audio(uploaded_audio)
                        if result['success']:
                            st.success(f"Transcribed: {result['text']}")
                            st.session_state['voice_query'] = result['text']
                            return result['text']
                        else:
                            st.error("Failed to transcribe audio")
        
        return st.session_state.get('voice_query', "")
