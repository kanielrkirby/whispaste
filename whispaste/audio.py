"""
Audio Engine: Recording and Transcription logic.
Note: Optimized for instant recording start.
"""
import os
import wave
import io
from typing import Optional
from .config import CONFIG
from .system import System

class AudioEngine:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.buffer = []
        
    def record_until_stop(self, check_stop_fn):
        """
        Records audio until check_stop_fn returns True.
        Imports and starts recording as fast as possible.
        """
        # Import at call time for fastest possible startup
        import sounddevice as sd
        import numpy as np
        
        def callback(indata, frames, time, status):
            self.buffer.append(indata.copy())
            
        # Start recording immediately - PortAudio init happens here
        with sd.InputStream(samplerate=self.sample_rate, channels=1, callback=callback):
            while not check_stop_fn():
                sd.sleep(50)
                
        if not self.buffer:
            return None
        return np.concatenate(self.buffer)

    def transcribe(self, audio_data, post_prompt=None, post_model=None) -> Optional[str]:
        """
        Sends audio data to OpenAI Whisper API.
        """
        if audio_data is None: return None
        
        CONFIG.load_env()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            System.notify("Error: OPENAI_API_KEY not found")
            return None

        # Lazy Import: OpenAI client is heavy
        import numpy as np
        from openai import OpenAI
        
        # Convert numpy array to WAV in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            # Normalize and convert to 16-bit PCM
            wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
        wav_buffer.seek(0)
        wav_buffer.name = "audio.wav" 

        client = OpenAI(api_key=api_key)
        
        try:
            System.notify("Transcribing...")
            transcript = client.audio.transcriptions.create(
                model='gpt-4o-mini-transcribe', # Using the optimized model
                file=wav_buffer,
                response_format='text'
            )
            text = str(transcript).strip()
            
            # Optional Post-Processing
            if post_prompt and text:
                System.notify("Refining text...")
                completion = client.chat.completions.create(
                    model=post_model or 'gpt-4o-mini',
                    messages=[
                        {'role': 'system', 'content': post_prompt},
                        {'role': 'user', 'content': text}
                    ]
                )
                text = completion.choices[0].message.content.strip()
                
            return text
        except Exception as e:
            System.notify(f"API Error: {str(e)}")
            System.log(f"API Error: {e}")
            return None
